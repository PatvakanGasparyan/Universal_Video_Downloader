"""API tests for cookies upload."""

import pytest


@pytest.mark.asyncio
async def test_cookies_status(client):
    response = await client.get("/api/settings/cookies")
    assert response.status_code == 200
    data = response.json()
    assert "exists" in data
    assert "path" in data


@pytest.mark.asyncio
async def test_upload_cookies_content(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    content = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\ttestvalue\n"
    response = await client.post(
        "/api/settings/cookies",
        data={"content": content},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Cookies saved successfully"

    status = await client.get("/api/settings/cookies")
    assert status.json()["exists"] is True


@pytest.mark.asyncio
async def test_upload_cookies_empty(client):
    response = await client.post("/api/settings/cookies", data={})
    assert response.status_code == 400
