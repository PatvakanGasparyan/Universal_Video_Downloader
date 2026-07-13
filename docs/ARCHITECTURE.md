# 🏗️ Architecture

> A deep dive into how **Universal Video Downloader** is built, with Mermaid diagrams that render natively on GitHub.

## 📑 Contents

- [System Architecture](#system-architecture)
- [Request Flow](#request-flow)
- [Component Diagram](#component-diagram)
- [Sequence Diagram](#sequence-diagram)
- [Download Pipeline](#download-pipeline)
- [Cookie Authentication Flow](#cookie-authentication-flow)
- [Error Handling Flow](#error-handling-flow)
- [Configuration Flow](#configuration-flow)
- [Application Startup Flow](#application-startup-flow)
- [Data Flow](#data-flow)
- [Class Diagram](#class-diagram)
- [Docker Architecture](#docker-architecture)
- [AWS Deployment](#aws-deployment)
- [Network Flow](#network-flow)
- [Folder Structure](#folder-structure)

---

## System Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Client"]
        B[Browser<br/>Alpine.js UI]
    end

    subgraph Server["🐳 Application Server"]
        direction TB
        N[Nginx<br/>optional reverse proxy]
        subgraph FastAPI["⚡ FastAPI"]
            R[REST Routes]
            WS[WebSocket /ws/download]
            MW[Middleware:<br/>CORS · GZip · Rate limit · Security headers]
        end
        DM[Download Manager<br/>async queue]
        YS[yt-dlp Service<br/>cookie fallback]
        DB[(SQLite<br/>history + settings)]
        FS[/Downloads dir/]
    end

    subgraph External["🌍 External"]
        SITES[Video sites<br/>YouTube, TikTok, …]
        FF[FFmpeg]
        S3[(AWS S3)]
    end

    B -->|HTTPS| N --> MW --> R
    B -.->|WebSocket| WS
    R --> DM --> YS --> SITES
    YS --> FF
    DM --> DB
    DM --> FS
    FS -.optional.-> S3
    WS --- DM
```

---

## Request Flow

```mermaid
flowchart LR
    U([User]) --> UI[Frontend]
    UI -->|POST /api/info| INFO[Info route]
    UI -->|POST /api/download| DL[Download route]
    INFO --> CACHE{Cached?}
    CACHE -->|yes| RESP1[Return metadata]
    CACHE -->|no| YT1[yt-dlp extract]
    YT1 --> RESP1
    DL --> Q[Enqueue job]
    Q --> WSc[WebSocket progress]
    WSc --> U
```

---

## Component Diagram

```mermaid
flowchart TB
    subgraph API["API Layer (backend/api)"]
        routes[routes/*]
        deps[deps.py]
        middleware[middleware.py]
    end
    subgraph SVC["Service Layer (backend/services)"]
        ytdlp[ytdlp_service]
        manager[download_manager]
        cookies[cookies]
        exceptions[exceptions]
        history[history_service]
        cache[metadata_cache]
        s3[s3_service]
        security[security]
    end
    subgraph DATA["Data Layer (backend/models, database)"]
        schemas[schemas]
        session[session]
        migrations[migrations]
    end

    routes --> deps --> SVC
    manager --> ytdlp --> cookies
    ytdlp --> exceptions
    manager --> history --> session
    manager --> s3
    routes --> schemas
    ytdlp --> security
```

---

## Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant F as Frontend
    participant A as FastAPI
    participant M as DownloadManager
    participant Y as yt-dlp Service
    participant DB as SQLite
    participant W as WebSocket

    U->>F: Paste URL, Analyze
    F->>A: POST /api/info
    A->>Y: extract_info()
    Y-->>A: VideoMetadata
    A-->>F: JSON (formats)
    U->>F: Select quality, Download
    F->>A: POST /api/download
    A->>M: enqueue()
    M->>DB: create history record
    A-->>F: { download_id }
    F->>W: connect ?download_id
    M->>Y: download() (thread)
    loop progress hooks
        Y-->>M: {downloaded, total, speed}
        M-->>W: DownloadProgress
        W-->>F: live UI update
    end
    M->>DB: mark completed
    M-->>W: status=completed
```

---

## Download Pipeline

```mermaid
flowchart TD
    Start([enqueue]) --> Val[Validate + sanitize URL]
    Val --> Dup{Duplicate<br/>in-flight?}
    Dup -->|yes| Reuse[Reuse existing download_id]
    Dup -->|no| Queue[Add to PriorityQueue]
    Queue --> Sem{Semaphore<br/>slot free?}
    Sem -->|wait| Sem
    Sem -->|acquire| Run[Run download in thread]
    Run --> Hook[Progress hooks → WebSocket]
    Run --> Done{Success?}
    Done -->|yes| S3{S3 enabled?}
    S3 -->|yes| Up[Upload + cleanup local]
    S3 -->|no| Save[Keep local file]
    Up --> Complete[Mark COMPLETED]
    Save --> Complete
    Done -->|no| Err[Classify error + cleanup partials]
    Err --> Failed[Mark FAILED / CANCELLED]
    Complete --> End([release semaphore])
    Failed --> End
    Reuse --> End
```

---

## Cookie Authentication Flow

```mermaid
flowchart TD
    A[Start extraction] --> Anon[Try anonymous]
    Anon --> C1{Auth error?}
    C1 -->|no| OK[✅ Success]
    C1 -->|yes| BR{COOKIES_FROM_BROWSER?}
    BR -->|true| Chrome[Try chrome] --> C2{OK?}
    C2 -->|no| Chromium[Try chromium] --> C3{OK?}
    C3 -->|no| Edge[Try edge] --> C4{OK?}
    C4 -->|no| Firefox[Try firefox] --> C5{OK?}
    C2 -->|yes| OK
    C3 -->|yes| OK
    C4 -->|yes| OK
    C5 -->|yes| OK
    C5 -->|no| File
    BR -->|false| File[Try cookies.txt]
    File --> C6{OK?}
    C6 -->|yes| OK
    C6 -->|no| Fail[🚫 youtube_auth_required<br/>+ solution hint]
```

---

## Error Handling Flow

```mermaid
flowchart TD
    E[yt-dlp / runtime exception] --> Classify[classify_ytdlp_error]
    Classify --> T{Category}
    T -->|bot / sign-in| Auth[AuthRequiredError · 401]
    T -->|private / 404| Unavail[VideoUnavailableError · 404]
    T -->|country block| Geo[GeoRestrictedError · 451]
    T -->|429| Rate[RateLimitedError · 429]
    T -->|unsupported| Uns[UnsupportedURLError · 400]
    T -->|timeout| Net[NetworkError · 502]
    T -->|other| Gen[DownloaderError · 422]
    Auth --> Env[Structured JSON envelope]
    Unavail --> Env
    Geo --> Env
    Rate --> Env
    Uns --> Env
    Net --> Env
    Gen --> Env
    Env --> Log[[Log raw debug server-side only]]
    Env --> Client[Client receives<br/>success/error/message/solution]
```

---

## Configuration Flow

```mermaid
flowchart LR
    ENV[.env / env vars] --> S[Settings pydantic-settings]
    CM[k8s ConfigMap] --> ENV
    SEC[k8s Secret] --> ENV
    S --> APP[App components]
    UI[Settings page] --> DB[(app_settings row)]
    DB --> APP
```

---

## Application Startup Flow

```mermaid
flowchart TD
    Boot([uvicorn start]) --> Log[setup_logging]
    Log --> Init[init_db + migrations]
    Init --> Mgr[download_manager.start]
    Mgr --> Ready[Serve routes + WS]
    Ready --> Shutdown{SIGTERM?}
    Shutdown -->|yes| Drain[Cancel in-flight + drain tasks]
    Drain --> Stop([graceful shutdown])
```

---

## Data Flow

```mermaid
flowchart LR
    URL[Video URL] --> Meta[Metadata extract]
    Meta --> Cache[(Metadata cache)]
    Meta --> Choose[User picks format]
    Choose --> Job[Download job]
    Job --> Bytes[Media bytes]
    Bytes --> FF[FFmpeg merge/convert]
    FF --> File[Output file]
    File --> Hist[(History record)]
    File --> S3[(S3, optional)]
```

---

## Class Diagram

```mermaid
classDiagram
    class DownloaderError {
        +str error
        +str message
        +str solution
        +int http_status
        +str debug
        +to_dict() dict
    }
    class AuthRequiredError
    class VideoUnavailableError
    class NetworkError
    class RateLimitedError
    DownloaderError <|-- AuthRequiredError
    DownloaderError <|-- VideoUnavailableError
    DownloaderError <|-- NetworkError
    DownloaderError <|-- RateLimitedError

    class YtDlpService {
        +extract_info(url) VideoMetadata
        +download(...) Path
        -_cookie_strategies() list
        -_execute_with_fallback()
    }
    class DownloadManager {
        +enqueue() str
        +pause() bool
        +resume() bool
        +cancel() bool
        -_run_download()
    }
    DownloadManager --> YtDlpService
    YtDlpService ..> DownloaderError
```

---

## Docker Architecture

```mermaid
flowchart TB
    subgraph Build["Multi-stage build"]
        B1[builder<br/>python:3.13-slim + gcc]
        B2[final<br/>python:3.13-slim + ffmpeg]
        B1 -->|copy /root/.local| B2
    end

    subgraph Compose["docker-compose"]
        APP[app :8000]
        REDIS[(redis · profile queue)]
        NGINX[nginx · profile proxy :80/:443]
        NGINX --> APP
    end

    subgraph Volumes["Persistent volumes"]
        V1[/data — SQLite + cookies/]
        V2[/backend/downloads/]
        V3[/logs/]
    end

    B2 --> APP
    APP --- V1
    APP --- V2
    APP --- V3
```

---

## AWS Deployment

```mermaid
flowchart TB
    Dev[Developer] -->|git push master| GH[GitHub]
    GH --> GA[GitHub Actions]
    GA -->|build + push| GHCR[(GHCR image)]
    GA -->|SSH deploy| EC2

    subgraph VPC["AWS VPC 10.20.0.0/16"]
        subgraph Subnet["Public subnet"]
            EC2[EC2 Ubuntu · k3s]
        end
        SG[Security Group<br/>22 + 8000]
    end

    IAM[IAM Role] --> EC2
    EC2 -->|pull| GHCR
    EC2 -->|IAM creds| S3[(S3 bucket)]
    User([User]) -->|:8000| SG --> EC2
```

---

## Network Flow

```mermaid
flowchart LR
    User([User]) -->|TCP 8000| SG[EC2 Security Group]
    SG --> Host[EC2 host]
    Host --> K3S[k3s NodePort/Service]
    K3S --> Pod[uvd-backend pod :8000]
    Pod -->|HTTPS 443| Sites[Video sites]
    Pod -->|HTTPS 443| S3[(S3)]
```

---

## Folder Structure

```mermaid
flowchart TD
    Root[universal-video-downloader] --> BE[backend]
    Root --> FE[frontend]
    Root --> TF[terraform]
    Root --> K8S[k8s]
    Root --> DOCS[docs]
    Root --> TESTS[tests]
    BE --> api
    BE --> services
    BE --> models
    BE --> database
    BE --> config
    BE --> websocket
    FE --> html
    FE --> css
    FE --> js
    FE --> localization
```

See the full annotated tree in the [README](../README.md#-project-structure).
