"""Download API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.deps import get_download_manager
from backend.api.middleware import limiter
from backend.models.schemas import (
    DownloadProgress,
    DownloadRequest,
    DownloadResponse,
    DownloadStatus,
)
from backend.services.download_manager import DownloadManager
from backend.services.exceptions import InvalidURLError
from backend.services.security import validate_url

router = APIRouter(prefix="/api", tags=["download"])


@router.post("/download", response_model=DownloadResponse)
@limiter.limit("10/minute")
async def start_download(
    request: Request,
    body: DownloadRequest,
    manager: DownloadManager = Depends(get_download_manager),
) -> DownloadResponse:
    """Queue a new download."""
    try:
        url = validate_url(str(body.url))
    except ValueError as exc:
        raise InvalidURLError(message=str(exc), debug=str(exc)) from exc

    download_id = await manager.enqueue(
        url=url,
        quality=body.quality,
        fmt=body.format,
        audio_only=body.audio_only,
        priority=body.priority,
    )
    return DownloadResponse(
        download_id=download_id,
        status=DownloadStatus.QUEUED,
        message="Download queued successfully",
    )


@router.get("/status/{download_id}", response_model=DownloadProgress)
async def get_download_status(
    download_id: str,
    manager: DownloadManager = Depends(get_download_manager),
) -> DownloadProgress:
    """Get current download status."""
    status = await manager.get_status(download_id)
    if not status:
        raise HTTPException(status_code=404, detail="Download not found")
    return status


@router.post("/download/{download_id}/pause")
async def pause_download(
    download_id: str,
    manager: DownloadManager = Depends(get_download_manager),
) -> dict[str, str]:
    if not await manager.pause(download_id):
        raise HTTPException(status_code=404, detail="Download not found")
    return {"message": "Download paused"}


@router.post("/download/{download_id}/resume")
async def resume_download(
    download_id: str,
    manager: DownloadManager = Depends(get_download_manager),
) -> dict[str, str]:
    if not await manager.resume(download_id):
        raise HTTPException(status_code=404, detail="Download not found")
    return {"message": "Download resumed"}


@router.post("/download/{download_id}/cancel")
async def cancel_download(
    download_id: str,
    manager: DownloadManager = Depends(get_download_manager),
) -> dict[str, str]:
    if not await manager.cancel(download_id):
        raise HTTPException(status_code=404, detail="Download not found")
    return {"message": "Download cancelled"}
