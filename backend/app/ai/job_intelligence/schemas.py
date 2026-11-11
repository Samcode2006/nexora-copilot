"""Normalized, provider-independent job listing models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

WorkMode = Literal["remote", "hybrid", "on_site"]
EmploymentType = Literal[
    "full_time",
    "part_time",
    "contract",
    "internship",
    "freelance",
    "temporary",
    "other",
]


class JobListing(BaseModel):
    """A normalized job with source attribution and no invented missing data."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    title: str | None = None
    company: str | None = None
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    eligibility_criteria: list[str] = Field(default_factory=list)
    min_experience_years: float | None = Field(default=None, ge=0)
    max_experience_years: float | None = Field(default=None, ge=0)
    location: str | None = None
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str | None = None
    salary_period: Literal["hour", "day", "week", "month", "year"] | None = None
    salary_text: str | None = None
    application_url: HttpUrl | None = None
    source_url: HttpUrl | None = None
    application_deadline: date | None = None
    published_at: datetime | None = None
    last_updated: datetime | None = None
    source_provider: str = Field(min_length=1)
    source_job_id: str | None = None
    is_mock: bool = False
    warnings: list[str] = Field(default_factory=list)

    @field_validator("title", "company", "description", "location", "source_job_id", "salary_text")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None

    @field_validator("required_skills", "preferred_skills", "eligibility_criteria")
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]

    @field_validator("source_provider")
    @classmethod
    def normalize_provider_name(cls, value: str) -> str:
        return value.strip().casefold()

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value and value.strip() else None

    @model_validator(mode="after")
    def validate_ranges(self) -> JobListing:
        if (
            self.min_experience_years is not None
            and self.max_experience_years is not None
            and self.min_experience_years > self.max_experience_years
        ):
            raise ValueError("minimum experience cannot exceed maximum experience")
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min cannot exceed salary_max")
        return self
