"""Lightweight SQLite schema migrations for existing databases."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)

# (table_name, column_name, column_ddl_suffix)
_SQLITE_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("app_settings", "cookies_file", "TEXT NOT NULL DEFAULT ''"),
    ("download_history", "s3_key", "TEXT NOT NULL DEFAULT ''"),
    ("download_history", "s3_url", "TEXT NOT NULL DEFAULT ''"),
    ("download_history", "download_id", "VARCHAR(32) NOT NULL DEFAULT ''"),
]


def apply_sqlite_migrations(connection: Connection) -> None:
    """Add missing columns to existing SQLite tables."""
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())

    for table_name, column_name, column_ddl in _SQLITE_COLUMN_MIGRATIONS:
        if table_name not in existing_tables:
            continue

        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        if column_name in existing_columns:
            continue

        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}"
        connection.execute(text(sql))
        logger.info("Applied migration: %s.%s", table_name, column_name)
