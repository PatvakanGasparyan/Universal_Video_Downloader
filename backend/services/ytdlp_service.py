"""yt-dlp integration service for metadata extraction and downloads."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from backend.config.settings import Settings, get_settings
from backend.models.schemas import FormatOption, VideoMetadata
from backend.services.cookies import resolve_cookies_file
from backend.services.security import sanitize_filename, validate_url

logger = logging.getLogger("downloads")

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

    def _base_opts(self, cookies_override: str | None = None) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
        }
        if self.settings.ffmpeg_location:
            opts["ffmpeg_location"] = self.settings.ffmpeg_location

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
                "YouTube may block requests — add config/cookies.txt"
            )

        # Helps with YouTube bot checks when combined with cookies
        opts["extractor_args"] = {"youtube": {"player_client": ["android", "web"]}}

        return opts

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
        """Extract video metadata without downloading."""
        url = validate_url(url)
        opts = self._base_opts(cookies_override=cookies_file)
        opts["skip_download"] = True

        info = await asyncio.to_thread(self._extract_sync, url, opts)
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
        """Download a video and return the output file path."""
        url = validate_url(url)
        output_dir.mkdir(parents=True, exist_ok=True)

        outtmpl = str(output_dir / sanitize_filename(f"{download_id}_%(title)s.%(ext)s"))

        opts = self._base_opts(cookies_override=cookies_file)
        opts.update(
            {
                "format": self._build_format_selector(quality, fmt, audio_only),
                "outtmpl": outtmpl,
                "merge_output_format": fmt if fmt in VIDEO_FORMATS else "mp4",
                "postprocessors": self._postprocessor(fmt, audio_only),
                "progress_hooks": [self._make_hook(progress_callback, cancel_event, pause_event)],
            }
        )

        result_path = await asyncio.to_thread(self._download_sync, url, opts)
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
                import time

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
