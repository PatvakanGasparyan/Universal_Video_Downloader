"""Pydantic schemas and ORM models for downloads."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class DownloadStatus(StrEnum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    CONVERTING = "converting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadRecord(Base):
    """Persisted download history entry."""

    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(512), default="")
    channel: Mapped[str] = mapped_column(String(256), default="")
    format: Mapped[str] = mapped_column(String(32), default="mp4")
    quality: Mapped[str] = mapped_column(String(32), default="best")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str] = mapped_column(Text, default="")
    file_name: Mapped[str] = mapped_column(String(512), default="")
    s3_key: Mapped[str] = mapped_column(Text, default="")
    s3_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=DownloadStatus.QUEUED)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")


class AppSettingsRecord(Base):
    """Persisted user settings (single-row configuration)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    default_quality: Mapped[str] = mapped_column(String(32), default="best")
    default_format: Mapped[str] = mapped_column(String(32), default="mp4")
    default_folder: Mapped[str] = mapped_column(Text, default="")
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    theme: Mapped[str] = mapped_column(String(16), default="dark")
    max_concurrent_downloads: Mapped[int] = mapped_column(Integer, default=3)
    auto_convert_mp3: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_update_ytdlp: Mapped[bool] = mapped_column(Boolean, default=False)
    ffmpeg_location: Mapped[str] = mapped_column(Text, default="")
    cookies_file: Mapped[str] = mapped_column(Text, default="")


class FormatOption(BaseModel):
    """Available download format option."""

    id: str
    label: str
    quality: str
    format: str
    codec: str = ""
    fps: float | None = None
    bitrate: int | None = None
    estimated_size: int | None = None
    has_audio: bool = True
    has_video: bool = True

    @field_validator("bitrate", "estimated_size", mode="before")
    @classmethod
    def coerce_int_fields(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, float):
            return round(value)
        return int(value)


class VideoMetadata(BaseModel):
    """Extracted video metadata."""

    url: str
    title: str = ""
    channel: str = ""
    duration: int | None = None
    upload_date: str | None = None
    thumbnail: str | None = None
    resolution: str | None = None
    codec: str | None = None
    fps: float | None = None
    bitrate: int | None = None
    estimated_size: int | None = None
    formats: list[FormatOption] = Field(default_factory=list)
    extractor: str = ""

    @field_validator("bitrate", "estimated_size", "duration", mode="before")
    @classmethod
    def coerce_int_fields(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, float):
            return round(value)
        return int(value)


class InfoRequest(BaseModel):
    url: HttpUrl


class DownloadRequest(BaseModel):
    url: HttpUrl
    quality: str = "best"
    format: str = "mp4"
    audio_only: bool = False
    priority: int = 0


class DownloadProgress(BaseModel):
    """Live download progress payload."""

    download_id: str
    status: DownloadStatus
    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float = 0.0
    eta: int | None = None
    current_file: str = ""
    stage: str = ""
    message: str = ""


class DownloadResponse(BaseModel):
    download_id: str
    status: DownloadStatus
    message: str = ""


class HistoryItem(BaseModel):
    id: int
    url: str
    title: str
    format: str
    quality: str
    file_size: int
    status: str
    is_favorite: bool
    created_at: datetime
    file_name: str = ""
    s3_key: str = ""
    s3_url: str = ""

    model_config = {"from_attributes": True}


class SettingsSchema(BaseModel):
    default_quality: str = "best"
    default_format: str = "mp4"
    default_folder: str = ""
    preferred_language: str = "en"
    theme: str = "dark"
    max_concurrent_downloads: int = 3
    auto_convert_mp3: bool = False
    auto_update_ytdlp: bool = False
    ffmpeg_location: str = ""
    cookies_file: str = ""

    model_config = {"from_attributes": True}


class HistorySearchParams(BaseModel):
    query: str = ""
    favorite_only: bool = False


class ApiMessage(BaseModel):
    message: str
    detail: Any | None = None
