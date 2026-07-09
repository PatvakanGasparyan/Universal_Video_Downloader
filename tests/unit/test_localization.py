"""Unit tests for localization loader."""

from backend.localization.loader import load_locale, supported_languages


def test_supported_languages():
    langs = supported_languages()
    assert "en" in langs
    assert "ru" in langs
    assert "hy" in langs


def test_load_english():
    strings = load_locale("en")
    assert "app_title" in strings


def test_load_fallback():
    strings = load_locale("xx")
    assert "app_title" in strings
