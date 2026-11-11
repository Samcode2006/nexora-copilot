"""Offline reliability and error-hygiene tests for AI provider boundaries."""

from __future__ import annotations

import logging
import sys
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError

import pytest
from pydantic import BaseModel, ConfigDict

from app.ai.job_intelligence import (
    JobProviderConfigurationError,
    JobProviderError,
    MockJobProvider,
    RemotiveJobProvider,
    create_job_provider_from_env,
    search_jobs,
)
from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching import match_jobs
from app.ai.job_matching.embeddings import (
    EmbeddingProviderError,
    SentenceTransformerEmbeddingProvider,
)
from app.ai.providers import (
    GeminiProvider,
    LLMService,
    ProviderUnavailableError,
    create_llm_service,
)
from app.ai.resume_intelligence import (
    EducationProfile,
    EvidenceValue,
    PersonalInformation,
    ProjectProfile,
    SkillProfile,
    StudentProfile,
    StudentProfileFields,
    extract_student_profile,
)

SECRET_SENTINEL = "secret-provider-token-DO-NOT-LEAK"


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str


class _FakeModels:
    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate_content(self, **_: Any) -> SimpleNamespace:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return SimpleNamespace(text=response)


class _FakeClient:
    def __init__(self, *responses: Any) -> None:
        self.models = _FakeModels(*responses)


class _QueueProvider:
    name = "offline_provider_fixture"

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        del prompt, response_model
        self.calls += 1
        if not self.responses:
            raise AssertionError("Provider called more times than the test configured.")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def _generate(
    provider: GeminiProvider | _QueueProvider,
    *,
    attempts: int = 2,
):
    return LLMService(provider).generate_structured(
        prompt=f"Test prompt with private resume text {SECRET_SENTINEL}",
        response_model=StrictOutput,
        fallback=lambda: StrictOutput(summary="Deterministic fixture fallback."),
        max_attempts=attempts,
    )


def test_missing_gemini_credentials_use_safe_labeled_fallback(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = create_llm_service()

    result = service.generate_structured(
        prompt="offline",
        response_model=StrictOutput,
        fallback=lambda: StrictOutput(summary="fallback"),
    )

    assert service.provider is None
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    assert result.value.summary == "fallback"
    assert result.fallback_reason == "No LLM provider is configured."
    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY is not configured"):
        GeminiProvider()


@pytest.mark.parametrize("api_key", ["", "   "])
def test_blank_gemini_credentials_are_rejected_safely(api_key: str) -> None:
    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY is not configured") as error:
        GeminiProvider(api_key=api_key)
    assert "Authorization" not in str(error.value)


def test_invalid_gemini_model_configuration_is_rejected_safely() -> None:
    with pytest.raises(ProviderUnavailableError, match="model configuration is invalid"):
        GeminiProvider(api_key="offline-test-key", model="   ")


def test_gemini_client_initialization_failure_is_sanitized(monkeypatch, caplog) -> None:
    from google import genai

    def reject_client(*, api_key: str, **_: Any) -> None:
        assert api_key == SECRET_SENTINEL
        raise RuntimeError(f"invalid credential {api_key}; Authorization: Bearer {api_key}")

    monkeypatch.setenv("GEMINI_API_KEY", SECRET_SENTINEL)
    monkeypatch.setattr(genai, "Client", reject_client)
    caplog.set_level(logging.WARNING)

    service = create_llm_service()
    result = service.generate_structured(
        prompt="offline",
        response_model=StrictOutput,
        fallback=lambda: StrictOutput(summary="fallback"),
    )

    assert service.provider is None
    assert result.is_fallback is True
    assert result.fallback_reason
    assert "initial" in result.fallback_reason.casefold()
    assert SECRET_SENTINEL not in result.fallback_reason
    assert SECRET_SENTINEL not in caplog.text
    assert "RuntimeError" in caplog.text


def test_gemini_client_has_a_finite_request_timeout(monkeypatch) -> None:
    from google import genai

    captured: dict[str, Any] = {}

    def make_client(*, api_key: str, http_options: Any) -> _FakeClient:
        captured["api_key"] = api_key
        captured["http_options"] = http_options
        return _FakeClient('{"summary":"ok"}')

    monkeypatch.setattr(genai, "Client", make_client)
    provider = GeminiProvider(api_key="offline-test-key")
    assert provider is not None
    options = captured["http_options"]
    timeout_ms = options.timeout if hasattr(options, "timeout") else options["timeout"]
    assert isinstance(timeout_ms, int)
    assert 0 < timeout_ms <= 120_000


@pytest.mark.parametrize(
    "response_text",
    [
        "{invalid-json",
        "{}",  # missing required field
        '{"summary":"ok","unexpected":"field"}',
        '{"summary":42}',
        None,
        "",
    ],
    ids=["invalid-json", "missing-field", "unexpected-field", "wrong-type", "null-response", "empty-response"],
)
def test_malformed_gemini_responses_retry_then_use_safe_fallback(
    response_text: Any,
    caplog,
) -> None:
    provider = GeminiProvider(
        api_key=SECRET_SENTINEL,
        client=_FakeClient(response_text, response_text),
    )
    caplog.set_level(logging.WARNING)

    result = _generate(provider)

    assert provider._client.models.calls == 2
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    assert result.value.summary == "Deterministic fixture fallback."
    assert result.fallback_reason
    assert SECRET_SENTINEL not in result.fallback_reason
    assert "Test prompt" not in caplog.text
    assert SECRET_SENTINEL not in caplog.text


def test_invalid_structured_payload_retries_and_recovers() -> None:
    provider = _QueueProvider({"unexpected": "first"}, {"summary": "second try"})
    result = _generate(provider)
    assert provider.calls == 2
    assert result.value.summary == "second try"
    assert result.provider == "offline_provider_fixture"
    assert result.is_fallback is False


def test_unexpected_provider_exception_is_sanitized_and_not_retried(caplog) -> None:
    provider = _QueueProvider(
        RuntimeError(f"SDK failed with {SECRET_SENTINEL}; Authorization: Bearer {SECRET_SENTINEL}")
    )
    caplog.set_level(logging.WARNING)

    result = _generate(provider)

    assert provider.calls == 1
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    assert "provider" in (result.fallback_reason or "").casefold()
    assert SECRET_SENTINEL not in (result.fallback_reason or "")
    assert SECRET_SENTINEL not in caplog.text
    assert "RuntimeError" in caplog.text
    assert "Test prompt" not in caplog.text


class _StatusError(RuntimeError):
    def __init__(self, status: int) -> None:
        self.code = status
        self.status_code = status
        super().__init__(f"HTTP {status} with {SECRET_SENTINEL}; Authorization: Bearer {SECRET_SENTINEL}")


@pytest.mark.parametrize(
    ("failure", "expected_calls", "category"),
    [
        (TimeoutError(f"timeout {SECRET_SENTINEL}"), 2, "timed out"),
        (ConnectionError(f"connection failed {SECRET_SENTINEL}"), 2, "connection"),
        (_StatusError(429), 2, "rate"),
        (_StatusError(500), 2, "server"),
        (_StatusError(503), 2, "server"),
        (_StatusError(401), 1, "auth"),
        (_StatusError(403), 1, "auth"),
        (RuntimeError(f"unexpected SDK error {SECRET_SENTINEL}"), 1, "provider"),
    ],
    ids=["timeout", "connection", "rate-limit", "server-500", "server-503", "auth-401", "auth-403", "unexpected-sdk-error"],
)
def test_gemini_failure_categories_are_bounded_and_sanitized(
    failure: BaseException,
    expected_calls: int,
    category: str,
    caplog,
) -> None:
    provider = GeminiProvider(
        api_key=SECRET_SENTINEL,
        client=_FakeClient(failure, failure),
    )
    caplog.set_level(logging.WARNING)

    result = _generate(provider)

    assert provider._client.models.calls == expected_calls
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    assert category in (result.fallback_reason or "").casefold()
    assert SECRET_SENTINEL not in (result.fallback_reason or "")
    assert SECRET_SENTINEL not in caplog.text
    assert "Test prompt" not in caplog.text
    assert "Gemini" in caplog.text


def test_remotive_retries_only_transient_http_failures_and_sanitizes_logs(
    caplog,
) -> None:
    caplog.set_level(logging.WARNING)
    for status, expected_calls in ((429, 2), (500, 2), (503, 2), (401, 1), (403, 1)):
        calls = 0
        secret_url = f"https://remotive.invalid/jobs?token={SECRET_SENTINEL}"

        def fail(url: str, timeout: float, *, status: int = status) -> bytes:
            nonlocal calls
            calls += 1
            raise HTTPError(
                url,
                status,
                f"provider detail {SECRET_SENTINEL}",
                hdrs={"Authorization": f"Bearer {SECRET_SENTINEL}"},
                fp=None,
            )

        provider = RemotiveJobProvider(
            endpoint=secret_url,
            fetcher=fail,
            retry_backoff_seconds=0,
        )
        with pytest.raises(JobProviderError) as error:
            search_jobs("backend", provider=provider)

        assert calls == expected_calls
        assert f"HTTP {status}" in str(error.value)
        assert SECRET_SENTINEL not in str(error.value)
        assert SECRET_SENTINEL not in caplog.text
        assert f"HTTP {status}" in caplog.text


def test_missing_job_provider_configuration_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("JOBS_PROVIDER", raising=False)
    provider = create_job_provider_from_env()
    assert isinstance(provider, MockJobProvider)
    assert provider.is_mock is True


@pytest.mark.parametrize(
    ("variable", "value", "expected_message"),
    [
        ("JOBS_PROVIDER", "invalid-provider-secret", "Unsupported JOBS_PROVIDER"),
        ("JOB_PROVIDER_TIMEOUT_SECONDS", "not-a-number-secret", "must be a number"),
        ("REMOTIVE_API_URL", "http://secret.invalid/jobs", "must use HTTPS"),
    ],
)
def test_invalid_job_provider_configuration_is_safe(
    monkeypatch,
    variable: str,
    value: str,
    expected_message: str,
) -> None:
    monkeypatch.setenv("JOBS_PROVIDER", "remotive")
    monkeypatch.setenv(variable, value)
    with pytest.raises(JobProviderConfigurationError) as error:
        create_job_provider_from_env()
    assert expected_message in str(error.value)
    assert value not in str(error.value)


def _supported_profile_and_job() -> tuple[StudentProfile, JobListing]:
    profile = StudentProfile(
        education=[
            EducationProfile(
                branch=EvidenceValue(
                    value="Computer Science",
                    source_text="Branch: Computer Science",
                    evidence_status="explicit",
                    verification_status="unverified",
                )
            )
        ],
        skills=SkillProfile(
            programming_languages=[
                EvidenceValue(
                    value="Python",
                    source_text="Programming Languages: Python",
                    evidence_status="explicit",
                    verification_status="unverified",
                )
            ]
        ),
        projects=[
            ProjectProfile(
                description=EvidenceValue(
                    value="Built Python APIs",
                    source_text="Built Python APIs",
                    evidence_status="explicit",
                    verification_status="unverified",
                )
            )
        ],
    )
    job = JobListing(
        job_id="fixture:backend",
        title="Python Backend Engineer",
        description="Build APIs and data services.",
        required_skills=["Python"],
        source_provider="fixture",
        source_job_id="backend",
    )
    return profile, job


def test_missing_embedding_package_uses_keyword_fallback(monkeypatch, caplog) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "sentence-transformers")
    monkeypatch.setenv("JOB_MATCH_MODEL", "nexora-offline-test-model")
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    profile, job = _supported_profile_and_job()
    caplog.set_level(logging.WARNING)

    matches = match_jobs(profile, [job])

    assert len(matches) == 1
    assert matches[0].matching_method == "keyword_fallback"
    assert any("Semantic embeddings were unavailable" in warning for warning in matches[0].warnings)
    assert "sentence-transformers is not installed" in caplog.text
    assert "Built Python APIs" not in caplog.text


def test_invalid_embedding_mode_is_reported_and_falls_back(monkeypatch, caplog) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", f"invalid-{SECRET_SENTINEL}")
    profile, job = _supported_profile_and_job()
    caplog.set_level(logging.WARNING)

    matches = match_jobs(profile, [job])

    assert matches[0].matching_method == "keyword_fallback"
    assert any("Unsupported JOB_MATCH_EMBEDDINGS" in warning for warning in matches[0].warnings)
    assert SECRET_SENTINEL not in caplog.text
    assert "Built Python APIs" not in caplog.text


def test_optional_embedding_provider_error_is_a_safe_typed_error(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    provider = SentenceTransformerEmbeddingProvider("nexora-offline-test-model")
    with pytest.raises(EmbeddingProviderError, match="sentence-transformers is not installed"):
        provider.similarities([("profile", "job")])


def test_schema_valid_provider_output_with_unsupported_claim_is_omitted() -> None:
    unsupported = StudentProfileFields(
        personal_information=PersonalInformation(
            name=EvidenceValue(value="Asha Rao", source_text="Name: Asha Rao")
        ),
        projects=[
            ProjectProfile(
                achievements=[
                    EvidenceValue(
                        value="Increased revenue by 80%.",
                        source_text="Name: Asha Rao",
                    )
                ]
            )
        ],
    )
    provider = _QueueProvider(unsupported)

    profile = extract_student_profile(
        "Name: Asha Rao",
        llm_service=LLMService(provider),
    )

    assert profile.personal_information.name is not None
    assert profile.personal_information.name.value == "Asha Rao"
    assert profile.projects == []
    assert profile.is_fallback is False
    assert any("unsupported" in warning for warning in profile.warnings)

