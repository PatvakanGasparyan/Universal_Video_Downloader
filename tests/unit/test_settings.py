"""Unit tests for application settings."""

from backend.config.settings import Settings, get_settings


def test_default_settings():
    settings = Settings()
    assert settings.backend_port == 8000
    assert settings.max_concurrent_downloads == 3


def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_resolved_downloads_dir(tmp_path, monkeypatch):
    settings = Settings(downloads_dir=tmp_path / "dl")
    path = settings.resolved_downloads_dir
    assert path.exists()
