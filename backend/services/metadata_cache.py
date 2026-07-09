"""In-memory metadata cache with TTL."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.config.settings import get_settings


class MetadataCache:
    """Thread-safe async metadata cache."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
        self._ttl = get_settings().metadata_cache_ttl

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = (time.time() + self._ttl, value)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()


metadata_cache = MetadataCache()
