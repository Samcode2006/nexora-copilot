"""Traceability helpers to prevent unsupported profile facts affecting matches."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.ai.resume_intelligence.profile_schemas import EvidenceValue

from .schemas import EvidenceReference


def is_traceable(evidence: EvidenceValue[Any] | None) -> bool:
    if evidence is None or not evidence.source_text:
        return False
    value = evidence.value
    source = _normalize(evidence.source_text)
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        try:
            expected = Decimal(str(value))
        except InvalidOperation:
            return False
        for token in re.findall(r"(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)", source):
            try:
                if Decimal(token.rstrip("%").replace(",", ".")) == expected:
                    return True
            except InvalidOperation:
                continue
        return False
    text = _normalize(str(value))
    if not text:
        return False
    if len(text) <= 2:
        return re.search(rf"(?<!\w){re.escape(text)}(?!\w)", source) is not None
    return text in source


def is_supported_fact(evidence: EvidenceValue[Any] | None) -> bool:
    """Accept explicit source facts or facts the student has verified."""
    return bool(
        is_traceable(evidence)
        and evidence is not None
        and (evidence.evidence_status == "explicit" or evidence.verification_status == "verified")
    )


def to_reference(profile_path: str, evidence: EvidenceValue[Any]) -> EvidenceReference:
    return EvidenceReference(
        profile_path=profile_path,
        value=str(evidence.value),
        source_text=evidence.source_text or "",
        source_section=evidence.source_section,
        confidence=evidence.confidence,
        evidence_status=evidence.evidence_status,
        verification_status=evidence.verification_status,
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()
