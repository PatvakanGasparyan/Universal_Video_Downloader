# 🐳 Docker Guide

Everything about building, running, and operating the app with Docker.

## 📑 Contents

- [Quick start](#quick-start)
- [The Dockerfile (multi-stage)](#the-dockerfile-multi-stage)
- [docker-compose services](#docker-compose-services)
- [Profiles](#profiles)
- [Volumes](#volumes)
- [Networks](#networks)
- [Environment](#environment)
- [Restart policy](#restart-policy)
- [Health checks](#health-checks)
- [Common commands](#common-commands)
- [Troubleshooting](#troubleshooting)

---

## Quick start

```bash
cp .env.example .env
docker compose up -d --build
# → http://localhost:8000
```

---

## The Dockerfile (multi-stage)

The image uses a **two-stage build** to stay small and fast:

| Stage | Base | Purpose |
|-------|------|---------|
| `builder` | `python:3.13-slim` | Installs build deps (`gcc`, `libffi-dev`) and `pip install --user` the runtime requirements |
| `final` | `python:3.13-slim` | Installs only **ffmpeg**, copies `/root/.local` from builder, adds app code |

Benefits: no compilers in the final image, smaller size, faster pulls on constrained hosts (e.g. `t3.micro`).

```dockerfile
FROM python:3.13-slim AS builder
# gcc, libffi-dev … + pip install --user -r requirements-prod.txt

FROM python:3.13-slim
# ffmpeg only + COPY --from=builder /root/.local /root/.local
# COPY backend frontend config scripts
# CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## docker-compose services

| Service | Image | Ports | Profile |
|---------|-------|-------|---------|
| `app` | built from `Dockerfile` | `${BACKEND_PORT:-8000}:8000` | default |
| `redis` | `redis:7-alpine` | `6379:6379` | `queue` |
| `nginx` | `nginx:alpine` | `80:80`, `443:443` | `proxy` |

---

## Profiles

```bash
docker compose up -d                     # app only
docker compose --profile proxy up -d     # app + nginx
docker compose --profile queue up -d     # app + redis
```

---

## Volumes

Persistent host mounts keep data across restarts:

| Host path | Container path | Contents |
|-----------|----------------|----------|
| `./data` | `/app/data` | SQLite DB **and** `cookies.txt` |
| `./backend/downloads` | `/app/backend/downloads` | Downloaded media |
| `./logs` | `/app/logs` | Application logs |

> [!WARNING]
> `docker compose down -v` deletes volumes — including your database and cookies.

---

## Networks

Compose creates a default bridge network. `nginx` reaches `app` by its service name (`http://app:8000`). No manual network config needed for the default setup.

---

## Environment

Variables come from `.env` via `env_file`. See **[CONFIGURATION.md](CONFIGURATION.md)** for every option.

```bash
# override the port at runtime
BACKEND_PORT=9000 docker compose up -d
```

---

## Restart policy

`app`, `redis`, and `nginx` all use `restart: unless-stopped`, so they come back after a crash or host reboot unless you explicitly stopped them.

---

## Health checks

The container defines a health check hitting `/api/health`:

```bash
docker inspect --format '{{.State.Health.Status}}' $(docker compose ps -q app)
# healthy
```

---

## Common commands

```bash
docker compose logs -f app          # tail logs
docker compose restart app          # restart
docker compose build --no-cache app # rebuild (also refreshes yt-dlp)
docker compose exec app sh          # shell into the container
docker compose ps                   # status
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No space left on device` | `docker system prune -af`; use the multi-stage image |
| Site broke after a while | `docker compose build --no-cache app` to refresh yt-dlp |
| Cookies not persisting | Ensure the `./data` volume is mounted |
| Port already in use | Change `BACKEND_PORT` in `.env` |

More: **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.
