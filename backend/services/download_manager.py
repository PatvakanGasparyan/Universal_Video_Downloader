"""Download queue manager with pause, resume, cancel, and priority support."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from backend.config.settings import get_settings
from backend.database.session import async_session_factory
from backend.models.schemas import DownloadProgress, DownloadRecord, DownloadStatus
from backend.services.exceptions import (
    DownloadCancelledError,
    DownloaderError,
    classify_ytdlp_error,
)
from backend.services.history_service import settings_service
from backend.services.s3_service import s3_storage
from backend.services.security import safe_join
from backend.services.ytdlp_service import ytdlp_service

logger = logging.getLogger("downloads")

_TERMINAL_STATUSES = {
    DownloadStatus.COMPLETED,
    DownloadStatus.FAILED,
    DownloadStatus.CANCELLED,
}


@dataclass(order=True)
class QueueItem:
    priority: int
    download_id: str = field(compare=False)
    url: str = field(compare=False)
    quality: str = field(compare=False, default="best")
    format: str = field(compare=False, default="mp4")
    audio_only: bool = field(compare=False, default=False)


@dataclass
class ActiveDownload:
    download_id: str
    url: str
    quality: str
    format: str
    audio_only: bool
    cancel_event: asyncio.Event | None = None
    pause_event: asyncio.Event | None = None
    progress: DownloadProgress = field(default_factory=lambda: DownloadProgress(
        download_id="", status=DownloadStatus.QUEUED
    ))
    task: asyncio.Task[Any] | None = None

    def __post_init__(self) -> None:
        if self.cancel_event is None:
            self.cancel_event = asyncio.Event()
        if self.pause_event is None:
            self.pause_event = asyncio.Event()


class DownloadManager:
    """Manages concurrent download queue with WebSocket broadcasting."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._queue: asyncio.PriorityQueue[QueueItem] | None = None
        self._active: dict[str, ActiveDownload] = {}
        self._signatures: dict[str, str] = {}
        self._tasks: set[asyncio.Task[Any]] = set()
        self._listeners: dict[str, set[Any]] = {}
        self._global_listeners: set[Any] = set()
        self._worker_task: asyncio.Task[Any] | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._lock: asyncio.Lock | None = None
        self._running = False

    def _ensure_async_primitives(self) -> None:
        """Create asyncio primitives inside the running event loop."""
        if self._queue is None:
            self._queue = asyncio.PriorityQueue()
        if self._lock is None:
            self._lock = asyncio.Lock()

    @staticmethod
    def _signature(url: str, quality: str, fmt: str, audio_only: bool) -> str:
        return f"{url}|{quality}|{fmt}|{int(audio_only)}"

    async def start(self) -> None:
        if self._running:
            return
        self._ensure_async_primitives()
        self._running = True
        max_dl = self.settings.max_concurrent_downloads
        self._semaphore = asyncio.Semaphore(max_dl)
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Download manager started with max_concurrent=%s", max_dl)

    async def stop(self) -> None:
        """Gracefully stop: signal cancellation, drain in-flight tasks."""
        self._running = False

        # Ask active downloads to stop, then let their tasks unwind.
        for active in list(self._active.values()):
            if active.cancel_event and active.progress.status not in _TERMINAL_STATUSES:
                active.cancel_event.set()

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        pending = [t for t in self._tasks if not t.done()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._tasks.clear()
        logger.info("Download manager stopped")

    def subscribe(self, ws: Any, download_id: str | None = None) -> None:
        if download_id:
            self._listeners.setdefault(download_id, set()).add(ws)
        else:
            self._global_listeners.add(ws)

    def unsubscribe(self, ws: Any, download_id: str | None = None) -> None:
        if download_id and download_id in self._listeners:
            self._listeners[download_id].discard(ws)
        self._global_listeners.discard(ws)

    async def _broadcast(self, progress: DownloadProgress) -> None:
        payload = progress.model_dump(mode="json")
        listeners = set(self._global_listeners)
        listeners.update(self._listeners.get(progress.download_id, set()))
        dead: list[Any] = []
        for ws in listeners:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unsubscribe(ws)
            self.unsubscribe(ws, progress.download_id)

    async def enqueue(
        self,
        url: str,
        quality: str = "best",
        fmt: str = "mp4",
        audio_only: bool = False,
        priority: int = 0,
    ) -> str:
        self._ensure_async_primitives()
        assert self._lock is not None and self._queue is not None

        signature = self._signature(url, quality, fmt, audio_only)

        async with self._lock:
            # Duplicate prevention: reuse the id of an identical in-flight job.
            existing_id = self._signatures.get(signature)
            if existing_id and existing_id in self._active:
                existing = self._active[existing_id]
                if existing.progress.status not in _TERMINAL_STATUSES:
                    logger.info("Duplicate download coalesced to %s: %s", existing_id, url)
                    return existing_id

            download_id = str(uuid.uuid4())[:12]
            active = ActiveDownload(
                download_id=download_id,
                url=url,
                quality=quality,
                format=fmt,
                audio_only=audio_only,
                progress=DownloadProgress(
                    download_id=download_id,
                    status=DownloadStatus.QUEUED,
                    message="Waiting in queue...",
                ),
            )
            self._active[download_id] = active
            self._signatures[signature] = download_id

        item = QueueItem(
            priority=-priority,
            download_id=download_id,
            url=url,
            quality=quality,
            format=fmt,
            audio_only=audio_only,
        )
        await self._queue.put(item)
        await self._broadcast(active.progress)
        await self._create_history_record(download_id, url, quality, fmt)
        return download_id

    async def get_status(self, download_id: str) -> DownloadProgress | None:
        active = self._active.get(download_id)
        if active:
            return active.progress
        return None

    async def pause(self, download_id: str) -> bool:
        active = self._active.get(download_id)
        if not active:
            return False
        active.pause_event.set()
        active.progress.status = DownloadStatus.PAUSED
        active.progress.message = "Paused"
        await self._broadcast(active.progress)
        return True

    async def resume(self, download_id: str) -> bool:
        active = self._active.get(download_id)
        if not active:
            return False
        active.pause_event.clear()
        active.progress.status = DownloadStatus.DOWNLOADING
        active.progress.message = "Resuming..."
        await self._broadcast(active.progress)
        return True

    async def cancel(self, download_id: str) -> bool:
        active = self._active.get(download_id)
        if not active:
            return False
        active.cancel_event.set()
        active.progress.status = DownloadStatus.CANCELLED
        active.progress.message = "Cancelled"
        await self._broadcast(active.progress)
        await self._update_history_status(download_id, DownloadStatus.CANCELLED)
        return True

    async def _worker_loop(self) -> None:
        assert self._queue is not None
        while self._running:
            item = await self._queue.get()
            assert self._semaphore is not None
            await self._semaphore.acquire()
            task = asyncio.create_task(self._process_item(item))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _process_item(self, item: QueueItem) -> None:
        assert self._semaphore is not None
        active = self._active.get(item.download_id)
        if not active:
            self._semaphore.release()
            return

        try:
            await self._run_download(active)
        finally:
            self._semaphore.release()
            # Allow the same URL/format to be requested again once finished.
            if active.progress.status in _TERMINAL_STATUSES:
                signature = self._signature(
                    active.url, active.quality, active.format, active.audio_only
                )
                if self._signatures.get(signature) == active.download_id:
                    self._signatures.pop(signature, None)

    async def _run_download(self, active: ActiveDownload) -> None:
        download_id = active.download_id
        loop = asyncio.get_running_loop()

        def schedule_broadcast() -> None:
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._broadcast(active.progress))
            )

        def progress_hook(d: dict[str, Any]) -> None:
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                speed = d.get("speed") or 0
                eta = d.get("eta")
                percent = (downloaded / total * 100) if total else 0
                active.progress = DownloadProgress(
                    download_id=download_id,
                    status=DownloadStatus.DOWNLOADING,
                    percent=round(percent, 1),
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    speed=speed,
                    eta=eta,
                    current_file=d.get("filename", ""),
                    stage="Downloading",
                    message="Downloading...",
                )
            elif d.get("status") == "finished":
                active.progress.status = DownloadStatus.MERGING
                active.progress.stage = "Merging"
                active.progress.message = "Merging audio..."
            schedule_broadcast()

        try:
            active.progress.status = DownloadStatus.DOWNLOADING
            active.progress.message = "Starting download..."
            await self._broadcast(active.progress)

            app_settings = await settings_service.get_settings()
            output_dir = self.settings.resolved_downloads_dir
            file_path = await ytdlp_service.download(
                url=active.url,
                quality=active.quality,
                fmt=active.format,
                output_dir=output_dir,
                download_id=download_id,
                audio_only=active.audio_only,
                progress_callback=progress_hook,
                cancel_event=active.cancel_event,
                pause_event=active.pause_event,
                cookies_file=app_settings.cookies_file or None,
            )

            active.progress.status = DownloadStatus.COMPLETED
            active.progress.percent = 100.0
            active.progress.message = "Finished"
            active.progress.stage = "Complete"
            file_size = file_path.stat().st_size if file_path.exists() else 0
            if file_path.exists():
                active.progress.downloaded_bytes = file_size
                active.progress.total_bytes = file_size

            s3_key = ""
            s3_url = ""
            final_path = file_path

            if s3_storage.is_enabled and file_path.exists():
                active.progress.status = DownloadStatus.CONVERTING
                active.progress.stage = "Uploading"
                active.progress.message = "Uploading to S3..."
                await self._broadcast(active.progress)
                s3_key, s3_url = await s3_storage.upload_and_cleanup(file_path, download_id)
                final_path = Path(s3_url)

            await self._update_history_complete(
                download_id,
                final_path,
                DownloadStatus.COMPLETED,
                s3_key=s3_key,
                s3_url=s3_url,
                file_size=file_size,
            )
            await self._broadcast(active.progress)
            logger.info("Download completed: %s", download_id, extra={"download_id": download_id})

        except (DownloadCancelledError, asyncio.CancelledError):
            active.progress.status = DownloadStatus.CANCELLED
            active.progress.message = "Cancelled"
            self._cleanup_partial_files(download_id)
            await self._update_history_status(download_id, DownloadStatus.CANCELLED)
            await self._broadcast(active.progress)
            logger.info("Download cancelled: %s", download_id, extra={"download_id": download_id})

        except Exception as exc:  # noqa: BLE001 - translated to structured error
            # Cancellation can surface as a generic yt-dlp DownloadError.
            if active.cancel_event and active.cancel_event.is_set():
                active.progress.status = DownloadStatus.CANCELLED
                active.progress.message = "Cancelled"
                self._cleanup_partial_files(download_id)
                await self._update_history_status(download_id, DownloadStatus.CANCELLED)
                await self._broadcast(active.progress)
                return

            error = exc if isinstance(exc, DownloaderError) else classify_ytdlp_error(
                exc, url=active.url
            )
            active.progress.status = DownloadStatus.FAILED
            active.progress.message = error.message
            active.progress.error = error.error
            active.progress.solution = error.solution
            self._cleanup_partial_files(download_id)
            await self._update_history_status(download_id, DownloadStatus.FAILED, error.message)
            await self._broadcast(active.progress)
            logger.error(
                "Download failed [%s]: %s",
                error.error,
                error.debug or error.message,
                extra={"download_id": download_id},
            )

    def _cleanup_partial_files(self, download_id: str) -> None:
        """Remove partial/temporary artefacts for a failed or cancelled job."""
        patterns = (f"{download_id}_*", f"{download_id}_*.part", f"{download_id}_*.ytdl")
        for base in (self.settings.resolved_downloads_dir, self.settings.resolved_temp_dir):
            try:
                for pattern in patterns:
                    for leftover in base.glob(pattern):
                        try:
                            leftover.unlink()
                            logger.debug("Removed leftover file: %s", leftover)
                        except OSError:
                            pass
            except Exception:  # noqa: BLE001 - cleanup must never raise
                logger.debug("Cleanup skipped for %s in %s", download_id, base)

    async def _create_history_record(
        self, download_id: str, url: str, quality: str, fmt: str
    ) -> None:
        async with async_session_factory() as session:
            record = DownloadRecord(
                download_id=download_id,
                url=url,
                title=f"Download {download_id}",
                quality=quality,
                format=fmt,
                status=DownloadStatus.QUEUED,
            )
            session.add(record)
            await session.commit()

    async def _get_record(self, session: Any, download_id: str) -> DownloadRecord | None:
        result = await session.execute(
            select(DownloadRecord)
            .where(DownloadRecord.download_id == download_id)
            .order_by(DownloadRecord.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _update_history_status(
        self, download_id: str, status: DownloadStatus, error: str = ""
    ) -> None:
        async with async_session_factory() as session:
            record = await self._get_record(session, download_id)
            if record:
                record.status = status
                record.error_message = error
                await session.commit()

    async def _update_history_complete(
        self,
        download_id: str,
        file_path: Path,
        status: DownloadStatus,
        s3_key: str = "",
        s3_url: str = "",
        file_size: int = 0,
    ) -> None:
        async with async_session_factory() as session:
            record = await self._get_record(session, download_id)
            if record:
                record.status = status
                if s3_url:
                    record.file_path = s3_url
                    record.s3_key = s3_key
                    record.s3_url = s3_url
                else:
                    record.file_path = str(safe_join(
                        self.settings.resolved_downloads_dir,
                        file_path.name,
                    ))
                record.file_name = Path(s3_key).name if s3_key else file_path.name
                record.file_size = file_size if file_size else (
                    file_path.stat().st_size if file_path.exists() else 0
                )
                record.completed_at = datetime.now(UTC)
                try:
                    app_settings = await settings_service.get_settings()
                    meta = await ytdlp_service.extract_info(
                        record.url,
                        cookies_file=app_settings.cookies_file or None,
                    )
                    record.title = meta.title
                    record.channel = meta.channel
                except Exception:
                    pass
                await session.commit()


download_manager = DownloadManager()
