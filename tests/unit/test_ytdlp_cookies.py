"""Unit tests for yt-dlp cookie configuration."""

from unittest.mock import patch

from backend.services.ytdlp_service import YtDlpService


def test_base_opts_includes_cookiefile(tmp_path):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape\n", encoding="utf-8")

    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=cookies):
        svc = YtDlpService()
        opts = svc._base_opts()
        assert opts["cookiefile"] == str(cookies)


def test_base_opts_without_cookies():
    with patch("backend.services.ytdlp_service.resolve_cookies_file", return_value=None):
        svc = YtDlpService()
        opts = svc._base_opts()
        assert "cookiefile" not in opts
