"""Unit tests for S3 storage service."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.config.settings import Settings
from backend.services.s3_service import S3StorageService


@pytest.fixture
def s3_settings(tmp_path):
    return Settings.model_construct(
        s3_enabled=True,
        aws_region="us-east-1",
        aws_s3_bucket="test-video-bucket",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        s3_prefix="downloads",
        s3_delete_local_after_upload=True,
        downloads_dir=tmp_path / "downloads",
    )


def test_is_enabled_requires_bucket(s3_settings):
    svc = S3StorageService(s3_settings)
    assert svc.is_enabled is True

    disabled = Settings.model_construct(s3_enabled=True, aws_s3_bucket="")
    assert S3StorageService(disabled).is_enabled is False


def test_build_object_key(s3_settings):
    svc = S3StorageService(s3_settings)
    key = svc.build_object_key("abc123", "My Video.mp4")
    assert key == "downloads/abc123/My Video.mp4"


def test_build_object_url(s3_settings):
    svc = S3StorageService(s3_settings)
    assert svc.build_object_url("downloads/x/file.mp4") == (
        "s3://test-video-bucket/downloads/x/file.mp4"
    )


@pytest.mark.asyncio
async def test_upload_file(s3_settings, tmp_path):
    local_file = tmp_path / "video.mp4"
    local_file.write_bytes(b"fake-video-data")

    mock_client = MagicMock()
    svc = S3StorageService(s3_settings)
    svc._client = mock_client

    key, uri = await svc.upload_file(local_file, "dl001")

    assert key == "downloads/dl001/video.mp4"
    assert uri == "s3://test-video-bucket/downloads/dl001/video.mp4"
    mock_client.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_upload_and_cleanup_deletes_local(s3_settings, tmp_path):
    local_file = tmp_path / "video.mp4"
    local_file.write_bytes(b"data")

    svc = S3StorageService(s3_settings)
    svc._client = MagicMock()

    await svc.upload_and_cleanup(local_file, "dl002")
    assert not local_file.exists()


@pytest.mark.asyncio
async def test_upload_disabled_raises(s3_settings):
    s3_settings.s3_enabled = False
    svc = S3StorageService(s3_settings)
    with pytest.raises(RuntimeError, match="not enabled"):
        await svc.upload_file(Path("missing.mp4"), "id")
