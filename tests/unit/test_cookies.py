"""Unit tests for cookies file resolution and persistence."""

from pathlib import Path

import pytest

from backend.services.cookies import (
    resolve_cookies_file,
    save_cookies_content,
)


def test_resolve_cookies_from_env(tmp_path):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text(
        "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tA\tB\n",
        encoding="utf-8",
    )
    result = resolve_cookies_file(env_path=cookies)
    assert result == cookies.resolve()


def test_settings_override_takes_precedence(tmp_path):
    env_cookies = tmp_path / "env.txt"
    env_cookies.write_text(".youtube.com\tTRUE\t/\tFALSE\t0\tA\tenv\n", encoding="utf-8")
    user_cookies = tmp_path / "user.txt"
    user_cookies.write_text(".youtube.com\tTRUE\t/\tFALSE\t0\tA\tuser\n", encoding="utf-8")
    result = resolve_cookies_file(
        env_path=env_cookies,
        override_path=str(user_cookies),
    )
    assert result == user_cookies.resolve()


def test_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_cookies_file(env_path="./nonexistent/cookies.txt") is None


def test_relative_path_resolved_from_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cookies = config_dir / "cookies.txt"
    cookies.write_text(".youtube.com\tTRUE\t/\tFALSE\t0\tA\tB\n", encoding="utf-8")
    result = resolve_cookies_file(env_path=Path("./config/cookies.txt"))
    assert result == cookies.resolve()


def test_save_cookies_content(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    content = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tabc123\n"
    path = save_cookies_content(content)
    assert path.exists()
    assert "SID" in path.read_text(encoding="utf-8")
    assert resolve_cookies_file() == path


def test_save_cookies_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        save_cookies_content("   ")
