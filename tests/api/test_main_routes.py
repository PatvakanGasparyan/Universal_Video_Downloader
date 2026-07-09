"""Tests for main app routes."""

import pytest


@pytest.mark.asyncio
async def test_robots_txt(client):
    response = await client.get("/robots.txt")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_manifest(client):
    response = await client.get("/manifest.json")
    assert response.status_code == 200
