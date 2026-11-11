"""Validated student profile models with claim-level source evidence."""

from __future__ import annotations

import re
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

ValueT = TypeVar("ValueT")
Confidence = Literal["high", "medium", "low"]
EvidenceStatus = Literal["explicit", "inferred", "uncertain"]
VerificationStatus = Literal["unverified", "needs_review", "verified"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceValue(StrictModel, Generic[ValueT]):
    """One extracted fact and the source excerpt that supports it.

    ``confidence``, ``evidence_status`` and ``verification_status`` returned
    from a provider are treated as suggestions only. The extraction service
    recomputes them and never marks resume content as student-verified.
    """

    value: ValueT
    source_text: str | None = Field(
        default=None,
        description="Verbatim supporting excerpt from the supplied resume text.",
    )
    source_section: str | None = None
    confidence: Confidence = "low"
    evidence_status: EvidenceStatus = "uncertain"
    verification_status: VerificationStatus = "needs_review"

    @field_validator("value")
    @classmethod
    def reject_empty_string(cls, value: ValueT) -> ValueT:
        if isinstance(value, str):
            value = value.strip()  # type: ignore[assignment]
            if not value:
                raise ValueError("evidence values cannot be empty")
        return value


class PersonalInformation(StrictModel):
    name: EvidenceValue[str] | None = None
    email: EvidenceValue[str] | None = None
    phone: EvidenceValue[str] | None = None
    location: EvidenceValue[str] | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EvidenceValue[str] | None) -> EvidenceValue[str] | None:
        if value is not None and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value.value):
            raise ValueError("email must have a valid address format")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: EvidenceValue[str] | None) -> EvidenceValue[str] | None:
        if value is not None:
            digit_count = sum(character.isdigit() for character in value.value)
            if not 7 <= digit_count <= 15:
                raise ValueError("phone must contain between 7 and 15 digits")
        return value


class EducationProfile(StrictModel):
    institution: EvidenceValue[str] | None = None
    degree: EvidenceValue[str] | None = None
    branch: EvidenceValue[str] | None = None
    graduation_year: EvidenceValue[int] | None = None
    cgpa: EvidenceValue[float] | None = None
    percentage: EvidenceValue[float] | None = None

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(
        cls, value: EvidenceValue[int] | None
    ) -> EvidenceValue[int] | None:
        if value is not None and not 1900 <= value.value <= 2200:
            raise ValueError("graduation year must be a plausible four-digit year")
        return value

    @field_validator("cgpa", "percentage")
    @classmethod
    def validate_score(
        cls, value: EvidenceValue[float] | None
    ) -> EvidenceValue[float] | None:
        if value is not None and not 0 <= value.value <= 100:
            raise ValueError("CGPA and percentage must be between 0 and 100")
        return value


class SkillProfile(StrictModel):
    programming_languages: list[EvidenceValue[str]] = Field(default_factory=list)
    frameworks: list[EvidenceValue[str]] = Field(default_factory=list)
    databases: list[EvidenceValue[str]] = Field(default_factory=list)
    cloud_technologies: list[EvidenceValue[str]] = Field(default_factory=list)
    tools: list[EvidenceValue[str]] = Field(default_factory=list)
    technical_domains: list[EvidenceValue[str]] = Field(default_factory=list)


class ProjectProfile(StrictModel):
    name: EvidenceValue[str] | None = None
    description: EvidenceValue[str] | None = None
    technologies: list[EvidenceValue[str]] = Field(default_factory=list)
    responsibilities: list[EvidenceValue[str]] = Field(default_factory=list)
    achievements: list[EvidenceValue[str]] = Field(default_factory=list)


class ExperienceProfile(StrictModel):
    company: EvidenceValue[str] | None = None
    position: EvidenceValue[str] | None = None
    duration: EvidenceValue[str] | None = None
    responsibilities: list[EvidenceValue[str]] = Field(default_factory=list)
    achievements: list[EvidenceValue[str]] = Field(default_factory=list)


class StudentProfileFields(StrictModel):
    """The factual profile draft requested from a structured LLM provider."""

    personal_information: PersonalInformation = Field(default_factory=PersonalInformation)
    education: list[EducationProfile] = Field(default_factory=list)
    skills: SkillProfile = Field(default_factory=SkillProfile)
    projects: list[ProjectProfile] = Field(default_factory=list)
    experience: list[ExperienceProfile] = Field(default_factory=list)
    internships: list[ExperienceProfile] = Field(default_factory=list)
    certifications: list[EvidenceValue[str]] = Field(default_factory=list)
    awards: list[EvidenceValue[str]] = Field(default_factory=list)
    achievements: list[EvidenceValue[str]] = Field(default_factory=list)


class StudentProfile(StudentProfileFields):
    """Sanitized profile with extraction provenance for downstream callers."""

    extraction_provider: str = "deterministic_fallback"
    is_fallback: bool = True
    warnings: list[str] = Field(default_factory=list)
