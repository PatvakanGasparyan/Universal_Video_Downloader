"""API tests for download and info routes."""

import pytest


@pytest.mark.asyncio
async def test_download_invalid_url(client):
    response = await client.post("/api/download", json={
        "url": "not-valid",
        "quality": "720p",
        "format": "mp4",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_download_valid_url(client):
    response = await client.post("/api/download", json={
        "url": "https://example.com/video.mp4",
        "quality": "720p",
        "format": "mp4",
    })
    assert response.status_code == 200
    data = response.json()
    assert "download_id" in data


@pytest.mark.asyncio
async def test_status_not_found(client):
    response = await client.get("/api/status/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pause_not_found(client):
    response = await client.post("/api/download/fake/pause")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_info_invalid_url(client):
    response = await client.post("/api/info", json={"url": "ftp://bad.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_history_not_found(client):
    response = await client.delete("/api/history/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_favorite_not_found(client):
    response = await client.post("/api/history/99999/favorite")
    assert response.status_code == 404
