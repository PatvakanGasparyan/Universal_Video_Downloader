"""Unit tests for database session helpers."""

import pytest

from backend.database.session import get_session, init_db


@pytest.mark.asyncio
async def test_get_session():
    gen = get_session()
    session = await gen.__anext__()
    assert session is not None
    await gen.aclose()


@pytest.mark.asyncio
async def test_init_db():
    await init_db()
