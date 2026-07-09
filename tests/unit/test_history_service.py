"""Unit tests for history and settings services."""

import pytest

from backend.services.history_service import HistoryService, SettingsService


@pytest.mark.asyncio
async def test_settings_get_and_update():
    svc = SettingsService()
    settings = await svc.get_settings()
    assert settings.default_format == "mp4"

    updated = await svc.update_settings(
        settings.model_copy(update={"default_quality": "480p", "theme": "light"})
    )
    assert updated.default_quality == "480p"
    assert updated.theme == "light"


@pytest.mark.asyncio
async def test_history_list_empty():
    svc = HistoryService()
    items = await svc.list_history()
    assert isinstance(items, list)


@pytest.mark.asyncio
async def test_history_delete_nonexistent():
    svc = HistoryService()
    result = await svc.delete(99999)
    assert result is False


@pytest.mark.asyncio
async def test_history_toggle_favorite_nonexistent():
    svc = HistoryService()
    result = await svc.toggle_favorite(99999)
    assert result is None
