"""Security utilities for path sanitization and validation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_PATH_PATTERNS = ("..", "~", "\0")
URL_PATTERN = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$",
    re.IGNORECASE,
)


def validate_url(url: str) -> str:
    """Validate and normalize a video URL."""
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("URL must use http or https scheme")
    if not parsed.netloc:
        raise ValueError("URL must include a valid host")

    if not URL_PATTERN.match(url):
        raise ValueError("Invalid URL format")

    return url


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Sanitize a filename to prevent path traversal."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    cleaned = cleaned.strip(". ")
    if not cleaned:
        cleaned = "download"
    return cleaned[:max_length]


def safe_join(base: Path, *parts: str) -> Path:
    """Join paths and ensure result stays within base directory."""
    for part in parts:
        if any(blocked in part for blocked in BLOCKED_PATH_PATTERNS):
            raise ValueError("Invalid path component")

    result = (base / Path(*parts)).resolve()
    base_resolved = base.resolve()

    if not str(result).startswith(str(base_resolved)):
        raise ValueError("Path traversal detected")

    return result
