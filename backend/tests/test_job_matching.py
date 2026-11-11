from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching import (
    MatchConfig,
    MatchWeights,
    match_jobs,
)
from app.ai.resume_intelligence import (
    EducationProfile,
    EvidenceValue,
    ExperienceProfile,
    ProjectProfile,
    SkillProfile,
    StudentProfile,
)


def _fact(
    value: Any,
    source_text: str | None = None,
    *,
    verified: bool = False,
    evidence_status: str = "explicit",
) -> EvidenceValue[Any]:
    return EvidenceValue(
        value=value,
        source_text=source_text if source_text is not None else str(value),
        source_section="test-section",
        confidence="high",
        evidence_status=evidence_status,  # type: ignore[arg-type]
        verification_status="verified" if verified else "unverified",
    )


def _profile(
    *,
    skills: list[EvidenceValue[str]] | None = None,
    education: list[EducationProfile] | None = None,
    experience: list[ExperienceProfile] | None = None,
    projects: list[ProjectProfile] | None = None,
) -> StudentProfile:
    return StudentProfile(
        skills=SkillProfile(programming_languages=skills or []),
        education=education or [],
        experience=experience or [],
        projects=projects or [],
        extraction_provider="test",
        is_fallback=False,
    )


def _job(job_id: str = "job-1", **updates: Any) -> JobListing:
    values: dict[str, Any] = {
        "job_id": job_id,
        "title": "Python Backend Engineer",
        "company": "Example Co",
        "description": "Build APIs and distributed backend services using Python and PostgreSQL.",
        "required_skills": ["Python", "PostgreSQL"],
        "preferred_skills": ["Docker"],
        "source_provider": "test-feed",
        "source_job_id": job_id,
    }
    values.update(updates)
    return JobListing(**values)


class _FixedEmbeddingProvider:
    name = "stub_embeddings"

    def __init__(self, score: float = 0.8) -> None:
        self.score = score
        self.pairs: list[tuple[str, str]] = []

    def similarities(self, pairs):
        self.pairs.extend(pairs)
        return [self.score] * len(pairs)


class _FailingEmbeddingProvider:
    name = "broken_embeddings"

    def similarities(self, pairs):
        raise RuntimeError("model unavailable")


def test_exact_skill_matches_include_supporting_evidence(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    result = match_jobs(profile, [_job()])[0]
    assert [(item.job_skill, item.student_skill, item.match_type) for item in result.matched_skills] == [
        ("Python", "Python", "exact")
    ]
    assert result.missing_required_skills == ["PostgreSQL"]
    assert result.missing_preferred_skills == ["Docker"]
    assert result.matched_skills[0].evidence[0].source_text == "Skills: Python"
    assert result.matching_method == "keyword_fallback"


def test_common_skill_synonyms_match_deterministically(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("JS", "Skills: JS")])
    result = match_jobs(
        profile,
        [_job(required_skills=["JavaScript"], preferred_skills=[])],
    )[0]
    assert result.matched_skills[0].match_type == "synonym"
    assert result.dimension_scores["required_skills"].score == 100


def test_unmatched_required_skill_is_not_treated_as_confirmed_absence(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    result = match_jobs(profile, [_job(required_skills=["Rust"], preferred_skills=[])])[0]
    assert result.missing_required_skills == ["Rust"]
    assessment = next(item for item in result.skill_assessments if item.job_skill == "Rust")
    assert assessment.status == "not_evidenced"
    assert "does not confirm the student lacks it" in assessment.explanation


def test_missing_preferred_skill_is_reported_separately(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    result = match_jobs(
        profile,
        [_job(required_skills=["Python"], preferred_skills=["Docker"])],
    )[0]
    assert result.missing_required_skills == []
    assert result.missing_preferred_skills == ["Docker"]


def test_education_relevance_uses_embedding_similarity() -> None:
    profile = _profile(
        education=[
            EducationProfile(
                degree=_fact("B.Tech"),
                branch=_fact("Computer Science"),
            )
        ]
    )
    embeddings = _FixedEmbeddingProvider(0.84)
    result = match_jobs(profile, [_job()], embedding_provider=embeddings)[0]
    assert result.dimension_scores["education_relevance"].score == 84
    assert result.matching_method == "stub_embeddings"
    assert embeddings.pairs


def test_experience_relevance_uses_supported_role_and_responsibilities() -> None:
    profile = _profile(
        experience=[
            ExperienceProfile(
                position=_fact("Backend Intern", "Position: Backend Intern"),
                responsibilities=[
                    _fact("Built APIs with Python", "Built APIs with Python")
                ],
            )
        ]
    )
    result = match_jobs(profile, [_job()], embedding_provider=_FixedEmbeddingProvider(0.71))[0]
    assert result.dimension_scores["experience_relevance"].score == 71
    assert any(
        reference.profile_path.startswith("experience[0]")
        for reference in result.dimension_scores["experience_relevance"].evidence_references
    )


def test_project_relevance_works_with_keyword_baseline(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(
        projects=[
            ProjectProfile(
                description=_fact("Built Python APIs for a student event service."),
                technologies=[_fact("Python"), _fact("PostgreSQL")],
            )
        ]
    )
    result = match_jobs(profile, [_job()])[0]
    assert result.dimension_scores["project_relevance"].status == "assessed"
    assert result.dimension_scores["project_relevance"].score > 0
    assert any(
        reference.profile_path.startswith("projects[0]")
        for reference in result.dimension_scores["project_relevance"].evidence_references
    )


def test_verified_eligibility_mismatch_caps_overall_score(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(
        skills=[_fact("Python", "Skills: Python", verified=True)],
        education=[EducationProfile(cgpa=_fact(6.4, "CGPA: 6.4", verified=True))],
    )
    job = _job(
        eligibility_criteria=["Minimum CGPA: 7.0"],
        required_skills=["Python"],
        preferred_skills=[],
    )
    result = match_jobs(profile, [job])[0]
    assert result.eligibility_assessment.status == "not_eligible"
    assert result.dimension_scores["eligibility"].score == 0
    assert result.overall_score <= 39
    assert "capped" in result.explanation or any("capped" in warning for warning in result.warnings)


def test_unknown_eligibility_is_not_assumed_qualified(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    job = _job(eligibility_criteria=["Must be authorized to work in the United States"])
    result = match_jobs(profile, [job])[0]
    assert result.eligibility_assessment.status == "unknown"
    assert result.dimension_scores["eligibility"].score is None
    assert result.overall_score <= 69
    assert any("unknown" in reason.lower() for reason in result.uncertainty)


def test_unverified_eligibility_fact_stays_unknown(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(
        education=[EducationProfile(cgpa=_fact(8.2, "CGPA: 8.2", verified=False))]
    )
    job = _job(eligibility_criteria=["Minimum CGPA: 7.0"])
    result = match_jobs(profile, [job])[0]
    assert result.eligibility_assessment.status == "unknown"
    assert result.eligibility_assessment.criteria[0].status == "unknown"


def test_empty_profile_returns_unknown_scores() -> None:
    result = match_jobs(_profile(), [_job()])[0]
    assert result.overall_score is None
    assert result.confidence == "low"
    assert result.dimension_scores["required_skills"].status == "unknown"
    assert result.eligibility_assessment.status == "not_applicable"


def test_empty_job_listings_returns_empty_results() -> None:
    assert match_jobs(_profile(), []) == []


def test_multiple_jobs_are_ranked_by_match_score(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(
        skills=[_fact("Python", "Skills: Python"), _fact("PostgreSQL", "Skills: PostgreSQL")],
        projects=[
            ProjectProfile(
                description=_fact("Built backend APIs with Python and PostgreSQL"),
                technologies=[_fact("Python"), _fact("PostgreSQL")],
            )
        ],
    )
    jobs = [
        _job("partial", required_skills=["Python", "Rust"], preferred_skills=[]),
        _job("strong", required_skills=["Python", "PostgreSQL"], preferred_skills=[]),
    ]
    result = match_jobs(profile, jobs)
    assert [job.job_id for job in result] == ["strong", "partial"]
    assert [job.rank for job in result] == [1, 2]


def test_keyword_method_is_reported_when_embeddings_are_disabled(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    result = match_jobs(_profile(skills=[_fact("Python")]), [_job()])[0]
    assert result.matching_method == "keyword_fallback"
    assert "keyword overlap" in result.dimension_scores["project_relevance"].explanation or result.dimension_scores[
        "project_relevance"
    ].status == "unknown"


def test_embedding_failure_rescores_every_dimension_with_keyword_fallback(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(
        projects=[ProjectProfile(description=_fact("Built a data dashboard."))]
    )
    result = match_jobs(profile, [_job()], embedding_provider=_FailingEmbeddingProvider())[0]
    assert result.matching_method == "keyword_fallback"
    assert any("Semantic embeddings were unavailable" in warning for warning in result.warnings)


def test_embedding_provider_scores_are_validated() -> None:
    class InvalidEmbeddingProvider:
        name = "invalid"

        def similarities(self, pairs):
            return [2.5] * len(pairs)

    profile = _profile(education=[EducationProfile(degree=_fact("B.Tech"))])
    result = match_jobs(profile, [_job()], embedding_provider=InvalidEmbeddingProvider())[0]
    assert result.matching_method == "keyword_fallback"
    assert result.dimension_scores["education_relevance"].score == 0


def test_untraceable_profile_value_is_not_used_as_a_qualification(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Source text only mentions Java")])
    result = match_jobs(profile, [_job(required_skills=["Python"], preferred_skills=[])])[0]
    assert result.matched_skills == []
    assert result.missing_required_skills == ["Python"]
    assert result.dimension_scores["required_skills"].status == "unknown"
    assert any("ignored" in warning.lower() for warning in result.uncertainty)


def test_default_weights_and_weight_validation() -> None:
    weights = MatchWeights()
    assert sum(getattr(weights, name) for name in type(weights).model_fields) == pytest.approx(1.0)
    with pytest.raises(ValidationError, match="sum to 1.0"):
        MatchWeights(required_skills=0.6)
    with pytest.raises(ValidationError):
        MatchConfig(ineligible_score_cap=101)


def test_weighted_score_uses_only_assessed_dimensions(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    job = _job(
        required_skills=["Python", "PostgreSQL"],
        preferred_skills=["Docker"],
    )
    result = match_jobs(profile, [job])[0]
    # Required: 50 at 0.30, preferred: 0 at 0.10, then renormalize by 0.40.
    assert result.overall_score == 37.5
    assert result.score_coverage == pytest.approx(0.4)


def test_matching_configurable_weights_are_used(monkeypatch) -> None:
    monkeypatch.setenv("JOB_MATCH_EMBEDDINGS", "keyword")
    profile = _profile(skills=[_fact("Python", "Skills: Python")])
    config = MatchConfig(
        weights=MatchWeights(
            required_skills=0.6,
            preferred_skills=0.0,
            education_relevance=0.1,
            experience_relevance=0.1,
            project_relevance=0.1,
            eligibility=0.1,
        )
    )
    result = match_jobs(
        profile,
        [_job(required_skills=["Python", "PostgreSQL"], preferred_skills=[])],
        config=config,
    )[0]
    assert result.dimension_scores["required_skills"].weight == 0.6
