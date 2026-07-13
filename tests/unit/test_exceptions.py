"""Unit tests for structured error classification."""

from backend.services.exceptions import (
    AuthRequiredError,
    DownloaderError,
    GeoRestrictedError,
    NetworkError,
    RateLimitedError,
    UnsupportedURLError,
    VideoUnavailableError,
    classify_ytdlp_error,
    is_auth_error,
    is_transient,
)


def test_classify_bot_check_is_auth():
    err = classify_ytdlp_error(
        Exception("ERROR: [youtube] xyz: Sign in to confirm you're not a bot"),
        url="https://youtube.com/watch?v=xyz",
    )
    assert isinstance(err, AuthRequiredError)
    assert err.error == "youtube_auth_required"
    assert err.http_status == 401


def test_classify_rutube_404_unavailable():
    err = classify_ytdlp_error(
        Exception("ERROR: [rutube] abc: Unable to download options JSON: HTTP Error 404"),
    )
    assert isinstance(err, VideoUnavailableError)
    assert err.error == "video_unavailable"


def test_classify_geo():
    err = classify_ytdlp_error(Exception("This video is not available in your country"))
    assert isinstance(err, GeoRestrictedError)


def test_classify_rate_limited():
    err = classify_ytdlp_error(Exception("HTTP Error 429: Too Many Requests"))
    assert isinstance(err, RateLimitedError)


def test_classify_network():
    err = classify_ytdlp_error(Exception("Read operation timed out"))
    assert isinstance(err, NetworkError)


def test_classify_unsupported():
    err = classify_ytdlp_error(Exception("Unsupported URL: file:///etc/passwd"))
    assert isinstance(err, UnsupportedURLError)


def test_classify_generic_fallback():
    err = classify_ytdlp_error(Exception("some totally unknown failure"))
    assert err.error == "download_failed"
    assert err.http_status == 422


def test_downloader_error_envelope_hides_debug():
    err = AuthRequiredError(debug="raw secret cookie details")
    payload = err.to_dict()
    assert payload == {
        "success": False,
        "error": "youtube_auth_required",
        "message": "Authentication required.",
        "solution": err.solution,
    }
    assert "debug" not in payload


def test_classify_passthrough_downloader_error():
    original = VideoUnavailableError(debug="x")
    assert classify_ytdlp_error(original) is original


def test_is_auth_and_transient_helpers():
    assert is_auth_error("Sign in to confirm you're not a bot")
    assert is_auth_error("HTTP Error 429")
    assert not is_auth_error("Video unavailable")
    assert is_transient(NetworkError())
    assert is_transient(RateLimitedError())
    assert not is_transient(VideoUnavailableError())
    assert not is_transient(DownloaderError())
