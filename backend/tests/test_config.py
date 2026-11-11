"""Tests for application settings — contract §16 defaults and env-var loading."""

import pytest

from app.core.config import Settings, get_settings


def test_settings_fields_have_contract_defaults() -> None:
    """Every new field exists with the contract §16 default (checked via model metadata)."""
    fields = Settings.model_fields

    assert "gemini_api_key" in fields
    assert fields["gemini_api_key"].default is None
    assert fields["gemini_api_key"].repr is False  # secret: never logged

    assert fields["gemini_model"].default == "gemini-2.5-flash"
    assert fields["resume_max_bytes"].default == 5_242_880
    assert fields["resume_parse_max_concurrency"].default == 2
    assert fields["rate_limit_resume_parses_per_hour"].default == 10
    assert fields["task_timeout_resume_parse_seconds"].default == 60
    assert fields["task_watchdog_interval_seconds"].default == 60
    assert fields["task_watchdog_grace_seconds"].default == 30


def test_env_overrides_new_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override the defaults."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("RESUME_MAX_BYTES", "1048576")
    monkeypatch.setenv("RESUME_PARSE_MAX_CONCURRENCY", "4")
    monkeypatch.setenv("RATE_LIMIT_RESUME_PARSES_PER_HOUR", "20")
    monkeypatch.setenv("TASK_TIMEOUT_RESUME_PARSE_SECONDS", "30")
    monkeypatch.setenv("TASK_WATCHDOG_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("TASK_WATCHDOG_GRACE_SECONDS", "15")

    get_settings.cache_clear()
    try:
        settings = Settings()  # type: ignore[call-arg]
        assert settings.gemini_api_key == "test-key"
        assert settings.gemini_model == "gemini-2.5-pro"
        assert settings.resume_max_bytes == 1_048_576
        assert settings.resume_parse_max_concurrency == 4
        assert settings.rate_limit_resume_parses_per_hour == 20
        assert settings.task_timeout_resume_parse_seconds == 30
        assert settings.task_watchdog_interval_seconds == 45
        assert settings.task_watchdog_grace_seconds == 15
    finally:
        get_settings.cache_clear()


def test_gemini_api_key_not_in_repr() -> None:
    """The Gemini API key must never appear in the Settings repr."""
    get_settings.cache_clear()
    try:
        settings = Settings(gemini_api_key="secret-key-value")  # type: ignore[call-arg]
        assert "secret-key-value" not in repr(settings)
    finally:
        get_settings.cache_clear()
