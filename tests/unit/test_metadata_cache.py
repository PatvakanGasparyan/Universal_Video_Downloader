"""Unit tests for metadata cache."""

import pytest

from backend.services.metadata_cache import MetadataCache


@pytest.mark.asyncio
async def test_cache_set_and_get():
    cache = MetadataCache()
    cache._ttl = 60
    await cache.set("key1", {"title": "Test"})
    result = await cache.get("key1")
    assert result == {"title": "Test"}


@pytest.mark.asyncio
async def test_cache_miss():
    cache = MetadataCache()
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_clear():
    cache = MetadataCache()
    await cache.set("key", "value")
    await cache.clear()
    assert await cache.get("key") is None
