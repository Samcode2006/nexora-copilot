"""Offline cross-module workflows for the NEXORA AI service package."""

from __future__ import annotations

import io
import json
import socket
from collections.abc import Iterator, Mapping
from copy import deepcopy
from importlib import import_module
from typing import Any

import pytest
from pydantic import BaseModel

from app.ai.interview_intelligence import (
    InterviewSession,
    get_interview_report,
    serialize_interview_session,
    start_interview,
    submit_interview_answer,
)
from app.ai.job_intelligence import JobListing, MockJobProvider, search_jobs
from app.ai.job_matching import match_jobs
from app.ai.providers import LLMService
from app.ai.resume_intelligence import (
    EvidenceValue,
    ParsedResume,
    StudentProfile,
    extract_student_profile,
    parse_resume,
)
from app.ai.resume_tailoring import generate_cover_letter, tailor_resume
from app.ai.resume_tailoring.schemas import ValidatedClaim


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove ambient credentials and fail the test if code tries network I/O."""
    connection_attempts: list[str] = []

    def blocked_connect(*_args: Any, **_kwargs: Any) -> None:
        connection_attempts.append("socket.connect")
        raise OSError("network access is disabled in offline workflow tests")

    def blocked_urlopen(*_args: Any, **_kwargs: Any) -> None:
        connection_attempts.append("urllib.urlopen")
        raise OSError("network access is disabled in offline workflow tests")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # An explicitly injected provider must remain independent of this live setting.
    monkeypatch.setenv("JOBS_PROVIDER", "remotive")
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_connect)
    job_providers = import_module("app.ai.job_intelligence.providers")
    monkeypatch.setattr(job_providers, "urlopen", blocked_urlopen)

    yield

    assert connection_attempts == [], (
        "Offline AI workflow attempted network access: "
        + ", ".join(connection_attempts)
    )


def _pdf_bytes(text: str) -> bytes:
    try:
        pymupdf = import_module("pymupdf")
    except ImportError:
        pymupdf = import_module("fitz")
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def _docx_bytes(text: str) -> bytes:
    docx = import_module("docx")
    document = docx.Document()
    for line in text.splitlines():
        if line.strip():
            document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def offline_profile(
    sample_resume_text: str,
    run_pipeline_stage,
) -> tuple[ParsedResume, StudentProfile]:
    parsed = run_pipeline_stage(
        "Resume parsing",
        lambda: parse_resume(_pdf_bytes(sample_resume_text), "asha-resume.pdf"),
    )
    profile = run_pipeline_stage(
        "StudentProfile extraction",
        lambda: extract_student_profile(
            parsed.text,
            llm_service=LLMService(provider=None),
        ),
    )
    return parsed, profile


@pytest.fixture
def selected_job(
    offline_job_provider: MockJobProvider,
    run_pipeline_stage,
) -> JobListing:
    jobs = run_pipeline_stage(
        "JobListing search",
        lambda: search_jobs("python", limit=10, provider=offline_job_provider),
    )
    assert jobs, "Pipeline stage 'JobListing search' returned no offline fixtures"
    return jobs[0]


def _walk_evidence(value: Any) -> Iterator[EvidenceValue[Any]]:
    if isinstance(value, EvidenceValue):
        yield value
    elif isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            yield from _walk_evidence(getattr(value, field_name))
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_evidence(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_evidence(child)


def _walk_claims(value: Any) -> Iterator[ValidatedClaim]:
    if isinstance(value, ValidatedClaim):
        yield value
    elif isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            yield from _walk_claims(getattr(value, field_name))
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_claims(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_claims(child)


def test_resume_onboarding_parses_pdf_and_docx_before_profile_extraction(
    sample_resume_text: str,
    run_pipeline_stage,
) -> None:
    for filename, content in (
        ("asha-resume.pdf", _pdf_bytes(sample_resume_text)),
        ("asha-resume.docx", _docx_bytes(sample_resume_text)),
    ):
        parsed = run_pipeline_stage(
            f"Resume parsing ({filename})",
            lambda content=content, filename=filename: parse_resume(content, filename),
        )
        profile = run_pipeline_stage(
            f"StudentProfile extraction ({filename})",
            lambda parsed=parsed: extract_student_profile(
                parsed.text,
                llm_service=LLMService(provider=None),
            ),
        )

        assert parsed.source_format in {"pdf", "docx"}
        assert isinstance(profile, StudentProfile)
        assert profile.extraction_provider == "deterministic_fallback"
        assert profile.is_fallback is True
        assert profile.personal_information.name is not None
        assert profile.personal_information.name.value == "Asha Rao"
        assert profile.personal_information.phone is None
        assert profile.education[0].institution is not None
        assert profile.education[0].institution.value == "Nexora University"
        assert profile.projects == []
        assert profile.experience == []
        assert profile.certifications == []
        evidence = list(_walk_evidence(profile))
        assert evidence
        for item in evidence:
            assert item.source_text
            assert item.source_text in parsed.text
            assert item.verification_status in {"unverified", "needs_review"}


def test_mock_job_discovery_normalizes_deduplicates_and_matches_with_unknowns(
    offline_profile: tuple[Any, StudentProfile],
    run_pipeline_stage,
) -> None:
    _parsed, profile = offline_profile
    repeated_job = {
        "id": "offline-python-backend-1",
        "job_title": "Python Backend Intern",
        "organization": "Offline Fixture Labs",
        "job_description": "Build backend APIs using Python and FastAPI.",
        "required_skills": ["Python", "Rust"],
        "eligibility_criteria": ["CGPA >= 8.0"],
        "candidate_required_location": "Pune, India",
    }
    provider = MockJobProvider([repeated_job, repeated_job])
    jobs = run_pipeline_stage(
        "Mock provider normalization",
        lambda: search_jobs("Python Backend", provider=provider),
    )

    assert len(jobs) == 1, "Pipeline stage 'JobListing normalization' did not remove duplicate records"
    job = jobs[0]
    assert job.title == "Python Backend Intern"
    assert job.company == "Offline Fixture Labs"
    assert job.required_skills == ["Python", "Rust"]
    assert job.source_provider == "mock"
    assert job.is_mock is True

    matches = run_pipeline_stage(
        "JobMatch scoring",
        lambda: match_jobs(profile, jobs),
    )
    assert len(matches) == 1
    match = matches[0]
    assert match.job_id == job.job_id
    assert match.matching_method == "keyword_fallback"
    assert match.missing_required_skills == ["Rust"]
    assert match.eligibility_assessment.status == "unknown"
    assert match.overall_score is not None and match.overall_score <= 69
    assert match.explanation
    assert match.dimension_scores["required_skills"].explanation
    assert any(
        reference.profile_path.startswith("skills.") and reference.source_text
        for reference in match.evidence_references
    )


class _FixedStructuredProvider:
    """In-memory successful provider fixture; no transport or credential use."""

    name = "offline_workflow_fixture"
    model = "offline-fixture-v1"

    def __init__(self, responses: Mapping[str, Any]) -> None:
        self._responses = deepcopy(dict(responses))
        self.response_models: list[str] = []

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        del prompt
        key = response_model.__name__
        self.response_models.append(key)
        if key not in self._responses:
            raise AssertionError(f"No offline response fixture for {key}.")
        return deepcopy(self._responses[key])


def _grounded_resume_draft() -> dict[str, Any]:
    return {
        "professional_summary": {
            "text": "Python Backend Developer Intern candidate with Computer Science",
            "evidence_paths": [
                "education[0].branch",
                "skills.programming_languages[0]",
                "job_listing.title",
            ],
        },
        "skill_order": [
            "skills.programming_languages[0]",
            "skills.frameworks[0]",
        ],
    }


def _grounded_cover_letter_draft() -> dict[str, Any]:
    return {
        "relevant_experience": None,
        "role_relevance": {
            "text": "My Python and FastAPI skills for the Python Backend Developer Intern role",
            "evidence_paths": [
                "skills.programming_languages[0]",
                "skills.frameworks[0]",
                "job_listing.title",
            ],
        },
    }


def test_application_preparation_accepts_grounded_mock_provider_outputs(
    offline_profile: tuple[Any, StudentProfile],
    selected_job,
    run_pipeline_stage,
) -> None:
    parsed, profile = offline_profile
    provider = _FixedStructuredProvider(
        {
            "ResumeGenerationDraft": _grounded_resume_draft(),
            "CoverLetterGenerationDraft": _grounded_cover_letter_draft(),
        }
    )
    service = LLMService(provider=provider)
    tailored = run_pipeline_stage(
        "Resume tailoring",
        lambda: tailor_resume(profile, selected_job, llm_service=service),
    )
    letter = run_pipeline_stage(
        "Cover-letter generation",
        lambda: generate_cover_letter(profile, selected_job, tailored, llm_service=service),
    )

    assert provider.response_models == ["ResumeGenerationDraft", "CoverLetterGenerationDraft"]
    assert tailored.generation.provider == "offline_workflow_fixture"
    assert tailored.generation.generation_method == "llm_validated"
    assert tailored.generation.is_fallback is False
    assert tailored.professional_summary is not None
    assert letter.generation.provider == "offline_workflow_fixture"
    assert letter.generation.generation_method == "llm_validated", [
        item.reason for item in letter.validation_report.omitted_claims
    ]
    assert letter.generation.is_fallback is False
    assert letter.role_relevance_paragraph is not None
    assert letter.closing_paragraph == (
        "Thank you for considering my application. "
        "I would welcome the opportunity to discuss my application further."
    )
    for claim in [*_walk_claims(tailored), *_walk_claims(letter)]:
        assert claim.evidence_references
        for reference in claim.evidence_references:
            assert reference.source_path
            assert reference.source_text
            if reference.source_type == "student_profile":
                assert reference.source_text in parsed.text


def test_application_preparation_fallback_is_explicit_and_fact_grounded(
    offline_profile: tuple[Any, StudentProfile],
    selected_job,
    run_pipeline_stage,
) -> None:
    parsed, profile = offline_profile
    tailored = run_pipeline_stage(
        "Resume tailoring fallback",
        lambda: tailor_resume(profile, selected_job, llm_service=LLMService(provider=None)),
    )
    letter = run_pipeline_stage(
        "Cover-letter fallback",
        lambda: generate_cover_letter(
            profile,
            selected_job,
            tailored,
            llm_service=LLMService(provider=None),
        ),
    )

    assert tailored.generation.is_fallback is True
    assert tailored.generation.generation_method == "deterministic_fallback"
    assert letter.generation.is_fallback is True
    assert letter.generation.generation_method == "deterministic_fallback"
    assert profile.experience == []
    assert profile.projects == []
    assert profile.certifications == []
    assert all(
        reference.source_text in parsed.text
        for output in (tailored, letter)
        for claim in _walk_claims(output)
        for reference in claim.evidence_references
        if reference.source_type == "student_profile"
    )
    document_claims = " ".join(
        claim.text
        for output in (tailored, letter)
        for claim in _walk_claims(output)
    )
    assert "team of" not in document_claims.casefold()
    assert "certified" not in document_claims.casefold()
    assert "%" not in document_claims


def test_application_preparation_omits_unsupported_mock_provider_claims(
    offline_profile: tuple[Any, StudentProfile],
    selected_job,
    run_pipeline_stage,
) -> None:
    _parsed, profile = offline_profile
    resume_draft = _grounded_resume_draft()
    resume_draft["professional_summary"] = {
        "text": "Reduced defects by 80%.",
        "evidence_paths": ["skills.programming_languages[0]"],
    }
    resume_draft["skill_order"] = []
    cover_draft = _grounded_cover_letter_draft()
    cover_draft["role_relevance"] = {
        "text": "Led a team of 12 engineers using Python.",
        "evidence_paths": ["skills.programming_languages[0]"],
    }
    provider = _FixedStructuredProvider(
        {
            "ResumeGenerationDraft": resume_draft,
            "CoverLetterGenerationDraft": cover_draft,
        }
    )
    service = LLMService(provider=provider)
    tailored = run_pipeline_stage(
        "Resume claim validation",
        lambda: tailor_resume(profile, selected_job, llm_service=service),
    )
    letter = run_pipeline_stage(
        "Cover-letter claim validation",
        lambda: generate_cover_letter(profile, selected_job, tailored, llm_service=service),
    )

    assert provider.response_models == ["ResumeGenerationDraft", "CoverLetterGenerationDraft"]
    assert any("80%" in item.proposed_text for item in tailored.validation_report.omitted_claims)
    assert any(
        "team of 12" in item.proposed_text
        for item in letter.validation_report.omitted_claims
    )
    included_text = " ".join(
        claim.text
        for output in (tailored, letter)
        for claim in _walk_claims(output)
    ).casefold()
    assert "80%" not in included_text
    assert "team of 12" not in included_text
    assert tailored.generation.generation_method == "deterministic_fallback_after_validation"
    assert letter.generation.generation_method == "deterministic_fallback_after_validation"


def test_interview_workflow_reconstructs_adapts_and_reports_offline_session(
    offline_profile: tuple[Any, StudentProfile],
    selected_job,
    run_pipeline_stage,
) -> None:
    _parsed, profile = offline_profile
    llm_service = LLMService(provider=None)
    session = run_pipeline_stage(
        "Interview question generation",
        lambda: start_interview(
            profile,
            selected_job,
            "technical",
            difficulty="intermediate",
            question_count=2,
            llm_service=llm_service,
        ),
    )
    assert session.status == "in_progress"
    assert len(session.question_history) == 1
    assert session.question_history[0].generation_provider == "deterministic_fallback"
    assert session.question_history[0].generation_method == "deterministic_templates"
    assert session.question_history[0].question_text
    assert session.question_history[0].evaluation_rubric.weights

    first_answered = run_pipeline_stage(
        "Interview answer evaluation and adaptation",
        lambda: submit_interview_answer(session, "I don't know.", llm_service=llm_service),
    )
    assert len(first_answered.turn_history) == 1
    evaluation = first_answered.evaluation_history[0]
    assert evaluation.evaluation_method == "deterministic_heuristic"
    assert evaluation.generation_provider == "deterministic_fallback"
    assert evaluation.is_fallback is True
    assert evaluation.dimension_scores["technical_correctness"].status == "not_assessed"
    assert first_answered.current_difficulty == "beginner"
    assert first_answered.question_history[-1].difficulty == "beginner"
    assert first_answered.question_history[-1].selection_reason
    assert first_answered.competency_performance

    trusted_json = serialize_interview_session(
        first_answered,
        include_evaluation_material=True,
    )
    trusted_payload = json.loads(trusted_json)
    evaluator_fields = {
        "expected_answer_points",
        "evaluation_rubric",
        "evaluation_keywords",
    }
    for question in trusted_payload["question_history"]:
        assert evaluator_fields <= question.keys()
    for turn in trusted_payload["turn_history"]:
        assert evaluator_fields <= turn["question"].keys()

    reconstructed = run_pipeline_stage(
        "Trusted interview deserialization",
        lambda: InterviewSession.model_validate_json(trusted_json),
    )
    assert reconstructed == first_answered
    assert len(reconstructed.question_history) == 2
    assert len(reconstructed.answer_history) == 1
    assert len(reconstructed.evaluation_history) == 1
    assert len(reconstructed.turn_history) == 1

    completed = run_pipeline_stage(
        "Interview completion",
        lambda: submit_interview_answer(
            reconstructed,
            "Python uses indentation to define code blocks. First, I would validate the input, then test the endpoint. For example, I would add a request validation test.",
            llm_service=llm_service,
        ),
    )
    assert completed.status == "completed"
    assert len(completed.turn_history) == 2
    assert completed.competency_performance
    report = run_pipeline_stage(
        "Interview report generation",
        lambda: get_interview_report(completed),
    )
    assert report.session_status == "completed"
    assert report.questions_completed == 2
    assert report.planned_questions == 2
    assert report.competency_breakdown
    assert report.evaluation_limitations

