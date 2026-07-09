"""Unit tests for Pydantic schemas."""

from backend.models.schemas import (
    DownloadProgress,
    DownloadRequest,
    DownloadStatus,
    FormatOption,
    SettingsSchema,
    VideoMetadata,
)


def test_video_metadata_defaults():
    meta = VideoMetadata(url="https://example.com")
    assert meta.title == ""
    assert meta.formats == []


def test_format_option():
    fmt = FormatOption(id="1080p-mp4", label="1080p MP4", quality="1080p", format="mp4")
    assert fmt.has_audio is True
    assert fmt.has_video is True


def test_download_request_defaults():
    req = DownloadRequest(url="https://youtube.com/watch?v=abc")
    assert req.quality == "best"
    assert req.format == "mp4"
    assert req.audio_only is False


def test_download_progress():
    progress = DownloadProgress(download_id="abc", status=DownloadStatus.DOWNLOADING)
    assert progress.percent == 0.0


def test_settings_schema():
    settings = SettingsSchema()
    assert settings.theme == "dark"
    assert settings.max_concurrent_downloads == 3
