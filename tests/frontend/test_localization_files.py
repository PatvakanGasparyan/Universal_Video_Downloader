"""Frontend localization file tests."""

import json
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "localization"
REQUIRED_KEYS = [
    "app_title", "app_subtitle", "download_btn", "nav_home",
    "nav_history", "nav_settings", "url_placeholder",
]


def test_all_locale_files_exist():
    for lang in ["en", "ru", "hy"]:
        assert (LOCALE_DIR / f"{lang}.json").exists()


def test_locale_files_have_required_keys():
    for lang in ["en", "ru", "hy"]:
        with open(LOCALE_DIR / f"{lang}.json", encoding="utf-8") as f:
            data = json.load(f)
        for key in REQUIRED_KEYS:
            assert key in data, f"Missing key '{key}' in {lang}.json"


def test_locale_files_valid_json():
    for path in LOCALE_DIR.glob("*.json"):
        with open(path, encoding="utf-8") as f:
            json.load(f)
