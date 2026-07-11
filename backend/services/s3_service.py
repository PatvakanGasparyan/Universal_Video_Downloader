"""AWS S3 storage service for uploaded video files."""

from __future__ import annotations

import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.config.settings import Settings, get_settings
from backend.services.security import sanitize_filename

logger = logging.getLogger("downloads")


class S3StorageService:
    """Upload downloaded media files to Amazon S3."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any | None = None

    @property
    def is_enabled(self) -> bool:
        """Return True when S3 uploads are configured."""
        return self.settings.s3_enabled and bool(self.settings.aws_s3_bucket)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        session_kwargs: dict[str, Any] = {"region_name": self.settings.aws_region}
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = self.settings.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = self.settings.aws_secret_access_key

        session = boto3.session.Session(**session_kwargs)
        self._client = session.client("s3")
        return self._client

    def build_object_key(self, download_id: str, filename: str) -> str:
        """Build a safe S3 object key for a downloaded file."""
        safe_name = sanitize_filename(filename)
        prefix = self.settings.s3_prefix.strip("/")
        if prefix:
            return f"{prefix}/{download_id}/{safe_name}"
        return f"{download_id}/{safe_name}"

    def build_object_url(self, key: str) -> str:
        """Build the canonical S3 URI for an object."""
        return f"s3://{self.settings.aws_s3_bucket}/{key}"

    def _upload_sync(self, local_path: Path, key: str) -> None:
        content_type, _ = mimetypes.guess_type(local_path.name)
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type

        client = self._get_client()
        try:
            if extra_args:
                client.upload_file(
                    str(local_path),
                    self.settings.aws_s3_bucket,
                    key,
                    ExtraArgs=extra_args,
                )
            else:
                client.upload_file(str(local_path), self.settings.aws_s3_bucket, key)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"S3 upload failed: {exc}") from exc

    async def upload_file(self, local_path: Path, download_id: str) -> tuple[str, str]:
        """
        Upload a local file to S3.

        Returns:
            Tuple of (object_key, s3_uri).
        """
        if not self.is_enabled:
            raise RuntimeError("S3 storage is not enabled")

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        key = self.build_object_key(download_id, local_path.name)
        logger.info(
            "Uploading to S3: bucket=%s key=%s",
            self.settings.aws_s3_bucket,
            key,
            extra={"download_id": download_id},
        )
        await asyncio.to_thread(self._upload_sync, local_path, key)
        return key, self.build_object_url(key)

    async def upload_and_cleanup(self, local_path: Path, download_id: str) -> tuple[str, str]:
        """Upload to S3 and optionally remove the local temporary file."""
        key, uri = await self.upload_file(local_path, download_id)
        if self.settings.s3_delete_local_after_upload and local_path.exists():
            local_path.unlink()
            logger.debug("Removed local file after S3 upload: %s", local_path)
        return key, uri


s3_storage = S3StorageService()
