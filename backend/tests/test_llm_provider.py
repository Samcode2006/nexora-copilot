import sys
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.ai.providers import GeminiProvider, LLMService


class SampleOutput(BaseModel):
    summary: str


def test_service_labels_deterministic_fallback() -> None:
    service = LLMService()
    result = service.generate_structured(
        prompt="Summarize the source text.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Source text retained for review."),
    )
    assert result.value.summary == "Source text retained for review."
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True


class _FakeModels:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.response_text)


class _FakeClient:
    def __init__(self, response_text: str) -> None:
        self.models = _FakeModels(response_text)


def test_gemini_provider_validates_structured_output_without_network() -> None:
    provider = GeminiProvider(
        api_key="test-key",
        client=_FakeClient('{"summary":"Parsed by the test provider."}'),
    )
    result = LLMService(provider).generate_structured(
        prompt="Generate a summary.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Fallback."),
    )
    assert result.value.summary == "Parsed by the test provider."
    assert result.provider == "gemini"
    assert result.is_fallback is False


@pytest.fixture
def google_sdk_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `import google.genai` fail, as when the optional 'gemini' extra is absent."""
    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.genai", None)


def test_injected_client_works_without_google_sdk(google_sdk_unavailable: None) -> None:
    client = _FakeClient('{"summary":"Parsed by the test provider."}')
    result = LLMService(GeminiProvider(api_key="test-key", client=client)).generate_structured(
        prompt="Generate a summary.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Fallback."),
    )
    assert result.value.summary == "Parsed by the test provider."
    assert result.is_fallback is False
    (call,) = client.models.calls
    assert call["model"] == "gemini-2.5-flash"
    assert call["config"] == {
        "response_mime_type": "application/json",
        "response_schema": SampleOutput,
    }


def test_response_not_matching_schema_uses_and_labels_fallback() -> None:
    provider = GeminiProvider(api_key="test-key", client=_FakeClient('{"wrong": 1}'))
    result = LLMService(provider).generate_structured(
        prompt="Generate a summary.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Deterministic fallback."),
    )
    assert result.value.summary == "Deterministic fallback."
    assert result.is_fallback is True
    assert result.fallback_reason == "Gemini returned invalid structured output."


class _FailingModels:
    def generate_content(self, **_: object) -> None:
        raise OSError("offline")


class _FailingClient:
    models = _FailingModels()


def test_provider_error_uses_and_labels_feature_fallback(google_sdk_unavailable: None) -> None:
    provider = GeminiProvider(api_key="test-key", client=_FailingClient())
    result = LLMService(provider).generate_structured(
        prompt="Generate a summary.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Deterministic fallback."),
    )
    assert result.value.summary == "Deterministic fallback."
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    # Preserve a safe category while omitting raw provider details.
    assert result.fallback_reason == "Gemini request failed: connection error."


class _BuggyModels:
    def generate_content(self, **_: object) -> None:
        raise TypeError("unexpected keyword argument")


class _BuggyClient:
    models = _BuggyModels()


def test_programming_errors_are_not_converted_to_fallback() -> None:
    provider = GeminiProvider(api_key="test-key", client=_BuggyClient())
    with pytest.raises(TypeError):
        LLMService(provider).generate_structured(
            prompt="Generate a summary.",
            response_model=SampleOutput,
            fallback=lambda: SampleOutput(summary="Should not be used."),
        )
