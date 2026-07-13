# 🔌 API Reference

The backend exposes a REST API and a WebSocket for live progress. Interactive docs are always available at **`/docs`** (Swagger UI) and **`/redoc`** (ReDoc).

- **Base URL:** `http://SERVER_IP:8000`
- **Content type:** `application/json` (except cookie upload = `multipart/form-data`)
- **Rate limits:** `/api/info` → 20/min · `/api/download` → 10/min · global default → 30/min

## 📑 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | [`/api/info`](#post-apiinfo) | Extract metadata |
| POST | [`/api/download`](#post-apidownload) | Queue a download |
| GET | [`/api/status/{id}`](#get-apistatusid) | Download status |
| POST | [`/api/download/{id}/pause`](#download-controls) | Pause |
| POST | [`/api/download/{id}/resume`](#download-controls) | Resume |
| POST | [`/api/download/{id}/cancel`](#download-controls) | Cancel |
| GET | [`/api/history`](#get-apihistory) | List history |
| DELETE | [`/api/history/{id}`](#delete-apihistoryid) | Delete entry |
| POST | [`/api/history/{id}/favorite`](#post-apihistoryidfavorite) | Toggle favorite |
| GET | [`/api/settings`](#get-apisettings) | Get settings |
| POST | [`/api/settings`](#post-apisettings) | Update settings |
| GET | [`/api/settings/cookies`](#get-apisettingscookies) | Cookie status |
| POST | [`/api/settings/cookies`](#post-apisettingscookies) | Upload cookies |
| GET | [`/api/formats`](#get-apiformats) | Formats & platforms |
| GET | [`/api/health`](#get-apihealth) | Health check |
| WS | [`/ws/download`](#websocket-wsdownload) | Live progress |

---

## POST `/api/info`

Extract metadata for a URL (cached for `METADATA_CACHE_TTL`).

**Request**

```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

**Response `200`**

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Video title",
  "channel": "Channel name",
  "duration": 213,
  "upload_date": "20090101",
  "thumbnail": "https://…/thumb.jpg",
  "resolution": "1920x1080",
  "codec": "avc1",
  "fps": 30,
  "bitrate": 2500,
  "estimated_size": 41943040,
  "extractor": "youtube",
  "formats": [
    { "id": "video-1080p-mp4", "label": "1080p MP4", "quality": "1080p", "format": "mp4", "estimated_size": 41943040 }
  ]
}
```

**Errors:** `invalid_url` (400), `youtube_auth_required` (401), `video_unavailable` (404), `unsupported_url` (400), `network_error` (502). See [ERRORS.md](ERRORS.md).

```bash
curl -X POST http://SERVER_IP:8000/api/info \
  -H "Content-Type: application/json" \
  -d '{"url":"https://vimeo.com/76979871"}'
```

---

## POST `/api/download`

Queue a download. Returns immediately with a `download_id`.

**Request**

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `url` | string (URL) | — | Required |
| `quality` | string | `best` | `best`,`8k`,`4k`,`1440p`,`1080p`,`720p`,`480p`,`360p` |
| `format` | string | `mp4` | Video: mp4/mkv/webm/avi/mov · Audio: mp3/aac/m4a/flac/wav/ogg |
| `audio_only` | bool | `false` | Extract audio only |
| `priority` | int | `0` | Higher = sooner |

```json
{ "url": "https://youtu.be/abc", "quality": "1080p", "format": "mp4", "audio_only": false, "priority": 0 }
```

**Response `200`**

```json
{ "download_id": "a1b2c3d4e5f6", "status": "queued", "message": "Download queued successfully" }
```

> Identical in-flight requests are **coalesced** — you get the existing `download_id`.

---

## GET `/api/status/{id}`

**Response `200`**

```json
{
  "download_id": "a1b2c3d4e5f6",
  "status": "downloading",
  "percent": 62.5,
  "downloaded_bytes": 26214400,
  "total_bytes": 41943040,
  "speed": 1887436.8,
  "eta": 8,
  "current_file": "a1b2…_Video.mp4",
  "stage": "Downloading",
  "message": "Downloading...",
  "error": "",
  "solution": ""
}
```

`status` ∈ `queued · downloading · merging · converting · paused · completed · failed · cancelled`.
`404` if the id is unknown.

---

## Download controls

`POST /api/download/{id}/pause` · `POST /api/download/{id}/resume` · `POST /api/download/{id}/cancel`

**Response `200`**: `{ "message": "Download paused" }` · `404` if unknown.

---

## GET `/api/history`

Query params: `query` (search title/URL), `favorite_only` (bool).

```bash
curl "http://SERVER_IP:8000/api/history?favorite_only=true"
```

**Response `200`** — array of history items:

```json
[
  { "id": 1, "url": "https://…", "title": "…", "format": "mp4", "quality": "1080p",
    "file_size": 41943040, "status": "completed", "is_favorite": true,
    "created_at": "2026-07-14T01:00:00", "file_name": "video.mp4", "s3_key": "", "s3_url": "" }
]
```

---

## DELETE `/api/history/{id}`

`200` → `{ "message": "Deleted successfully" }` · `404` if not found.

---

## POST `/api/history/{id}/favorite`

Toggles favorite; returns the updated item. `404` if not found.

---

## GET `/api/settings`

Returns the current settings object (see [CONFIGURATION.md](CONFIGURATION.md)).

## POST `/api/settings`

Body = full settings object. Returns the saved settings.

```json
{
  "default_quality": "1080p", "default_format": "mp4", "default_folder": "",
  "preferred_language": "en", "theme": "dark", "max_concurrent_downloads": 3,
  "auto_convert_mp3": false, "auto_update_ytdlp": false, "ffmpeg_location": "", "cookies_file": ""
}
```

---

## GET `/api/settings/cookies`

```json
{ "exists": true, "path": "/app/data/cookies.txt", "size": 20480 }
```

## POST `/api/settings/cookies`

`multipart/form-data` — send **either** a `file` or a `content` field.

```bash
# Upload a file
curl -X POST http://SERVER_IP:8000/api/settings/cookies -F "file=@cookies.txt"

# Or paste content
curl -X POST http://SERVER_IP:8000/api/settings/cookies --form-string "content=$(cat cookies.txt)"
```

`200` → `{ "message": "Cookies saved successfully", "detail": { "path": "…", "size": 20480 } }`.
`400` if the content isn't valid Netscape cookies / not UTF-8.

---

## GET `/api/formats`

```json
{
  "video_qualities": ["best","8k","4k","1440p","1080p","720p","480p","360p"],
  "video_formats": ["mp4","mkv","webm","avi","mov"],
  "audio_formats": ["mp3","aac","m4a","flac","wav","ogg"],
  "platforms": [ { "name": "YouTube", "url": "https://www.youtube.com", "icon": "youtube" } ]
}
```

---

## GET `/api/health`

```json
{ "status": "healthy" }
```

---

## WebSocket `/ws/download`

Connect with a query param to receive live `DownloadProgress` JSON events:

```
ws://SERVER_IP:8000/ws/download?download_id=a1b2c3d4e5f6
```

```javascript
const ws = new WebSocket(`ws://SERVER_IP:8000/ws/download?download_id=${id}`);
ws.onmessage = (e) => {
  const p = JSON.parse(e.data);
  console.log(p.percent, p.status, p.message);
  if (p.status === "failed") console.warn(p.error, p.solution);
};
```

Omit `download_id` to subscribe to **all** downloads (global feed). On failure, the payload includes structured `error` and `solution` fields.

---

## Error envelope

All errors share one shape (never raw yt-dlp text):

```json
{ "success": false, "error": "youtube_auth_required", "message": "Authentication required.", "solution": "Upload cookies.txt in Settings, then try again." }
```

Full list: **[ERRORS.md](ERRORS.md)**.
