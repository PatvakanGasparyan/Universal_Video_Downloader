# 🔒 Security Policy

## Supported versions

| Version | Supported |
| ------- | :-------: |
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

---

## Reporting a vulnerability

> [!IMPORTANT]
> **Do not** open a public GitHub issue for security vulnerabilities.

Please report privately via **[GitHub Security Advisories](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/security/advisories/new)** (preferred) or by contacting the maintainer directly.

Include:
- A clear description and impact
- Steps to reproduce / proof of concept
- Affected version(s) and environment

**Response targets:** acknowledgment within **48 hours**, and a remediation timeline after triage. Please practice responsible disclosure and give us reasonable time to fix before going public.

---

## Security measures in this project

- ✅ Input validation & URL sanitization (`backend/services/security.py`)
- ✅ Path-traversal protection (`safe_join`, filename sanitization)
- ✅ Rate limiting on API endpoints (slowapi)
- ✅ Security headers + CORS configuration
- ✅ Structured errors — **no raw exceptions / stack traces** leak to clients
- ✅ Secrets via environment variables / Kubernetes Secrets
- ✅ Minimal Docker image (no build tools in the final layer)

---

## 🍪 Cookie security

`cookies.txt` contains a **live login session**. Treat it like a password.

- Stored locally at `./data/cookies.txt`, **gitignored**, never committed.
- Never logged and never included in API responses.
- Prefer a dedicated/throwaway account for downloading.
- Restrict who can reach the `/settings` page (auth proxy / network rules).

See **[docs/COOKIES.md](docs/COOKIES.md#security)**.

---

## 🔑 Authentication & secrets

- Change the default `SECRET_KEY` before production.
- On AWS, prefer **IAM roles** over static `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`.
- Store secrets in `.env` (gitignored) or k8s Secrets — never in code or the image.

---

## 🐳 Docker & deployment hardening

- Run behind a reverse proxy with **HTTPS** (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)).
- Expose only the ports you need (22, 80/443, 8000) in your firewall / Security Group.
- Keep `yt-dlp` and base images updated (Dependabot is configured).
- Set `DEBUG=false` and `COOKIES_FROM_BROWSER=false` on servers.
- Back up the `data/` directory; restrict access to the download directory.
