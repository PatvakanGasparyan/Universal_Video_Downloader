"""Test fixtures and configuration."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DOWNLOADS_DIR"] = "./backend/downloads/test"
os.environ["TEMP_DIR"] = "./backend/downloads/test/temp"

import pytest
from httpx import ASGITransport, AsyncClient

from backend.config.settings import get_settings
from backend.database.session import engine
from backend.main import app
from backend.services.download_manager import download_manager

get_settings.cache_clear()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        from backend.database.base import Base
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def manager():
    if not download_manager._running:
        await download_manager.start()
    yield download_manager
