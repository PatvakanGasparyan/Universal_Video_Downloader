"""Tests for thread-safe progress broadcasting during downloads."""

import asyncio
from unittest.mock import patch

import pytest

from backend.models.schemas import DownloadStatus
from backend.services.download_manager import ActiveDownload, DownloadManager


@pytest.mark.asyncio
async def test_progress_hook_from_worker_thread_does_not_raise(tmp_path):
    """yt-dlp progress hooks run in a thread pool; broadcasting must be loop-safe."""
    manager = DownloadManager()
    await manager.start()
    manager.settings.downloads_dir = tmp_path

    async def mock_download(*_args, progress_callback=None, **_kwargs):
        if progress_callback:
            await asyncio.to_thread(
                progress_callback,
                {
                    "status": "downloading",
                    "downloaded_bytes": 512,
                    "total_bytes": 1024,
                    "speed": 100000,
                    "eta": 10,
                    "filename": "video.mp4",
                },
            )
        out = tmp_path / "video.mp4"
        out.write_bytes(b"test")
        return out

    with patch(
        "backend.services.download_manager.ytdlp_service.download",
        side_effect=mock_download,
    ):
        download_id = await manager.enqueue(
            "https://example.com/video",
            quality="720p",
            fmt="mp4",
        )
        await asyncio.sleep(0.2)

    status = await manager.get_status(download_id)
    assert status is not None
    assert status.status in {DownloadStatus.DOWNLOADING, DownloadStatus.COMPLETED}
    await manager.stop()


@pytest.mark.asyncio
async def test_active_download_events_created_in_loop():
    manager = DownloadManager()
    await manager.start()
    active = ActiveDownload(
        download_id="evt1",
        url="https://example.com",
        quality="best",
        format="mp4",
        audio_only=False,
    )
    assert active.cancel_event is not None
    assert active.pause_event is not None
    assert not active.cancel_event.is_set()
    await manager.stop()
