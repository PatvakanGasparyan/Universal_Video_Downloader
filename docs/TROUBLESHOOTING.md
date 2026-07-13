# 🩺 Troubleshooting

A systematic guide to diagnosing and fixing common problems.

## 📑 Contents

- [First steps](#first-steps)
- [YouTube bot detection](#youtube-bot-detection)
- [yt-dlp / extractor problems](#yt-dlp--extractor-problems)
- [FFmpeg problems](#ffmpeg-problems)
- [Cookie problems](#cookie-problems)
- [Docker problems](#docker-problems)
- [Permission problems](#permission-problems)
- [Disk space](#disk-space)
- [Port 8000 & networking](#port-8000--networking)
- [AWS firewall / Security Group](#aws-firewall--security-group)
- [WebSocket / live progress](#websocket--live-progress)
- [Browser authentication](#browser-authentication)
- [Collecting logs](#collecting-logs)

---

## First steps

```bash
# Is the app healthy?
curl http://localhost:8000/api/health   # {"status":"healthy"}

# What do the logs say?
docker compose logs --tail=100 app      # docker
tail -n 100 logs/app.log                 # native
```

> [!TIP]
> 90% of "a site broke" issues are fixed by updating yt-dlp: `pip install -U yt-dlp` or rebuilding the image.

---

## YouTube bot detection

**Symptom:** `youtube_auth_required` / "Sign in to confirm you're not a bot."

1. Export fresh `cookies.txt` while logged in to YouTube.
2. Upload via **Settings → Cookies**.
3. On servers, set `COOKIES_FROM_BROWSER=false`.
4. Retry. Full guide: **[COOKIES.md](COOKIES.md)**.

---

## yt-dlp / extractor problems

| Symptom | Fix |
|---------|-----|
| A specific site fails suddenly | `pip install -U yt-dlp` / rebuild image |
| Rutube `HTTP Error 404` | Ensure `yt-dlp>=2025.6.9` (rebuild image) |
| `Requested format is not available` | Try `best` quality or a different container |
| `Unsupported URL` | The site isn't supported / URL is wrong |

---

## FFmpeg problems

| Symptom | Fix |
|---------|-----|
| `FFmpeg not found` | Install FFmpeg or set `FFMPEG_LOCATION` |
| Merge/convert fails | Verify `ffmpeg -version` works on the host |
| Wrong output format | Some containers require re-encoding — try MP4 |

```bash
# Verify
ffmpeg -version
```

---

## Cookie problems

| Symptom | Fix |
|---------|-----|
| "Invalid cookies.txt format" | Export in **Netscape** format |
| Still blocked | Cookies expired — re-export |
| Cookies not persisting (Docker) | Ensure `./data` volume is mounted |
| Browser cookies not read | Close browser / run app as same OS user, or upload a file |

---

## Docker problems

```bash
docker compose ps                     # container status
docker compose logs -f app            # follow logs
docker compose build --no-cache app   # rebuild (refresh yt-dlp)
docker compose down && docker compose up -d
```

| Symptom | Fix |
|---------|-----|
| Port in use | Change `BACKEND_PORT` |
| Unhealthy container | Check `/api/health`, inspect logs |
| Old yt-dlp after rebuild | Build with `--no-cache` |

---

## Permission problems

```bash
# Ensure data/downloads/logs are writable
sudo chown -R "$USER" data backend/downloads logs
chmod -R u+rw data backend/downloads logs
```

In Docker, the volumes are owned by the container user; avoid mounting read-only.

---

## Disk space

```bash
df -h                       # host disk
docker system df            # docker usage
docker system prune -af     # reclaim space
```

Enable `S3_DELETE_LOCAL_AFTER_UPLOAD=true` to remove local files after S3 upload.

---

## Port 8000 & networking

```bash
# Is the app listening?
ss -tlnp | grep 8000        # Linux
netstat -ano | findstr 8000 # Windows
```

If local works but remote doesn't, it's almost always a firewall/Security Group.

---

## AWS firewall / Security Group

> [!IMPORTANT]
> Add an inbound rule: **Custom TCP · port 8000 · source 0.0.0.0/0** (or your IP). See **[AWS.md](AWS.md#security-groups--port-8000)**.

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxx --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

---

## WebSocket / live progress

| Symptom | Fix |
|---------|-----|
| Progress bar frozen | Ensure WebSocket upgrades pass through your proxy |
| Nginx blocks WS | Add the `/ws/` `Upgrade` block (see [DEPLOYMENT.md](DEPLOYMENT.md)) |
| Cloudflare | Enable **WebSockets** in Network settings |

---

## Browser authentication

`--cookies-from-browser` needs a real browser profile accessible by the app's OS user:

- **Desktop:** close the browser (locked cookie DB) or ensure the same user.
- **Server:** there's no browser — set `COOKIES_FROM_BROWSER=false` and upload cookies.

---

## Collecting logs

When opening an issue, include:

```bash
# App + versions
python --version
pip show yt-dlp | grep Version
ffmpeg -version | head -n1

# Recent logs (redact cookies/secrets!)
docker compose logs --tail=200 app
```

Then file a **[bug report](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/issues/new?template=bug_report.yml)**.
