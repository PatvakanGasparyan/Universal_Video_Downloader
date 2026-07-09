"""Backend localization loader."""

from __future__ import annotations

import json
from pathlib import Path

LOCALIZATION_DIR = Path(__file__).parent


def load_locale(lang: str) -> dict[str, str]:
    """Load localization strings for a language."""
    path = LOCALIZATION_DIR / f"{lang}.json"
    if not path.exists():
        path = LOCALIZATION_DIR / "en.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def supported_languages() -> list[str]:
    return ["en", "ru", "hy"]
