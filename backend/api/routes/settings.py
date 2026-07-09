"""User settings API routes."""

from fastapi import APIRouter, Depends

from backend.api.deps import get_settings_service
from backend.models.schemas import SettingsSchema
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
