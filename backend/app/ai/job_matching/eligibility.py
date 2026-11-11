"""Conservative evaluation of explicit, machine-checkable job requirements."""

from __future__ import annotations

import re

from app.ai.job_intelligence.schemas import JobListing
from app.ai.resume_intelligence.profile_schemas import EvidenceValue, StudentProfile

from .evidence import is_supported_fact, to_reference
from .schemas import (
    EligibilityAssessment,
    EligibilityCriterionAssessment,
)


def assess_eligibility(profile: StudentProfile, job: JobListing) -> EligibilityAssessment:
    assessments: list[EligibilityCriterionAssessment] = []
    for criterion in job.eligibility_criteria:
        assessments.append(_assess_text_criterion(profile, criterion))
    if job.min_experience_years is not None and job.min_experience_years > 0:
        assessments.append(
            _assess_minimum_experience(profile, job.min_experience_years)
        )

    if any(item.status == "mismatch" for item in assessments):
        status = "not_eligible"
    elif any(item.status == "unknown" for item in assessments):
        status = "unknown"
    elif assessments:
        status = "eligible"
    else:
        status = "not_applicable"

    warnings: list[str] = []
    if status == "not_eligible":
        warnings.append(
            "A directly comparable, resume-stated fact does not meet a listed hard requirement; confirm the fact before acting."
        )
    elif status == "unknown":
        warnings.append(
            "At least one eligibility requirement is unknown because the profile lacks enough directly supported information."
        )
    return EligibilityAssessment(status=status, criteria=assessments, warnings=warnings)


def _assess_text_criterion(
    profile: StudentProfile,
    criterion: str,
) -> EligibilityCriterionAssessment:
    cgpa_required = _cgpa_requirement(criterion)
    if cgpa_required is not None:
        facts = _education_facts(profile, "cgpa")
        if not facts:
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="unknown",
                explanation="No resume-stated CGPA is available to evaluate this requirement.",
            )
        qualifying = [fact for fact in facts if float(fact.value) >= cgpa_required]
        if qualifying:
            verified = [fact for fact in qualifying if fact.verification_status == "verified"]
            if not verified:
                return EligibilityCriterionAssessment(
                    criterion=criterion,
                    status="unknown",
                    explanation="The resume-stated CGPA meets the threshold but is not student-verified.",
                    evidence_references=[
                        to_reference(f"education[{index}].cgpa", fact)
                        for index, fact in _education_facts_with_index(profile, "cgpa")
                        if fact in qualifying
                    ],
                )
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="met",
                explanation=f"A resume-stated CGPA is at least {cgpa_required:g}.",
                evidence_references=[
                    to_reference(f"education[{index}].cgpa", fact)
                    for index, fact in _education_facts_with_index(profile, "cgpa")
                    if fact in verified
                ],
            )
        if any(fact.verification_status != "verified" for fact in facts):
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="unknown",
                explanation="A resume-stated CGPA is below the threshold but has not been student-verified.",
                evidence_references=[
                    to_reference(f"education[{index}].cgpa", fact)
                    for index, fact in _education_facts_with_index(profile, "cgpa")
                ],
            )
        return EligibilityCriterionAssessment(
            criterion=criterion,
            status="mismatch",
            explanation=f"The resume-stated CGPA is below the required {cgpa_required:g}.",
            evidence_references=[
                to_reference(f"education[{index}].cgpa", fact)
                for index, fact in _education_facts_with_index(profile, "cgpa")
            ],
        )

    year_range = _graduation_year_requirement(criterion)
    if year_range is not None:
        years = _education_facts(profile, "graduation_year")
        if not years:
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="unknown",
                explanation="No resume-stated graduation year is available to evaluate this requirement.",
            )
        lower, upper = year_range
        qualifying = [
            fact
            for fact in years
            if (lower is None or int(fact.value) >= lower)
            and (upper is None or int(fact.value) <= upper)
        ]
        if qualifying:
            verified = [fact for fact in qualifying if fact.verification_status == "verified"]
            if not verified:
                return EligibilityCriterionAssessment(
                    criterion=criterion,
                    status="unknown",
                    explanation="The resume-stated graduation year fits but is not student-verified.",
                    evidence_references=[
                        to_reference(f"education[{index}].graduation_year", fact)
                        for index, fact in _education_facts_with_index(profile, "graduation_year")
                        if fact in qualifying
                    ],
                )
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="met",
                explanation="A resume-stated graduation year falls within the required range.",
                evidence_references=[
                    to_reference(f"education[{index}].graduation_year", fact)
                    for index, fact in _education_facts_with_index(profile, "graduation_year")
                    if fact in verified
                ],
            )
        if any(fact.verification_status != "verified" for fact in years):
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="unknown",
                explanation="The resume-stated graduation year is outside the range but is not student-verified.",
                evidence_references=[
                    to_reference(f"education[{index}].graduation_year", fact)
                    for index, fact in _education_facts_with_index(profile, "graduation_year")
                ],
            )
        return EligibilityCriterionAssessment(
            criterion=criterion,
            status="mismatch",
            explanation="The resume-stated graduation year is outside the required range.",
            evidence_references=[
                to_reference(f"education[{index}].graduation_year", fact)
                for index, fact in _education_facts_with_index(profile, "graduation_year")
            ],
        )

    return EligibilityCriterionAssessment(
        criterion=criterion,
        status="unknown",
        explanation="This criterion is not safely machine-checkable from the available student profile fields.",
    )


def _assess_minimum_experience(
    profile: StudentProfile,
    required_years: float,
) -> EligibilityCriterionAssessment:
    criterion = f"Minimum {required_years:g} years of experience"
    total_facts: list[tuple[int, EvidenceValue[str], float]] = []
    single_role_facts: list[tuple[int, EvidenceValue[str], float]] = []
    for index, experience in enumerate(profile.experience):
        duration = experience.duration
        if duration is None:
            continue
        years = _duration_years(duration.value)
        if years is None:
            continue
        if re.search(r"\b(total|overall|combined)\b", duration.value, re.IGNORECASE):
            total_facts.append((index, duration, years))
        else:
            single_role_facts.append((index, duration, years))

    sufficient = [fact for fact in total_facts + single_role_facts if fact[2] >= required_years]
    verified_sufficient = [fact for fact in sufficient if fact[1].verification_status == "verified"]
    if verified_sufficient:
        return EligibilityCriterionAssessment(
            criterion=criterion,
            status="met",
            explanation="A directly stated experience duration meets the minimum.",
            evidence_references=[
                to_reference(f"experience[{index}].duration", fact)
                for index, fact, _years in verified_sufficient
            ],
        )
    if sufficient:
        return EligibilityCriterionAssessment(
            criterion=criterion,
            status="unknown",
            explanation="The resume-stated duration meets the minimum but is not student-verified.",
            evidence_references=[
                to_reference(f"experience[{index}].duration", fact)
                for index, fact, _years in sufficient
            ],
        )
    if total_facts:
        if any(fact.verification_status != "verified" for _index, fact, _years in total_facts):
            return EligibilityCriterionAssessment(
                criterion=criterion,
                status="unknown",
                explanation="The resume-stated total experience is below the minimum but is not student-verified.",
                evidence_references=[
                    to_reference(f"experience[{index}].duration", fact)
                    for index, fact, _years in total_facts
                ],
            )
        return EligibilityCriterionAssessment(
            criterion=criterion,
            status="mismatch",
            explanation="The resume explicitly states total experience below the minimum.",
            evidence_references=[
                to_reference(f"experience[{index}].duration", fact)
                for index, fact, _years in total_facts
            ],
        )
    return EligibilityCriterionAssessment(
        criterion=criterion,
        status="unknown",
        explanation="The profile does not state a directly comparable total experience duration.",
        evidence_references=[
            to_reference(f"experience[{index}].duration", fact)
            for index, fact, _years in single_role_facts
        ],
    )


def _cgpa_requirement(criterion: str) -> float | None:
    patterns = (
        r"\b(?:cgpa|gpa)\b\s*(?:of\s*)?(?:>=|>|:|=|at least\s+|minimum\s+|min\s+)?\s*(\d+(?:\.\d+)?)",
        r"\b(?:minimum|min(?:imum)?|at least)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:cgpa|gpa)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, criterion, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _graduation_year_requirement(criterion: str) -> tuple[int | None, int | None] | None:
    if not re.search(r"graduat|class of", criterion, re.IGNORECASE):
        return None
    years = [int(year) for year in re.findall(r"\b(?:19|20|21)\d{2}\b", criterion)]
    if not years:
        return None
    if len(years) >= 2:
        return min(years[0], years[1]), max(years[0], years[1])
    year = years[0]
    if re.search(r"\b(before|by|through|until)\b", criterion, re.IGNORECASE):
        return None, year
    if re.search(r"\b(after|from|on or after)\b", criterion, re.IGNORECASE):
        return year, None
    return year, year


def _education_facts(profile: StudentProfile, field_name: str) -> list[EvidenceValue]:
    return [fact for _index, fact in _education_facts_with_index(profile, field_name)]


def _education_facts_with_index(
    profile: StudentProfile,
    field_name: str,
) -> list[tuple[int, EvidenceValue]]:
    facts: list[tuple[int, EvidenceValue]] = []
    for index, education in enumerate(profile.education):
        fact = getattr(education, field_name)
        if fact is not None and is_supported_fact(fact):
            facts.append((index, fact))
    return facts


def _duration_years(value: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?)\b", value, re.IGNORECASE)
    if match is None:
        return None
    amount = float(match.group(1))
    if match.group(2).casefold().startswith("month"):
        return amount / 12
    return amount
