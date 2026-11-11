"""Validated schemas for adaptive mock interviews and their assessments."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.resume_intelligence.profile_schemas import StudentProfile

InterviewType = Literal["technical", "project_based", "hr_behavioral", "role_specific"]
Difficulty = Literal["beginner", "intermediate", "advanced"]
EvaluationMethod = Literal["llm_rubric", "deterministic_heuristic"]
EvaluationConfidence = Literal["low", "medium", "high"]
DimensionName = Literal[
    "technical_correctness",
    "conceptual_understanding",
    "depth_of_explanation",
    "relevance",
    "problem_solving",
    "communication_clarity",
    "practical_application",
]
_DIMENSION_NAMES = {
    "technical_correctness",
    "conceptual_understanding",
    "depth_of_explanation",
    "relevance",
    "problem_solving",
    "communication_clarity",
    "practical_application",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionEvidenceReference(StrictModel):
    profile_path: str
    value: str
    source_text: str
    source_section: str | None = None
    confidence: Literal["high", "medium", "low"]
    evidence_status: Literal["explicit", "inferred", "uncertain"]
    verification_status: Literal["unverified", "needs_review", "verified"]


class RubricWeights(StrictModel):
    """Dimension weights for one question; applicable weights sum to 1."""

    technical_correctness: float = Field(ge=0, le=1)
    conceptual_understanding: float = Field(ge=0, le=1)
    depth_of_explanation: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    problem_solving: float = Field(ge=0, le=1)
    communication_clarity: float = Field(ge=0, le=1)
    practical_application: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_total_weight(self) -> RubricWeights:
        total = sum(getattr(self, name) for name in type(self).model_fields)
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"rubric weights must sum to 1.0; got {total:.6f}")
        return self


class EvaluationRubric(StrictModel):
    weights: RubricWeights
    criteria: dict[DimensionName, str]


class InterviewQuestion(StrictModel):
    """Student-visible question plus internal, serialization-hidden answer key."""

    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1, max_length=1200)
    interview_type: InterviewType
    difficulty: Difficulty
    competency: str = Field(min_length=1, max_length=120)
    relevant_job_requirement: str | None = None
    profile_evidence_references: list[QuestionEvidenceReference] = Field(default_factory=list)
    follow_up_guidance: str = Field(min_length=1, max_length=1000)
    selection_reason: str = "Initial question selected from the interview category and job context."
    generation_provider: str
    generation_method: Literal["llm_structured", "deterministic_templates"]
    generation_warning: str | None = None
    expected_answer_points: list[str] = Field(default_factory=list, exclude=True)
    evaluation_rubric: EvaluationRubric = Field(exclude=True)
    evaluation_keywords: list[str] = Field(default_factory=list, exclude=True)


class QuestionDraft(StrictModel):
    question_text: str = Field(min_length=1, max_length=1200)
    interview_type: InterviewType
    difficulty: Difficulty
    competency: str = Field(min_length=1, max_length=120)
    relevant_job_requirement: str | None = None
    expected_answer_points: list[str] = Field(default_factory=list, max_length=12)
    profile_evidence_paths: list[str] = Field(default_factory=list, max_length=20)
    follow_up_guidance: str = Field(min_length=1, max_length=1000)


class QuestionBatchDraft(StrictModel):
    questions: list[QuestionDraft] = Field(default_factory=list, max_length=30)


class QuestionEvaluationMaterial(StrictModel):
    question_id: str
    expected_answer_points: list[str]
    rubric: EvaluationRubric


class InterviewAnswer(StrictModel):
    question_id: str
    answer_text: str = Field(max_length=12000)
    submitted_at: datetime


class AnswerEvidence(StrictModel):
    dimension: DimensionName
    excerpt: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=500)


class DimensionScore(StrictModel):
    score: float | None = Field(default=None, ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    status: Literal["assessed", "not_assessed"]
    explanation: str
    answer_evidence: list[AnswerEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def status_matches_score(self) -> DimensionScore:
        if (self.score is None) != (self.status == "not_assessed"):
            raise ValueError("dimension status must agree with whether a score is present")
        return self


class AnswerEvaluation(StrictModel):
    question_id: str
    overall_score: float | None = Field(default=None, ge=0, le=100)
    score_coverage: float = Field(ge=0, le=1)
    dimension_scores: dict[DimensionName, DimensionScore]
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    example_areas_to_improve: list[str] = Field(default_factory=list)
    confidence: EvaluationConfidence
    evaluation_method: EvaluationMethod
    generation_provider: str
    is_fallback: bool
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def weighted_score_is_consistent(self) -> AnswerEvaluation:
        if set(self.dimension_scores) != _DIMENSION_NAMES:
            raise ValueError("an evaluation must contain every rubric dimension")
        total_weight = sum(dimension.weight for dimension in self.dimension_scores.values())
        if not math.isclose(total_weight, 1.0, abs_tol=1e-6):
            raise ValueError("dimension weights must sum to 1.0")
        assessed = [
            dimension
            for dimension in self.dimension_scores.values()
            if dimension.status == "assessed" and dimension.score is not None
        ]
        coverage = sum(dimension.weight for dimension in assessed)
        expected_coverage = min(1.0, coverage)
        if not math.isclose(self.score_coverage, expected_coverage, abs_tol=0.01):
            raise ValueError("score_coverage does not match assessed rubric weights")
        expected_score = (
            sum(dimension.score * dimension.weight for dimension in assessed) / coverage
            if coverage > 0
            else None
        )
        if expected_score is None:
            if self.overall_score is not None:
                raise ValueError("overall_score must be null when no rubric weight was assessed")
        elif self.overall_score is None or not math.isclose(
            self.overall_score, expected_score, abs_tol=0.2
        ):
            raise ValueError("overall_score must equal the normalized weighted rubric score")
        return self


class RubricDimensionScores(StrictModel):
    technical_correctness: float = Field(ge=0, le=100)
    conceptual_understanding: float = Field(ge=0, le=100)
    depth_of_explanation: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    problem_solving: float = Field(ge=0, le=100)
    communication_clarity: float = Field(ge=0, le=100)
    practical_application: float = Field(ge=0, le=100)


class AnswerEvaluationDraft(StrictModel):
    dimension_scores: RubricDimensionScores
    explanations: dict[DimensionName, str]
    strengths: list[str] = Field(default_factory=list, max_length=8)
    weaknesses: list[str] = Field(default_factory=list, max_length=8)
    missing_concepts: list[str] = Field(default_factory=list, max_length=12)
    improvement_suggestions: list[str] = Field(default_factory=list, max_length=8)
    example_areas_to_improve: list[str] = Field(default_factory=list, max_length=5)
    answer_evidence_quotes: dict[DimensionName, list[str]] = Field(default_factory=dict)


class InterviewTurn(StrictModel):
    question: InterviewQuestion
    answer: InterviewAnswer
    evaluation: AnswerEvaluation
    selection_reason: str
    created_at: datetime


class CompetencyPerformance(StrictModel):
    competency: str
    questions_attempted: int = Field(ge=0)
    scores: list[float] = Field(default_factory=list)
    unscored_attempts: int = Field(default=0, ge=0)
    fallback_attempts: int = Field(default=0, ge=0)
    average_score: float | None = Field(default=None, ge=0, le=100)
    trend: Literal["insufficient_data", "improving", "declining", "stable"] = "insufficient_data"
    repeated_weaknesses: int = Field(default=0, ge=0)
    confidence: EvaluationConfidence = "low"

    @model_validator(mode="after")
    def validate_attempt_summary(self) -> CompetencyPerformance:
        if self.questions_attempted != len(self.scores) + self.unscored_attempts:
            raise ValueError("questions_attempted must equal scored plus unscored attempts")
        if self.fallback_attempts > self.questions_attempted:
            raise ValueError("fallback_attempts cannot exceed total attempts")
        expected = sum(self.scores) / len(self.scores) if self.scores else None
        if expected is None:
            if self.average_score is not None:
                raise ValueError("average_score must be null without scores")
        elif self.average_score is None or not math.isclose(self.average_score, expected, abs_tol=0.1):
            raise ValueError("average_score must match recorded scores")
        return self


class InterviewSession(StrictModel):
    session_id: str = Field(min_length=1)
    student_profile: StudentProfile
    job_listing: JobListing
    job_match: JobMatch | None = None
    interview_type: InterviewType
    difficulty: Difficulty
    current_difficulty: Difficulty
    total_planned_questions: int = Field(ge=1, le=30)
    current_question_index: int = Field(ge=0)
    question_history: list[InterviewQuestion] = Field(default_factory=list)
    answer_history: list[InterviewAnswer] = Field(default_factory=list)
    evaluation_history: list[AnswerEvaluation] = Field(default_factory=list)
    turn_history: list[InterviewTurn] = Field(default_factory=list)
    competency_performance: dict[str, CompetencyPerformance] = Field(default_factory=dict)
    identified_strengths: list[str] = Field(default_factory=list)
    identified_weaknesses: list[str] = Field(default_factory=list)
    repeated_weaknesses: list[str] = Field(default_factory=list)
    status: Literal["in_progress", "completed", "terminated"] = "in_progress"
    termination_reason: str | None = None
    last_focus_competency: str | None = None
    focus_reinforcement_used: bool = False
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_session_history(self) -> InterviewSession:
        if self.job_match and self.job_match.job_id != self.job_listing.job_id:
            raise ValueError("job_match must refer to the session job")
        if not (
            len(self.answer_history)
            == len(self.evaluation_history)
            == len(self.turn_history)
        ):
            raise ValueError("answers, evaluations, and turns must remain aligned")
        if len(self.question_history) not in {
            len(self.turn_history),
            len(self.turn_history) + 1,
        }:
            raise ValueError("question history must contain completed turns and at most one pending question")
        if self.status == "in_progress" and len(self.question_history) != len(self.turn_history) + 1:
            raise ValueError("an in-progress session must have one unanswered current question")
        if self.status == "completed" and len(self.question_history) != len(self.turn_history):
            raise ValueError("a completed session cannot have a pending question")
        if self.current_question_index != len(self.turn_history):
            raise ValueError("current_question_index must equal the number of completed turns")
        if len({question.question_id for question in self.question_history}) != len(self.question_history):
            raise ValueError("question history cannot contain duplicate question ids")
        for index, turn in enumerate(self.turn_history):
            if turn.question.question_id != turn.answer.question_id or turn.question.question_id != turn.evaluation.question_id:
                raise ValueError("each turn question, answer, and evaluation must use the same question id")
            if self.question_history[index].question_id != turn.question.question_id:
                raise ValueError("turn history must align with question history")
        return self


class QuestionSelection(StrictModel):
    question: InterviewQuestion
    selection_reason: str
    targeted_competency: str
    reinforcement: bool = False

    @model_validator(mode="after")
    def competency_matches_question(self) -> QuestionSelection:
        if self.targeted_competency != self.question.competency:
            raise ValueError("targeted_competency must match the selected question")
        return self


class InterviewReport(StrictModel):
    session_id: str
    session_status: Literal["in_progress", "completed", "terminated"]
    questions_completed: int = Field(ge=0)
    planned_questions: int = Field(ge=1)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    technical_performance: float | None = Field(default=None, ge=0, le=100)
    communication_performance: float | None = Field(default=None, ge=0, le=100)
    competency_breakdown: dict[str, CompetencyPerformance] = Field(default_factory=dict)
    strong_areas: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)
    repeated_mistakes: list[str] = Field(default_factory=list)
    improvement_recommendations: list[str] = Field(default_factory=list)
    suggested_practice_topics: list[str] = Field(default_factory=list)
    readiness_observations: list[str] = Field(default_factory=list)
    evaluation_limitations: list[str] = Field(default_factory=list)
    confidence: EvaluationConfidence
    generated_at: datetime

    @model_validator(mode="after")
    def question_count_is_valid(self) -> InterviewReport:
        if self.questions_completed > self.planned_questions:
            raise ValueError("questions_completed cannot exceed planned_questions")
        return self


class InterviewStartRequest(StrictModel):
    student_profile: StudentProfile
    job_listing: JobListing
    job_match: JobMatch | None = None
    interview_type: InterviewType
    difficulty: Difficulty = "intermediate"
    question_count: int = Field(default=10, ge=1, le=30)

    @model_validator(mode="after")
    def match_must_belong_to_job(self) -> InterviewStartRequest:
        if self.job_match and self.job_match.job_id != self.job_listing.job_id:
            raise ValueError("job_match must refer to the selected job_listing")
        return self


class InterviewSubmitRequest(StrictModel):
    answer_text: str = Field(max_length=12000)
