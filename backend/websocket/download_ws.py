"""WebSocket handler for live download progress."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.download_manager import download_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/download")
async def download_websocket(websocket: WebSocket) -> None:
    """Stream download progress updates to connected clients."""
    await websocket.accept()
    download_id = websocket.query_params.get("download_id")
    download_manager.subscribe(websocket, download_id)

    if download_id:
        status = await download_manager.get_status(download_id)
        if status:
            await websocket.send_json(status.model_dump(mode="json"))

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        download_manager.unsubscribe(websocket, download_id)
        logger.debug("WebSocket disconnected: %s", download_id)
