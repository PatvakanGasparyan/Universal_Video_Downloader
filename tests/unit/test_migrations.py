"""Tests for SQLite schema migrations."""

import pytest
from sqlalchemy import inspect, text

from backend.database.migrations import apply_sqlite_migrations
from backend.database.session import engine, init_db


def _column_names(connection, table: str) -> set[str]:
    return {col["name"] for col in inspect(connection).get_columns(table)}


@pytest.mark.asyncio
async def test_migration_adds_cookies_file_column():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY,
                    default_quality VARCHAR(32) DEFAULT 'best',
                    ffmpeg_location TEXT DEFAULT ''
                )
                """
            )
        )

    async with engine.begin() as conn:
        await conn.run_sync(apply_sqlite_migrations)

    async with engine.connect() as conn:
        columns = await conn.run_sync(_column_names, "app_settings")
        assert "cookies_file" in columns


@pytest.mark.asyncio
async def test_init_db_applies_migrations():
    await init_db()
    async with engine.connect() as conn:
        columns = await conn.run_sync(_column_names, "app_settings")
        assert "cookies_file" in columns
