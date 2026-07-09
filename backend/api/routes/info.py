"""Video info/metadata API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.deps import get_settings_service, get_ytdlp
from backend.api.middleware import limiter
from backend.models.schemas import InfoRequest, VideoMetadata
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
    """Extract metadata for a video URL."""
    url = validate_url(str(body.url))
    cached = await metadata_cache.get(url)
    if cached:
        return cached

    app_settings = await settings_service.get_settings()

    try:
        metadata = await ytdlp.extract_info(url, cookies_file=app_settings.cookies_file)
        await metadata_cache.set(url, metadata)
        return metadata
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract video info: {exc}",
        ) from exc
