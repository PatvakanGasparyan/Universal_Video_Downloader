"""Unit tests for the yt-dlp cookie fallback pipeline."""

from unittest.mock import patch

import pytest

from backend.services.exceptions import AuthRequiredError, VideoUnavailableError
from backend.services.ytdlp_service import YtDlpService


def _svc_with_cookies(tmp_path, browsers=True):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape\n.youtube.com\tTRUE\t/\tTRUE\t0\tk\tv\n", encoding="utf-8")
    svc = YtDlpService()
    svc.settings.cookies_from_browser = browsers
    svc.settings.cookie_browser_order = ["chrome", "chromium", "edge", "firefox"]
    svc.settings.transient_retry_attempts = 0
    return svc, cookies


def test_strategy_order_full_chain(tmp_path):
    svc, cookies = _svc_with_cookies(tmp_path, browsers=True)
    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        strategies = svc._cookie_strategies()

    labels = [name for name, _ in strategies]
    assert labels == [
        "anonymous",
        "browser:chrome",
        "browser:chromium",
        "browser:edge",
        "browser:firefox",
        "cookies.txt",
    ]
    # cookiesfrombrowser must be a proper 4-tuple for yt-dlp.
    assert strategies[1][1]["cookiesfrombrowser"] == ("chrome", None, None, None)
    assert strategies[-1][1]["cookiefile"] == str(cookies)


def test_strategy_order_no_browser(tmp_path):
    svc, cookies = _svc_with_cookies(tmp_path, browsers=False)
    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        labels = [name for name, _ in svc._cookie_strategies()]
    assert labels == ["anonymous", "cookies.txt"]


@pytest.mark.asyncio
async def test_fallback_advances_on_auth_then_succeeds_with_cookies(tmp_path):
    svc, cookies = _svc_with_cookies(tmp_path, browsers=False)
    tried: list[bool] = []

    def runner(url, opts):
        has_cookie = "cookiefile" in opts
        tried.append(has_cookie)
        if not has_cookie:
            raise Exception("Sign in to confirm you're not a bot")
        return {"ok": True}

    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        result = await svc._execute_with_fallback(
            "https://youtube.com/watch?v=x", {"skip_download": True}, runner, label="test"
        )

    assert result == {"ok": True}
    # anonymous (no cookie) first, then cookies.txt succeeded.
    assert tried == [False, True]


@pytest.mark.asyncio
async def test_fallback_all_auth_raises_auth_error(tmp_path):
    svc, cookies = _svc_with_cookies(tmp_path, browsers=False)

    def runner(url, opts):
        raise Exception("Sign in to confirm you're not a bot")

    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        with pytest.raises(AuthRequiredError):
            await svc._execute_with_fallback(
                "https://youtube.com/watch?v=x", {}, runner, label="test"
            )


@pytest.mark.asyncio
async def test_fallback_non_auth_fails_fast(tmp_path):
    svc, cookies = _svc_with_cookies(tmp_path, browsers=True)
    calls = {"n": 0}

    def runner(url, opts):
        calls["n"] += 1
        raise Exception("Video unavailable")

    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        with pytest.raises(VideoUnavailableError):
            await svc._execute_with_fallback("https://youtube.com/x", {}, runner, label="test")

    # Must not try further strategies for a non-auth failure.
    assert calls["n"] == 1
