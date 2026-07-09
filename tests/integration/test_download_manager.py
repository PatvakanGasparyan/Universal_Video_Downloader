"""Integration tests for download manager."""

import pytest

from backend.services.download_manager import DownloadManager


@pytest.mark.asyncio
async def test_manager_start_stop():
    manager = DownloadManager()
    await manager.start()
    assert manager._running is True
    await manager.stop()


@pytest.mark.asyncio
async def test_enqueue_download(manager):
    download_id = await manager.enqueue(
        url="https://example.com/video",
        quality="720p",
        fmt="mp4",
    )
    assert len(download_id) == 12
    status = await manager.get_status(download_id)
    assert status is not None
    await manager.cancel(download_id)


@pytest.mark.asyncio
async def test_pause_resume_unknown():
    manager = DownloadManager()
    assert await manager.pause("nonexistent") is False
    assert await manager.resume("nonexistent") is False
    assert await manager.cancel("nonexistent") is False


@pytest.mark.asyncio
async def test_manager_subscribe(manager):
    class FakeWS:
        async def send_json(self, data):
            pass

    ws = FakeWS()
    manager.subscribe(ws, "test-id")
    manager.unsubscribe(ws, "test-id")
    manager.unsubscribe(ws)


@pytest.mark.asyncio
async def test_pause_resume_active(manager):
    download_id = await manager.enqueue(
        url="https://example.com/video2",
        quality="480p",
        fmt="mp4",
    )
    assert await manager.pause(download_id) is True
    assert await manager.resume(download_id) is True
    await manager.cancel(download_id)
