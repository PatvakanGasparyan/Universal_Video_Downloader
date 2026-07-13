"""User settings API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.api.deps import get_settings_service
from backend.models.schemas import ApiMessage, SettingsSchema
from backend.services.cookies import cookies_status, default_cookies_path, save_cookies_content
from backend.services.history_service import SettingsService

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=SettingsSchema)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
) -> SettingsSchema:
    return await service.get_settings()


@router.post("/settings", response_model=SettingsSchema)
async def update_settings(
    settings: SettingsSchema,
    service: SettingsService = Depends(get_settings_service),
) -> SettingsSchema:
    return await service.update_settings(settings)


@router.get("/settings/cookies")
async def get_cookies_status() -> dict:
    """Return whether cookies.txt is present and usable."""
    return cookies_status()


@router.post("/settings/cookies", response_model=ApiMessage)
async def upload_cookies(
    service: SettingsService = Depends(get_settings_service),
    file: UploadFile | None = File(default=None),
    content: str | None = Form(default=None),
) -> ApiMessage:
    """
    Upload or paste Netscape cookies.txt content.

    Accepts either a multipart file upload or a pasted `content` form field.
    Saves to config/cookies.txt and updates settings.cookies_file.
    """
    raw = ""
    if file is not None and file.filename:
        data = await file.read()
        try:
            raw = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="Cookies file must be UTF-8 text") from exc
    elif content:
        raw = content
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide a cookies.txt file upload or paste content",
        )

    try:
        path = save_cookies_content(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    current = await service.get_settings()
    updated = current.model_copy(update={"cookies_file": str(default_cookies_path())})
    await service.update_settings(updated)

    return ApiMessage(
        message="Cookies saved successfully",
        detail={"path": str(path), "size": path.stat().st_size},
    )
