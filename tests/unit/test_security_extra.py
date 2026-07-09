"""Unit tests for security edge cases."""

import pytest

from backend.services.security import safe_join, sanitize_filename, validate_url


def test_sanitize_truncation():
    assert len(sanitize_filename("a" * 300)) == 200


def test_safe_join_valid(tmp_path):
    result = safe_join(tmp_path, "video.mp4")
    assert result.parent == tmp_path.resolve()


def test_validate_url_strips_whitespace():
    url = validate_url("  https://youtube.com/watch?v=abc  ")
    assert url == "https://youtube.com/watch?v=abc"


def test_validate_url_invalid_format():
    with pytest.raises(ValueError):
        validate_url("https://")
