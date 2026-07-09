"""Unit tests for logging configuration."""

from backend.config.logging_config import setup_logging
from backend.config.settings import Settings


def test_setup_logging():
    settings = Settings(log_dir=Settings().log_dir, log_level="DEBUG")
    setup_logging(settings)
