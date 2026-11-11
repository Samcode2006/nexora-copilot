"""Job provider boundaries, demo data, and the public Remotive adapter."""

from __future__ import annotations

import copy
import json
import os
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_CACHE_TTL_SECONDS = 6 * 60 * 60
REMOTIVE_FETCH_LIMIT = 1000


class JobProviderError(RuntimeError):
    """A provider setup, transport, or response error."""


class JobProviderConfigurationError(JobProviderError):
    """Raised for unsupported providers or invalid provider configuration."""


class JobProviderResponseError(JobProviderError):
    """Raised when an upstream response does not match its documented shape."""


class JobProvider(Protocol):
    """Provider interface returning raw listings for later normalization."""

    name: str
    is_mock: bool

    def search(self, query: str, *, limit: int) -> Sequence[Mapping[str, Any]]:
        """Return raw listings; query and result limits are also enforced locally."""


class MockJobProvider:
    """Clearly labelled sample data for local development and demos."""

    name = "mock"
    is_mock = True

    def __init__(self, jobs: Sequence[Mapping[str, Any]] | None = None) -> None:
        self._jobs = copy.deepcopy(list(jobs) if jobs is not None else _DEMO_JOBS)

    def search(self, query: str, *, limit: int) -> Sequence[Mapping[str, Any]]:
        return copy.deepcopy(self._jobs)


class RemotiveJobProvider:
    """Cached adapter for Remotive's public remote jobs API.

    The API advises developers to fetch data no more than four times per day.
    A six-hour in-memory cache is used by default. Search and location filters
    are applied locally to the cached feed, avoiding one API request per query.
    """

    name = "remotive"
    is_mock = False

    def __init__(
        self,
        *,
        endpoint: str = DEFAULT_REMOTIVE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        fetcher: Callable[[str, float], bytes] | None = None,
        retry_backoff_seconds: float = 0.1,
    ) -> None:
        if not endpoint.startswith("https://"):
            raise JobProviderConfigurationError("Remotive endpoint must use HTTPS.")
        if timeout_seconds <= 0:
            raise JobProviderConfigurationError("Provider timeout must be positive.")
        if cache_ttl_seconds <= 0:
            raise JobProviderConfigurationError("Provider cache TTL must be positive.")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self._fetcher = fetcher or _fetch_url
        self._retry_backoff_seconds = max(0, retry_backoff_seconds)
        self._cached_jobs: list[Mapping[str, Any]] | None = None
        self._cached_at = 0.0
        self._cache_lock = threading.Lock()

    def search(self, query: str, *, limit: int) -> Sequence[Mapping[str, Any]]:
        # Remotive is remote-only. Fetch a single bounded snapshot and let the
        # shared service filter every query without increasing API call volume.
        return copy.deepcopy(self._get_snapshot())

    def _get_snapshot(self) -> list[Mapping[str, Any]]:
        with self._cache_lock:
            now = time.monotonic()
            if (
                self._cached_jobs is not None
                and now - self._cached_at < self.cache_ttl_seconds
            ):
                return self._cached_jobs

            jobs = self._fetch_jobs()
            self._cached_jobs = jobs
            self._cached_at = time.monotonic()
            return jobs

    def _fetch_jobs(self) -> list[Mapping[str, Any]]:
        query_string = urlencode({"limit": REMOTIVE_FETCH_LIMIT})
        separator = "&" if "?" in self.endpoint else "?"
        url = f"{self.endpoint}{separator}{query_string}"
        payload: bytes | None = None

        for attempt in range(2):
            try:
                payload = self._fetcher(url, self.timeout_seconds)
                break
            except HTTPError as exc:
                if attempt == 0 and exc.code in {429, 500, 502, 503, 504}:
                    time.sleep(self._retry_backoff_seconds)
                    continue
                raise JobProviderError(
                    f"Remotive returned HTTP {exc.code}."
                ) from exc
            except (TimeoutError, OSError, URLError) as exc:
                if attempt == 0:
                    time.sleep(self._retry_backoff_seconds)
                    continue
                raise JobProviderError("Remotive request failed or timed out.") from exc
            except Exception as exc:
                raise JobProviderError("Remotive request failed.") from exc

        if payload is None:
            raise JobProviderError("Remotive returned no response body.")
        try:
            response = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
            raise JobProviderResponseError("Remotive returned invalid JSON.") from exc
        if not isinstance(response, Mapping) or not isinstance(response.get("jobs"), list):
            raise JobProviderResponseError(
                "Remotive response must be an object containing a jobs array."
            )
        if any(not isinstance(job, Mapping) for job in response["jobs"]):
            raise JobProviderResponseError("Remotive jobs must be JSON objects.")
        return list(response["jobs"])


_PROVIDER_CACHE: dict[tuple[str, str, float, int], JobProvider] = {}
_PROVIDER_CACHE_LOCK = threading.Lock()


def create_job_provider_from_env() -> JobProvider:
    """Create the provider selected by ``JOBS_PROVIDER`` (defaults to mock)."""
    provider_name = os.getenv("JOBS_PROVIDER", "mock").strip().casefold()
    if provider_name == "mock":
        return MockJobProvider()
    if provider_name != "remotive":
        raise JobProviderConfigurationError(
            "Unsupported JOBS_PROVIDER. Choose 'mock' or 'remotive'."
        )

    endpoint = os.getenv("REMOTIVE_API_URL", DEFAULT_REMOTIVE_URL).strip()
    timeout_seconds = _positive_float_env(
        "JOB_PROVIDER_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
    )
    cache_ttl_seconds = _positive_int_env(
        "REMOTIVE_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS
    )
    key = (provider_name, endpoint, timeout_seconds, cache_ttl_seconds)
    with _PROVIDER_CACHE_LOCK:
        provider = _PROVIDER_CACHE.get(key)
        if provider is None:
            provider = RemotiveJobProvider(
                endpoint=endpoint,
                timeout_seconds=timeout_seconds,
                cache_ttl_seconds=cache_ttl_seconds,
            )
            _PROVIDER_CACHE[key] = provider
        return provider


def _positive_float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise JobProviderConfigurationError(f"{name} must be a number.") from exc
    if value <= 0:
        raise JobProviderConfigurationError(f"{name} must be positive.")
    return value


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise JobProviderConfigurationError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise JobProviderConfigurationError(f"{name} must be positive.")
    return value


def _fetch_url(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "NEXORA-job-discovery/0.1",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


_DEMO_JOBS: list[dict[str, Any]] = [
    {
        "id": "demo-python-intern-001",
        "title": "Python Developer Intern (Demo)",
        "company_name": "NEXORA Demo Labs",
        "description": "DEMO DATA — not a live job opening. Build sample backend services.",
        "tags": ["Python", "FastAPI", "PostgreSQL"],
        "job_type": "internship",
        "candidate_required_location": "Bengaluru, India",
        "work_mode": "hybrid",
    },
    {
        "id": "demo-data-analyst-002",
        "title": "Junior Data Analyst (Demo)",
        "company_name": "NEXORA Sample Analytics",
        "description": "DEMO DATA — not a live job opening. Practice SQL and reporting.",
        "tags": ["SQL", "Python", "Data Analysis"],
        "job_type": "full_time",
        "candidate_required_location": "Remote - India",
        "work_mode": "remote",
    },
    {
        "id": "demo-frontend-003",
        "title": "Frontend Engineering Trainee (Demo)",
        "company_name": "NEXORA Sample Studio",
        "description": "DEMO DATA — not a live job opening. Work with a sample React UI.",
        "tags": ["React", "TypeScript", "CSS"],
        "job_type": "internship",
        "candidate_required_location": "Worldwide",
        "work_mode": "remote",
    },
]
