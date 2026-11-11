"""Validated schemas and configurable policy for job matching results."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MatchDimension = Literal[
    "required_skills",
    "preferred_skills",
    "education_relevance",
    "experience_relevance",
    "project_relevance",
    "eligibility",
]
EligibilityStatus = Literal["eligible", "not_eligible", "unknown", "not_applicable"]
AssessmentStatus = Literal["assessed", "unknown", "not_applicable"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatchWeights(StrictModel):
    """Scoring weights; all dimensions must total 1.0."""

    required_skills: float = Field(default=0.30, ge=0, le=1)
    preferred_skills: float = Field(default=0.10, ge=0, le=1)
    education_relevance: float = Field(default=0.15, ge=0, le=1)
    experience_relevance: float = Field(default=0.15, ge=0, le=1)
    project_relevance: float = Field(default=0.15, ge=0, le=1)
    eligibility: float = Field(default=0.15, ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> MatchWeights:
        total = sum(getattr(self, name) for name in type(self).model_fields)
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"matching weights must sum to 1.0; got {total:.6f}")
        return self


class MatchConfig(StrictModel):
    weights: MatchWeights = Field(default_factory=MatchWeights)
    ineligible_score_cap: float = Field(default=39.0, ge=0, le=100)
    unknown_eligibility_score_cap: float = Field(default=69.0, ge=0, le=100)


class EvidenceReference(StrictModel):
    profile_path: str
    value: str
    source_text: str
    source_section: str | None = None
    confidence: Literal["high", "medium", "low"]
    evidence_status: Literal["explicit", "inferred", "uncertain"]
    verification_status: Literal["unverified", "needs_review", "verified"]


class SkillMatch(StrictModel):
    job_skill: str
    student_skill: str
    category: Literal["required", "preferred"]
    match_type: Literal["exact", "synonym"]
    evidence: list[EvidenceReference] = Field(default_factory=list)


class SkillAssessment(StrictModel):
    job_skill: str
    category: Literal["required", "preferred"]
    status: Literal["matched", "not_evidenced"]
    explanation: str


class DimensionScore(StrictModel):
    score: float | None = Field(default=None, ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    status: AssessmentStatus
    explanation: str
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


class EligibilityCriterionAssessment(StrictModel):
    criterion: str
    status: Literal["met", "mismatch", "unknown"]
    explanation: str
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


class EligibilityAssessment(StrictModel):
    status: EligibilityStatus
    criteria: list[EligibilityCriterionAssessment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class JobMatch(StrictModel):
    job_id: str
    job_title: str | None = None
    rank: int = Field(ge=1)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    score_coverage: float = Field(ge=0, le=1)
    dimension_scores: dict[MatchDimension, DimensionScore]
    matched_skills: list[SkillMatch] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    skill_assessments: list[SkillAssessment] = Field(default_factory=list)
    eligibility_assessment: EligibilityAssessment
    explanation: str
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    matching_method: str
    confidence: Literal["high", "medium", "low"]
    uncertainty: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
