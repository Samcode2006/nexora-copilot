"""Provider-independent job search, filtering, normalization, and ranking order."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .normalizer import JobNormalizationError, normalize_jobs
from .providers import (
    JobProvider,
    JobProviderError,
    JobProviderResponseError,
    create_job_provider_from_env,
)
from .schemas import JobListing

DEFAULT_RESULT_LIMIT = 20
MAX_RESULT_LIMIT = 100
PROVIDER_FETCH_LIMIT = 1000


def search_jobs(
    query: str,
    location: str | None = None,
    limit: int = DEFAULT_RESULT_LIMIT,
    *,
    provider: JobProvider | None = None,
) -> list[JobListing]:
    """Search a configured provider and return deduplicated normalized jobs.

    The provider is injectable for tests and demos. Without an injected
    provider, ``JOBS_PROVIDER`` selects ``mock`` (default) or ``remotive``.
    Provider failures are raised; they are never hidden by demo results.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    query = query.strip()
    if len(query) > 200:
        raise ValueError("query must be 200 characters or fewer")
    if location is not None:
        if not isinstance(location, str):
            raise ValueError("location must be a string or None")
        location = location.strip() or None
        if location is not None and len(location) > 100:
            raise ValueError("location must be 100 characters or fewer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULT_LIMIT:
        raise ValueError(f"limit must be an integer between 1 and {MAX_RESULT_LIMIT}")

    selected_provider = provider or create_job_provider_from_env()
    provider_name = getattr(selected_provider, "name", None)
    if not isinstance(provider_name, str) or not provider_name.strip():
        raise JobProviderResponseError("Job provider is missing a valid name.")
    is_mock = getattr(selected_provider, "is_mock", None)
    if not isinstance(is_mock, bool):
        raise JobProviderResponseError("Job provider must declare whether it is mock data.")

    try:
        raw_jobs = selected_provider.search(query, limit=PROVIDER_FETCH_LIMIT)
    except JobProviderError:
        raise
    except Exception as exc:
        raise JobProviderError("Job provider search failed.") from exc

    if isinstance(raw_jobs, (str, bytes)) or not isinstance(raw_jobs, Sequence):
        raise JobProviderResponseError("Job provider must return an array of listings.")
    try:
        normalized_jobs = normalize_jobs(raw_jobs, provider_name, is_mock=is_mock)
    except JobNormalizationError as exc:
        raise JobProviderResponseError(f"Job provider returned malformed listings: {exc}") from exc

    matches = [job for job in normalized_jobs if _query_matches(job, query)]
    if location:
        matches = [job for job in matches if _location_matches(job, location)]
    return matches[:limit]


def _query_matches(job: JobListing, query: str) -> bool:
    searchable = " ".join(
        value
        for value in (
            job.title or "",
            job.company or "",
            job.description or "",
            job.location or "",
            *job.required_skills,
            *job.preferred_skills,
            *job.eligibility_criteria,
        )
    ).casefold()
    normalized_query = re.sub(r"\s+", " ", query.casefold()).strip()
    if normalized_query in searchable:
        return True
    terms = normalized_query.split()
    return bool(terms) and all(_term_matches(term, searchable) for term in terms)


def _term_matches(term: str, searchable: str) -> bool:
    if len(term) <= 2:
        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", searchable) is not None
    return term in searchable


def _location_matches(job: JobListing, location: str) -> bool:
    target = re.sub(r"\s+", " ", location.casefold()).strip()
    if target in {"remote", "work from home", "wfh"}:
        return job.work_mode == "remote"
    job_location = (job.location or "").casefold()
    if target in job_location:
        return True
    global_locations = ("worldwide", "anywhere", "global")
    if job.work_mode == "remote" and any(value in job_location for value in global_locations):
        return True
    return False
