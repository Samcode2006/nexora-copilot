"""Validated input, generation, evidence, and draft schemas for tailoring."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.resume_intelligence.profile_schemas import StudentProfile

Tone = Literal["concise", "professional", "technical", "ats_friendly"]
ClaimStatus = Literal["supported", "needs_review"]
SourceType = Literal["student_profile", "job_listing"]
CANONICAL_COVER_LETTER_CLOSING = (
    "Thank you for considering my application. "
    "I would welcome the opportunity to discuss my application further."
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResumeFormatPreferences(StrictModel):
    section_order: list[
        Literal[
            "summary",
            "skills",
            "projects",
            "experience",
            "internships",
            "education",
            "certifications",
            "awards",
            "achievements",
        ]
    ] = Field(
        default_factory=lambda: [
            "summary",
            "skills",
            "projects",
            "experience",
            "internships",
            "education",
            "certifications",
            "awards",
            "achievements",
        ]
    )
    include_contact_details: bool = True
    bullet_style: Literal["bullets", "numbered"] = "bullets"

    @model_validator(mode="after")
    def section_order_is_unique(self) -> ResumeFormatPreferences:
        if len(self.section_order) != len(set(self.section_order)):
            raise ValueError("section_order cannot contain duplicate sections")
        return self


class TailoringPreferences(StrictModel):
    target_resume_length: Literal[
        "one_page", "two_pages", "concise", "standard", "detailed"
    ] = "standard"
    tone: Tone = "professional"
    student_instructions: str | None = Field(default=None, max_length=2000)
    cover_letter_length: Literal["short", "standard", "long"] = "standard"
    format_preferences: ResumeFormatPreferences = Field(
        default_factory=ResumeFormatPreferences
    )

    @model_validator(mode="after")
    def normalize_instructions(self) -> TailoringPreferences:
        if self.student_instructions is not None:
            clean = self.student_instructions.strip()
            self.student_instructions = clean or None
        return self


class TailoringRequest(StrictModel):
    student_profile: StudentProfile
    job_listing: JobListing
    job_match: JobMatch | None = None
    preferences: TailoringPreferences = Field(default_factory=TailoringPreferences)

    @model_validator(mode="after")
    def match_must_belong_to_selected_job(self) -> TailoringRequest:
        if self.job_match and self.job_match.job_id != self.job_listing.job_id:
            raise ValueError("job_match must refer to the selected job_listing")
        return self


class TailoringEvidenceReference(StrictModel):
    source_type: SourceType
    source_path: str
    value: str
    source_text: str
    source_section: str | None = None
    confidence: Literal["high", "medium", "low"]
    evidence_status: Literal["explicit", "inferred", "uncertain"]
    verification_status: Literal[
        "unverified", "needs_review", "verified", "not_applicable"
    ]


class ValidatedClaim(StrictModel):
    """One fact-bearing string approved by deterministic source validation."""

    text: str = Field(min_length=1)
    evidence_references: list[TailoringEvidenceReference] = Field(min_length=1)
    validation_status: ClaimStatus
    confidence: Literal["high", "medium", "low"]
    student_confirmation_required: bool


class OmittedClaim(StrictModel):
    """Audit-only record for generated text withheld from document content."""

    proposed_text: str
    validation_status: Literal["unsupported", "omitted"]
    reason: str
    evidence_paths: list[str] = Field(default_factory=list)


class ValidationReport(StrictModel):
    supported_claim_count: int = Field(ge=0)
    needs_review_claim_count: int = Field(ge=0)
    omitted_claims: list[OmittedClaim] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerationMetadata(StrictModel):
    provider: str
    is_fallback: bool
    generation_method: Literal[
        "llm_validated",
        "mixed_llm_and_fallback",
        "deterministic_fallback",
        "deterministic_fallback_after_validation",
    ]
    warnings: list[str] = Field(default_factory=list)


class DocumentReviewMetadata(StrictModel):
    generation_state: Literal["ai_generated_draft"] = "ai_generated_draft"
    validation_state: Literal["validated_draft"] = "validated_draft"
    review_state: Literal["not_reviewed", "student_reviewed_draft"] = "not_reviewed"
    approval_state: Literal["not_approved", "student_approved_document"] = "not_approved"

    @model_validator(mode="after")
    def approval_requires_review(self) -> DocumentReviewMetadata:
        if (
            self.approval_state == "student_approved_document"
            and self.review_state != "student_reviewed_draft"
        ):
            raise ValueError("a document must be student-reviewed before approval")
        return self


class TailoredSkill(StrictModel):
    skill: ValidatedClaim
    category: str
    evidence_class: Literal["demonstrated_in_context", "listed_skill"]


class TailoredEntry(StrictModel):
    heading: ValidatedClaim | None = None
    claims: list[ValidatedClaim] = Field(default_factory=list)


class TailoredResume(StrictModel):
    job_id: str
    job_title: str | None = None
    target_resume_length: Literal[
        "one_page", "two_pages", "concise", "standard", "detailed"
    ] = "standard"
    tone: Tone = "professional"
    bullet_style: Literal["bullets", "numbered"] = "bullets"
    personal_information: list[ValidatedClaim] = Field(default_factory=list)
    professional_summary: ValidatedClaim | None = None
    skills: list[TailoredSkill] = Field(default_factory=list)
    education: list[TailoredEntry] = Field(default_factory=list)
    projects: list[TailoredEntry] = Field(default_factory=list)
    experience: list[TailoredEntry] = Field(default_factory=list)
    internships: list[TailoredEntry] = Field(default_factory=list)
    certifications: list[ValidatedClaim] = Field(default_factory=list)
    awards: list[ValidatedClaim] = Field(default_factory=list)
    achievements: list[ValidatedClaim] = Field(default_factory=list)
    section_order: list[str] = Field(default_factory=list)
    change_explanations: list[str] = Field(default_factory=list)
    validation_report: ValidationReport
    generation: GenerationMetadata
    review: DocumentReviewMetadata = Field(default_factory=DocumentReviewMetadata)


class CoverLetter(StrictModel):
    job_id: str
    target_length: Literal["short", "standard", "long"] = "standard"
    tone: Tone = "professional"
    greeting: str
    opening_paragraph: ValidatedClaim
    relevant_experience_paragraph: ValidatedClaim | None = None
    role_relevance_paragraph: ValidatedClaim | None = None
    closing_paragraph: str
    sign_off: str = "Sincerely,"
    sign_off_name: ValidatedClaim | None = None
    validation_report: ValidationReport
    generation: GenerationMetadata
    review: DocumentReviewMetadata = Field(default_factory=DocumentReviewMetadata)

    @field_validator("closing_paragraph")
    @classmethod
    def _closing_paragraph_must_be_canonical(cls, value: str) -> str:
        if value != CANONICAL_COVER_LETTER_CLOSING:
            raise ValueError("closing_paragraph must use the canonical neutral closing")
        return value


class GeneratedClaimDraft(StrictModel):
    text: str = Field(min_length=1, max_length=1500)
    evidence_paths: list[str] = Field(min_length=1, max_length=12)


class ClaimRewriteDraft(StrictModel):
    source_path: str = Field(min_length=1, max_length=160)
    claim: GeneratedClaimDraft


class ResumeGenerationDraft(StrictModel):
    professional_summary: GeneratedClaimDraft | None = None
    rewrites: list[ClaimRewriteDraft] = Field(default_factory=list, max_length=80)
    skill_order: list[str] = Field(default_factory=list, max_length=100)
    project_order: list[int] = Field(default_factory=list, max_length=50)
    experience_order: list[int] = Field(default_factory=list, max_length=50)
    internship_order: list[int] = Field(default_factory=list, max_length=50)


class CoverLetterGenerationDraft(StrictModel):
    relevant_experience: GeneratedClaimDraft | None = None
    role_relevance: GeneratedClaimDraft | None = None
