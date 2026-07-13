"""Supported formats API route."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["formats"])

VIDEO_QUALITIES = ["best", "8k", "4k", "1440p", "1080p", "720p", "480p", "360p"]
VIDEO_FORMATS = ["mp4", "mkv", "webm", "avi", "mov"]
AUDIO_FORMATS = ["mp3", "aac", "m4a", "flac", "wav", "ogg"]

PLATFORMS = [
    {"name": "YouTube", "url": "https://www.youtube.com", "icon": "youtube"},
    {"name": "Rutube", "url": "https://rutube.ru", "icon": "rutube"},
    {"name": "Vimeo", "url": "https://vimeo.com", "icon": "vimeo"},
    {"name": "Twitch", "url": "https://www.twitch.tv", "icon": "twitch"},
    {"name": "TikTok", "url": "https://www.tiktok.com", "icon": "tiktok"},
    {"name": "X (Twitter)", "url": "https://x.com", "icon": "x"},
    {"name": "Facebook", "url": "https://www.facebook.com", "icon": "facebook"},
    {"name": "Instagram", "url": "https://www.instagram.com", "icon": "instagram"},
    {"name": "Dailymotion", "url": "https://www.dailymotion.com", "icon": "dailymotion"},
    {"name": "Bilibili", "url": "https://www.bilibili.com", "icon": "bilibili"},
    {"name": "SoundCloud", "url": "https://soundcloud.com", "icon": "soundcloud"},
    {"name": "Reddit", "url": "https://www.reddit.com", "icon": "reddit"},
    {"name": "VK", "url": "https://vk.com", "icon": "vk"},
    {"name": "Threads", "url": "https://www.threads.net", "icon": "threads"},
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
