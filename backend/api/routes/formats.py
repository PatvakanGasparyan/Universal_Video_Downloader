"""Supported formats API route."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["formats"])

VIDEO_QUALITIES = ["best", "8k", "4k", "1440p", "1080p", "720p", "480p", "360p"]
VIDEO_FORMATS = ["mp4", "mkv", "webm", "avi", "mov"]
AUDIO_FORMATS = ["mp3", "aac", "m4a", "flac", "wav", "ogg"]

PLATFORMS = [
    "YouTube", "Rutube", "Vimeo", "Twitch", "TikTok", "X (Twitter)",
    "Facebook", "Instagram", "Dailymotion", "Bilibili", "SoundCloud",
    "Reddit", "VK", "Threads",
]


@router.get("/formats")
async def get_formats() -> dict:
    return {
        "video_qualities": VIDEO_QUALITIES,
        "video_formats": VIDEO_FORMATS,
        "audio_formats": AUDIO_FORMATS,
        "platforms": PLATFORMS,
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
