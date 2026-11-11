from types import SimpleNamespace

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

    def generate_content(self, **_: object) -> SimpleNamespace:
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


class _FailingModels:
    def generate_content(self, **_: object) -> None:
        raise OSError("offline")


class _FailingClient:
    models = _FailingModels()


def test_provider_error_uses_and_labels_feature_fallback() -> None:
    provider = GeminiProvider(api_key="test-key", client=_FailingClient())
    result = LLMService(provider).generate_structured(
        prompt="Generate a summary.",
        response_model=SampleOutput,
        fallback=lambda: SampleOutput(summary="Deterministic fallback."),
    )
    assert result.value.summary == "Deterministic fallback."
    assert result.provider == "deterministic_fallback"
    assert result.is_fallback is True
    assert "Gemini request failed" in (result.fallback_reason or "")
