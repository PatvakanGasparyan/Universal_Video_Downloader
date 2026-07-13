"""yt-dlp integration service for metadata extraction and downloads.

The extraction/download pipeline implements an automatic authentication
fallback chain so that YouTube's "Sign in to confirm you're not a bot" (and
similar) blocks are handled transparently:

    1. Anonymous (no cookies).
    2. Browser cookies: chrome -> chromium -> edge -> firefox (configurable).
    3. cookies.txt file.
    4. If everything fails with an auth error -> AuthRequiredError.

Only authentication/rate-limit failures advance the chain; a "video
unavailable" or "unsupported URL" error is raised immediately because cookies
cannot fix it. All raw yt-dlp exceptions are classified into structured
:class:`DownloaderError` instances before leaving this module.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from backend.config.settings import Settings, get_settings
from backend.models.schemas import FormatOption, VideoMetadata
from backend.services.cookies import normalize_browser_order, resolve_cookies_file
from backend.services.exceptions import (
    DownloadCancelledError,
    DownloaderError,
    NetworkError,
    classify_ytdlp_error,
    is_transient,
)
from backend.services.security import sanitize_filename, validate_url

logger = logging.getLogger("downloads")

_COOKIE_KEYS = ("cookiefile", "cookiesfrombrowser")

QUALITY_HEIGHTS = {
    "8k": 4320,
    "4k": 2160,
    "1440p": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
}

AUDIO_FORMATS = {"mp3", "aac", "m4a", "flac", "wav", "ogg"}
VIDEO_FORMATS = {"mp4", "mkv", "webm", "avi", "mov"}


def _to_int(value: Any) -> int | None:
    """Coerce numeric values to int (yt-dlp often returns floats for tbr/filesize)."""
    if value is None:
        return None
    if isinstance(value, float):
        return round(value)
    return int(value)


class YtDlpService:
    """Wrapper around yt-dlp for async operations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _common_opts(self) -> dict[str, Any]:
        """Base yt-dlp options shared by every strategy (no cookies)."""
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": self.settings.ytdlp_socket_timeout,
            "retries": self.settings.ytdlp_retries,
            "fragment_retries": self.settings.ytdlp_retries,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            # TV/mobile clients trigger YouTube's bot check far less than "web".
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv", "mweb", "web_safari", "android", "ios"],
                }
            },
        }
        if self.settings.ffmpeg_location:
            opts["ffmpeg_location"] = self.settings.ffmpeg_location
        return opts

    def _base_opts(self, cookies_override: str | None = None) -> dict[str, Any]:
        """Common options plus a cookies.txt file when one is available.

        Kept for backward compatibility and direct callers; the download
        pipeline itself uses :meth:`_cookie_strategies` for the full fallback
        chain.
        """
        opts = self._common_opts()
        cookies_path = resolve_cookies_file(
            env_path=self.settings.cookies_file,
            override_path=cookies_override,
        )
        if cookies_path:
            opts["cookiefile"] = str(cookies_path)
            logger.info("yt-dlp using cookies file: %s", cookies_path)
        else:
            logger.warning(
                "No cookies file found (checked COOKIES_FILE and settings). "
                "Sites like YouTube may block requests — upload cookies in Settings"
            )
        return opts

    def _cookie_strategies(
        self, cookies_override: str | None = None
    ) -> list[tuple[str, dict[str, Any]]]:
        """Return the ordered authentication strategies to attempt.

        Order: anonymous -> browser cookies (chrome, chromium, edge, firefox)
        -> cookies.txt. Each entry is ``(label, cookie_opts)`` where
        ``cookie_opts`` are merged into the base yt-dlp options.
        """
        strategies: list[tuple[str, dict[str, Any]]] = [("anonymous", {})]

        if self.settings.cookies_from_browser:
            for browser in normalize_browser_order(self.settings.cookie_browser_order):
                strategies.append(
                    (f"browser:{browser}", {"cookiesfrombrowser": (browser, None, None, None)})
                )

        cookie_path = resolve_cookies_file(
            env_path=self.settings.cookies_file,
            override_path=cookies_override,
        )
        if cookie_path:
            strategies.append(("cookies.txt", {"cookiefile": str(cookie_path)}))

        return strategies

    def _run_blocking(self, runner: Callable[[str, dict[str, Any]], Any], url: str,
                      opts: dict[str, Any]) -> Any:
        return runner(url, opts)

    async def _execute_with_fallback(
        self,
        url: str,
        base_opts: dict[str, Any],
        runner: Callable[[str, dict[str, Any]], Any],
        *,
        cookies_override: str | None = None,
        timeout: int | None = None,
        cancel_event: asyncio.Event | None = None,
        label: str = "extract",
    ) -> Any:
        """Run ``runner`` across the cookie fallback chain with retries.

        Advances to the next authentication strategy only for auth/rate-limit
        failures; other errors are raised immediately. Transient network errors
        are retried within the same strategy before moving on.
        """
        strategies = self._cookie_strategies(cookies_override)
        last_error: DownloaderError | None = None

        for name, cookie_opts in strategies:
            opts = {k: v for k, v in base_opts.items() if k not in _COOKIE_KEYS}
            opts.update(cookie_opts)

            max_attempts = 1 + max(0, self.settings.transient_retry_attempts)
            for attempt in range(1, max_attempts + 1):
                if cancel_event and cancel_event.is_set():
                    raise DownloadCancelledError(debug="cancelled before start")
                try:
                    logger.info(
                        "%s attempt via strategy '%s' (try %s/%s): %s",
                        label, name, attempt, max_attempts, url,
                    )
                    coro = asyncio.to_thread(self._run_blocking, runner, url, opts)
                    if timeout:
                        return await asyncio.wait_for(coro, timeout=timeout)
                    return await coro
                except (asyncio.TimeoutError, TimeoutError) as exc:
                    error: DownloaderError = NetworkError(debug=f"timeout after {timeout}s")
                    logger.warning("%s timed out (strategy '%s'): %s", label, name, exc)
                except Exception as exc:  # noqa: BLE001 - translated below
                    if "cancel" in str(exc).lower() and cancel_event and cancel_event.is_set():
                        raise DownloadCancelledError(debug=str(exc)) from exc
                    error = classify_ytdlp_error(exc, url=url)
                    logger.warning(
                        "%s failed (strategy '%s'): [%s] %s",
                        label, name, error.error, error.debug or error.message,
                    )

                last_error = error
                if is_transient(error) and attempt < max_attempts:
                    time.sleep(min(2 ** attempt, 5))
                    continue
                break

            # Only auth/rate-limit issues are worth trying the next strategy;
            # anything else (unavailable, unsupported, geo) cannot be fixed by
            # cookies, so fail fast.
            if last_error is not None and last_error.error not in {
                "youtube_auth_required",
                "auth_required",
                "rate_limited",
            }:
                raise last_error

        raise last_error or classify_ytdlp_error(
            RuntimeError("All authentication strategies failed"), url=url
        )

    def _build_format_selector(
        self,
        quality: str,
        fmt: str,
        audio_only: bool = False,
    ) -> str:
        quality = quality.lower()
        fmt = fmt.lower()

        if audio_only or fmt in AUDIO_FORMATS:
            return "bestaudio/best"

        if quality == "best":
            if fmt == "mp4":
                return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            return f"bestvideo[ext={fmt}]+bestaudio/best[ext={fmt}]/best"

        height = QUALITY_HEIGHTS.get(quality.replace("p", "p"), None)
        if height is None:
            try:
                height = int(quality.rstrip("p"))
            except ValueError:
                height = 1080

        if fmt == "mp4":
            return (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"best[height<={height}][ext=mp4]/best[height<={height}]"
            )
        return (
            f"bestvideo[height<={height}][ext={fmt}]+bestaudio/"
            f"best[height<={height}][ext={fmt}]/best[height<={height}]"
        )

    def _postprocessor(self, fmt: str, audio_only: bool) -> list[dict[str, Any]]:
        if audio_only or fmt in AUDIO_FORMATS:
            codec = fmt if fmt in AUDIO_FORMATS else "mp3"
            return [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": "192",
                }
            ]
        if fmt in {"mp4", "mkv", "webm", "avi", "mov"}:
            return [{"key": "FFmpegVideoConvertor", "preferedformat": fmt}]
        return []

    async def extract_info(self, url: str, cookies_file: str | None = None) -> VideoMetadata:
        """Extract video metadata without downloading (with auth fallback)."""
        url = validate_url(url)
        opts = self._common_opts()
        opts["skip_download"] = True

        info = await self._execute_with_fallback(
            url,
            opts,
            self._extract_sync,
            cookies_override=cookies_file,
            timeout=self.settings.extract_timeout,
            label="metadata",
        )
        return self._parse_metadata(url, info)

    def _extract_sync(self, url: str, opts: dict[str, Any]) -> dict[str, Any]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _parse_metadata(self, url: str, info: dict[str, Any]) -> VideoMetadata:
        formats = self._build_format_options(info)
        best = info.get("format_id")
        selected = next((f for f in info.get("formats", []) if f.get("format_id") == best), {})

        return VideoMetadata(
            url=url,
            title=info.get("title") or "",
            channel=info.get("uploader") or info.get("channel") or "",
            duration=_to_int(info.get("duration")),
            upload_date=info.get("upload_date"),
            thumbnail=info.get("thumbnail"),
            resolution=selected.get("resolution") or info.get("resolution"),
            codec=selected.get("vcodec") or info.get("vcodec"),
            fps=selected.get("fps") or info.get("fps"),
            bitrate=_to_int(selected.get("tbr") or info.get("tbr")),
            estimated_size=_to_int(info.get("filesize") or info.get("filesize_approx")),
            formats=formats,
            extractor=info.get("extractor_key") or info.get("extractor") or "",
        )

    def _build_format_options(self, info: dict[str, Any]) -> list[FormatOption]:
        options: list[FormatOption] = []
        seen: set[str] = set()

        presets = [
            ("best", "best", "mp4"),
            ("8k", "8K", "mp4"),
            ("4k", "4K", "mp4"),
            ("1440p", "1440p", "mp4"),
            ("1080p", "1080p", "mp4"),
            ("720p", "720p", "mp4"),
            ("480p", "480p", "mp4"),
            ("360p", "360p", "mp4"),
        ]

        for quality_id, label, fmt in presets:
            key = f"video-{quality_id}-{fmt}"
            if key in seen:
                continue
            seen.add(key)
            size = self._estimate_size(info, quality_id, fmt)
            options.append(
                FormatOption(
                    id=key,
                    label=f"{label} MP4",
                    quality=quality_id,
                    format=fmt,
                    codec="h264",
                    estimated_size=size,
                )
            )

        for fmt in VIDEO_FORMATS - {"mp4"}:
            key = f"video-best-{fmt}"
            if key not in seen:
                seen.add(key)
                options.append(
                    FormatOption(
                        id=key,
                        label=f"Best {fmt.upper()}",
                        quality="best",
                        format=fmt,
                        estimated_size=self._estimate_size(info, "best", fmt),
                    )
                )

        for audio_fmt in AUDIO_FORMATS:
            key = f"audio-{audio_fmt}"
            if key not in seen:
                seen.add(key)
                options.append(
                    FormatOption(
                        id=key,
                        label=audio_fmt.upper(),
                        quality="audio",
                        format=audio_fmt,
                        has_video=False,
                        estimated_size=self._estimate_audio_size(info),
                    )
                )

        return options

    def _estimate_size(self, info: dict[str, Any], quality: str, fmt: str) -> int | None:
        base = info.get("filesize") or info.get("filesize_approx")
        if not base:
            duration = info.get("duration") or 0
            if duration:
                bitrates = {
                    "8k": 50_000_000,
                    "4k": 25_000_000,
                    "1440p": 12_000_000,
                    "1080p": 8_000_000,
                    "720p": 4_000_000,
                    "480p": 2_000_000,
                    "360p": 1_000_000,
                    "best": 10_000_000,
                }
                bps = bitrates.get(quality, 5_000_000)
                return int((bps / 8) * duration)
        if quality == "best":
            return base
        height = QUALITY_HEIGHTS.get(quality, 1080)
        max_height = info.get("height") or 1080
        ratio = min(height / max(max_height, 1), 1.0)
        return int(base * ratio * ratio)

    def _estimate_audio_size(self, info: dict[str, Any]) -> int | None:
        duration = info.get("duration") or 0
        if duration:
            return int((192_000 / 8) * duration)
        return info.get("filesize_approx")

    async def download(
        self,
        url: str,
        quality: str,
        fmt: str,
        output_dir: Path,
        download_id: str,
        audio_only: bool = False,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_event: asyncio.Event | None = None,
        pause_event: asyncio.Event | None = None,
        cookies_file: str | None = None,
    ) -> Path:
        """Download a video and return the output file path (with auth fallback)."""
        url = validate_url(url)
        output_dir.mkdir(parents=True, exist_ok=True)

        outtmpl = str(output_dir / sanitize_filename(f"{download_id}_%(title)s.%(ext)s"))

        opts = self._common_opts()
        opts.update(
            {
                "format": self._build_format_selector(quality, fmt, audio_only),
                "outtmpl": outtmpl,
                "merge_output_format": fmt if fmt in VIDEO_FORMATS else "mp4",
                "postprocessors": self._postprocessor(fmt, audio_only),
                "progress_hooks": [self._make_hook(progress_callback, cancel_event, pause_event)],
            }
        )

        # No wall-clock timeout for downloads (they can be long); rely on
        # socket_timeout, progress hooks, and cancellation instead.
        result_path = await self._execute_with_fallback(
            url,
            opts,
            self._download_sync,
            cookies_override=cookies_file,
            timeout=None,
            cancel_event=cancel_event,
            label="download",
        )
        return Path(result_path)

    def _make_hook(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
        cancel_event: asyncio.Event | None,
        pause_event: asyncio.Event | None,
    ) -> Callable[[dict[str, Any]], None]:
        def hook(d: dict[str, Any]) -> None:
            if cancel_event and cancel_event.is_set():
                raise yt_dlp.utils.DownloadError("Download cancelled")

            while pause_event and pause_event.is_set():
                time.sleep(0.5)
                if cancel_event and cancel_event.is_set():
                    raise yt_dlp.utils.DownloadError("Download cancelled")

            if callback:
                callback(d)

        return hook

    def _download_sync(self, url: str, opts: dict[str, Any]) -> str:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise yt_dlp.utils.DownloadError("No download info returned")
            return ydl.prepare_filename(info)


ytdlp_service = YtDlpService()
