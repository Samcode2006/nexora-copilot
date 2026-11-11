"""Personalized, evidence-backed cover-letter generation."""

from __future__ import annotations

import re
from typing import Any

from app.ai.job_intelligence.schemas import JobListing
from app.ai.providers import LLMService
from app.ai.resume_intelligence.profile_schemas import StudentProfile

from .generation import DraftGeneration, generate_draft
from .prompts import build_cover_letter_prompt
from .schemas import (
    CoverLetter,
    CoverLetterGenerationDraft,
    GenerationMetadata,
    OmittedClaim,
    TailoredResume,
    TailoringPreferences,
    ValidationReport,
    ValidatedClaim,
)
from .validation import (
    SourceFact,
    build_direct_claim,
    collect_job_facts,
    collect_profile_facts,
    validate_generated_claim,
)

_SKILL_ALIASES = {
    "js": "javascript",
    "postgres": "postgresql",
    "node": "node.js",
    "nodejs": "node.js",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "aws": "amazon web services",
}


def generate_cover_letter(
    student_profile: StudentProfile,
    job_listing: JobListing,
    tailored_resume: TailoredResume | None = None,
    preferences: TailoringPreferences | dict[str, Any] | None = None,
    *,
    llm_service: LLMService | None = None,
) -> CoverLetter:
    """Draft a cover letter without adding unsupported student qualifications."""
    parsed_preferences = TailoringPreferences.model_validate(preferences or {})
    if tailored_resume is not None and tailored_resume.job_id != job_listing.job_id:
        raise ValueError("tailored_resume must refer to the selected job_listing")

    profile_facts, unsupported_paths = collect_profile_facts(student_profile)
    job_facts = collect_job_facts(job_listing)
    generated: DraftGeneration = generate_draft(
        prompt=build_cover_letter_prompt(
            job=job_listing,
            preferences=parsed_preferences,
            profile_facts=profile_facts,
        ),
        response_model=CoverLetterGenerationDraft,
        fallback=CoverLetterGenerationDraft(),
        llm_service=llm_service,
    )
    draft = CoverLetterGenerationDraft.model_validate(generated.value)
    omitted: list[OmittedClaim] = []
    warnings = list(generated.warnings)
    if unsupported_paths:
        warnings.append(
            f"Ignored {len(unsupported_paths)} profile value(s) without usable source evidence."
        )

    opening = _opening_paragraph(job_listing, job_facts)
    relevant_experience: ValidatedClaim | None = None
    role_relevance: ValidatedClaim | None = None
    llm_experience_accepted = False
    llm_role_relevance_accepted = False

    if draft.relevant_experience is not None:
        validation = validate_generated_claim(
            draft.relevant_experience,
            profile_facts=profile_facts,
        )
        if validation.claim is not None:
            relevant_experience = validation.claim
            llm_experience_accepted = True
        elif validation.omission is not None:
            omitted.append(validation.omission)
            warnings.append("Omitted the provider-generated experience paragraph after evidence validation failed.")
    if relevant_experience is None:
        relevant_experience = _fallback_experience(
            student_profile,
            profile_facts,
            parsed_preferences.cover_letter_length,
        )

    if draft.role_relevance is not None:
        validation = validate_generated_claim(
            draft.role_relevance,
            profile_facts=profile_facts,
            job_facts=job_facts,
        )
        if validation.claim is not None:
            role_relevance = validation.claim
            llm_role_relevance_accepted = True
        elif validation.omission is not None:
            omitted.append(validation.omission)
            warnings.append("Omitted the provider-generated role-relevance paragraph after evidence validation failed.")
    if role_relevance is None:
        role_relevance = _fallback_role_relevance(
            student_profile,
            profile_facts,
            job_listing,
            job_facts,
            tailored_resume,
        )

    sign_off_name = None
    name_fact = profile_facts.get("personal_information.name")
    if name_fact is not None:
        sign_off_name = build_direct_claim(name_fact.value, [name_fact])

    included = [opening]
    included.extend(
        claim for claim in (relevant_experience, role_relevance, sign_off_name) if claim
    )
    if not relevant_experience and not role_relevance:
        warnings.append(
            "The profile has no usable project or experience details to personalize the letter further."
        )
    method, is_fallback = _generation_method(
        generated,
        has_valid_llm_content=llm_experience_accepted or llm_role_relevance_accepted,
        rejected_count=len(omitted),
    )
    if is_fallback and not generated.is_fallback:
        warnings.append("Provider wording was rejected by factual validation; deterministic wording was used.")
    report = ValidationReport(
        supported_claim_count=sum(claim.validation_status == "supported" for claim in included),
        needs_review_claim_count=sum(claim.validation_status == "needs_review" for claim in included),
        omitted_claims=omitted,
        warnings=list(dict.fromkeys(warnings)),
    )
    return CoverLetter(
        job_id=job_listing.job_id,
        target_length=parsed_preferences.cover_letter_length,
        tone=parsed_preferences.tone,
        greeting="Dear Hiring Team,",
        opening_paragraph=opening,
        relevant_experience_paragraph=relevant_experience,
        role_relevance_paragraph=role_relevance,
        closing_paragraph="Thank you for considering my application. I would welcome the opportunity to discuss my application further.",
        sign_off="Sincerely,",
        sign_off_name=sign_off_name,
        validation_report=report,
        generation=GenerationMetadata(
            provider=generated.provider,
            is_fallback=is_fallback,
            generation_method=method,
            warnings=list(dict.fromkeys(warnings)),
        ),
    )


def _opening_paragraph(
    job: JobListing, job_facts: dict[str, SourceFact]
) -> ValidatedClaim:
    references: list[SourceFact] = []
    title = job.title
    company = job.company
    if title and (fact := job_facts.get("job_listing.title")):
        references.append(fact)
    if company and (fact := job_facts.get("job_listing.company")):
        references.append(fact)
    if title and company:
        text = f"I am applying for the {title} role at {company}."
    elif title:
        text = f"I am applying for the {title} role."
    elif job.description and (fact := job_facts.get("job_listing.description")):
        references.append(fact)
        text = "I am writing to express my interest in the position described in this listing."
    else:
        text = "I am writing to express my interest in the selected position."
    if not references:
        # The selected listing is the provenance for this non-qualification
        # statement when upstream metadata lacks a human-readable title.
        references.append(
            SourceFact(
                path="job_listing.job_id",
                value=job.job_id,
                source_text=job.job_id,
                source_section="job_listing",
                confidence="medium",
                evidence_status="explicit",
                verification_status="not_applicable",
                source_type="job_listing",
            )
        )
    claim = build_direct_claim(text, references)
    assert claim is not None
    return claim


def _fallback_experience(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    length: str,
) -> ValidatedClaim | None:
    max_details = {"short": 1, "standard": 2, "long": 4}[length]
    # Prefer work experience, then internships, then project experience. This
    # ordering changes presentation only; it does not imply employment.
    for root, entities in (
        ("experience", profile.experience),
        ("internships", profile.internships),
        ("projects", profile.projects),
    ):
        for entity_index, entity in enumerate(entities):
            prefix = f"{root}[{entity_index}]"
            fields = (
                ("position", "company", "duration", "responsibilities", "achievements")
                if root != "projects"
                else ("name", "description", "technologies", "responsibilities", "achievements")
            )
            refs: list[SourceFact] = []
            parts: list[str] = []
            for field_name in fields:
                path = f"{prefix}.{field_name}"
                if field_name in {"responsibilities", "achievements", "technologies"}:
                    list_values = [
                        facts[f"{path}[{index}]"]
                        for index in range(len(getattr(entity, field_name)))
                        if f"{path}[{index}]" in facts
                    ]
                    for fact in list_values[:max_details]:
                        parts.append(fact.value)
                        refs.append(fact)
                elif path in facts:
                    parts.append(facts[path].value)
                    refs.append(facts[path])
            if parts and refs:
                prefix_label = "Project details: " if root == "projects" else "Experience details: "
                return build_direct_claim(". ".join(parts), refs, prefix=prefix_label)
    return None


def _fallback_role_relevance(
    profile: StudentProfile,
    profile_facts: dict[str, SourceFact],
    job: JobListing,
    job_facts: dict[str, SourceFact],
    tailored_resume: TailoredResume | None,
) -> ValidatedClaim | None:
    listed_skills = _profile_skill_facts(profile, profile_facts, tailored_resume)
    requested_skills = [*job.required_skills, *job.preferred_skills]
    overlaps: list[tuple[SourceFact, SourceFact]] = []
    for student_fact in listed_skills:
        for index, job_skill in enumerate(requested_skills):
            if _skill_key(student_fact.value) == _skill_key(job_skill):
                field = "required_skills" if index < len(job.required_skills) else "preferred_skills"
                field_index = index if field == "required_skills" else index - len(job.required_skills)
                job_fact = job_facts.get(f"job_listing.{field}[{field_index}]")
                if job_fact:
                    overlaps.append((student_fact, job_fact))
                break
    if not overlaps:
        return None
    unique_student: dict[str, SourceFact] = {}
    unique_job: dict[str, SourceFact] = {}
    for student_fact, job_fact in overlaps:
        unique_student[student_fact.path] = student_fact
        unique_job[job_fact.path] = job_fact
    skills = ", ".join(fact.value for fact in unique_student.values())
    text = f"The profile lists {skills}, which also appear in the selected job's listed skills."
    return build_direct_claim(text, [*unique_student.values(), *unique_job.values()])


def _profile_skill_facts(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    tailored_resume: TailoredResume | None,
) -> list[SourceFact]:
    if tailored_resume is not None:
        paths = [
            reference.source_path
            for skill in tailored_resume.skills
            for reference in skill.skill.evidence_references
            if reference.source_type == "student_profile"
        ]
        if paths:
            return list(dict.fromkeys(facts[path] for path in paths if path in facts))
    return [fact for path, fact in facts.items() if path.startswith("skills.")]


def _generation_method(
    generation: DraftGeneration,
    *,
    has_valid_llm_content: bool,
    rejected_count: int,
) -> tuple[str, bool]:
    if generation.is_fallback:
        return "deterministic_fallback", True
    if rejected_count and has_valid_llm_content:
        return "mixed_llm_and_fallback", False
    if rejected_count and not has_valid_llm_content:
        return "deterministic_fallback_after_validation", True
    if has_valid_llm_content:
        return "llm_validated", False
    return "deterministic_fallback_after_validation", True


def _skill_key(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.casefold()).strip()
    normalized = re.sub(r"[^a-z0-9+#. ]", "", normalized)
    return _SKILL_ALIASES.get(normalized, normalized)
