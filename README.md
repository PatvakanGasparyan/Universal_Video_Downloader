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

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `FRONTEND_PORT` | `3000` | Reference port (frontend served by backend) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/app.db` | Database connection |
| `DOWNLOADS_DIR` | `./backend/downloads` | Download output directory |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads |
| `FFMPEG_LOCATION` | _(system PATH)_ | Custom FFmpeg binary path |
| `COOKIES_FILE` | `./config/cookies.txt` | Netscape cookies.txt for YouTube/site auth |
| `SECRET_KEY` | `change-me-in-production` | Application secret |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RATE_LIMIT` | `30/minute` | API rate limit |
| `REDIS_URL` | _(none)_ | Optional Redis for queue |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:8000"]` | Allowed origins |

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

### 2. Place the file in your project

Save the exported file here (project root):

```
universal-video-downloader/
└── config/
    └── cookies.txt    ← your exported file
```

This path is the default (`COOKIES_FILE=./config/cookies.txt` in `.env`).

**Security:** `config/cookies.txt` is gitignored — it contains your login session. Never commit or share it.

### 3. Configure (optional)

**Option A — Environment variable** (`.env`):

```env
COOKIES_FILE=./config/cookies.txt
```

**Option B — Settings page** (http://localhost:8000/settings):

Set **Cookies file** to `./config/cookies.txt` or an absolute path. UI settings override the env default when set.

### 4. Restart the server

```bash
python scripts/run_dev.py
```

The backend passes the file to yt-dlp via the `cookiefile` option for both metadata (`/api/info`) and downloads.

See also: [config/README.md](config/README.md)

## Troubleshooting

### YouTube "Sign in to confirm you're not a bot"
Export fresh cookies while logged into YouTube, save to `config/cookies.txt`, and restart the app. Update yt-dlp: `pip install -U yt-dlp`. Cookies expire — re-export if errors return.

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
