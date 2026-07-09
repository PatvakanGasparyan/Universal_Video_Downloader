"""Unit tests for security utilities."""

import pytest

from backend.services.security import safe_join, sanitize_filename, validate_url


class TestValidateUrl:
    def test_valid_https_url(self):
        assert validate_url("https://www.youtube.com/watch?v=abc") == "https://www.youtube.com/watch?v=abc"

    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_url("")

    def test_invalid_scheme(self):
        with pytest.raises(ValueError, match="http or https"):
            validate_url("ftp://example.com/video")

    def test_no_host(self):
        with pytest.raises(ValueError, match="valid host"):
            validate_url("https://")


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert sanitize_filename('file<>:"/\\|?*.mp4') == "file_________.mp4"

    def test_empty_name_defaults(self):
        assert sanitize_filename("...") == "download"

    def test_truncates_long_names(self):
        name = "a" * 300
        assert len(sanitize_filename(name)) == 200


class TestSafeJoin:
    def test_valid_join(self, tmp_path):
        result = safe_join(tmp_path, "subdir", "file.mp4")
        assert str(result).startswith(str(tmp_path.resolve()))

    def test_traversal_blocked(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid path"):
            safe_join(tmp_path, "..", "etc", "passwd")

    def test_blocked_patterns(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid path"):
            safe_join(tmp_path, "~/.ssh/id_rsa")
