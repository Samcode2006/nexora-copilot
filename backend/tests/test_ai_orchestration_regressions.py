from __future__ import annotations

import inspect
import sys
from types import SimpleNamespace

from pydantic import BaseModel

from app.ai.interview_intelligence.evaluation import evaluate_interview_answer
from app.ai.interview_intelligence.question_generator import generate_interview_questions
from app.ai.job_intelligence.discovery import search_jobs
from app.ai.job_intelligence.normalizer import normalize_job, normalize_jobs
from app.ai.job_matching.scoring import match_jobs
from app.ai.orchestration.services import OrchestrationServices
from app.ai.providers import GeminiProvider, LLMService
from app.ai.resume_intelligence.parser import parse_resume
from app.ai.resume_intelligence.profile_extractor import extract_student_profile
from app.ai.resume_tailoring.cover_letter import generate_cover_letter
from app.ai.resume_tailoring.tailoring import tailor_resume


def test_existing_public_ai_service_signatures_remain_unchanged() -> None:
    assert tuple(inspect.signature(parse_resume).parameters) == (
        "content",
        "filename",
        "max_file_bytes",
    )
    assert tuple(inspect.signature(extract_student_profile).parameters) == (
        "resume_text",
        "llm_service",
    )
    assert tuple(inspect.signature(search_jobs).parameters) == (
        "query",
        "location",
        "limit",
        "provider",
    )
    assert tuple(inspect.signature(normalize_job).parameters) == (
        "raw_job",
        "source_provider",
        "is_mock",
    )
    assert tuple(inspect.signature(normalize_jobs).parameters) == (
        "raw_jobs",
        "source_provider",
        "is_mock",
    )
    assert tuple(inspect.signature(match_jobs).parameters) == (
        "student_profile",
        "job_listings",
        "config",
        "embedding_provider",
    )
    assert tuple(inspect.signature(tailor_resume).parameters) == (
        "student_profile",
        "job_listing",
        "job_match",
        "preferences",
        "llm_service",
    )
    assert tuple(inspect.signature(generate_cover_letter).parameters) == (
        "student_profile",
        "job_listing",
        "tailored_resume",
        "preferences",
        "llm_service",
    )
    assert tuple(inspect.signature(generate_interview_questions).parameters) == (
        "student_profile",
        "job_listing",
        "interview_type",
        "difficulty",
        "question_count",
        "job_match",
        "llm_service",
        "focus_competency",
        "exclude_question_texts",
        "variant_offset",
    )
    assert tuple(inspect.signature(evaluate_interview_answer).parameters) == (
        "question",
        "answer",
        "student_profile",
        "job_listing",
        "llm_service",
        "rubric_weights",
    )


class _FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text='{"answer":"ok"}')


class _FakeClient:
    def __init__(self) -> None:
        self.models = _FakeModels()


class _Output(BaseModel):
    answer: str


def test_orchestration_injection_preserves_gemini_client_without_sdk(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.genai", None)
    client = _FakeClient()
    service = LLMService(GeminiProvider(api_key="test-key", client=client))
    dependencies = OrchestrationServices(llm_service=service)

    result = dependencies.llm_service.generate_structured(
        prompt="Generate a structured response.",
        response_model=_Output,
        fallback=lambda: _Output(answer="fallback"),
    )

    assert result.value.answer == "ok"
    assert result.is_fallback is False
    (call,) = client.models.calls
    assert call["model"] == "gemini-2.5-flash"
