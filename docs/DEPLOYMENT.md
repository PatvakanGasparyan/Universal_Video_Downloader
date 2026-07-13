# 🚀 Deployment Guide

How to run **Universal Video Downloader** in production — on a VPS, bare Linux, or behind a reverse proxy.

## 📑 Contents

- [Deployment options](#deployment-options)
- [VPS / bare Linux (systemd)](#vps--bare-linux-systemd)
- [Docker Compose (recommended)](#docker-compose-recommended)
- [AWS EC2 + k3s](#aws-ec2--k3s)
- [Reverse proxy: Nginx](#reverse-proxy-nginx)
- [Reverse proxy: Apache](#reverse-proxy-apache)
- [Cloudflare](#cloudflare)
- [HTTPS / TLS](#https--tls)
- [Production checklist](#production-checklist)

---

## Deployment options

| Method | Best for | Difficulty |
|--------|----------|:----------:|
| Docker Compose | Most self-hosters | 🟢 Easy |
| systemd service | Minimal VPS, no Docker | 🟡 Medium |
| AWS EC2 + k3s | Cloud / portfolio | 🔴 Advanced |

---

## VPS / bare Linux (systemd)

```bash
# Install (see INSTALL.md), then create a service
sudo tee /etc/systemd/system/uvd.service >/dev/null <<'EOF'
[Unit]
Description=Universal Video Downloader
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/universal-video-downloader
Environment=PYTHONPATH=/opt/universal-video-downloader
ExecStart=/opt/universal-video-downloader/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now uvd
sudo systemctl status uvd
```

---

## Docker Compose (recommended)

```bash
cp .env.example .env      # edit SECRET_KEY, ports, etc.
docker compose up -d --build
docker compose logs -f app
```

`restart: unless-stopped` keeps the app alive across reboots. See **[DOCKER.md](DOCKER.md)**.

---

## AWS EC2 + k3s

This repo includes Terraform (`terraform/`) and k3s manifests (`k8s/`) plus a GitHub Actions pipeline. See the dedicated guide: **[AWS.md](AWS.md)**.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply
```

---

## Reverse proxy: Nginx

A ready config lives at `docker/nginx.conf`. Minimal manual example:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket upgrade for live progress
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
```

Or just: `docker compose --profile proxy up -d`.

---

## Reverse proxy: Apache

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ProxyPreserveHost On
    ProxyPass /ws/ ws://127.0.0.1:8000/ws/
    ProxyPassReverse /ws/ ws://127.0.0.1:8000/ws/
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

Enable modules: `sudo a2enmod proxy proxy_http proxy_wstunnel`.

---

## Cloudflare

1. Point an **A record** at your server's public IP.
2. Enable the proxy (orange cloud) for DDoS protection + free TLS.
3. Under **Network**, enable **WebSockets**.
4. Set SSL/TLS mode to **Full** (or **Full (strict)** with a valid origin cert).

---

## HTTPS / TLS

Use **Let's Encrypt** via Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Then update `CORS_ORIGINS` in `.env` to your `https://` domain.

---

## Production checklist

- [ ] Changed `SECRET_KEY`
- [ ] `DEBUG=false`
- [ ] `COOKIES_FROM_BROWSER=false` on headless servers
- [ ] Firewall / Security Group allows only needed ports (22, 80/443, 8000)
- [ ] HTTPS enabled behind a reverse proxy
- [ ] `CORS_ORIGINS` set to your real domain
- [ ] Backups for `data/` (SQLite + cookies)
- [ ] `yt-dlp` kept up to date
