"""Cookie file path resolution and persistence for yt-dlp authentication."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Prefer data/ (mounted volume in k8s) so cookies survive pod restarts
DEFAULT_COOKIES_PATH = Path("./data/cookies.txt")
LEGACY_COOKIES_PATH = Path("./config/cookies.txt")


def default_cookies_path() -> Path:
    """Return the canonical cookies.txt path (writable data volume)."""
    path = DEFAULT_COOKIES_PATH
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_cookies_file(
    env_path: Path | str | None = None,
    override_path: str | None = None,
) -> Path | None:
    """
    Resolve a Netscape-format cookies.txt file for yt-dlp.

    Priority: settings override → env path → data/cookies.txt → config/cookies.txt.
    """
    candidates: list[tuple[str, str]] = []
    if override_path and override_path.strip():
        candidates.append(("settings", override_path.strip()))
    if env_path:
        candidates.append(("environment", str(env_path)))
    candidates.append(("default", str(DEFAULT_COOKIES_PATH)))
    candidates.append(("legacy", str(LEGACY_COOKIES_PATH)))

    for source, raw in candidates:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()

        if path.is_file() and path.stat().st_size > 0:
            logger.info("Using cookies file from %s: %s", source, path)
            return path

        if source in {"settings", "environment"}:
            logger.warning("Cookies file configured in %s but not found: %s", source, path)

    return None


def save_cookies_content(content: str) -> Path:
    """Validate and save Netscape cookies.txt content to the default path."""
    text = content.strip().lstrip("\ufeff")
    if not text:
        raise ValueError("Cookies content is empty")

    has_tabs = "\t" in text
    has_header = any(
        marker in text
        for marker in ("# Netscape", "# HTTP Cookie File", "# This file")
    )
    data_lines = [
        line for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not has_tabs and not has_header and not data_lines:
        raise ValueError("Invalid cookies.txt format")

    path = default_cookies_path()
    path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    logger.info("Saved cookies file to %s (%s bytes)", path, path.stat().st_size)
    return path


def cookies_status() -> dict[str, object]:
    """Return whether a usable cookies file exists."""
    path = resolve_cookies_file()
    if path is None:
        return {"exists": False, "path": str(default_cookies_path()), "size": 0}
    return {"exists": True, "path": str(path), "size": path.stat().st_size}
