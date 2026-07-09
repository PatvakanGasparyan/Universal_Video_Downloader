"""Unit tests for API dependencies."""

from backend.api.deps import (
    get_download_manager,
    get_history_service,
    get_settings_service,
    get_ytdlp,
)


def test_dependency_getters():
    assert get_ytdlp() is not None
    assert get_download_manager() is not None
    assert get_history_service() is not None
    assert get_settings_service() is not None
