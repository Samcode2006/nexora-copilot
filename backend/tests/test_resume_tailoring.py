"""Offline deterministic tests; no test in this module calls a live provider."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.job_intelligence import JobListing
from app.ai.providers import LLMProviderError, LLMService
from app.ai.resume_intelligence import (
    EducationProfile,
    EvidenceValue,
    ExperienceProfile,
    PersonalInformation,
    ProjectProfile,
    SkillProfile,
    StudentProfile,
)
from app.ai.resume_tailoring import (
    DocumentReviewMetadata,
    TailoringPreferences,
    generate_cover_letter,
    tailor_resume,
)
from app.ai.resume_tailoring.schemas import GeneratedClaimDraft


def _fact(
    value: Any,
    source_text: str | None = None,
    *,
    verified: bool = False,
    evidence_status: str = "explicit",
) -> EvidenceValue[Any]:
    return EvidenceValue(
        value=value,
        source_text=source_text if source_text is not None else str(value),
        source_section="test-section",
        confidence="high",
        evidence_status=evidence_status,  # type: ignore[arg-type]
        verification_status="verified" if verified else "unverified",
    )


@pytest.fixture
def complete_profile() -> StudentProfile:
    return StudentProfile(
        personal_information=PersonalInformation(
            name=_fact("Maya Patel", "Name: Maya Patel"),
            email=_fact("maya.patel@example.test", "Email: maya.patel@example.test"),
            location=_fact("Pune, India", "Location: Pune, India"),
        ),
        education=[
            EducationProfile(
                institution=_fact("North Valley University", "Institution: North Valley University"),
                degree=_fact("B.Tech", "Degree: B.Tech"),
                branch=_fact("Computer Science", "Branch: Computer Science"),
                graduation_year=_fact(2025, "Graduation year: 2025"),
                cgpa=_fact(8.7, "CGPA: 8.7"),
            )
        ],
        skills=SkillProfile(
            programming_languages=[_fact("Python", "Programming Languages: Python, Java")],
            frameworks=[_fact("FastAPI", "Frameworks: FastAPI")],
            databases=[_fact("PostgreSQL", "Databases: PostgreSQL")],
            tools=[_fact("Git", "Tools: Git")],
        ),
        projects=[
            ProjectProfile(
                name=_fact("Campus Planner", "Project: Campus Planner"),
                description=_fact(
                    "Built a calendar application for campus events using Python and FastAPI.",
                    "Description: Built a calendar application for campus events using Python and FastAPI.",
                ),
                technologies=[
                    _fact("Python", "Technologies: Python, FastAPI"),
                    _fact("FastAPI", "Technologies: Python, FastAPI"),
                ],
                responsibilities=[_fact("Designed API endpoints.")],
                achievements=[_fact("Improved registration flow by 20%.")],
            )
        ],
        experience=[
            ExperienceProfile(
                company=_fact("Example Labs", "Company: Example Labs"),
                position=_fact("Software Intern", "Position: Software Intern"),
                duration=_fact("June 2024 - August 2024"),
                responsibilities=[_fact("Built dashboards in Python.")],
                achievements=[_fact("Reduced report processing time by 20%.")],
            )
        ],
        certifications=[_fact("AWS Certified Cloud Practitioner")],
        awards=[_fact("Dean's List 2024")],
        extraction_provider="fixture",
        is_fallback=False,
    )


@pytest.fixture
def selected_job() -> JobListing:
    return JobListing(
        job_id="fixture:backend-intern",
        title="Python Backend Intern",
        company="Acme Robotics",
        description="Build APIs for data services using Python, FastAPI, and PostgreSQL.",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        preferred_skills=["Git"],
        source_provider="fixture",
        source_job_id="backend-intern",
    )


class _QueueProvider:
    name = "mock_tailoring"
    model = "offline-fixture"

    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls = 0
        self.prompts: list[str] = []

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        self.calls += 1
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _resume_draft(profile: StudentProfile, summary: str | None = None, rewrites=None) -> dict[str, Any]:
    return {
        "professional_summary": (
            {
                "text": summary,
                "evidence_paths": [
                    "education[0].branch",
                    "skills.programming_languages[0]",
                    "skills.frameworks[0]",
                    "job_listing.title",
                ],
            }
            if summary
            else None
        ),
        "rewrites": rewrites or [],
        "skill_order": [
            "skills.programming_languages[0]",
            "skills.frameworks[0]",
            "skills.databases[0]",
        ],
        "project_order": [0],
    }


def test_successful_resume_tailoring_uses_validated_provider_draft(complete_profile, selected_job) -> None:
    summary = "Python Backend Intern candidate with Computer Science skills"
    provider = _QueueProvider([_resume_draft(complete_profile, summary)])
    result = tailor_resume(
        complete_profile,
        selected_job,
        llm_service=LLMService(provider=provider),
    )
    assert result.job_id == selected_job.job_id
    assert result.professional_summary is not None
    assert result.professional_summary.text == summary
    assert result.generation.provider == "mock_tailoring"
    assert result.generation.generation_method == "llm_validated"
    assert not result.generation.is_fallback


def test_professional_summary_is_job_specific_and_evidence_backed(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert result.professional_summary is not None
    assert "Python Backend Intern" in result.professional_summary.text
    assert "Python" in result.professional_summary.text
    assert result.professional_summary.evidence_references


def test_relevant_skills_are_prioritized_and_labeled(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    skill_values = [item.skill.text.split(": ", 1)[-1] for item in result.skills]
    assert skill_values[:3] == ["Python", "FastAPI", "PostgreSQL"]
    assert any(item.evidence_class == "listed_skill" for item in result.skills)


def test_contextual_skill_is_distinguished_from_listed_skill(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    python_skill = next(item for item in result.skills if item.skill.text.endswith("Python"))
    assert python_skill.evidence_class == "demonstrated_in_context"
    assert any(
        ref.source_path.startswith("projects[") or ref.source_path.startswith("experience[")
        for ref in python_skill.skill.evidence_references
    )


def test_project_rewrite_preserves_source_support(complete_profile, selected_job) -> None:
    rewrite = {
        "source_path": "projects[0].description",
        "claim": {
            "text": "Built a calendar application for campus events using Python and FastAPI.",
            "evidence_paths": ["projects[0].description"],
        },
    }
    provider = _QueueProvider([_resume_draft(complete_profile, rewrites=[rewrite])])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    project_text = " ".join(claim.text for claim in result.projects[0].claims)
    assert "Built a calendar application" in project_text
    assert any("projects[0].description" in ref.source_path for claim in result.projects[0].claims for ref in claim.evidence_references)


def test_experience_and_education_facts_are_preserved(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert "Software Intern" in result.experience[0].heading.text
    assert any("Built dashboards in Python." in claim.text for claim in result.experience[0].claims)
    education_text = " ".join(
        [result.education[0].heading.text]
        + [claim.text for claim in result.education[0].claims]
    )
    assert "North Valley University" in education_text
    assert "B.Tech" in education_text
    assert "2025" in education_text
    assert "8.7" in education_text


def test_cover_letter_has_structured_personalized_content(complete_profile, selected_job) -> None:
    tailored = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    letter = generate_cover_letter(
        complete_profile,
        selected_job,
        tailored_resume=tailored,
        llm_service=LLMService(),
    )
    assert letter.greeting == "Dear Hiring Team,"
    assert "Python Backend Intern" in letter.opening_paragraph.text
    assert letter.relevant_experience_paragraph is not None
    assert letter.role_relevance_paragraph is not None
    assert letter.closing_paragraph
    assert letter.sign_off_name is not None
    assert letter.sign_off_name.text == "Maya Patel"


def test_missing_company_does_not_invent_company_name(complete_profile, selected_job) -> None:
    job = selected_job.model_copy(update={"company": None})
    letter = generate_cover_letter(complete_profile, job, llm_service=LLMService())
    assert "at Acme Robotics" not in letter.opening_paragraph.text
    assert "Python Backend Intern" in letter.opening_paragraph.text
    assert all(ref.source_path != "job_listing.company" for ref in letter.opening_paragraph.evidence_references)


def test_empty_student_profile_is_handled_without_fabricated_facts(selected_job) -> None:
    profile = StudentProfile()
    resume = tailor_resume(profile, selected_job, llm_service=LLMService())
    letter = generate_cover_letter(profile, selected_job, llm_service=LLMService())
    assert resume.professional_summary is None
    assert resume.skills == []
    assert resume.generation.generation_method == "deterministic_fallback"
    assert letter.relevant_experience_paragraph is None
    assert letter.role_relevance_paragraph is None
    assert letter.sign_off_name is None


def test_profile_with_only_project_facts_gets_a_supported_summary(selected_job) -> None:
    profile = StudentProfile(
        projects=[
            ProjectProfile(
                name=_fact("Campus Planner", "Project: Campus Planner"),
                description=_fact("Built a calendar application.", "Built a calendar application."),
            )
        ]
    )
    result = tailor_resume(profile, selected_job, llm_service=LLMService())
    assert result.professional_summary is not None
    assert "Campus Planner" in result.professional_summary.text or "calendar application" in result.professional_summary.text
    assert any(
        reference.source_path.startswith("projects[")
        for reference in result.professional_summary.evidence_references
    )


def test_unsupported_numerical_claim_is_omitted(complete_profile, selected_job) -> None:
    draft = _resume_draft(complete_profile)
    draft["professional_summary"] = {
        "text": "Reduced report processing time by 80%.",
        "evidence_paths": [
            "experience[0].achievements[0]",
            "skills.programming_languages[0]",
        ],
    }
    draft["skill_order"] = []
    draft["project_order"] = []
    provider = _QueueProvider([draft])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    assert result.professional_summary is not None
    assert "80%" not in result.professional_summary.text
    assert any("number or percentage" in item.reason for item in result.validation_report.omitted_claims)
    assert result.generation.generation_method == "deterministic_fallback_after_validation"


def test_fabricated_experience_rewrite_is_rejected(complete_profile, selected_job) -> None:
    rewrite = {
        "source_path": "experience[0].responsibilities[0]",
        "claim": {
            "text": "Led a team of 12 engineers to build dashboards in Python.",
            "evidence_paths": ["experience[0].responsibilities[0]"],
        },
    }
    provider = _QueueProvider([_resume_draft(complete_profile, rewrites=[rewrite])])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    content = " ".join(claim.text for entry in result.experience for claim in entry.claims)
    assert "team of 12" not in content
    assert "Built dashboards in Python." in content
    assert any("Led a team" in item.proposed_text for item in result.validation_report.omitted_claims)


def test_unsupported_skill_claim_is_rejected(complete_profile, selected_job) -> None:
    provider = _QueueProvider([_resume_draft(complete_profile, "Kubernetes expert with Python skills")])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    assert result.professional_summary is not None
    assert "Kubernetes" not in result.professional_summary.text
    assert any("Kubernetes" in item.proposed_text for item in result.validation_report.omitted_claims)


def test_every_included_claim_has_valid_evidence_references(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    claims = [result.professional_summary] if result.professional_summary else []
    claims.extend(result.personal_information)
    claims.extend(skill.skill for skill in result.skills)
    for entry in [*result.education, *result.projects, *result.experience, *result.internships]:
        if entry.heading:
            claims.append(entry.heading)
        claims.extend(entry.claims)
    assert claims
    for claim in claims:
        assert claim.evidence_references
        assert claim.validation_status in {"supported", "needs_review"}
        for reference in claim.evidence_references:
            assert reference.source_path
            assert reference.source_text
            if reference.source_type == "student_profile":
                assert reference.verification_status in {"unverified", "verified", "needs_review"}


def test_invalid_structured_output_retries_and_recovers(complete_profile, selected_job) -> None:
    provider = _QueueProvider([{"skill_order": 4}, _resume_draft(complete_profile, "Python Backend Intern candidate")])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    assert provider.calls == 2
    assert result.generation.provider == "mock_tailoring"
    assert result.generation.generation_method == "llm_validated"


def test_provider_failure_uses_labeled_deterministic_fallback(complete_profile, selected_job) -> None:
    provider = _QueueProvider([LLMProviderError("offline"), LLMProviderError("offline")])
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService(provider=provider))
    assert provider.calls == 2
    assert result.generation.provider == "deterministic_fallback"
    assert result.generation.is_fallback
    assert result.generation.generation_method == "deterministic_fallback"
    assert result.professional_summary is not None


def test_missing_credentials_fallback_is_deterministic(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert result.generation.provider == "deterministic_fallback"
    assert result.generation.is_fallback
    assert result.generation.generation_method == "deterministic_fallback"
    assert result.professional_summary is not None


def test_empty_job_description_is_handled(complete_profile, selected_job) -> None:
    job = selected_job.model_copy(update={"title": None, "description": None, "required_skills": [], "preferred_skills": []})
    result = tailor_resume(complete_profile, job, llm_service=LLMService())
    assert result.job_id == job.job_id
    assert result.professional_summary is not None
    assert any("no title or description" in warning for warning in result.validation_report.warnings)


def test_output_is_a_validated_unapproved_draft(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert result.review.generation_state == "ai_generated_draft"
    assert result.review.validation_state == "validated_draft"
    assert result.review.review_state == "not_reviewed"
    assert result.review.approval_state == "not_approved"
    with pytest.raises(ValidationError, match="student-reviewed"):
        DocumentReviewMetadata(approval_state="student_approved_document")


def test_original_profile_is_not_mutated(complete_profile, selected_job) -> None:
    original = deepcopy(complete_profile.model_dump(mode="json"))
    tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert complete_profile.model_dump(mode="json") == original


def test_multiple_job_requests_are_isolated(complete_profile, selected_job) -> None:
    another_job = selected_job.model_copy(
        update={"job_id": "fixture:data-analyst", "title": "Python Data Analyst", "company": "Data Co"}
    )
    first = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    second = tailor_resume(complete_profile, another_job, llm_service=LLMService())
    assert first.job_id == selected_job.job_id
    assert second.job_id == another_job.job_id
    assert "Python Backend Intern" in first.professional_summary.text
    assert "Python Data Analyst" in second.professional_summary.text


def test_match_for_different_job_is_rejected(complete_profile, selected_job) -> None:
    from app.ai.job_matching.schemas import JobMatch

    wrong_match = JobMatch(
        job_id="another-job",
        rank=1,
        score_coverage=0,
        dimension_scores={},
        eligibility_assessment={"status": "not_applicable"},
        explanation="",
        matching_method="keyword_fallback",
        confidence="low",
    )
    with pytest.raises(ValidationError, match="job_match must refer"):
        tailor_resume(complete_profile, selected_job, wrong_match, llm_service=LLMService())


def test_preferences_are_validated_and_render_order_is_preserved(complete_profile, selected_job) -> None:
    with pytest.raises(ValidationError):
        TailoringPreferences(tone="casual")  # type: ignore[arg-type]
    preferences = TailoringPreferences(
        tone="technical",
        target_resume_length="concise",
        format_preferences={"section_order": ["skills", "summary", "education"]},
    )
    result = tailor_resume(complete_profile, selected_job, preferences=preferences, llm_service=LLMService())
    assert result.section_order == ["skills", "summary", "education"]


def test_unverified_facts_require_student_confirmation(complete_profile, selected_job) -> None:
    result = tailor_resume(complete_profile, selected_job, llm_service=LLMService())
    assert result.professional_summary is not None
    assert result.professional_summary.validation_status == "needs_review"
    assert result.professional_summary.student_confirmation_required


def test_cover_letter_provider_claims_are_validated(complete_profile, selected_job) -> None:
    provider = _QueueProvider(
        [
            {
                "relevant_experience": {
                    "text": "Managed a team of 30 engineers at Google.",
                    "evidence_paths": ["experience[0].responsibilities[0]"],
                },
                "role_relevance": None,
            }
        ]
    )
    letter = generate_cover_letter(
        complete_profile,
        selected_job,
        llm_service=LLMService(provider=provider),
    )
    assert letter.relevant_experience_paragraph is not None
    assert "Managed a team" not in letter.relevant_experience_paragraph.text
    assert any("Managed a team" in item.proposed_text for item in letter.validation_report.omitted_claims)


def test_valid_provider_cover_letter_claim_is_used(complete_profile, selected_job) -> None:
    provider = _QueueProvider(
        [
            {
                "relevant_experience": {
                    "text": "Built dashboards in Python.",
                    "evidence_paths": ["experience[0].responsibilities[0]"],
                },
                "role_relevance": None,
            }
        ]
    )
    letter = generate_cover_letter(
        complete_profile,
        selected_job,
        llm_service=LLMService(provider=provider),
    )
    assert letter.relevant_experience_paragraph is not None
    assert letter.relevant_experience_paragraph.text == "Built dashboards in Python."
    assert letter.generation.generation_method == "llm_validated"


def test_one_page_preference_limits_project_entries(complete_profile, selected_job) -> None:
    extra_projects = [
        ProjectProfile(
            name=_fact(f"Sample Project {index}", f"Project: Sample Project {index}"),
            description=_fact(
                f"Built sample service {index} with Python.",
                f"Description: Built sample service {index} with Python.",
            ),
        )
        for index in (2, 3)
    ]
    profile = complete_profile.model_copy(
        update={"projects": [*complete_profile.projects, *extra_projects]}
    )
    result = tailor_resume(
        profile,
        selected_job,
        preferences=TailoringPreferences(target_resume_length="one_page"),
        llm_service=LLMService(),
    )
    assert result.target_resume_length == "one_page"
    assert len(result.projects) == 2
    assert any("Limited projects" in warning for warning in result.validation_report.warnings)


def test_tailoring_request_rejects_duplicate_section_order(complete_profile, selected_job) -> None:
    with pytest.raises(ValidationError, match="duplicate sections"):
        TailoringPreferences(format_preferences={"section_order": ["skills", "skills"]})
