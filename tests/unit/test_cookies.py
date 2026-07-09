"""Unit tests for cookies file resolution."""

from pathlib import Path

from backend.services.cookies import resolve_cookies_file


def test_resolve_cookies_from_env(tmp_path):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    result = resolve_cookies_file(env_path=cookies)
    assert result == cookies.resolve()


def test_settings_override_takes_precedence(tmp_path):
    env_cookies = tmp_path / "env.txt"
    env_cookies.write_text("env", encoding="utf-8")
    user_cookies = tmp_path / "user.txt"
    user_cookies.write_text("user", encoding="utf-8")
    result = resolve_cookies_file(
        env_path=env_cookies,
        override_path=str(user_cookies),
    )
    assert result == user_cookies.resolve()


def test_returns_none_when_missing():
    assert resolve_cookies_file(env_path="./nonexistent/cookies.txt") is None


def test_relative_path_resolved_from_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cookies = config_dir / "cookies.txt"
    cookies.write_text("data", encoding="utf-8")
    result = resolve_cookies_file(env_path=Path("./config/cookies.txt"))
    assert result == cookies.resolve()
