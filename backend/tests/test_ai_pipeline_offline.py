"""Offline end-to-end coverage for resume-to-job matching.

This module injects deterministic fallback and mock providers. Any tests that
contact live LLM or job APIs should live in a separately named live-test module.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import pytest

from app.ai.job_intelligence import MockJobProvider, search_jobs
from app.ai.job_matching import match_jobs
from app.ai.providers import LLMService
from app.ai.resume_intelligence import StudentProfile, extract_student_profile

T = TypeVar("T")


@pytest.fixture
def sample_resume_text() -> str:
    return """Name: Asha Rao
Email: asha.rao@example.test
Location: Pune, India

Education
Institution: Nexora University
Degree: B.Tech
Branch: Computer Science
Graduation year: 2027
CGPA: 8.4

Skills
Programming Languages: Python, Java
Frameworks: FastAPI
Databases: PostgreSQL
Tools: Git
"""


@pytest.fixture
def offline_job_provider() -> MockJobProvider:
    return MockJobProvider(
        jobs=[
            {
                "id": "sample-backend-1",
                "title": "Python Backend Developer Intern",
                "company_name": "Demo Backend Co",
                "description": "Build APIs with FastAPI and PostgreSQL.",
                "tags": ["Python", "FastAPI", "PostgreSQL"],
                "job_type": "internship",
                "candidate_required_location": "Bengaluru, India",
                "work_mode": "hybrid",
            },
            {
                "id": "sample-data-2",
                "title": "Python Data Analyst Intern",
                "company_name": "Demo Data Co",
                "description": "Analyze datasets and prepare reports with SQL and pandas.",
                "tags": ["Python", "SQL", "pandas"],
                "job_type": "internship",
                "candidate_required_location": "Remote - India",
                "work_mode": "remote",
            },
            {
                "id": "sample-frontend-3",
                "title": "Python Frontend Trainee",
                "company_name": "Demo UI Co",
                "description": "Build interfaces using React and TypeScript.",
                "tags": ["Python", "React", "TypeScript"],
                "job_type": "internship",
                "candidate_required_location": "Worldwide",
                "work_mode": "remote",
            },
        ]
    )


def _run_stage(stage: str, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except Exception as exc:
        pytest.fail(
            f"Pipeline stage '{stage}' raised {type(exc).__name__}: {exc}",
            pytrace=True,
        )


def test_offline_resume_to_job_match_pipeline(
    sample_resume_text: str,
    offline_job_provider: MockJobProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise extraction, offline job discovery, and deterministic ranking."""
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")

    profile = _run_stage(
        "StudentProfile extraction",
        lambda: extract_student_profile(
            sample_resume_text,
            llm_service=LLMService(provider=None),
        ),
    )
    assert isinstance(profile, StudentProfile), (
        "Pipeline stage 'StudentProfile extraction' returned the wrong schema"
    )
    assert profile.extraction_provider == "deterministic_fallback", (
        "Pipeline stage 'StudentProfile extraction' reported an unexpected provider"
    )
    assert profile.is_fallback is True, (
        "Pipeline stage 'StudentProfile extraction' did not label fallback output"
    )
    assert profile.personal_information.name is not None, (
        "Pipeline stage 'StudentProfile extraction' omitted the resume name"
    )
    assert profile.personal_information.name.value == "Asha Rao", (
        "Pipeline stage 'StudentProfile extraction' did not retain the resume name"
    )
    assert profile.education, (
        "Pipeline stage 'StudentProfile extraction' omitted the education section"
    )
    assert profile.education[0].institution is not None, (
        "Pipeline stage 'StudentProfile extraction' omitted the institution field"
    )
    assert profile.education[0].institution.value == "Nexora University", (
        "Pipeline stage 'StudentProfile extraction' did not retain the resume institution"
    )

    listings = _run_stage(
        "JobListing search",
        lambda: search_jobs("python", limit=10, provider=offline_job_provider),
    )
    assert len(listings) == 3, (
        "Pipeline stage 'JobListing search' returned an unexpected listing count"
    )
    assert all(listing.source_provider == "mock" for listing in listings), (
        "Pipeline stage 'JobListing search' lost the mock provider attribution"
    )
    assert all(listing.is_mock for listing in listings), (
        "Pipeline stage 'JobListing search' mislabeled demo listings as live"
    )

    ranked_matches = _run_stage(
        "JobMatch ranking",
        lambda: match_jobs(profile, listings),
    )
    assert len(ranked_matches) == 3, (
        "Pipeline stage 'JobMatch ranking' returned an unexpected result count"
    )
    assert all(match.matching_method == "keyword_fallback" for match in ranked_matches), (
        "Pipeline stage 'JobMatch ranking' did not report the deterministic method"
    )
    assert [match.job_id for match in ranked_matches] == [
        "mock:sample-backend-1",
        "mock:sample-data-2",
        "mock:sample-frontend-3",
    ], "Pipeline stage 'JobMatch ranking' returned an unexpected relevance order"
    assert [match.rank for match in ranked_matches] == [1, 2, 3], (
        "Pipeline stage 'JobMatch ranking' returned invalid rank values"
    )
    assert [skill.job_skill for skill in ranked_matches[0].matched_skills] == [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ], "Pipeline stage 'JobMatch ranking' failed to preserve matched-skill evidence"
