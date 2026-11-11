"""Configurable interview-type rubrics and criteria."""

from __future__ import annotations

from .schemas import EvaluationRubric, InterviewType, RubricWeights

_DEFAULT_WEIGHTS: dict[InterviewType, dict[str, float]] = {
    "technical": {
        "technical_correctness": 0.25,
        "conceptual_understanding": 0.18,
        "depth_of_explanation": 0.12,
        "relevance": 0.14,
        "problem_solving": 0.12,
        "communication_clarity": 0.09,
        "practical_application": 0.10,
    },
    "project_based": {
        "technical_correctness": 0.15,
        "conceptual_understanding": 0.15,
        "depth_of_explanation": 0.15,
        "relevance": 0.15,
        "problem_solving": 0.15,
        "communication_clarity": 0.10,
        "practical_application": 0.15,
    },
    "hr_behavioral": {
        "technical_correctness": 0.0,
        "conceptual_understanding": 0.10,
        "depth_of_explanation": 0.15,
        "relevance": 0.20,
        "problem_solving": 0.20,
        "communication_clarity": 0.25,
        "practical_application": 0.10,
    },
    "role_specific": {
        "technical_correctness": 0.20,
        "conceptual_understanding": 0.16,
        "depth_of_explanation": 0.12,
        "relevance": 0.18,
        "problem_solving": 0.14,
        "communication_clarity": 0.10,
        "practical_application": 0.10,
    },
}

_CRITERIA = {
    "technical_correctness": "Accuracy of concepts, terminology, and stated behavior; assess independently from fluency.",
    "conceptual_understanding": "Explanation of why the approach works and awareness of relevant concepts.",
    "depth_of_explanation": "Specificity, completeness, and appropriate detail for the question difficulty.",
    "relevance": "Directness and alignment with the question and selected role.",
    "problem_solving": "Structured reasoning, decomposition, trade-offs, and handling of constraints.",
    "communication_clarity": "Organization and clarity; fluency alone does not establish correctness.",
    "practical_application": "Connection between concepts and a realistic implementation or example.",
}


def default_rubric(
    interview_type: InterviewType,
    *,
    weights: RubricWeights | dict[str, float] | None = None,
) -> EvaluationRubric:
    """Return a validated rubric; callers may inject different dimension weights."""
    selected_weights = (
        RubricWeights.model_validate(weights)
        if weights is not None
        else RubricWeights.model_validate(_DEFAULT_WEIGHTS[interview_type])
    )
    return EvaluationRubric(weights=selected_weights, criteria=dict(_CRITERIA))


def default_rubric_weights(interview_type: InterviewType) -> RubricWeights:
    return RubricWeights.model_validate(_DEFAULT_WEIGHTS[interview_type])
