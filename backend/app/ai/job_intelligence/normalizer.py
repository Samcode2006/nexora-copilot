"""Normalize raw job records from APIs and fixtures into ``JobListing``."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from html.parser import HTMLParser
from typing import Any

from pydantic import HttpUrl, TypeAdapter, ValidationError

from .schemas import EmploymentType, JobListing, WorkMode


class JobNormalizationError(ValueError):
    """Raised when a provider record cannot be represented safely."""


_URL_ADAPTER = TypeAdapter(HttpUrl)
_TITLE_KEYS = ("title", "job_title", "name", "position")
_COMPANY_KEYS = ("company", "company_name", "employer", "organization")
_DESCRIPTION_KEYS = ("description", "job_description", "details", "content")
_URL_KEYS = ("url", "job_url", "source_url", "job_link", "external_url")
_APPLICATION_URL_KEYS = ("application_url", "apply_url", "application_link", "apply_link")
_ID_KEYS = ("source_job_id", "id", "job_id", "uuid", "slug")
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
)
_AMOUNT_RE = re.compile(
    r"(?<!\w)(?:[$€£₹]\s*)?(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|m|million)?\b",
    re.IGNORECASE,
)


def normalize_job(
    raw_job: Mapping[str, Any],
    source_provider: str,
    *,
    is_mock: bool = False,
) -> JobListing:
    """Convert one provider record, preserving unknown data as null or empty."""
    if not isinstance(raw_job, Mapping):
        raise JobNormalizationError("A job record must be a JSON object.")
    provider = source_provider.strip().casefold()
    if not provider:
        raise JobNormalizationError("source_provider is required.")

    warnings: list[str] = []
    source_job_id = _first(raw_job, _ID_KEYS)
    source_job_id = _stringify_identifier(source_job_id)
    source_url_raw = _first(raw_job, _URL_KEYS)
    application_url_raw = _first(raw_job, _APPLICATION_URL_KEYS)
    source_url = _validated_url(source_url_raw, "source", warnings)
    explicit_application_url = _validated_url(application_url_raw, "application", warnings)
    application_url = explicit_application_url or source_url

    title = _optional_text(_first(raw_job, _TITLE_KEYS))
    company = _optional_text(_first(raw_job, _COMPANY_KEYS))
    location = _location_text(_first(raw_job, ("location", "candidate_required_location", "candidate_location", "city", "locations")))
    description = _description_text(_first(raw_job, _DESCRIPTION_KEYS))

    min_experience, max_experience = _experience_range(raw_job)
    salary = _salary_values(raw_job)
    job_id = _normalized_job_id(provider, source_job_id, raw_job)
    mode = _work_mode(raw_job, provider)
    mock_listing = is_mock or provider == "mock" or bool(raw_job.get("is_demo"))
    if mock_listing:
        warnings.append("Demo data; this is not a live job opening.")

    return JobListing(
        job_id=job_id,
        title=title,
        company=company,
        description=description,
        required_skills=_normalize_string_list(
            _first(raw_job, ("required_skills", "skills", "tags"))
        ),
        preferred_skills=_normalize_string_list(
            _first(raw_job, ("preferred_skills", "nice_to_have_skills", "optional_skills"))
        ),
        eligibility_criteria=_normalize_string_list(
            _first(raw_job, ("eligibility_criteria", "eligibility", "requirements", "qualifications"))
        ),
        min_experience_years=min_experience,
        max_experience_years=max_experience,
        location=location,
        work_mode=mode,
        employment_type=_employment_type(
            _first(raw_job, ("employment_type", "job_type", "type", "contract_type"))
        ),
        salary_min=salary[0],
        salary_max=salary[1],
        salary_currency=salary[2],
        salary_period=salary[3],
        salary_text=salary[4],
        application_url=application_url,
        source_url=source_url,
        application_deadline=_parse_date(
            _first(raw_job, ("application_deadline", "deadline", "expires_at", "expiration_date"))
        ),
        published_at=_parse_datetime(
            _first(raw_job, ("published_at", "publication_date", "posted_at", "created_at"))
        ),
        last_updated=_parse_datetime(
            _first(raw_job, ("last_updated", "updated_at", "modified_at"))
        ),
        source_provider=provider,
        source_job_id=source_job_id,
        is_mock=mock_listing,
        warnings=warnings,
    )


def normalize_jobs(
    raw_jobs: Sequence[Mapping[str, Any]],
    source_provider: str,
    *,
    is_mock: bool = False,
) -> list[JobListing]:
    """Normalize listings and remove duplicate provider IDs or job fingerprints."""
    if isinstance(raw_jobs, (str, bytes)) or not isinstance(raw_jobs, Sequence):
        raise JobNormalizationError("Provider listings must be an array.")

    normalized: list[JobListing] = []
    seen: set[str] = set()
    for raw_job in raw_jobs:
        if not isinstance(raw_job, Mapping):
            raise JobNormalizationError("Every provider listing must be a JSON object.")
        job = normalize_job(raw_job, source_provider, is_mock=is_mock)
        fingerprint = _deduplication_key(job)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized.append(job)
    return normalized


def _first(record: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def _optional_text(value: Any) -> str | None:
    if value is None or isinstance(value, (Mapping, list, tuple)):
        return None
    text = str(value).strip()
    return text or None


def _stringify_identifier(value: Any) -> str | None:
    if value is None or isinstance(value, bool) or isinstance(value, (Mapping, list, tuple)):
        return None
    identifier = str(value).strip()
    return identifier or None


def _location_text(value: Any) -> str | None:
    if isinstance(value, (list, tuple)):
        parts = [_optional_text(item) for item in value]
        joined = ", ".join(part for part in parts if part)
        return joined or None
    if isinstance(value, Mapping):
        parts = [_optional_text(value.get(key)) for key in ("city", "region", "country", "name")]
        joined = ", ".join(part for part in parts if part)
        return joined or None
    return _optional_text(value)


def _description_text(value: Any) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    parser = _HTMLTextExtractor()
    parser.feed(text)
    parser.close()
    clean = html.unescape(" ".join(parser.parts))
    clean = re.sub(r"[ \t\u00a0]+", " ", clean)
    clean = re.sub(r"\s*\n\s*", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean or None


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"p", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items: list[Any] = list(value.values())
    elif isinstance(value, str):
        items = re.split(r"[,;\n|]", value)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = list(value)
    else:
        return []

    results: list[str] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, Mapping):
            item = _first(item, ("name", "skill", "label", "title", "value"))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            nested = _normalize_string_list(item)
            for nested_value in nested:
                key = nested_value.casefold()
                if key not in seen:
                    seen.add(key)
                    results.append(nested_value)
            continue
        text = _optional_text(item)
        if text:
            key = text.casefold()
            if key not in seen:
                seen.add(key)
                results.append(text)
    return results


def _experience_range(record: Mapping[str, Any]) -> tuple[float | None, float | None]:
    minimum = _number(_first(record, ("min_experience_years", "minimum_experience_years", "experience_min")))
    maximum = _number(_first(record, ("max_experience_years", "maximum_experience_years", "experience_max")))
    raw = _first(record, ("experience_requirements", "experience_level", "experience"))
    if isinstance(raw, Mapping):
        minimum = minimum if minimum is not None else _number(_first(raw, ("min", "minimum", "min_years")))
        maximum = maximum if maximum is not None else _number(_first(raw, ("max", "maximum", "max_years")))
    elif isinstance(raw, str) and minimum is None and maximum is None:
        numbers = [float(part) for part in re.findall(r"\d+(?:\.\d+)?", raw)]
        if len(numbers) > 1:
            minimum, maximum = min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
        elif len(numbers) == 1 and re.search(r"\+|more|at least|minimum", raw, re.IGNORECASE):
            minimum = numbers[0]
    if minimum is not None and minimum < 0:
        minimum = None
    if maximum is not None and maximum < 0:
        maximum = None
    if minimum is not None and maximum is not None and minimum > maximum:
        return None, None
    return minimum, maximum


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = _AMOUNT_RE.search(value)
        if match:
            return _amount(match)
    return None


def _salary_values(
    record: Mapping[str, Any],
) -> tuple[float | None, float | None, str | None, str | None, str | None]:
    raw = _first(record, ("salary", "salary_range", "compensation", "pay"))
    salary_text = _optional_text(raw)
    minimum = _number(_first(record, ("salary_min", "min_salary")))
    maximum = _number(_first(record, ("salary_max", "max_salary")))
    currency = _optional_text(_first(record, ("salary_currency", "currency")))
    period = _salary_period(_first(record, ("salary_period", "pay_period", "salary_interval")))

    if isinstance(raw, Mapping):
        minimum = minimum if minimum is not None else _number(_first(raw, ("min", "minimum", "min_value")))
        maximum = maximum if maximum is not None else _number(_first(raw, ("max", "maximum", "max_value")))
        currency = currency or _optional_text(_first(raw, ("currency", "currency_code")))
        period = period or _salary_period(_first(raw, ("period", "interval", "frequency")))
        salary_text = _optional_text(_first(raw, ("text", "description", "label"))) or salary_text

    if salary_text:
        if currency is None:
            currency = _currency_code(salary_text)
        if period is None:
            period = _salary_period(salary_text)
        if minimum is None and maximum is None:
            amounts = [_amount(match) for match in _AMOUNT_RE.finditer(salary_text)]
            if len(amounts) >= 2:
                minimum, maximum = sorted(amounts[:2])
    return minimum, maximum, currency, period, salary_text


def _amount(match: re.Match[str]) -> float:
    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").casefold()
    if unit in {"k", "thousand"}:
        amount *= 1000
    elif unit in {"m", "million"}:
        amount *= 1_000_000
    return amount


def _currency_code(text: str) -> str | None:
    for symbol, code in (("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("₹", "INR")):
        if symbol in text:
            return code
    match = re.search(r"\b(USD|EUR|GBP|INR|CAD|AUD)\b", text, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _salary_period(value: Any) -> str | None:
    text = _optional_text(value)
    if not text:
        return None
    folded = text.casefold()
    for aliases, period in (
        (("hour", "hourly", "/hr", "per hour"), "hour"),
        (("day", "daily", "per day"), "day"),
        (("week", "weekly", "per week"), "week"),
        (("month", "monthly", "per month"), "month"),
        (("year", "yearly", "annual", "annually", "per year"), "year"),
    ):
        if any(alias in folded for alias in aliases):
            return period
    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    parsed_datetime = _parse_datetime(text)
    if parsed_datetime is not None:
        return parsed_datetime.date()
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(iso_text)
    except ValueError:
        pass
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def _employment_type(value: Any) -> EmploymentType | None:
    text = _optional_text(value)
    if text is None:
        return None
    folded = re.sub(r"[\s-]+", "_", text.casefold())
    aliases: dict[str, EmploymentType] = {
        "full_time": "full_time",
        "fulltime": "full_time",
        "part_time": "part_time",
        "parttime": "part_time",
        "contract": "contract",
        "contractor": "contract",
        "internship": "internship",
        "intern": "internship",
        "freelance": "freelance",
        "freelancer": "freelance",
        "temporary": "temporary",
        "temp": "temporary",
        "other": "other",
    }
    return aliases.get(folded)


def _work_mode(record: Mapping[str, Any], provider: str) -> WorkMode | None:
    value = _first(record, ("work_mode", "workplace_type", "location_type", "remote_status"))
    text = _optional_text(value)
    if text:
        folded = text.casefold().replace("-", "_").replace(" ", "_")
        if any(word in folded for word in ("hybrid",)):
            return "hybrid"
        if any(word in folded for word in ("remote", "work_from_home", "wfh")):
            return "remote"
        if any(word in folded for word in ("on_site", "onsite", "office", "in_person")):
            return "on_site"
    remote_flag = _first(record, ("remote", "is_remote"))
    if remote_flag is True or (isinstance(remote_flag, str) and remote_flag.casefold() == "true"):
        return "remote"
    if provider == "remotive":
        return "remote"
    return None


def _validated_url(value: Any, field_name: str, warnings: list[str]) -> HttpUrl | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return _URL_ADAPTER.validate_python(text)
    except ValidationError:
        warnings.append(f"Invalid {field_name} URL was omitted.")
        return None


def _normalized_job_id(
    provider: str,
    source_job_id: str | None,
    raw_job: Mapping[str, Any],
) -> str:
    if source_job_id is not None:
        return f"{provider}:{source_job_id}"
    canonical = json.dumps(raw_job, sort_keys=True, ensure_ascii=False, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return f"{provider}:sha256-{digest}"


def _deduplication_key(job: JobListing) -> str:
    if job.source_job_id:
        return f"{job.source_provider}:{job.source_job_id.casefold()}"
    identity = "|".join(
        (
            (job.title or "").casefold(),
            (job.company or "").casefold(),
            (job.location or "").casefold(),
            str(job.source_url or "").casefold(),
        )
    )
    return f"{job.source_provider}:{identity}"
