from __future__ import annotations

import uuid

from app.ai.providers import LLMService
from app.ai.providers.service import create_llm_service
from app.ai.resume_intelligence import extract_student_profile
from app.api.v1.student_data import _safe_filename
from app.core.config import Settings
from app.services.resume_processing import _fact_drafts


def test_llm_provider_uses_centralized_settings(monkeypatch) -> None:
    seen: dict[str, str] = {}

    class FakeProvider:
        name = "fake"

        def __init__(self, *, api_key: str, model: str) -> None:
            seen["api_key"] = api_key
            seen["model"] = model

        def generate_structured(self, **_kwargs):  # pragma: no cover - not called here
            raise AssertionError("generation is not part of this test")

    monkeypatch.setattr("app.ai.providers.service.GeminiProvider", FakeProvider)
    settings = Settings(
        supabase_url="https://testref.supabase.co",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        gemini_api_key="settings-key",
        gemini_model="configured-model",
    )

    service = create_llm_service(settings)

    assert isinstance(service.provider, FakeProvider)
    assert seen == {"api_key": "settings-key", "model": "configured-model"}


def test_resume_filename_is_reduced_to_safe_display_name() -> None:
    assert _safe_filename(r"C:\private\..\resume.pdf") == "resume.pdf"


def test_resume_adapter_persists_only_evidenced_facts(sample_resume_text: str) -> None:
    profile = extract_student_profile(sample_resume_text, llm_service=LLMService(provider=None))
    drafts = _fact_drafts(profile, uuid.uuid4())

    assert drafts
    assert {draft["fact_type"] for draft in drafts} <= {
        "education",
        "skill",
        "project",
        "experience",
        "achievement",
        "certification",
    }
    assert all(draft["source_ref"]["resume_id"] for draft in drafts)
    assert all(draft["source_ref"]["excerpt"] for draft in drafts)
