"""Weighted, explainable job matching with a semantic embedding option."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.ai.job_intelligence.schemas import JobListing
from app.ai.resume_intelligence.profile_schemas import (
    EvidenceValue,
    StudentProfile,
)

from .eligibility import assess_eligibility
from .embeddings import (
    EmbeddingProvider,
    EmbeddingProviderError,
    _embedding_error,
    create_embedding_provider_from_env,
)
from .evidence import is_supported_fact, to_reference
from .schemas import (
    DimensionScore,
    EligibilityAssessment,
    JobMatch,
    MatchConfig,
    MatchDimension,
    SkillAssessment,
    SkillMatch,
)

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "the", "to", "with", "years", "year",
}
_SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "aws": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "google cloud platform": "google cloud platform",
    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "c sharp": "c#",
    "c#": "c#",
    "c plus plus": "c++",
    "c++": "c++",
}
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _TextCandidate:
    text: str
    evidence: tuple[Any, ...]


class _EmbeddingSession:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider
        self.used = False

    def similarities(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        try:
            raw = list(self.provider.similarities(pairs))
        except EmbeddingProviderError:
            raise
        # Replaceable embedding providers may raise implementation-specific
        # exceptions; normalize those into an explicit keyword fallback.
        except Exception as exc:  # noqa: BLE001
            raise _embedding_error(
                "Embedding provider failed.",
                diagnostic_exception_type=type(exc).__name__,
        ) from None
        if len(raw) != len(pairs):
            raise EmbeddingProviderError("Embedding provider returned the wrong number of scores.")
        output: list[float] = []
        for score in raw:
            try:
                numeric = float(score)
            except (TypeError, ValueError) as exc:
                raise EmbeddingProviderError("Embedding provider returned a non-numeric score.") from exc
            if not -1 <= numeric <= 1:
                raise EmbeddingProviderError("Embedding provider scores must be cosine values in [-1, 1].")
            output.append(numeric)
        self.used = True
        return output


def match_jobs(
    student_profile: StudentProfile,
    job_listings: list[JobListing] | tuple[JobListing, ...],
    *,
    config: MatchConfig | dict[str, Any] | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[JobMatch]:
    """Score and rank jobs using traceable profile evidence.

    Missing profile details stay unknown rather than becoming a zero score or
    an assumed qualification. ``missing_*_skills`` means not evidenced in the
    supplied profile, not that the student definitely lacks the skill.
    """
    profile = _validate_profile(student_profile)
    jobs = _validate_jobs(job_listings)
    if not jobs:
        return []
    matching_config = MatchConfig.model_validate(config or {})

    provider = embedding_provider
    provider_warning: str | None = None
    if provider is None:
        try:
            provider = create_embedding_provider_from_env()
        except EmbeddingProviderError as exc:
            provider_warning = str(exc)
            _log_embedding_failure(exc)

    if provider is not None:
        embedding_session = _EmbeddingSession(provider)
        try:
            results = [
                _score_job(profile, job, matching_config, embedding_session, None)
                for job in jobs
            ]
            method = provider.name if embedding_session.used else "keyword_fallback"
        except EmbeddingProviderError as exc:
            provider_warning = (
                "Semantic embeddings were unavailable; all jobs were rescored using the deterministic keyword baseline."
            )
            _log_embedding_failure(exc)
            results = [
                _score_job(profile, job, matching_config, None, provider_warning)
                for job in jobs
            ]
            method = "keyword_fallback"
    else:
        results = [
            _score_job(profile, job, matching_config, None, provider_warning)
            for job in jobs
        ]
        method = "keyword_fallback"

    results = [
        JobMatch.model_validate(
            {
                **result.model_dump(),
                "matching_method": method,
                "rank": result.rank,
            }
        )
        for result in results
    ]
    ranked = sorted(
        enumerate(results),
        key=lambda item: (
            item[1].overall_score is not None,
            item[1].overall_score if item[1].overall_score is not None else -1,
            -item[0],
        ),
        reverse=True,
    )
    return [
        JobMatch.model_validate({**result.model_dump(), "rank": rank})
        for rank, (_original_index, result) in enumerate(ranked, start=1)
    ]


def _log_embedding_failure(error: EmbeddingProviderError) -> None:
    message = str(error)
    if message.startswith("sentence-transformers is not installed"):
        safe_reason = "sentence-transformers is not installed; keyword fallback selected."
    elif message.startswith("Unsupported JOB_MATCH_EMBEDDINGS"):
        safe_reason = "Unsupported JOB_MATCH_EMBEDDINGS; keyword fallback selected."
    elif message.startswith("JOB_MATCH_MODEL must be non-empty"):
        safe_reason = "Invalid JOB_MATCH_MODEL configuration; keyword fallback selected."
    else:
        safe_reason = "Semantic embedding provider failed; keyword fallback selected."
    exception_type = error.diagnostic_exception_type or type(error).__name__
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", exception_type):
        exception_type = "EmbeddingProviderError"
    _LOGGER.warning(
        "Job matching embedding failure exception_type=%s; %s",
        exception_type,
        safe_reason,
    )


def _validate_profile(value: StudentProfile) -> StudentProfile:
    if isinstance(value, StudentProfile):
        return value
    if isinstance(value, BaseModel):
        return StudentProfile.model_validate(value.model_dump())
    return StudentProfile.model_validate(value)


def _validate_jobs(value: Any) -> list[JobListing]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise TypeError("job_listings must be a list or tuple of JobListing objects")
    return [
        job if isinstance(job, JobListing) else JobListing.model_validate(job)
        for job in value
    ]


def _score_job(
    profile: StudentProfile,
    job: JobListing,
    config: MatchConfig,
    embeddings: _EmbeddingSession | None,
    fallback_warning: str | None,
) -> JobMatch:
    skill_data = _assess_skills(profile, job)
    eligibility = assess_eligibility(profile, job)
    target = _job_target(job)

    dimensions: dict[MatchDimension, DimensionScore] = {
        "required_skills": _skill_dimension(
            "required", job.required_skills, skill_data, config.weights.required_skills
        ),
        "preferred_skills": _skill_dimension(
            "preferred", job.preferred_skills, skill_data, config.weights.preferred_skills
        ),
        "education_relevance": _relevance_dimension(
            "education_relevance",
            _education_candidates(profile),
            target,
            config.weights.education_relevance,
            embeddings,
        ),
        "experience_relevance": _relevance_dimension(
            "experience_relevance",
            _experience_candidates(profile),
            target,
            config.weights.experience_relevance,
            embeddings,
        ),
        "project_relevance": _relevance_dimension(
            "project_relevance",
            _project_candidates(profile),
            target,
            config.weights.project_relevance,
            embeddings,
        ),
        "eligibility": _eligibility_dimension(eligibility, config.weights.eligibility),
    }

    score_coverage = sum(
        dimension.weight
        for dimension in dimensions.values()
        if dimension.status == "assessed" and dimension.score is not None
    )
    weighted_total = sum(
        dimension.weight * dimension.score
        for dimension in dimensions.values()
        if dimension.status == "assessed" and dimension.score is not None
    )
    overall = round(weighted_total / score_coverage, 1) if score_coverage > 0 else None
    warnings: list[str] = []
    uncertainty: list[str] = []
    if overall is None:
        explanation = "Insufficient directly supported profile evidence to calculate a match score."
        uncertainty.append("No matching dimension could be scored from the available profile evidence.")
    else:
        raw_score = overall
        if eligibility.status == "not_eligible":
            overall = min(overall, config.ineligible_score_cap)
            warnings.append(
                f"Overall score capped at {config.ineligible_score_cap:g} because a verified hard eligibility requirement is not met."
            )
        elif eligibility.status == "unknown":
            overall = min(overall, config.unknown_eligibility_score_cap)
            uncertainty.append("Eligibility remains unknown; the score is capped until required facts are confirmed.")
            warnings.append(
                f"Overall score capped at {config.unknown_eligibility_score_cap:g} because eligibility could not be confirmed."
            )
        explanation = (
            f"Weighted evidence match {raw_score:.1f}/100 uses {score_coverage:.0%} of configured dimension weight; "
            "unknown dimensions are excluded and remaining weights are renormalized. This score is not a probability of selection."
        )

    if skill_data["has_supported_skills"] is False and (job.required_skills or job.preferred_skills):
        uncertainty.append("No directly supported student skills were available; listed skills are not evidenced, not confirmed absent.")
    if eligibility.status == "unknown":
        uncertainty.extend(
            warning for warning in eligibility.warnings if warning not in uncertainty
        )
    if fallback_warning:
        warnings.append(fallback_warning)
        uncertainty.append("Semantic similarity was not used; relevance dimensions use keyword overlap only.")
    if score_coverage < 0.5 and overall is not None:
        uncertainty.append("Less than half of the configured scoring weight had assessable evidence.")

    evidence_references = _unique_references(
        [
            *skill_data["references"],
            *(reference for dimension in dimensions.values() for reference in dimension.evidence_references),
            *(reference for criterion in eligibility.criteria for reference in criterion.evidence_references),
        ]
    )
    if _count_unsupported_profile_facts(profile):
        uncertainty.append("Profile values without explicit traceable source evidence were ignored.")

    return JobMatch(
        job_id=job.job_id,
        job_title=job.title,
        rank=1,
        overall_score=overall,
        score_coverage=round(score_coverage, 3),
        dimension_scores=dimensions,
        matched_skills=skill_data["matches"],
        missing_required_skills=skill_data["missing_required"],
        missing_preferred_skills=skill_data["missing_preferred"],
        skill_assessments=skill_data["assessments"],
        eligibility_assessment=eligibility,
        explanation=explanation,
        evidence_references=evidence_references,
        matching_method="pending",
        confidence=_confidence(score_coverage, evidence_references, eligibility),
        uncertainty=_unique_strings(uncertainty),
        warnings=_unique_strings(warnings),
    )


def _assess_skills(profile: StudentProfile, job: JobListing) -> dict[str, Any]:
    student_skills: list[tuple[str, str, Any]] = []
    categories = (
        "programming_languages",
        "frameworks",
        "databases",
        "cloud_technologies",
        "tools",
        "technical_domains",
    )
    for category in categories:
        for index, evidence in enumerate(getattr(profile.skills, category)):
            if is_supported_fact(evidence):
                path = f"skills.{category}[{index}]"
                student_skills.append((evidence.value, path, to_reference(path, evidence)))

    matches: list[SkillMatch] = []
    assessments: list[SkillAssessment] = []
    missing_required: list[str] = []
    missing_preferred: list[str] = []
    for category, requested in (("required", job.required_skills), ("preferred", job.preferred_skills)):
        for skill in _dedupe_text(requested):
            canonical = _canonical_skill(skill)
            found = next(
                (student for student in student_skills if _canonical_skill(student[0]) == canonical),
                None,
            )
            if found:
                match_type = "exact" if _surface_skill(found[0]) == _surface_skill(skill) else "synonym"
                matches.append(
                    SkillMatch(
                        job_skill=skill,
                        student_skill=found[0],
                        category=category,
                        match_type=match_type,
                        evidence=[found[2]],
                    )
                )
                assessments.append(
                    SkillAssessment(
                        job_skill=skill,
                        category=category,
                        status="matched",
                        explanation=(
                            "The profile contains a directly supported matching skill."
                            if match_type == "exact"
                            else "A documented skill matches through a configured synonym alias."
                        ),
                    )
                )
            else:
                (missing_required if category == "required" else missing_preferred).append(skill)
                assessments.append(
                    SkillAssessment(
                        job_skill=skill,
                        category=category,
                        status="not_evidenced",
                        explanation="This skill is not evidenced in the supplied profile; that does not confirm the student lacks it.",
                    )
                )

    refs = [match.evidence[0] for match in matches if match.evidence]
    return {
        "matches": matches,
        "assessments": assessments,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
        "references": refs,
        "has_supported_skills": bool(student_skills),
    }


def _skill_dimension(
    category: str,
    requested: list[str],
    skill_data: dict[str, Any],
    weight: float,
) -> DimensionScore:
    if not requested:
        return DimensionScore(
            score=None,
            weight=weight,
            status="not_applicable",
            explanation=f"The job does not list {category} skills.",
        )
    assessments = [
        item for item in skill_data["assessments"] if item.category == category
    ]
    if not skill_data["has_supported_skills"]:
        return DimensionScore(
            score=None,
            weight=weight,
            status="unknown",
            explanation=f"No directly supported student skills are available to assess {category} requirements.",
        )
    matched = sum(item.status == "matched" for item in assessments)
    score = 100 * matched / len(assessments) if assessments else None
    explanation = (
        f"{matched} of {len(assessments)} listed {category} skills are evidenced; "
        "unmatched requirements mean not evidenced, not confirmed absent."
    )
    return DimensionScore(
        score=score,
        weight=weight,
        status="assessed" if score is not None else "unknown",
        explanation=explanation,
        evidence_references=[
            reference
            for match in skill_data["matches"]
            if match.category == category
            for reference in match.evidence
        ],
    )


def _eligibility_dimension(
    assessment: EligibilityAssessment,
    weight: float,
) -> DimensionScore:
    if assessment.status == "eligible":
        score, status = 100.0, "assessed"
        explanation = "All machine-checkable hard criteria are met using student-verified facts."
    elif assessment.status == "not_eligible":
        score, status = 0.0, "assessed"
        explanation = "At least one hard criterion has a verified mismatch."
    elif assessment.status == "unknown":
        score, status = None, "unknown"
        explanation = "Eligibility is unknown because required facts are missing, unverified, or not safely machine-checkable."
    else:
        score, status = None, "not_applicable"
        explanation = "No explicit eligibility criteria were supplied for this job."
    return DimensionScore(
        score=score,
        weight=weight,
        status=status,
        explanation=explanation,
        evidence_references=[
            reference for criterion in assessment.criteria for reference in criterion.evidence_references
        ],
    )


def _education_candidates(profile: StudentProfile) -> list[_TextCandidate]:
    candidates: list[_TextCandidate] = []
    for index, education in enumerate(profile.education):
        pieces: list[str] = []
        refs = []
        for field in ("degree", "branch"):
            evidence = getattr(education, field)
            if is_supported_fact(evidence):
                pieces.append(evidence.value)
                refs.append(to_reference(f"education[{index}].{field}", evidence))
        if pieces:
            candidates.append(_TextCandidate(" ".join(pieces), tuple(refs)))
    return candidates


def _experience_candidates(profile: StudentProfile) -> list[_TextCandidate]:
    return _entity_candidates(
        profile.experience,
        "experience",
        ("position", "responsibilities", "achievements"),
    ) + _entity_candidates(
        profile.internships,
        "internships",
        ("position", "responsibilities", "achievements"),
    )


def _project_candidates(profile: StudentProfile) -> list[_TextCandidate]:
    return _entity_candidates(
        profile.projects,
        "projects",
        ("description", "technologies", "responsibilities", "achievements"),
    )


def _entity_candidates(entities: list[Any], root: str, fields: tuple[str, ...]) -> list[_TextCandidate]:
    candidates: list[_TextCandidate] = []
    for index, entity in enumerate(entities):
        texts: list[str] = []
        refs = []
        for field in fields:
            value = getattr(entity, field)
            values = value if isinstance(value, list) else [value]
            for item_index, evidence in enumerate(values):
                if not is_supported_fact(evidence):
                    continue
                texts.append(str(evidence.value))
                path = f"{root}[{index}].{field}"
                if isinstance(value, list):
                    path += f"[{item_index}]"
                refs.append(to_reference(path, evidence))
        if texts:
            candidates.append(_TextCandidate(" ".join(texts), tuple(refs)))
    return candidates


def _job_target(job: JobListing) -> str:
    parts = [
        job.title or "",
        job.description or "",
        *job.required_skills,
        *job.preferred_skills,
        *job.eligibility_criteria,
    ]
    return " ".join(part for part in parts if part)


def _relevance_dimension(
    name: str,
    candidates: list[_TextCandidate],
    target: str,
    weight: float,
    embeddings: _EmbeddingSession | None,
) -> DimensionScore:
    if not candidates:
        return DimensionScore(
            score=None,
            weight=weight,
            status="unknown",
            explanation=f"No directly supported student {name.removesuffix('_relevance')} information is available.",
        )
    if not _tokens(target):
        return DimensionScore(
            score=None,
            weight=weight,
            status="unknown",
            explanation="The job lacks enough title, description, or skill information for comparison.",
        )

    candidate_scores: list[tuple[float, _TextCandidate, str]] = []
    if embeddings is not None:
        pairs = [(_bounded_text(candidate.text), _bounded_text(target)) for candidate in candidates]
        scores = embeddings.similarities(pairs)
        for score, candidate in zip(scores, candidates, strict=True):
            candidate_scores.append((max(0.0, score) * 100, candidate, "semantic embedding"))
    else:
        target_tokens = _tokens(target)
        for candidate in candidates:
            candidate_tokens = _tokens(candidate.text)
            overlap = candidate_tokens & target_tokens
            score = 100 * len(overlap) / len(candidate_tokens) if candidate_tokens else 0.0
            candidate_scores.append((score, candidate, f"keyword overlap ({len(overlap)}/{len(candidate_tokens)} profile terms)"))

    score, best_candidate, method_note = max(candidate_scores, key=lambda item: item[0])
    if embeddings is not None:
        explanation = f"Best-supported {name.removesuffix('_relevance')} text has cosine similarity {score / 100:.2f} to the job context."
    else:
        explanation = f"Best-supported {name.removesuffix('_relevance')} text was evaluated by {method_note}."
    return DimensionScore(
        score=round(score, 1),
        weight=weight,
        status="assessed",
        explanation=explanation,
        evidence_references=list(best_candidate.evidence),
    )


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+(?:[+#.]?[a-z0-9+#.]*)", text.casefold())
        if token not in _STOP_WORDS and (len(token) > 1 or token in {"r", "c"})
    }


def _canonical_skill(skill: str) -> str:
    normalized = re.sub(r"\s+", " ", skill.casefold()).strip()
    punctuation_free = re.sub(r"[^a-z0-9+#. ]", "", normalized)
    return _SKILL_ALIASES.get(punctuation_free, punctuation_free)


def _surface_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.casefold()).strip()


def _dedupe_text(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = _canonical_skill(value)
        if key not in seen:
            seen.add(key)
            output.append(value)
    return output


def _unique_references(references: list[Any]) -> list[Any]:
    output = []
    seen: set[tuple[str, str]] = set()
    for reference in references:
        key = (reference.profile_path, reference.source_text)
        if key not in seen:
            seen.add(key)
            output.append(reference)
    return output


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _confidence(
    coverage: float,
    evidence: list[Any],
    eligibility: EligibilityAssessment,
) -> str:
    if not evidence or coverage < 0.6 or eligibility.status == "unknown":
        return "low"
    if all(reference.verification_status == "verified" for reference in evidence) and coverage >= 0.85:
        return "high"
    if all(reference.confidence in {"high", "medium"} for reference in evidence):
        return "medium"
    return "low"


def _count_unsupported_profile_facts(profile: StudentProfile) -> int:
    def count(value: Any) -> int:
        if isinstance(value, EvidenceValue):
            return 0 if is_supported_fact(value) else 1
        if isinstance(value, BaseModel):
            return sum(count(getattr(value, field)) for field in type(value).model_fields)
        if isinstance(value, list):
            return sum(count(item) for item in value)
        return 0

    return count(profile)


def _bounded_text(text: str) -> str:
    return text[:5000]
