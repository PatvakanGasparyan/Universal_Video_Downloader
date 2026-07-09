"""Structured logging configuration with rotation."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from backend.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure application-wide structured logging."""
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "download_id=%(download_id)s | %(message)s"
    )

    class DownloadContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "download_id"):
                record.download_id = "-"
            return True

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(log_format))
    console.addFilter(DownloadContextFilter())
    root.addHandler(console)

    for name in ("downloads", "errors", "performance"):
        file_path = settings.log_dir / f"{name}.log"
        handler = RotatingFileHandler(
            file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(log_format))
        handler.addFilter(DownloadContextFilter())
        root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
