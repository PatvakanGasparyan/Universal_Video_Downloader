# 📝 Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🍪 **Automatic cookie authentication pipeline**: anonymous → browser cookies (`chrome → chromium → edge → firefox`) → `cookies.txt` → friendly error.
- 🚦 **Structured JSON error envelopes** (`success` / `error` / `message` / `solution`) for all failures; raw yt-dlp exceptions are never exposed.
- ⚙️ New tunables: `COOKIES_FROM_BROWSER`, `COOKIE_BROWSER_ORDER`, `YTDLP_SOCKET_TIMEOUT`, `YTDLP_RETRIES`, `EXTRACT_TIMEOUT`, `TRANSIENT_RETRY_ATTEMPTS`.
- 🧱 Duplicate download coalescing, graceful shutdown, and partial-file cleanup.
- 🗄️ `download_id` column for correct history correlation (+ SQLite migration).
- 📚 World-class documentation set under `docs/` (Architecture, API, Cookies, Configuration, AWS, Docker, Deployment, FAQ, Errors, Troubleshooting, Roadmap).
- 🧰 GitHub community health files: issue/PR templates, Dependabot, release & stale workflows, funding, labels.

### Changed
- ⬆️ Pinned `yt-dlp>=2025.6.9` (fixes Rutube `HTTP Error 404` and improves YouTube reliability).
- 🔁 Updated YouTube player clients to `tv, mweb, web_safari, android, ios` to reduce bot checks.
- 📁 Default `COOKIES_FILE` is now `./data/cookies.txt` (persistent volume) with legacy `./config/cookies.txt` fallback.

### Fixed
- 🐛 History records now correlate by `download_id` instead of a broken URL match / "last row" heuristic.
- 🧵 Thread-safe progress broadcasting from yt-dlp worker threads.

## [1.0.0] - 2026-07-03

### Added
- Initial release of Universal Video Downloader
- FastAPI backend with yt-dlp integration
- Modern glassmorphism web UI with dark/light mode
- Multi-language support (English, Russian, Armenian)
- Download queue with pause, resume, and cancel
- WebSocket live progress updates
- Download history with search, favorites, and delete
- User settings page
- Docker and Docker Compose deployment
- GitHub Actions CI pipeline
- REST API with rate limiting and security headers
- SEO: meta tags, Open Graph, sitemap, robots.txt, manifest

[Unreleased]: https://github.com/PatvakanGasparyan/Universal_Video_Downloader/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/PatvakanGasparyan/Universal_Video_Downloader/releases/tag/v1.0.0
