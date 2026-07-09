"""FastAPI dependency injection helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import async_session_factory
from backend.services.download_manager import download_manager
from backend.services.history_service import history_service, settings_service
from backend.services.ytdlp_service import ytdlp_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_ytdlp():
    return ytdlp_service


def get_download_manager():
    return download_manager


def get_history_service():
    return history_service


def get_settings_service():
    return settings_service
