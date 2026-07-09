"""Cookie file path resolution for yt-dlp authentication."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_cookies_file(
    env_path: Path | str | None = None,
    override_path: str | None = None,
) -> Path | None:
    """
    Resolve a Netscape-format cookies.txt file for yt-dlp.

    The override path (from UI settings) takes precedence over the env default.
    Returns None if no valid file is found.
    """
    candidates: list[tuple[str, str]] = []
    if override_path and override_path.strip():
        candidates.append(("settings", override_path.strip()))
    if env_path:
        candidates.append(("environment", str(env_path)))

    for source, raw in candidates:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()

        if path.is_file():
            logger.debug("Using cookies file from %s: %s", source, path)
            return path

        logger.warning("Cookies file configured in %s but not found: %s", source, path)

    return None
