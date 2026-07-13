"""API integration tests."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_formats(client):
    response = await client.get("/api/formats")
    assert response.status_code == 200
    data = response.json()
    assert "video_qualities" in data
    assert "1080p" in data["video_qualities"]
    assert "mp4" in data["video_formats"]
    assert isinstance(data["platforms"], list)
    assert data["platforms"][0]["name"] == "YouTube"
    assert "url" in data["platforms"][0]


@pytest.mark.asyncio
async def test_get_settings(client):
    response = await client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["default_quality"] == "best"


@pytest.mark.asyncio
async def test_update_settings(client):
    response = await client.post("/api/settings", json={
        "default_quality": "720p",
        "default_format": "mp4",
        "default_folder": "",
        "preferred_language": "en",
        "theme": "dark",
        "max_concurrent_downloads": 2,
        "auto_convert_mp3": False,
        "auto_update_ytdlp": False,
        "ffmpeg_location": "",
        "cookies_file": "",
    })
    assert response.status_code == 200
    assert response.json()["default_quality"] == "720p"


@pytest.mark.asyncio
async def test_get_history(client):
    response = await client.get("/api/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_invalid_url_info(client):
    response = await client.post("/api/info", json={"url": "not-a-url"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_serve_index(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_serve_history_page(client):
    response = await client.get("/history")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_serve_settings_page(client):
    response = await client.get("/settings")
    assert response.status_code == 200
