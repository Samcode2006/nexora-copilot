"""Deterministic fixtures shared by LangGraph orchestration tests."""

from __future__ import annotations

from io import BytesIO

from docx import Document

from app.ai.job_intelligence.providers import MockJobProvider
from app.ai.job_intelligence.schemas import JobListing
from app.ai.orchestration.checkpoint import InMemoryMetadataCheckpointStore
from app.ai.orchestration.services import OrchestrationServices
from app.ai.providers import LLMService
from app.ai.resume_intelligence.profile_schemas import StudentProfile


def sample_profile(email: str = "asha@example.test") -> StudentProfile:
    return StudentProfile.model_validate(
        {
            "personal_information": {
                "name": {"value": "Asha Rao", "source_text": "Name: Asha Rao"},
                "email": {"value": email, "source_text": f"Email: {email}"},
            },
            "education": [
                {
                    "institution": {
                        "value": "Nexora University",
                        "source_text": "Institution: Nexora University",
                    },
                    "degree": {"value": "B.Tech", "source_text": "Degree: B.Tech"},
                    "branch": {
                        "value": "Computer Science",
                        "source_text": "Branch: Computer Science",
                    },
                    "graduation_year": {
                        "value": 2027,
                        "source_text": "Graduation year: 2027",
                    },
                }
            ],
            "skills": {
                "programming_languages": [
                    {"value": "Python", "source_text": "Programming Languages: Python"}
                ],
                "frameworks": [{"value": "FastAPI", "source_text": "Frameworks: FastAPI"}],
                "databases": [{"value": "PostgreSQL", "source_text": "Databases: PostgreSQL"}],
            },
            "projects": [
                {
                    "name": {"value": "Campus API", "source_text": "Project: Campus API"},
                    "description": {
                        "value": "Built a campus events API.",
                        "source_text": "Built a campus events API.",
                    },
                    "technologies": [{"value": "Python", "source_text": "Technologies: Python"}],
                }
            ],
        }
    )


def sample_job(job_id: str = "job-1", *, title: str = "Python Backend Intern") -> JobListing:
    return JobListing(
        job_id=job_id,
        title=title,
        company="Demo Systems",
        description="Build Python APIs with FastAPI and PostgreSQL.",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["PostgreSQL"],
        location="Pune, India",
        employment_type="internship",
        source_provider="mock",
        source_job_id=job_id,
        is_mock=True,
    )


def raw_job(job_id: str, title: str) -> dict[str, object]:
    return {
        "id": job_id,
        "title": title,
        "company_name": "Demo Systems",
        "description": "Build Python APIs with FastAPI and PostgreSQL.",
        "tags": ["Python", "FastAPI", "PostgreSQL"],
        "job_type": "internship",
        "candidate_required_location": "Pune, India",
    }


def mock_provider(*jobs: dict[str, object]) -> MockJobProvider:
    return MockJobProvider(jobs=list(jobs))


def fresh_store() -> InMemoryMetadataCheckpointStore:
    return InMemoryMetadataCheckpointStore()


def offline_services(
    *,
    store: InMemoryMetadataCheckpointStore | None = None,
    job_provider: MockJobProvider | None = None,
    **overrides,
) -> OrchestrationServices:
    values = {
        "checkpoint_store": store if store is not None else fresh_store(),
        "llm_service": LLMService(),
        "job_provider": job_provider,
    }
    values.update(overrides)
    return OrchestrationServices(**values)


def docx_bytes(text: str = "Name: Asha Rao\nSkills: Python\n") -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()
