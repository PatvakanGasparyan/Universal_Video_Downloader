"""Unit tests for yt-dlp service helpers."""

from backend.services.ytdlp_service import YtDlpService


def test_build_format_selector_best_mp4():
    svc = YtDlpService()
    result = svc._build_format_selector("best", "mp4")
    assert "bestvideo" in result


def test_build_format_selector_1080p():
    svc = YtDlpService()
    result = svc._build_format_selector("1080p", "mp4")
    assert "height<=1080" in result


def test_build_format_selector_audio():
    svc = YtDlpService()
    result = svc._build_format_selector("best", "mp3", audio_only=True)
    assert result == "bestaudio/best"


def test_estimate_size_with_duration():
    svc = YtDlpService()
    info = {"duration": 120}
    size = svc._estimate_size(info, "1080p", "mp4")
    assert size is not None
    assert size > 0


def test_estimate_audio_size():
    svc = YtDlpService()
    info = {"duration": 180}
    size = svc._estimate_audio_size(info)
    assert size == int((192_000 / 8) * 180)
