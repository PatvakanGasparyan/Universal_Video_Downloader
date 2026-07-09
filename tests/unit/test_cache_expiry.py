"""Unit tests for metadata cache expiry."""

import time

import pytest

from backend.services.metadata_cache import MetadataCache


@pytest.mark.asyncio
async def test_cache_expiry():
    cache = MetadataCache()
    cache._ttl = 0
    await cache.set("key", "value")
    time.sleep(0.01)
    assert await cache.get("key") is None
