"""Rubric-based answer assessment with an explicit deterministic fallback."""

from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import ValidationError

from app.ai.job_intelligence.schemas import JobListing
from app.ai.providers import LLMService, create_llm_service
from app.ai.resume_intelligence.profile_schemas import StudentProfile

from .prompts import build_evaluation_prompt
from .question_generator import _collect_profile_facts
from .rubrics import default_rubric
from .schemas import (
    AnswerEvaluation,
    AnswerEvaluationDraft,
    AnswerEvidence,
    DimensionName,
    DimensionScore,
    EvaluationRubric,
    InterviewQuestion,
    RubricWeights,
)

_DIMENSIONS: tuple[DimensionName, ...] = (
    "technical_correctness",
    "conceptual_understanding",
    "depth_of_explanation",
    "relevance",
    "problem_solving",
    "communication_clarity",
    "practical_application",
)
_WORD_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)


def evaluate_interview_answer(
    question: InterviewQuestion,
    answer: str,
    student_profile: StudentProfile,
    job_listing: JobListing,
    *,
    llm_service: LLMService | None = None,
    rubric_weights: RubricWeights | dict[str, float] | None = None,
) -> AnswerEvaluation:
    """Evaluate one answer and preserve method, evidence, and uncertainty.

    LLM scores are constrained to the validated rubric scale; the total is
    recomputed locally. Without a usable provider, technical correctness is
    left unassessed because the lexical checklist cannot establish truth.
    """
    if not isinstance(answer, str):
        raise TypeError("answer must be a string")
    if len(answer) > 12000:
        raise ValueError("answer must be no longer than 12000 characters")
    if not isinstance(student_profile, StudentProfile):
        student_profile = StudentProfile.model_validate(student_profile)
    if not isinstance(job_listing, JobListing):
        job_listing = JobListing.model_validate(job_listing)
    clean_answer = answer.strip()
    weights = (
        RubricWeights.model_validate(rubric_weights)
        if rubric_weights is not None
        else question.evaluation_rubric.weights
    )
    rubric = default_rubric(question.interview_type, weights=weights)
    if not clean_answer:
        return _empty_evaluation(question, rubric)

    service = llm_service if llm_service is not None else create_llm_service()
    supported_facts = _collect_profile_facts(student_profile)
    allowed_context_paths = ("skills.", "education[", "projects[", "experience[", "internships[")
    profile_evidence = [
        {
            "profile_path": reference.profile_path,
            "value": reference.value,
            "source_text": reference.source_text,
            "source_section": reference.source_section,
        }
        for reference in question.profile_evidence_references
        if reference.profile_path.startswith(allowed_context_paths)
        and reference.profile_path in supported_facts
        and supported_facts[reference.profile_path].value == reference.value
    ]
    prompt = build_evaluation_prompt(
        question_text=question.question_text,
        interview_type=question.interview_type,
        difficulty=question.difficulty,
        competency=question.competency,
        expected_answer_points=question.expected_answer_points,
        rubric_weights=weights.model_dump(),
        student_answer=clean_answer,
        job_listing=job_listing,
        profile_evidence=profile_evidence,
    )
    provider_warning: str | None = None
    try:
        result = service.generate_structured(
            prompt=prompt,
            response_model=AnswerEvaluationDraft,
            fallback=AnswerEvaluationDraft,
            max_attempts=2,
        )
        # An empty fallback value is never an assessment. Avoid accepting it as
        # LLM output if a custom LLMService returns an invalid empty object.
        if result.is_fallback:
            provider_warning = result.fallback_reason or "Provider unavailable."
            return _deterministic_evaluation(
                question, clean_answer, rubric, provider_warning
            )
        evaluation = _from_draft(question, clean_answer, rubric, result.value, result.provider)
        if evaluation is not None:
            return evaluation
        provider_warning = "Provider feedback could not be validated against the answer."
    except (ValidationError, ValueError, TypeError) as exc:
        provider_warning = f"Provider output was invalid ({type(exc).__name__})."
    except Exception as exc:  # provider adapters may raise transport-specific exceptions
        provider_warning = f"Evaluation provider failed ({type(exc).__name__})."
    return _deterministic_evaluation(question, clean_answer, rubric, provider_warning)


def _from_draft(
    question: InterviewQuestion,
    answer: str,
    rubric: EvaluationRubric,
    draft: AnswerEvaluationDraft,
    provider: str,
) -> AnswerEvaluation | None:
    dimensions: dict[DimensionName, DimensionScore] = {}
    scores = draft.dimension_scores.model_dump()
    explanations = draft.explanations
    for name in _DIMENSIONS:
        weight = getattr(rubric.weights, name)
        if weight == 0:
            dimensions[name] = DimensionScore(
                score=None,
                weight=weight,
                status="not_assessed",
                explanation="This dimension has zero weight for this interview rubric.",
            )
            continue
        explanation = explanations.get(name, "").strip()
        if not explanation:
            return None
        quotes = _validated_quotes(draft.answer_evidence_quotes.get(name, []), answer)
        dimensions[name] = DimensionScore(
            score=scores[name],
            weight=weight,
            status="assessed",
            explanation=explanation,
            answer_evidence=[
                AnswerEvidence(
                    dimension=name,
                    excerpt=quote[:500],
                    note=f"Exact excerpt from the submitted answer relevant to {name.replace('_', ' ')}.",
                )
                for quote in quotes
            ],
        )
    overall, coverage = _aggregate(dimensions)
    word_count = len(_WORD_RE.findall(answer))
    confidence = "medium" if word_count >= 35 else "low"
    limitations = [
        "LLM rubric judgments are not externally verified and may be uncertain.",
        "Expected answer points are a question-specific guide, not a complete answer key.",
    ]
    if word_count < 12:
        limitations.append("The short answer provides limited evidence for a reliable assessment.")
    return AnswerEvaluation(
        question_id=question.question_id,
        overall_score=overall,
        score_coverage=coverage,
        dimension_scores=dimensions,
        strengths=_dedupe(draft.strengths),
        weaknesses=_dedupe(draft.weaknesses),
        missing_concepts=_dedupe(draft.missing_concepts),
        improvement_suggestions=_dedupe(draft.improvement_suggestions),
        example_areas_to_improve=_dedupe(draft.example_areas_to_improve),
        confidence=confidence,
        evaluation_method="llm_rubric",
        generation_provider=provider,
        is_fallback=False,
        limitations=limitations,
    )


def _deterministic_evaluation(
    question: InterviewQuestion,
    answer: str,
    rubric: EvaluationRubric,
    provider_warning: str | None,
) -> AnswerEvaluation:
    answer_tokens = set(_tokens(answer))
    expected_tokens = {
        token
        for point in question.expected_answer_points
        for token in _tokens(point)
        if len(token) > 2
    }
    if question.evaluation_keywords:
        expected_tokens.update(
            token for token in question.evaluation_keywords if len(token) > 2
        )
    overlap = len(answer_tokens & expected_tokens) / len(expected_tokens) if expected_tokens else 0.0
    words = _WORD_RE.findall(answer)
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
    has_sequence = any(word in answer.casefold() for word in ("first", "then", "because", "therefore", "finally"))
    has_example = any(word in answer.casefold() for word in ("for example", "for instance", "such as"))
    source_excerpt = answer[:220].strip()

    heuristic_scores: dict[DimensionName, float] = {
        "technical_correctness": 0.0,  # deliberately not assessed offline
        "conceptual_understanding": min(100.0, overlap * 100.0),
        "depth_of_explanation": min(100.0, len(words) * 2.0),
        "relevance": min(100.0, 100.0 if overlap >= 0.12 else (65.0 if len(words) >= 8 else 35.0)),
        "problem_solving": min(100.0, (45.0 if has_sequence else 25.0) + (20.0 if has_example else 0.0)),
        "communication_clarity": min(100.0, (35.0 if len(words) >= 5 else 15.0) + min(45.0, len(sentences) * 15.0)),
        "practical_application": min(100.0, (55.0 if has_example else 25.0) + (20.0 if overlap >= 0.10 else 0.0)),
    }
    dimensions: dict[DimensionName, DimensionScore] = {}
    for name in _DIMENSIONS:
        weight = getattr(rubric.weights, name)
        not_assessed = weight == 0 or name == "technical_correctness"
        if not_assessed:
            explanation = (
                "Deterministic text heuristics cannot verify technical correctness."
                if name == "technical_correctness"
                else "This dimension has zero weight for this interview rubric."
            )
            dimensions[name] = DimensionScore(
                score=None,
                weight=weight,
                status="not_assessed",
                explanation=explanation,
            )
            continue
        score = round(heuristic_scores[name], 2)
        explanation = _heuristic_explanation(name, overlap, has_sequence, has_example, len(words))
        evidence = []
        if source_excerpt:
            evidence = [AnswerEvidence(
                dimension=name,
                excerpt=source_excerpt,
                note="Submitted answer excerpt used as text-only evidence; this does not establish correctness.",
            )]
        dimensions[name] = DimensionScore(
            score=score,
            weight=weight,
            status="assessed",
            explanation=explanation,
            answer_evidence=evidence,
        )
    overall, coverage = _aggregate(dimensions)
    missing = []
    for point in question.expected_answer_points:
        point_tokens = {token for token in _tokens(point) if len(token) > 2}
        if point_tokens and len(point_tokens & answer_tokens) / len(point_tokens) < 0.25:
            missing.append(point)
    weaknesses = []
    if missing:
        weaknesses.append("Some expected answer points were not evident in the response.")
    if len(words) < 15:
        weaknesses.append("The response is brief; add reasoning and a specific example where appropriate.")
    if not has_sequence:
        weaknesses.append("Make the reasoning steps easier to follow.")
    strengths = []
    if has_example:
        strengths.append("The response includes an example marker.")
    if overlap >= 0.15:
        strengths.append("The response uses terms related to the question's evaluation guide.")
    if not strengths:
        strengths.append("The response was captured and can be reviewed against the question.")
    limitations = [
        "Deterministic fallback uses token overlap, answer length, and basic structure only.",
        "Technical correctness is not assessed by this fallback.",
        "Text-only heuristics are not a calibrated measure of interview readiness.",
    ]
    if provider_warning:
        limitations.append(provider_warning)
    return AnswerEvaluation(
        question_id=question.question_id,
        overall_score=overall,
        score_coverage=coverage,
        dimension_scores=dimensions,
        strengths=strengths,
        weaknesses=weaknesses,
        missing_concepts=missing,
        improvement_suggestions=[
            "Address the specific concept or criterion named in the question.",
            "Explain your reasoning and include a concrete example when relevant.",
        ],
        example_areas_to_improve=[
            "Add a relevant implementation, test, or hypothetical application example."
        ] if not has_example else [],
        confidence="low",
        evaluation_method="deterministic_heuristic",
        generation_provider="deterministic_fallback",
        is_fallback=True,
        limitations=limitations,
    )


def _empty_evaluation(question: InterviewQuestion, rubric: EvaluationRubric) -> AnswerEvaluation:
    dimensions = {
        name: DimensionScore(
            score=None,
            weight=getattr(rubric.weights, name),
            status="not_assessed",
            explanation="No answer was submitted, so this dimension could not be assessed.",
        )
        for name in _DIMENSIONS
    }
    return AnswerEvaluation(
        question_id=question.question_id,
        overall_score=None,
        score_coverage=0,
        dimension_scores=dimensions,
        weaknesses=["No answer was submitted."],
        improvement_suggestions=["Attempt the question or explicitly skip it in the interview UI."],
        confidence="low",
        evaluation_method="deterministic_heuristic",
        generation_provider="deterministic_fallback",
        is_fallback=True,
        limitations=["An empty answer cannot be assessed."],
    )


def _aggregate(dimensions: dict[DimensionName, DimensionScore]) -> tuple[float | None, float]:
    assessed = [
        item for item in dimensions.values()
        if item.status == "assessed" and item.score is not None and item.weight > 0
    ]
    coverage = min(1.0, sum(item.weight for item in assessed))
    if not assessed:
        return None, coverage
    total_weight = sum(item.weight for item in assessed)
    return round(sum(item.score * item.weight for item in assessed) / total_weight, 2), round(coverage, 4)


def _validated_quotes(quotes: Iterable[str], answer: str) -> list[str]:
    found: list[str] = []
    for quote in quotes:
        if isinstance(quote, str) and quote.strip() and quote.strip() in answer and quote.strip() not in found:
            found.append(quote.strip())
    return found[:4]


def _heuristic_explanation(
    dimension: DimensionName,
    overlap: float,
    has_sequence: bool,
    has_example: bool,
    word_count: int,
) -> str:
    if dimension == "conceptual_understanding":
        return f"A text-only checklist found approximately {overlap:.0%} overlap with guide terms; this is not proof of correctness."
    if dimension == "depth_of_explanation":
        return f"The heuristic uses response length ({word_count} words) as a rough depth signal."
    if dimension == "relevance":
        return "Relevance is estimated from answer length and overlap with the question guide, not semantic verification."
    if dimension == "problem_solving":
        return "The heuristic checks for simple sequencing language; it does not validate the reasoning itself." if has_sequence else "Few explicit step markers were detected by the text-only heuristic."
    if dimension == "communication_clarity":
        return "Clarity is approximated from sentence count and answer length; grammar and spoken delivery are not assessed."
    if dimension == "practical_application":
        return "The heuristic checks for example phrases and guide-term overlap." if has_example else "No common example phrase was detected; a concrete example may still be present."
    return "Not assessed by deterministic fallback."


def _tokens(value: str) -> list[str]:
    return [token.casefold() for token in _WORD_RE.findall(value)]


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if isinstance(value, str) and value.strip()))
