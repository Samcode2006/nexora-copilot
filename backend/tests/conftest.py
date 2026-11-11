import os
from collections.abc import Callable
from typing import TypeVar

# Test environment: set BEFORE the app is imported. Real env vars override any .env file.
os.environ["SUPABASE_URL"] = "https://testref.supabase.co"
os.environ["SUPABASE_JWT_AUDIENCE"] = "authenticated"
os.environ["SUPABASE_JWT_SECRET"] = "test-hs256-secret-with-at-least-32-bytes!!"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
if os.environ.get("RUN_DB_TESTS") != "1":
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://u:p@127.0.0.1:1/none"
    os.environ.pop("MIGRATION_DATABASE_URL", None)

import httpx
import pytest

from app.ai.job_intelligence import MockJobProvider
from app.main import create_app

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


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def run_pipeline_stage() -> Callable[[str, Callable[[], T]], T]:
    def run(stage: str, operation: Callable[[], T]) -> T:
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"Pipeline stage '{stage}' raised {type(exc).__name__}: {exc}",
                pytrace=True,
            )

    return run
