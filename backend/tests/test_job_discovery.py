from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from urllib.error import HTTPError

import pytest

from app.ai.job_intelligence import (
    JobNormalizationError,
    JobProviderConfigurationError,
    JobProviderError,
    JobProviderResponseError,
    MockJobProvider,
    RemotiveJobProvider,
    normalize_job,
    normalize_jobs,
    create_job_provider_from_env,
    search_jobs,
)


def _remotive_record(**updates: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": 9876,
        "url": "https://remotive.com/remote-jobs/software-dev/backend-engineer-9876",
        "title": "Backend Engineer",
        "company_name": "Example Systems",
        "description": "<p>Build reliable APIs.</p><p>Use Python and PostgreSQL.</p>",
        "category": "Software Development",
        "tags": ["Python", {"name": "PostgreSQL"}, "Python"],
        "job_type": "full_time",
        "publication_date": "2026-06-14T10:30:00Z",
        "candidate_required_location": "Worldwide",
        "salary": "$70,000 - $95,000 yearly",
    }
    record.update(updates)
    return record


def _remotive_provider(payload: Any) -> RemotiveJobProvider:
    encoded = json.dumps(payload).encode("utf-8")
    return RemotiveJobProvider(
        fetcher=lambda url, timeout: encoded,
        cache_ttl_seconds=3600,
        retry_backoff_seconds=0,
    )


def test_mock_provider_returns_explicit_demo_jobs() -> None:
    jobs = search_jobs("python", provider=MockJobProvider())
    assert jobs
    assert all(job.is_mock for job in jobs)
    assert all(job.source_provider == "mock" for job in jobs)
    assert all(any("not a live" in warning for warning in job.warnings) for job in jobs)


def test_successful_remotive_response_is_normalized() -> None:
    provider = _remotive_provider({"jobs": [_remotive_record()]})
    jobs = search_jobs("backend engineer", location="India", provider=provider)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_id == "remotive:9876"
    assert job.title == "Backend Engineer"
    assert job.company == "Example Systems"
    assert job.description == "Build reliable APIs.\nUse Python and PostgreSQL."
    assert job.required_skills == ["Python", "PostgreSQL"]
    assert job.employment_type == "full_time"
    assert job.work_mode == "remote"
    assert job.location == "Worldwide"
    assert job.salary_min == 70000
    assert job.salary_max == 95000
    assert job.salary_currency == "USD"
    assert job.salary_period == "year"
    assert job.published_at == datetime.fromisoformat("2026-06-14T10:30:00+00:00")
    assert str(job.application_url).startswith("https://remotive.com/")
    assert str(job.source_url) == str(job.application_url)
    assert job.source_provider == "remotive"
    assert job.source_job_id == "9876"
    assert job.is_mock is False


def test_missing_job_fields_remain_null_or_empty() -> None:
    job = normalize_job({"id": 17}, "example")
    assert job.job_id == "example:17"
    assert job.title is None
    assert job.company is None
    assert job.description is None
    assert job.required_skills == []
    assert job.preferred_skills == []
    assert job.location is None
    assert job.salary_min is None
    assert job.application_url is None
    assert job.last_updated is None


def test_duplicate_source_job_ids_are_removed() -> None:
    record = _remotive_record()
    jobs = normalize_jobs([record, dict(record)], "remotive")
    assert len(jobs) == 1


def test_job_without_source_id_gets_stable_id_and_duplicate_fingerprint() -> None:
    record = {"title": "Analyst", "company_name": "Example", "location": "Remote"}
    first = normalize_job(record, "feed")
    second = normalize_job(dict(record), "feed")
    assert first.job_id == second.job_id
    assert len(normalize_jobs([record, dict(record)], "feed")) == 1
    assert first.source_job_id is None


def test_invalid_urls_are_omitted_with_warning() -> None:
    job = normalize_job(
        {
            "id": "bad-url",
            "title": "QA Analyst",
            "url": "javascript:alert(1)",
            "apply_url": "not a url",
        },
        "feed",
    )
    assert job.source_url is None
    assert job.application_url is None
    assert any("Invalid source URL" in warning for warning in job.warnings)
    assert any("Invalid application URL" in warning for warning in job.warnings)


def test_date_formats_are_normalized() -> None:
    job = normalize_job(
        {
            "id": 8,
            "title": "Data Engineer",
            "deadline": "31/05/2026",
            "updated_at": "May 4, 2026",
            "publication_date": "2026/04/03",
        },
        "feed",
    )
    assert job.application_deadline == date(2026, 5, 31)
    assert job.last_updated == datetime(2026, 5, 4)
    assert job.published_at == datetime(2026, 4, 3)


def test_string_skills_and_experience_ranges_are_normalized() -> None:
    job = normalize_job(
        {
            "id": 9,
            "title": "Software Engineer",
            "required_skills": "Python; SQL, FastAPI",
            "preferred_skills": [{"skill": "Docker"}, "AWS"],
            "experience": "2-4 years",
            "job_type": "Full-time",
        },
        "feed",
    )
    assert job.required_skills == ["Python", "SQL", "FastAPI"]
    assert job.preferred_skills == ["Docker", "AWS"]
    assert job.min_experience_years == 2
    assert job.max_experience_years == 4
    assert job.employment_type == "full_time"


def test_provider_failure_is_raised_without_mock_success_fallback() -> None:
    calls = 0

    def fail(url: str, timeout: float) -> bytes:
        nonlocal calls
        calls += 1
        raise TimeoutError("connection timed out")

    provider = RemotiveJobProvider(fetcher=fail, retry_backoff_seconds=0)
    with pytest.raises(JobProviderError):
        search_jobs("engineer", provider=provider)
    assert calls == 2


def test_transient_provider_failure_is_retried_once() -> None:
    calls = 0
    payload = json.dumps({"jobs": [_remotive_record()]}).encode()

    def fail_once(url: str, timeout: float) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary timeout")
        return payload

    provider = RemotiveJobProvider(fetcher=fail_once, retry_backoff_seconds=0)
    assert search_jobs("backend", provider=provider)
    assert calls == 2


def test_non_transient_http_error_is_not_retried() -> None:
    calls = 0

    def fail(url: str, timeout: float) -> bytes:
        nonlocal calls
        calls += 1
        raise HTTPError(url, 400, "bad request", None, None)

    provider = RemotiveJobProvider(fetcher=fail, retry_backoff_seconds=0)
    with pytest.raises(JobProviderError, match="HTTP 400"):
        search_jobs("engineer", provider=provider)
    assert calls == 1


def test_empty_search_results_are_empty() -> None:
    assert search_jobs("quantum pilot", provider=MockJobProvider([])) == []


def test_location_filtering_keeps_matching_and_worldwide_remote_jobs() -> None:
    provider = MockJobProvider(
        [
            {
                "id": "local",
                "title": "Python Engineer",
                "location": "Bengaluru, India",
                "work_mode": "on_site",
            },
            {
                "id": "global",
                "title": "Python Engineer",
                "location": "Worldwide",
                "work_mode": "remote",
            },
            {
                "id": "other",
                "title": "Python Engineer",
                "location": "Toronto, Canada",
            },
        ]
    )
    jobs = search_jobs("Python Engineer", location="India", provider=provider)
    assert [job.source_job_id for job in jobs] == ["local", "global"]


def test_result_limit_is_applied_after_filtering() -> None:
    provider = MockJobProvider(
        [
            {"id": str(index), "title": f"Python Intern {index}"}
            for index in range(5)
        ]
    )
    assert len(search_jobs("python intern", limit=2, provider=provider)) == 2


def test_remotive_snapshot_is_cached_across_different_searches() -> None:
    calls = 0
    payload = json.dumps({"jobs": [_remotive_record()]}).encode()

    def fetch(url: str, timeout: float) -> bytes:
        nonlocal calls
        calls += 1
        return payload

    provider = RemotiveJobProvider(fetcher=fetch, cache_ttl_seconds=3600)
    assert search_jobs("backend", provider=provider)
    assert search_jobs("python", provider=provider)
    assert calls == 1


def test_incorrect_provider_response_raises_clear_error() -> None:
    provider = _remotive_provider({"results": [_remotive_record()]})
    with pytest.raises(JobProviderResponseError, match="jobs array"):
        search_jobs("backend", provider=provider)


def test_environment_selects_remotive_without_an_api_key(monkeypatch) -> None:
    monkeypatch.setenv("JOBS_PROVIDER", "remotive")
    monkeypatch.delenv("REMOTIVE_API_KEY", raising=False)
    provider = create_job_provider_from_env()
    assert isinstance(provider, RemotiveJobProvider)
    assert provider.is_mock is False


def test_unsupported_environment_provider_fails_clearly(monkeypatch) -> None:
    monkeypatch.setenv("JOBS_PROVIDER", "unknown")
    with pytest.raises(JobProviderConfigurationError, match="Unsupported JOBS_PROVIDER"):
        create_job_provider_from_env()


def test_non_object_job_record_is_rejected() -> None:
    with pytest.raises(JobNormalizationError, match="JSON object"):
        normalize_jobs(["not a listing"], "feed")  # type: ignore[list-item]


def test_search_input_validation() -> None:
    provider = MockJobProvider([])
    with pytest.raises(ValueError, match="non-empty"):
        search_jobs(" ", provider=provider)
    with pytest.raises(ValueError, match="between 1 and 100"):
        search_jobs("engineer", limit=0, provider=provider)
