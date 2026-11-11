"""Evidence-preserving, job-specific resume tailoring service."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.providers import LLMService
from app.ai.resume_intelligence.profile_schemas import EvidenceValue, StudentProfile

from .generation import DraftGeneration, generate_draft
from .prompts import build_resume_prompt
from .schemas import (
    ClaimRewriteDraft,
    GenerationMetadata,
    OmittedClaim,
    ResumeGenerationDraft,
    TailoredEntry,
    TailoredResume,
    TailoredSkill,
    TailoringPreferences,
    TailoringRequest,
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
    "gcp": "google cloud platform",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[+#.]?[a-z0-9+#.]*)", re.IGNORECASE)
_SKILL_PATH_RE = re.compile(r"^skills\.([a-z_]+)\[(\d+)\]$")


def tailor_resume(
    student_profile: StudentProfile,
    job_listing: JobListing,
    job_match: JobMatch | None = None,
    preferences: TailoringPreferences | dict[str, Any] | None = None,
    *,
    llm_service: LLMService | None = None,
) -> TailoredResume:
    """Build a separate job-targeted resume draft using only supported facts.

    LLM-written claims must cite exact profile paths and pass deterministic
    lexical and numeric checks. Rejected wording is recorded in the audit, not
    placed in resume content. Existing profile facts remain unchanged.
    """
    request = TailoringRequest.model_validate(
        {
            "student_profile": student_profile,
            "job_listing": job_listing,
            "job_match": job_match,
            "preferences": preferences or {},
        }
    )
    profile = request.student_profile
    job = request.job_listing
    preference = request.preferences
    facts, unsupported_profile_paths = collect_profile_facts(profile)
    job_facts = collect_job_facts(job)
    generation = generate_draft(
        prompt=build_resume_prompt(
            job=job,
            preferences=preference,
            profile_facts=facts,
        ),
        response_model=ResumeGenerationDraft,
        fallback=ResumeGenerationDraft(),
        llm_service=llm_service,
    )
    draft = ResumeGenerationDraft.model_validate(generation.value)
    rejected: list[OmittedClaim] = []
    warnings = list(generation.warnings)
    if unsupported_profile_paths:
        warnings.append(
            f"Ignored {len(unsupported_profile_paths)} profile value(s) without usable source evidence."
        )

    accepted_summary: ValidatedClaim | None = None
    llm_summary_accepted = False
    if draft.professional_summary is not None:
        result = validate_generated_claim(
            draft.professional_summary,
            profile_facts=facts,
            job_facts=job_facts,
        )
        if result.claim is not None:
            accepted_summary = result.claim
            llm_summary_accepted = True
        elif result.omission is not None:
            rejected.append(result.omission)
            warnings.append("Omitted the provider-generated professional summary after evidence validation failed.")

    rewrite_map, rewrite_rejections = _validate_rewrites(draft.rewrites, facts)
    rejected.extend(rewrite_rejections)
    if rewrite_rejections:
        warnings.append(
            f"Omitted {len(rewrite_rejections)} generated rewrite(s) that could not be validated against source facts."
        )

    included_claims: list[ValidatedClaim] = []
    personal_information = _build_personal_information(
        profile, facts, preference, included_claims
    )
    skills = _build_skills(
        profile,
        facts,
        job,
        request.job_match,
        draft.skill_order,
        _skill_limit(preference.target_resume_length),
        included_claims,
        warnings,
    )
    education = _build_education(profile, facts, included_claims)
    projects = _build_entities(
        profile.projects,
        "projects",
        facts,
        rewrite_map,
        _ordered_indexes(
            profile.projects,
            "projects",
            draft.project_order,
            job,
            warnings,
            limit=_entity_limit(preference.target_resume_length),
        ),
        included_claims,
        heading_fields=("name",),
        detail_fields=("description", "technologies", "responsibilities", "achievements"),
    )
    experience = _build_entities(
        profile.experience,
        "experience",
        facts,
        rewrite_map,
        _ordered_indexes(
            profile.experience,
            "experience",
            draft.experience_order,
            job,
            warnings,
            limit=_entity_limit(preference.target_resume_length),
        ),
        included_claims,
        heading_fields=("position", "company"),
        detail_fields=("duration", "responsibilities", "achievements"),
    )
    internships = _build_entities(
        profile.internships,
        "internships",
        facts,
        rewrite_map,
        _ordered_indexes(
            profile.internships,
            "internships",
            draft.internship_order,
            job,
            warnings,
            limit=_entity_limit(preference.target_resume_length),
        ),
        included_claims,
        heading_fields=("position", "company"),
        detail_fields=("duration", "responsibilities", "achievements"),
    )
    certifications = _build_simple_evidence_list(
        profile.certifications, "certifications", facts, included_claims
    )
    awards = _build_simple_evidence_list(profile.awards, "awards", facts, included_claims)
    achievements = _build_simple_evidence_list(
        profile.achievements, "achievements", facts, included_claims
    )

    if accepted_summary is None:
        accepted_summary = _fallback_summary(profile, facts, job, skills)
        if accepted_summary is not None:
            included_claims.append(accepted_summary)
        elif draft.professional_summary is not None:
            warnings.append("No evidence-backed professional summary could be produced.")
    elif draft.professional_summary is not None:
        included_claims.append(accepted_summary)

    if not job.title and not job.description:
        warnings.append("The selected job has no title or description; tailoring relevance is limited.")

    method, is_fallback = _generation_method(
        generation,
        has_valid_llm_content=llm_summary_accepted
        or bool(rewrite_map)
        or bool(_valid_order_prefix(draft.skill_order, facts)),
        rejected_count=len(rejected),
    )
    if is_fallback and generation.is_fallback is False:
        warnings.append("Provider output was rejected by factual validation; deterministic content was used.")

    report = _validation_report(included_claims, rejected, warnings)
    return TailoredResume(
        job_id=job.job_id,
        job_title=job.title,
        target_resume_length=preference.target_resume_length,
        tone=preference.tone,
        bullet_style=preference.format_preferences.bullet_style,
        personal_information=personal_information,
        professional_summary=accepted_summary,
        skills=skills,
        education=education,
        projects=projects,
        experience=experience,
        internships=internships,
        certifications=certifications,
        awards=awards,
        achievements=achievements,
        section_order=preference.format_preferences.section_order,
        change_explanations=_change_explanations(job, skills, projects, experience),
        validation_report=report,
        generation=GenerationMetadata(
            provider=generation.provider,
            is_fallback=is_fallback,
            generation_method=method,
            warnings=list(dict.fromkeys(warnings)),
        ),
    )


def _validate_rewrites(
    rewrites: list[ClaimRewriteDraft], facts: dict[str, SourceFact]
) -> tuple[dict[str, ValidatedClaim], list[OmittedClaim]]:
    accepted: dict[str, ValidatedClaim] = {}
    rejected: list[OmittedClaim] = []
    for rewrite in rewrites:
        target = facts.get(rewrite.source_path)
        if target is None or not rewrite.source_path.startswith(
            ("projects[", "experience[", "internships[")
        ) or re.search(r"\.(description|responsibilities\[\d+\]|achievements\[\d+\])$", rewrite.source_path) is None:
            rejected.append(
                OmittedClaim(
                    proposed_text=rewrite.claim.text,
                    validation_status="unsupported",
                    reason="Rewrite target is not a supported project, experience, or internship fact.",
                    evidence_paths=rewrite.claim.evidence_paths,
                )
            )
            continue
        if rewrite.claim.evidence_paths != [rewrite.source_path]:
            rejected.append(
                OmittedClaim(
                    proposed_text=rewrite.claim.text,
                    validation_status="unsupported",
                    reason="A rewrite must cite only the exact source fact it replaces.",
                    evidence_paths=rewrite.claim.evidence_paths,
                )
            )
            continue
        result = validate_generated_claim(
            rewrite.claim,
            profile_facts=facts,
            require_profile_evidence=True,
        )
        if result.claim is not None:
            accepted[rewrite.source_path] = result.claim
        elif result.omission is not None:
            rejected.append(result.omission)
    return accepted, rejected


def _build_personal_information(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    preferences: TailoringPreferences,
    included: list[ValidatedClaim],
) -> list[ValidatedClaim]:
    if not preferences.format_preferences.include_contact_details:
        return []
    output: list[ValidatedClaim] = []
    for field_name in ("name", "email", "phone", "location"):
        path = f"personal_information.{field_name}"
        fact = facts.get(path)
        if fact is None:
            continue
        label = "Name" if field_name == "name" else field_name.replace("_", " ").title()
        claim = build_direct_claim(fact.value, [fact], prefix=f"{label}: ")
        if claim:
            output.append(claim)
            included.append(claim)
    return output


def _build_skills(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    job: JobListing,
    job_match: JobMatch | None,
    model_order: list[str],
    limit: int | None,
    included: list[ValidatedClaim],
    warnings: list[str],
) -> list[TailoredSkill]:
    paths = [path for path in facts if path.startswith("skills.")]
    if not paths:
        return []
    valid_model_order = _valid_order_prefix(model_order, facts)
    if len(valid_model_order) != len(model_order):
        warnings.append("Ignored invalid skill-order references from the LLM draft.")
    matched_paths: list[str] = []
    if job_match is not None:
        matched_paths = [
            evidence.profile_path
            for matched in job_match.matched_skills
            for evidence in matched.evidence
            if evidence.profile_path in facts and evidence.profile_path.startswith("skills.")
        ]
    request_terms = {
        _skill_key(skill)
        for skill in [*job.required_skills, *job.preferred_skills]
    }
    request_terms.discard("")
    relevant_paths = [
        path for path in paths if _skill_key(facts[path].value) in request_terms
    ]
    relevant_model_order = [path for path in valid_model_order if path in relevant_paths]
    remaining_model_order = [path for path in valid_model_order if path not in relevant_paths]
    ordered_paths = list(
        dict.fromkeys(
            [*matched_paths, *relevant_model_order, *relevant_paths, *remaining_model_order, *paths]
        )
    )
    if limit is not None and len(ordered_paths) > limit:
        warnings.append(f"Limited the skills section to {limit} items for the requested resume length.")
        ordered_paths = ordered_paths[:limit]
    contexts = _project_and_experience_text(facts)
    output: list[TailoredSkill] = []
    for path in ordered_paths:
        fact = facts.get(path)
        if fact is None:
            continue
        match = _SKILL_PATH_RE.match(path)
        if not match:
            continue
        category = match.group(1)
        label = f"{category.replace('_', ' ').title()}: {fact.value}"
        contextual = any(_contains_phrase(text.value, fact.value) for text in contexts)
        refs = [fact]
        if contextual:
            refs.extend(
                context_fact
                for context_fact in contexts
                if _contains_phrase(context_fact.value, fact.value)
            )
        claim = build_direct_claim(label, list(dict.fromkeys(refs)))
        if claim is None:
            continue
        included.append(claim)
        output.append(
            TailoredSkill(
                skill=claim,
                category=category,
                evidence_class="demonstrated_in_context" if contextual else "listed_skill",
            )
        )
    return output


def _build_education(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    included: list[ValidatedClaim],
) -> list[TailoredEntry]:
    output: list[TailoredEntry] = []
    for index, _education in enumerate(profile.education):
        prefix = f"education[{index}]"
        heading = _direct(facts, f"{prefix}.institution", included)
        detail_fields = (
            ("degree", "Degree: "),
            ("branch", "Branch: "),
            ("graduation_year", "Graduation year: "),
            ("cgpa", "CGPA: "),
            ("percentage", "Percentage: "),
        )
        claims = [
            claim
            for field_name, label in detail_fields
            if (claim := _direct(facts, f"{prefix}.{field_name}", included, label)) is not None
        ]
        if heading or claims:
            output.append(TailoredEntry(heading=heading, claims=claims))
    return output


def _build_entities(
    entities: list[Any],
    root: str,
    facts: dict[str, SourceFact],
    rewrites: dict[str, ValidatedClaim],
    indexes: list[int],
    included: list[ValidatedClaim],
    *,
    heading_fields: tuple[str, ...],
    detail_fields: tuple[str, ...],
) -> list[TailoredEntry]:
    output: list[TailoredEntry] = []
    for index in indexes:
        if index >= len(entities):
            continue
        prefix = f"{root}[{index}]"
        heading_facts = [
            facts[path]
            for field_name in heading_fields
            if (path := f"{prefix}.{field_name}") in facts
        ]
        heading = None
        if heading_facts:
            heading = build_direct_claim(" — ".join(fact.value for fact in heading_facts), heading_facts)
            if heading:
                included.append(heading)

        claims: list[ValidatedClaim] = []
        for field_name in detail_fields:
            path = f"{prefix}.{field_name}"
            if field_name in {"technologies", "responsibilities", "achievements"}:
                values = [
                    (item_index, facts[item_path])
                    for item_index in range(len(getattr(entities[index], field_name)))
                    if (item_path := f"{path}[{item_index}]") in facts
                ]
                if not values:
                    continue
                joined = ", ".join(fact.value for _, fact in values)
                label = {
                    "technologies": "Technologies: ",
                    "responsibilities": "Responsibilities: ",
                    "achievements": "Achievements: ",
                }[field_name]
                claim = build_direct_claim(joined, [fact for _, fact in values], prefix=label)
                if claim:
                    claims.append(claim)
                    included.append(claim)
                continue

            fact = facts.get(path)
            if fact is None:
                continue
            claim = rewrites.get(path)
            if claim is None:
                label = "Duration: " if field_name == "duration" else ""
                claim = build_direct_claim(fact.value, [fact], prefix=label)
            if claim:
                claims.append(claim)
                included.append(claim)
        if heading or claims:
            output.append(TailoredEntry(heading=heading, claims=claims))
    return output


def _build_simple_evidence_list(
    values: list[EvidenceValue[str]],
    root: str,
    facts: dict[str, SourceFact],
    included: list[ValidatedClaim],
) -> list[ValidatedClaim]:
    output: list[ValidatedClaim] = []
    for index in range(len(values)):
        claim = _direct(facts, f"{root}[{index}]", included)
        if claim:
            output.append(claim)
    return output


def _direct(
    facts: dict[str, SourceFact],
    path: str,
    included: list[ValidatedClaim],
    prefix: str = "",
) -> ValidatedClaim | None:
    fact = facts.get(path)
    if fact is None:
        return None
    claim = build_direct_claim(fact.value, [fact], prefix=prefix)
    if claim:
        included.append(claim)
    return claim


def _fallback_summary(
    profile: StudentProfile,
    facts: dict[str, SourceFact],
    job: JobListing,
    skills: list[TailoredSkill],
) -> ValidatedClaim | None:
    if not facts:
        return None
    parts: list[str] = []
    refs: list[SourceFact] = []
    if job.title:
        title_fact = collect_job_facts(job).get("job_listing.title")
        if title_fact:
            parts.append(f"Target role: {job.title}")
            refs.append(title_fact)
    if profile.education:
        for field_name in ("degree", "branch", "institution"):
            path = f"education[0].{field_name}"
            fact = facts.get(path)
            if fact:
                refs.append(fact)
        education_values = [fact.value for fact in refs if fact.path.startswith("education[0].")]
        if education_values:
            parts.append("Education: " + "; ".join(dict.fromkeys(education_values)))
    relevant_skills = [item for item in skills if _skill_key(item.skill.text.split(": ", 1)[-1]) in {
        _skill_key(skill) for skill in [*job.required_skills, *job.preferred_skills]
    }]
    selected_skills = relevant_skills or skills[:5]
    skill_values: list[str] = []
    for item in selected_skills[:5]:
        skill_value = item.skill.text.split(": ", 1)[-1]
        if skill_value not in skill_values:
            skill_values.append(skill_value)
            refs.extend(
                SourceFact(
                    path=reference.source_path,
                    value=reference.value,
                    source_text=reference.source_text,
                    source_section=reference.source_section,
                    confidence=reference.confidence,
                    evidence_status=reference.evidence_status,
                    verification_status=reference.verification_status,
                )
                for reference in item.skill.evidence_references
                if reference.source_type == "student_profile"
            )
    if skill_values:
        parts.append("Listed skills: " + ", ".join(skill_values))
    if not any(fact.source_type == "student_profile" for fact in refs):
        profile_detail = next(
            (
                fact
                for path, fact in facts.items()
                if path.startswith(("projects[", "experience[", "internships[", "certifications[", "achievements["))
            ),
            None,
        )
        if profile_detail is not None:
            parts.append(f"Profile detail: {profile_detail.value}")
            refs.append(profile_detail)
    if not parts:
        return None
    unique_refs = list({fact.path: fact for fact in refs}.values())
    if not any(fact.source_type == "student_profile" for fact in unique_refs):
        return None
    return build_direct_claim(". ".join(parts), unique_refs)


def _ordered_indexes(
    entities: list[Any],
    root: str,
    model_order: list[int],
    job: JobListing,
    warnings: list[str],
    *,
    limit: int | None,
) -> list[int]:
    valid = [index for index in model_order if isinstance(index, int) and 0 <= index < len(entities)]
    if len(valid) != len(model_order) or len(valid) != len(set(valid)):
        warnings.append(f"Ignored invalid {root} ordering values from the LLM draft.")
    target_tokens = _tokens(_job_text(job))
    relevance: list[tuple[int, int]] = []
    for index, entity in enumerate(entities):
        candidate_text = " ".join(
            fact.value
            for path, fact in collect_profile_facts_for_entity(entity, root, index).items()
        )
        overlap = len(_tokens(candidate_text) & target_tokens)
        relevance.append((index, overlap))
    deterministic = [index for index, _score in sorted(relevance, key=lambda item: (-item[1], item[0]))]
    ordered = list(dict.fromkeys([*valid, *deterministic]))
    if limit is not None and len(ordered) > limit:
        warnings.append(f"Limited {root} to {limit} entries for the requested resume length.")
        ordered = ordered[:limit]
    return ordered


def collect_profile_facts_for_entity(
    entity: Any, root: str, index: int
) -> dict[str, SourceFact]:
    # A temporary one-entity profile tree keeps prioritization independent of
    # the renderer; actual references are collected from the complete profile.
    output: dict[str, SourceFact] = {}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, EvidenceValue):
            if value.source_text and _value_is_traceable(value):
                output[path] = SourceFact(
                    path=path,
                    value=str(value.value),
                    source_text=value.source_text,
                    source_section=value.source_section,
                    confidence=value.confidence,
                    evidence_status=value.evidence_status,
                    verification_status=value.verification_status,
                )
        elif isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value, name), f"{path}.{name}")
        elif isinstance(value, list):
            for item_index, item in enumerate(value):
                visit(item, f"{path}[{item_index}]")

    visit(entity, f"{root}[{index}]")
    return output


def _value_is_traceable(evidence: EvidenceValue[Any]) -> bool:
    if not evidence.source_text:
        return False
    if evidence.evidence_status != "explicit" and evidence.verification_status != "verified":
        return False
    if isinstance(evidence.value, (int, float)):
        return str(evidence.value) in evidence.source_text
    return str(evidence.value).casefold() in evidence.source_text.casefold()


def _valid_order_prefix(values: list[str], facts: dict[str, SourceFact]) -> list[str]:
    return list(dict.fromkeys(path for path in values if path in facts and path.startswith("skills.")))


def _project_and_experience_text(facts: dict[str, SourceFact]) -> list[SourceFact]:
    prefixes = ("projects[", "experience[", "internships[")
    output = []
    for path, fact in facts.items():
        if path.startswith(prefixes) and any(
            f".{field}" in path for field in ("description", "responsibilities", "achievements")
        ):
            output.append(fact)
    return output


def _change_explanations(
    job: JobListing,
    skills: list[TailoredSkill],
    projects: list[TailoredEntry],
    experience: list[TailoredEntry],
) -> list[str]:
    changes: list[str] = []
    if skills and (job.required_skills or job.preferred_skills):
        changes.append("Prioritized documented skills that overlap the selected job's listed skills.")
    if projects:
        changes.append("Organized source-backed project details for the selected role.")
    if experience:
        changes.append("Preserved source-backed experience details and omitted unsupported rewrites.")
    changes.append("Included only profile facts with usable source evidence; student confirmation is still required.")
    return changes


def _validation_report(
    claims: list[ValidatedClaim],
    omitted: list[OmittedClaim],
    warnings: list[str],
) -> ValidationReport:
    return ValidationReport(
        supported_claim_count=sum(claim.validation_status == "supported" for claim in claims),
        needs_review_claim_count=sum(claim.validation_status == "needs_review" for claim in claims),
        omitted_claims=omitted,
        warnings=list(dict.fromkeys(warnings)),
    )


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


def _job_text(job: JobListing) -> str:
    return " ".join(
        value
        for value in [job.title, job.company, job.description, *job.required_skills, *job.preferred_skills]
        if value
    )


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in _TOKEN_RE.findall(text)}


def _skill_key(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.casefold()).strip()
    normalized = re.sub(r"[^a-z0-9+#. ]", "", normalized)
    return _SKILL_ALIASES.get(normalized, normalized)


def _skill_limit(length: str) -> int | None:
    return 10 if length in {"one_page", "concise"} else 20 if length in {"two_pages", "standard"} else None


def _entity_limit(length: str) -> int | None:
    return 2 if length in {"one_page", "concise"} else 4 if length in {"two_pages", "standard"} else None


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = re.sub(r"\s+", " ", text.casefold())
    normalized_phrase = re.sub(r"\s+", " ", phrase.casefold()).strip()
    if not normalized_phrase:
        return False
    if len(normalized_phrase) <= 2:
        return re.search(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", normalized_text) is not None
    return normalized_phrase in normalized_text
