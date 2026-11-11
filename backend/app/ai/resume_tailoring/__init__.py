"""Job-specific resume and cover-letter tailoring services."""

from .cover_letter import generate_cover_letter
from .schemas import (
    CoverLetter,
    DocumentReviewMetadata,
    GenerationMetadata,
    OmittedClaim,
    ResumeFormatPreferences,
    TailoredEntry,
    TailoredResume,
    TailoredSkill,
    TailoringPreferences,
    TailoringRequest,
    TailoringEvidenceReference,
    ValidatedClaim,
    ValidationReport,
)
from .tailoring import tailor_resume

__all__ = [
    "CoverLetter",
    "DocumentReviewMetadata",
    "GenerationMetadata",
    "OmittedClaim",
    "ResumeFormatPreferences",
    "TailoredEntry",
    "TailoredResume",
    "TailoredSkill",
    "TailoringEvidenceReference",
    "TailoringPreferences",
    "TailoringRequest",
    "ValidatedClaim",
    "ValidationReport",
    "generate_cover_letter",
    "tailor_resume",
]
