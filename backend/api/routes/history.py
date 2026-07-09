"""Download history API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_history_service
from backend.models.schemas import ApiMessage, HistoryItem
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
async def list_history(
    query: str = Query(default=""),
    favorite_only: bool = Query(default=False),
    service: HistoryService = Depends(get_history_service),
) -> list[HistoryItem]:
    return await service.list_history(query=query, favorite_only=favorite_only)


@router.delete("/history/{record_id}", response_model=ApiMessage)
async def delete_history_item(
    record_id: int,
    service: HistoryService = Depends(get_history_service),
) -> ApiMessage:
    if not await service.delete(record_id):
        raise HTTPException(status_code=404, detail="Record not found")
    return ApiMessage(message="Deleted successfully")


@router.post("/history/{record_id}/favorite", response_model=HistoryItem)
async def toggle_favorite(
    record_id: int,
    service: HistoryService = Depends(get_history_service),
) -> HistoryItem:
    item = await service.toggle_favorite(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Record not found")
    return item
