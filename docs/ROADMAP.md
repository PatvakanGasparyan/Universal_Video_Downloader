# 🗺️ Roadmap

Planned and completed work. Suggestions welcome via [Discussions](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/discussions) or [Feature Requests](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/issues/new?template=feature_request.md).

> This roadmap is indicative, not a commitment or timeline.

## ✅ Done

- [x] FastAPI + yt-dlp backend with async download queue
- [x] Glassmorphism UI, dark/light mode, responsive
- [x] Live progress over WebSockets (speed, ETA, %, stage)
- [x] Download history (search, favorites, delete)
- [x] Multi-language UI (EN / RU / HY)
- [x] **Automatic cookie fallback pipeline** (anonymous → browser → cookies.txt)
- [x] **Structured JSON error envelopes** (no raw yt-dlp leaks)
- [x] Duplicate download coalescing + graceful shutdown + temp cleanup
- [x] Docker multi-stage build + Docker Compose
- [x] Terraform (EC2, S3, IAM, VPC) + k3s manifests
- [x] GitHub Actions CI + GHCR build/deploy
- [x] Optional AWS S3 storage

## 🚧 In progress / next

- [ ] Playlist downloads
- [ ] Channel / user collection downloads
- [ ] Subtitle download & selection
- [ ] Automatic subtitle conversion (SRT / VTT)
- [ ] Thumbnail download option

## 🔮 Planned

- [ ] Optional user authentication (admin / user roles)
- [ ] Download scheduler
- [ ] Bandwidth limiter
- [ ] Metadata editor before saving
- [ ] Built-in media player preview
- [ ] Download statistics dashboard
- [ ] Theme customization with accent colors
- [ ] Export / import download history
- [ ] Plugin architecture for extensions
- [ ] PostgreSQL backend option (multi-pod safe)
- [ ] QR code sharing for downloads

## 💡 Ideas (unscheduled)

- [ ] Browser extension companion
- [ ] Webhook / notification integrations (Discord, Telegram)
- [ ] Per-site profiles and presets

---

Want to help build one of these? See **[CONTRIBUTING.md](../CONTRIBUTING.md)**.
