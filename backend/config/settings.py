"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Universal Video Downloader"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=3000, alias="FRONTEND_PORT")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        alias="DATABASE_URL",
    )
    downloads_dir: Path = Field(
        default=Path("./backend/downloads"),
        alias="DOWNLOADS_DIR",
    )
    temp_dir: Path = Field(default=Path("./backend/downloads/temp"), alias="TEMP_DIR")

    ffmpeg_location: str | None = Field(default=None, alias="FFMPEG_LOCATION")
    cookies_file: Path | None = Field(
        default=Path("./data/cookies.txt"),
        alias="COOKIES_FILE",
    )
    max_concurrent_downloads: int = Field(default=3, alias="MAX_CONCURRENT_DOWNLOADS")
    metadata_cache_ttl: int = Field(default=3600, alias="METADATA_CACHE_TTL")
    rate_limit: str = Field(default="30/minute", alias="RATE_LIMIT")

    # --- Download pipeline / yt-dlp reliability ---
    # When a site blocks anonymous access, try to load cookies directly from a
    # locally-installed browser before falling back to cookies.txt. Disable on
    # headless servers (no browser profile) to save time.
    cookies_from_browser: bool = Field(default=True, alias="COOKIES_FROM_BROWSER")
    cookie_browser_order: list[str] = Field(
        default=["chrome", "chromium", "edge", "firefox"],
        alias="COOKIE_BROWSER_ORDER",
    )
    ytdlp_socket_timeout: int = Field(default=30, alias="YTDLP_SOCKET_TIMEOUT")
    ytdlp_retries: int = Field(default=3, alias="YTDLP_RETRIES")
    extract_timeout: int = Field(default=90, alias="EXTRACT_TIMEOUT")
    transient_retry_attempts: int = Field(default=2, alias="TRANSIENT_RETRY_ATTEMPTS")

    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    default_quality: str = "best"
    default_format: str = "mp4"
    default_language: Literal["en", "ru", "hy"] = "en"
    auto_convert_mp3: bool = False
    auto_update_ytdlp: bool = False

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=Path("./logs"), alias="LOG_DIR")

    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # AWS S3 storage
    s3_enabled: bool = Field(default=False, alias="S3_ENABLED")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_s3_bucket: str = Field(default="", alias="AWS_S3_BUCKET")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    s3_prefix: str = Field(default="downloads", alias="S3_PREFIX")
    s3_delete_local_after_upload: bool = Field(
        default=True,
        alias="S3_DELETE_LOCAL_AFTER_UPLOAD",
    )

    @property
    def s3_configured(self) -> bool:
        """Return True when S3 uploads should be used."""
        return self.s3_enabled and bool(self.aws_s3_bucket)

    @property
    def resolved_downloads_dir(self) -> Path:
        path = self.downloads_dir.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_temp_dir(self) -> Path:
        path = self.temp_dir.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
