# Universal Video Downloader

A modern, production-quality, open-source web application for downloading videos from hundreds of supported websites via [yt-dlp](https://github.com/yt-dlp/yt-dlp).

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Screenshots

> Placeholder — run the app locally and add screenshots to `docs/screenshots/`

| Main Page | Download Progress | History |
|-----------|-------------------|---------|
| _Coming soon_ | _Coming soon_ | _Coming soon_ |

## Features

- **Universal support** — Every website yt-dlp legally supports (YouTube, TikTok, Instagram, Vimeo, Twitch, and hundreds more)
- **Modern UI** — Glassmorphism design, animated gradients, dark/light mode, fully responsive
- **Format selection** — Video (8K–360p) and audio (MP3, AAC, M4A, FLAC, WAV, OGG) in MP4, MKV, WEBM, AVI, MOV
- **Live progress** — WebSocket-powered real-time download progress with speed, ETA, and stage tracking
- **Download queue** — Pause, resume, cancel, and priority support with configurable concurrency
- **History** — Search, favorites, delete, and re-download from history
- **Multi-language** — English, Русский, Հայերեն with instant switching
- **Settings** — Default quality, format, folder, theme, FFmpeg path, and more
- **Security** — Rate limiting, input validation, path sanitization, security headers
- **Docker ready** — One-command deployment with Docker Compose

## Default Ports

| Service | Port | Environment Variable |
|---------|------|---------------------|
| Backend (FastAPI) | 8000 | `BACKEND_PORT` |
| Frontend (served by backend) | 8000 | `FRONTEND_PORT` (reference) |
| WebSocket | 8000/ws/download | — |
| Redis (optional) | 6379 | `REDIS_URL` |
| Nginx (optional) | 80 / 443 | — |

## Requirements

- **Python** 3.13+
- **FFmpeg** — Required for format merging and conversion
- **yt-dlp** — Installed via pip (included in requirements.txt)

### Installing FFmpeg

**Windows (winget):**
```powershell
winget install Gyan.FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/your-org/universal-video-downloader.git
cd universal-video-downloader
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 2. Run the development server

```bash
python scripts/run_dev.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### 3. Docker deployment

```bash
docker compose up -d
```

With Nginx reverse proxy:
```bash
docker compose --profile proxy up -d
```

## Environment Variables

Copy `.env.example` to `.env` and adjust. Every variable below is read by the app on startup.

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode / verbose errors |
| `SECRET_KEY` | `change-me-in-production` | Application secret (change in production!) |
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `FRONTEND_PORT` | `3000` | Reference port (frontend is served by the backend) |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:8000"]` | Allowed origins (JSON array) |
| `RATE_LIMIT` | `30/minute` | Per-client API rate limit |

### Database & storage

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/app.db` | Async database connection string |
| `DOWNLOADS_DIR` | `./backend/downloads` | Local download output directory |
| `TEMP_DIR` | `./backend/downloads/temp` | Temp directory for in-progress files |

### Downloads & media

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads |
| `FFMPEG_LOCATION` | _(system PATH)_ | Custom FFmpeg binary path |
| `COOKIES_FILE` | `./data/cookies.txt` | Netscape `cookies.txt` for YouTube/site auth |
| `METADATA_CACHE_TTL` | `3600` | Metadata cache lifetime (seconds) |

### Logging & optional services

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_DIR` | `./logs` | Log output directory |
| `REDIS_URL` | _(none)_ | Optional Redis for the download queue |

### AWS S3 (production storage)

Enable to upload finished downloads to S3 instead of (or in addition to) local disk.

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_ENABLED` | `false` | Set `true` to upload downloads to S3 |
| `AWS_REGION` | `us-east-1` | AWS region of the bucket |
| `AWS_S3_BUCKET` | _(empty)_ | Target S3 bucket name |
| `AWS_ACCESS_KEY_ID` | _(empty)_ | AWS access key (omit when using an IAM role) |
| `AWS_SECRET_ACCESS_KEY` | _(empty)_ | AWS secret key (omit when using an IAM role) |
| `S3_PREFIX` | `downloads` | Key prefix for uploaded objects |
| `S3_DELETE_LOCAL_AFTER_UPLOAD` | `true` | Delete the local file after a successful upload |

## API Documentation

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs) when running.

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/info` | Extract video metadata |
| `POST` | `/api/download` | Queue a download |
| `GET` | `/api/status/{id}` | Get download status |
| `POST` | `/api/download/{id}/pause` | Pause download |
| `POST` | `/api/download/{id}/resume` | Resume download |
| `POST` | `/api/download/{id}/cancel` | Cancel download |
| `GET` | `/api/history` | List download history |
| `DELETE` | `/api/history/{id}` | Delete history entry |
| `POST` | `/api/history/{id}/favorite` | Toggle favorite |
| `GET` | `/api/settings` | Get user settings |
| `POST` | `/api/settings` | Update settings |
| `GET` | `/api/formats` | List supported formats/platforms |
| `GET` | `/api/health` | Health check |

### WebSocket

```
ws://localhost:8000/ws/download?download_id={id}
```

Streams live `DownloadProgress` JSON events.

## Project Structure

```
project/
├── backend/
│   ├── api/            # REST route handlers
│   ├── services/       # Business logic (yt-dlp, queue, security)
│   ├── models/         # Pydantic schemas & SQLAlchemy models
│   ├── database/       # Async DB session
│   ├── localization/   # Backend i18n
│   ├── downloads/      # Download output (gitignored)
│   ├── websocket/      # WebSocket handlers
│   ├── config/         # Settings & logging
│   └── main.py         # Application entry point
├── frontend/
│   ├── html/           # Page templates
│   ├── css/            # Custom styles
│   ├── js/             # Alpine.js application
│   ├── assets/         # Icons, images
│   └── localization/   # Frontend i18n (en, ru, hy)
├── docs/               # Documentation
├── scripts/            # Utility scripts
├── tests/              # Unit, integration, API tests
├── docker/             # Nginx config
├── .github/            # CI/CD workflows
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Development

### Running tests

```bash
pytest --cov=backend --cov-report=term-missing -v
```

### Linting

```bash
ruff check backend tests
```

### Type checking

```bash
mypy backend
```

## Localization Guide

UI strings live in JSON files:

- `frontend/localization/en.json` — English
- `frontend/localization/ru.json` — Russian
- `frontend/localization/hy.json` — Armenian

To add a language:
1. Copy `en.json` to `{lang}.json`
2. Translate all values
3. Add the language to the selector in HTML templates
4. Update `backend/localization/loader.py` → `supported_languages()`

## YouTube Cookie Authentication

If YouTube returns **"Sign in to confirm you're not a bot"**, provide browser cookies to yt-dlp.

### 1. Export cookies from your browser

1. Log in to [YouTube](https://www.youtube.com) in Chrome, Firefox, or Edge.
2. Install a cookies export extension, for example **"Get cookies.txt LOCALLY"** (Chrome/Firefox).
3. Export cookies for `youtube.com` in **Netscape** format (`.txt`).

### 2. Provide the cookies to the app

**Option A — Settings page (recommended, works on the deployed server):**

Open **Settings → Cookies**, then upload the exported `cookies.txt` file or paste its
contents and click **Save**. The file is written to `./data/cookies.txt`, which is a
persistent volume in Docker/Kubernetes, so it survives restarts.

**Option B — Place the file manually (local dev):**

```
universal-video-downloader/
└── data/
    └── cookies.txt    ← your exported file
```

This path is the default (`COOKIES_FILE=./data/cookies.txt` in `.env`). A legacy
`./config/cookies.txt` path is also checked for backward compatibility.

**Security:** `cookies.txt` is gitignored — it contains your login session. Never commit or share it.

### 3. Restart the server (only when placing the file manually)

```bash
python scripts/run_dev.py
```

The backend passes the file to yt-dlp via the `cookiefile` option for both metadata (`/api/info`) and downloads. When you upload cookies via the Settings page, the metadata cache is cleared automatically so new cookies take effect immediately.

See also: [config/README.md](config/README.md)

## Troubleshooting

### YouTube "Sign in to confirm you're not a bot"
YouTube now blocks most anonymous requests. Export fresh cookies while logged into YouTube, upload them via **Settings → Cookies** (or save to `data/cookies.txt`), then try again. Cookies expire — re-export if errors return. Also keep yt-dlp current: `pip install -U yt-dlp`.

### Rutube "Unable to download options JSON: HTTP Error 404"
Rutube periodically changes its API and only recent yt-dlp releases support it. This is fixed by the `yt-dlp>=2025.6.9` pin. If you still hit it, update yt-dlp: `pip install -U yt-dlp` (or rebuild the Docker image so the latest yt-dlp is installed).

### FFmpeg not found
Set `FFMPEG_LOCATION` in `.env` to the full path of your FFmpeg binary.

### Download fails for a specific site
Update yt-dlp: `pip install -U yt-dlp`. Some sites require cookies or authentication.

### WebSocket not connecting
Ensure you're accessing the app via the same host/port. Check that no proxy is blocking WebSocket upgrades.

### Permission errors on downloads
Verify the `DOWNLOADS_DIR` path exists and is writable.

## FAQ

**Q: Is this legal?**
A: This tool uses yt-dlp for personal use. Respect copyright laws and platform Terms of Service in your jurisdiction.

**Q: Can I download playlists?**
A: Playlist support is planned as a nice-to-have feature. The architecture supports extending this.

**Q: Does it work on mobile?**
A: Yes — the UI is fully responsive with touch-friendly controls.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Download engine
- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [Alpine.js](https://alpinejs.dev/) — Frontend reactivity
