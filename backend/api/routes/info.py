"""Video info/metadata API routes."""

from fastapi import APIRouter, Depends, Request

from backend.api.deps import get_settings_service, get_ytdlp
from backend.api.middleware import limiter
from backend.models.schemas import InfoRequest, VideoMetadata
from backend.services.exceptions import InvalidURLError
from backend.services.history_service import SettingsService
from backend.services.metadata_cache import metadata_cache
from backend.services.security import validate_url
from backend.services.ytdlp_service import YtDlpService

router = APIRouter(prefix="/api", tags=["info"])


@router.post("/info", response_model=VideoMetadata)
@limiter.limit("20/minute")
async def get_video_info(
    request: Request,
    body: InfoRequest,
    ytdlp: YtDlpService = Depends(get_ytdlp),
    settings_service: SettingsService = Depends(get_settings_service),
) -> VideoMetadata:
    """Extract metadata for a video URL.

    Errors are raised as structured ``DownloaderError`` instances (handled
    globally); raw yt-dlp exceptions never reach the client.
    """
    try:
        url = validate_url(str(body.url))
    except ValueError as exc:
        raise InvalidURLError(message=str(exc), debug=str(exc)) from exc

    cached = await metadata_cache.get(url)
    if cached:
        return cached

    app_settings = await settings_service.get_settings()
    metadata = await ytdlp.extract_info(url, cookies_file=app_settings.cookies_file)
    await metadata_cache.set(url, metadata)
    return metadata
