"""Unit tests for yt-dlp metadata parsing."""

from backend.services.ytdlp_service import YtDlpService


def test_parse_metadata_float_bitrate():
    svc = YtDlpService()
    info = {
        "title": "Test Video",
        "uploader": "Test Channel",
        "duration": 120.7,
        "tbr": 289.47,
        "filesize_approx": 1024.8,
        "formats": [{"format_id": "22", "tbr": 289.47, "fps": 30}],
        "format_id": "22",
    }
    meta = svc._parse_metadata("https://youtube.com/watch?v=test", info)
    assert meta.bitrate == 289
    assert meta.duration == 121
    assert meta.estimated_size == 1025


def test_video_metadata_float_bitrate_validator():
    from backend.models.schemas import VideoMetadata

    meta = VideoMetadata(url="https://example.com", bitrate=289.47, estimated_size=1000.6)
    assert meta.bitrate == 289
    assert meta.estimated_size == 1001


def test_parse_metadata_basic():
    svc = YtDlpService()
    info = {
        "title": "Test Video",
        "uploader": "Test Channel",
        "duration": 120,
        "upload_date": "20260101",
        "thumbnail": "https://example.com/thumb.jpg",
        "extractor": "YouTube",
        "formats": [],
    }
    meta = svc._parse_metadata("https://youtube.com/watch?v=test", info)
    assert meta.title == "Test Video"
    assert meta.channel == "Test Channel"
    assert meta.duration == 120


def test_build_format_options():
    svc = YtDlpService()
    info = {"duration": 60, "height": 1080}
    options = svc._build_format_options(info)
    assert len(options) > 0
    assert any(o.quality == "1080p" for o in options)


def test_postprocessor_audio():
    svc = YtDlpService()
    pp = svc._postprocessor("mp3", audio_only=True)
    assert pp[0]["key"] == "FFmpegExtractAudio"


def test_postprocessor_video():
    svc = YtDlpService()
    pp = svc._postprocessor("mp4", audio_only=False)
    assert pp[0]["key"] == "FFmpegVideoConvertor"
