"""Evidence collection and deterministic validation for tailored claims."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel

from app.ai.job_intelligence.schemas import JobListing
from app.ai.resume_intelligence.profile_schemas import EvidenceValue, StudentProfile

from .schemas import (
    GeneratedClaimDraft,
    OmittedClaim,
    TailoringEvidenceReference,
    ValidatedClaim,
)

_SAFE_CONNECTORS = {
    "a", "about", "an", "and", "applying", "application", "as", "at",
    "candidate", "for", "from", "i", "in", "include", "includes",
    "including", "is", "it", "my", "of", "on", "or", "our", "position",
    "profile", "project", "projects", "relevant", "role", "skills", "the",
    "this", "to", "with", "would", "your",
}
_NUMBER_RE = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?\s*%?(?!\w)")
_WORD_RE = re.compile(r"[a-z0-9]+(?:[+#.]?[a-z0-9+#.]*)", re.IGNORECASE)


@dataclass(frozen=True)
class SourceFact:
    path: str
    value: str
    source_text: str
    source_section: str | None
    confidence: str
    evidence_status: str
    verification_status: str
    source_type: str = "student_profile"

    def as_reference(self) -> TailoringEvidenceReference:
        return TailoringEvidenceReference(
            source_type=self.source_type,  # type: ignore[arg-type]
            source_path=self.path,
            value=self.value,
            source_text=self.source_text,
            source_section=self.source_section,
            confidence=self.confidence,  # type: ignore[arg-type]
            evidence_status=self.evidence_status,  # type: ignore[arg-type]
            verification_status=(
                self.verification_status
                if self.source_type == "student_profile"
                else "not_applicable"
            ),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ClaimValidation:
    claim: ValidatedClaim | None
    omission: OmittedClaim | None


def collect_profile_facts(profile: StudentProfile) -> tuple[dict[str, SourceFact], list[str]]:
    """Collect profile facts that have source excerpts containing their values."""
    facts: dict[str, SourceFact] = {}
    unsupported_paths: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, EvidenceValue):
            if not _value_is_in_source(value.value, value.source_text):
                unsupported_paths.append(path)
                return
            if value.evidence_status != "explicit" and value.verification_status != "verified":
                unsupported_paths.append(path)
                return
            facts[path] = SourceFact(
                path=path,
                value=str(value.value),
                source_text=value.source_text or "",
                source_section=value.source_section,
                confidence=value.confidence,
                evidence_status=value.evidence_status,
                verification_status=value.verification_status,
            )
            return
        if isinstance(value, BaseModel):
            for field_name in type(value).model_fields:
                child_path = f"{path}.{field_name}" if path else field_name
                visit(getattr(value, field_name), child_path)
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(profile, "")
    return facts, unsupported_paths


def collect_job_facts(job: JobListing) -> dict[str, SourceFact]:
    """Create references to selected-job context for role-specific statements."""
    facts: dict[str, SourceFact] = {}
    for name in ("title", "company", "description", "location"):
        value = getattr(job, name)
        if value:
            path = f"job_listing.{name}"
            facts[path] = SourceFact(
                path=path,
                value=str(value),
                source_text=str(value),
                source_section="job_listing",
                confidence="medium",
                evidence_status="explicit",
                verification_status="not_applicable",
                source_type="job_listing",
            )
    for field_name in ("required_skills", "preferred_skills", "eligibility_criteria"):
        for index, value in enumerate(getattr(job, field_name)):
            path = f"job_listing.{field_name}[{index}]"
            facts[path] = SourceFact(
                path=path,
                value=str(value),
                source_text=str(value),
                source_section="job_listing",
                confidence="medium",
                evidence_status="explicit",
                verification_status="not_applicable",
                source_type="job_listing",
            )
    return facts


def validate_generated_claim(
    draft: GeneratedClaimDraft,
    *,
    profile_facts: dict[str, SourceFact],
    job_facts: dict[str, SourceFact] | None = None,
    require_profile_evidence: bool = True,
) -> ClaimValidation:
    """Accept generated text only when its content and numbers are source-backed.

    Content words must occur in the cited fact values (or be safe grammatical
    connectors), and every number including a percentage must be present in
    the cited values with the same unit. Unknown paths reject the whole claim.
    """
    all_facts = {**profile_facts, **(job_facts or {})}
    requested_paths = list(dict.fromkeys(draft.evidence_paths))
    if not requested_paths:
        return _unsupported(draft, "No source evidence was provided.")
    if any(path not in all_facts for path in requested_paths):
        return _unsupported(draft, "One or more source references do not exist or are not usable.")

    evidence = [all_facts[path] for path in requested_paths]
    profile_evidence = [fact for fact in evidence if fact.source_type == "student_profile"]
    if require_profile_evidence and not profile_evidence:
        return _unsupported(draft, "A student claim must cite at least one StudentProfile fact.")

    source_values = " ".join(fact.value for fact in evidence)
    source_words = {word.casefold() for word in _WORD_RE.findall(source_values)}
    claim_words = {word.casefold() for word in _WORD_RE.findall(draft.text)}
    source_numbers = _number_tokens(source_values)
    if not _number_tokens(draft.text).issubset(source_numbers):
        return _unsupported(
            draft,
            "Generated wording contains a number or percentage not present in its cited facts.",
        )
    unsupported_words = claim_words - source_words - _SAFE_CONNECTORS
    if unsupported_words:
        return _unsupported(
            draft,
            "Generated wording contains unsupported factual terms: "
            + ", ".join(sorted(unsupported_words)),
        )

    return _build_claim(draft.text, evidence)


def build_direct_claim(
    text: str,
    facts: list[SourceFact],
    *,
    prefix: str = "",
) -> ValidatedClaim | None:
    """Format existing evidence without adding new factual wording."""
    if not facts:
        return None
    clean_text = " ".join(text.split())
    if not clean_text:
        return None
    # For direct output, labels and punctuation are structural. Numeric values
    # and factual values remain exactly those present in the profile.
    if prefix:
        clean_text = f"{prefix}{clean_text}"
    return _build_claim(clean_text, facts).claim


def reference_for_fact(fact: SourceFact) -> TailoringEvidenceReference:
    return fact.as_reference()


def _build_claim(text: str, facts: list[SourceFact]) -> ClaimValidation:
    references = [fact.as_reference() for fact in facts]
    student_facts = [fact for fact in facts if fact.source_type == "student_profile"]
    requires_confirmation = any(
        fact.verification_status != "verified" or fact.evidence_status != "explicit"
        for fact in student_facts
    )
    status = "needs_review" if requires_confirmation else "supported"
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    confidence = min(
        (fact.confidence for fact in student_facts),
        key=lambda item: confidence_rank[item],
        default="medium",
    )
    return ClaimValidation(
        claim=ValidatedClaim(
            text=text,
            evidence_references=references,
            validation_status=status,  # type: ignore[arg-type]
            confidence=confidence,  # type: ignore[arg-type]
            student_confirmation_required=requires_confirmation,
        ),
        omission=None,
    )


def _unsupported(draft: GeneratedClaimDraft, reason: str) -> ClaimValidation:
    return ClaimValidation(
        claim=None,
        omission=OmittedClaim(
            proposed_text=draft.text,
            validation_status="unsupported",
            reason=reason,
            evidence_paths=draft.evidence_paths,
        ),
    )


def _value_is_in_source(value: Any, source_text: str | None) -> bool:
    if not source_text:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        try:
            expected = Decimal(str(value))
        except InvalidOperation:
            return False
        return any(
            _decimal_value(token) == expected
            for token in _number_matches(source_text)
            if _decimal_value(token) is not None
        )
    normalized_value = _normalize(str(value))
    normalized_source = _normalize(source_text)
    if len(normalized_value) <= 2:
        return re.search(rf"(?<!\w){re.escape(normalized_value)}(?!\w)", normalized_source) is not None
    return normalized_value in normalized_source


def _number_tokens(text: str) -> set[tuple[str, bool]]:
    tokens: set[tuple[str, bool]] = set()
    for value in _number_matches(text):
        is_percent = "%" in value
        number = value.replace("%", "").replace(" ", "").replace(",", ".")
        try:
            normalized = format(Decimal(number).normalize(), "f")
        except InvalidOperation:
            continue
        tokens.add((normalized, is_percent))
    return tokens


def _number_matches(text: str) -> list[str]:
    return _NUMBER_RE.findall(text)


def _decimal_value(token: str) -> Decimal | None:
    try:
        return Decimal(token.replace("%", "").replace(" ", "").replace(",", "."))
    except InvalidOperation:
        return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()
