"""Service-level lifecycle for adaptive mock interview sessions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.providers import LLMService
from app.ai.resume_intelligence.profile_schemas import StudentProfile

from .adaptive_engine import select_next_question
from .evaluation import evaluate_interview_answer
from .question_generator import generate_interview_questions
from .schemas import (
    AnswerEvaluation,
    CompetencyPerformance,
    InterviewAnswer,
    InterviewQuestion,
    InterviewReport,
    InterviewSession,
    InterviewStartRequest,
    InterviewSubmitRequest,
    InterviewTurn,
    InterviewType,
    Difficulty,
    QuestionEvaluationMaterial,
)


def start_interview(
    student_profile: StudentProfile,
    job_listing: JobListing,
    interview_type: InterviewType,
    difficulty: Difficulty = "intermediate",
    question_count: int = 10,
    *,
    job_match: JobMatch | None = None,
    llm_service: LLMService | None = None,
) -> InterviewSession:
    """Create an in-memory session and its first question."""
    request = InterviewStartRequest(
        student_profile=student_profile,
        job_listing=job_listing,
        job_match=job_match,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
    )
    questions = generate_interview_questions(
        request.student_profile,
        request.job_listing,
        request.interview_type,
        request.difficulty,
        1,
        job_match=request.job_match,
        llm_service=llm_service,
    )
    if not questions:
        raise RuntimeError("question generation did not return an initial question")
    now = _now()
    return InterviewSession(
        session_id=str(uuid.uuid4()),
        student_profile=request.student_profile,
        job_listing=request.job_listing,
        job_match=request.job_match,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        current_difficulty=request.difficulty,
        total_planned_questions=request.question_count,
        current_question_index=0,
        question_history=[questions[0]],
        created_at=now,
        updated_at=now,
    )


def submit_interview_answer(
    interview_session: InterviewSession,
    answer_text: str,
    *,
    llm_service: LLMService | None = None,
) -> InterviewSession:
    """Evaluate the current answer, update session metrics, and select a follow-up."""
    if interview_session.status != "in_progress":
        raise ValueError("cannot submit an answer to a session that is not in progress")
    if not interview_session.question_history or len(interview_session.question_history) != len(interview_session.turn_history) + 1:
        raise ValueError("session has no pending question")
    validated_answer = InterviewSubmitRequest(answer_text=answer_text)
    question = interview_session.question_history[-1]
    now = _now()
    answer = InterviewAnswer(
        question_id=question.question_id,
        answer_text=validated_answer.answer_text,
        submitted_at=now,
    )
    evaluation = evaluate_interview_answer(
        question,
        validated_answer.answer_text,
        interview_session.student_profile,
        interview_session.job_listing,
        llm_service=llm_service,
    )
    answers = [*interview_session.answer_history, answer]
    evaluations = [*interview_session.evaluation_history, evaluation]
    turns = [
        *interview_session.turn_history,
        InterviewTurn(
            question=question,
            answer=answer,
            evaluation=evaluation,
            selection_reason=question.selection_reason,
            created_at=now,
        ),
    ]
    performance = _update_performance(interview_session.competency_performance, question, evaluation)
    strengths = _merge(interview_session.identified_strengths, evaluation.strengths)
    weaknesses = _merge(interview_session.identified_weaknesses, evaluation.weaknesses)
    repeated = list(interview_session.repeated_weaknesses)
    item = performance[question.competency]
    if item.repeated_weaknesses >= 2 and item.average_score is not None and item.average_score < 65:
        repeated = _merge(repeated, [question.competency])

    current_difficulty = _adjust_difficulty(interview_session.current_difficulty, evaluation.overall_score)
    same_competency_as_previous = (
        interview_session.last_focus_competency is not None
        and _key(interview_session.last_focus_competency) == _key(question.competency)
    )
    reinforcement_already_used = interview_session.focus_reinforcement_used and same_competency_as_previous
    used_now = reinforcement_already_used
    updated = interview_session.model_copy(
        update={
            "answer_history": answers,
            "evaluation_history": evaluations,
            "turn_history": turns,
            "competency_performance": performance,
            "identified_strengths": strengths,
            "identified_weaknesses": weaknesses,
            "repeated_weaknesses": repeated,
            "current_difficulty": current_difficulty,
            "current_question_index": len(turns),
            "last_focus_competency": question.competency,
            "focus_reinforcement_used": used_now,
            "updated_at": now,
        }
    )

    if len(turns) >= interview_session.total_planned_questions:
        return updated.model_copy(update={"status": "completed"})

    selection = select_next_question(updated, llm_service=llm_service)
    if selection is None:
        return updated.model_copy(update={"status": "completed"})
    # The follow-up consumes the one-reinforcement allowance for this focus.
    if selection.reinforcement:
        updated = updated.model_copy(update={"focus_reinforcement_used": True})
    next_questions = [*updated.question_history, selection.question]
    return updated.model_copy(
        update={"question_history": next_questions, "status": "in_progress"}
    )


def end_interview(
    interview_session: InterviewSession,
    reason: str = "student_requested",
) -> InterviewSession:
    """Terminate an interview early while retaining its completed turns."""
    if interview_session.status != "in_progress":
        return interview_session
    clean_reason = reason.strip()
    if not clean_reason:
        clean_reason = "student_requested"
    if len(clean_reason) > 240:
        raise ValueError("termination reason must be no longer than 240 characters")
    return interview_session.model_copy(
        update={"status": "terminated", "termination_reason": clean_reason, "updated_at": _now()}
    )


def get_interview_report(interview_session: InterviewSession) -> InterviewReport:
    """Summarize only this interview; it does not infer cross-session readiness."""
    evaluations = interview_session.evaluation_history
    scores = [item.overall_score for item in evaluations if item.overall_score is not None]
    overall = round(sum(scores) / len(scores), 2) if scores else None
    technical = _dimension_average(evaluations, "technical_correctness")
    communication = _dimension_average(evaluations, "communication_clarity")
    strong = [
        name for name, item in interview_session.competency_performance.items()
        if item.average_score is not None and item.average_score >= 75
    ]
    weak = [
        name for name, item in interview_session.competency_performance.items()
        if item.average_score is not None and item.average_score < 60
    ]
    repeated = list(interview_session.repeated_weaknesses)
    recommendations: list[str] = _merge(
        [], [suggestion for evaluation in evaluations for suggestion in evaluation.improvement_suggestions]
    )
    for competency in weak:
        recommendations = _merge(
            recommendations,
            [f"Practice {competency.replace('_', ' ')} with short explanations and worked examples."],
        )
    recommendations = recommendations[:12]
    if not recommendations and evaluations:
        recommendations.append("Review the feedback for each answer and practice explaining the reasoning aloud.")
    if not evaluations:
        recommendations.append("Complete at least one interview question to receive answer-specific feedback.")
    missing_concepts = [concept for evaluation in evaluations for concept in evaluation.missing_concepts]
    practice = _merge(_merge(weak, repeated), missing_concepts)[:20]
    observations = [
        "This report describes one mock interview and is not a hiring decision or validated readiness certification."
    ]
    if interview_session.status == "in_progress":
        observations.append("The interview is incomplete; scores may change as additional answers are evaluated.")
    elif interview_session.status == "terminated":
        observations.append("The interview ended early; the report covers completed answers only.")
    elif overall is None:
        observations.append("No answer received an assessable score, so no overall score is reported.")
    limitations = _merge(
        [
            "Assessment is based only on submitted text; spoken delivery and external fact checking are not available.",
            "Deterministic fallback scores are heuristic and leave technical correctness unassessed.",
            "Session observations do not imply long-term learning or progress across interviews.",
        ],
        [limitation for item in evaluations for limitation in item.limitations],
    )
    confidence = (
        "medium"
        if evaluations and all(item.evaluation_method == "llm_rubric" and item.confidence == "medium" for item in evaluations)
        else "low"
    )
    return InterviewReport(
        session_id=interview_session.session_id,
        session_status=interview_session.status,
        questions_completed=len(interview_session.turn_history),
        planned_questions=interview_session.total_planned_questions,
        overall_score=overall,
        technical_performance=technical,
        communication_performance=communication,
        competency_breakdown=interview_session.competency_performance,
        strong_areas=strong,
        weak_areas=weak,
        repeated_mistakes=repeated,
        improvement_recommendations=recommendations,
        suggested_practice_topics=practice,
        readiness_observations=observations,
        evaluation_limitations=limitations,
        confidence=confidence,
        generated_at=_now(),
    )


def get_question_evaluation_material(
    question: InterviewQuestion,
    *,
    explicitly_requested: bool = False,
) -> QuestionEvaluationMaterial:
    """Expose hidden answer guidance only for an authorized evaluation flow."""
    if not explicitly_requested:
        raise PermissionError("evaluation material is hidden until explicitly requested")
    return QuestionEvaluationMaterial(
        question_id=question.question_id,
        expected_answer_points=question.expected_answer_points,
        rubric=question.evaluation_rubric,
    )


def serialize_interview_session(
    interview_session: InterviewSession,
    *,
    include_evaluation_material: bool = False,
) -> str:
    """Serialize session JSON; evaluation keys are omitted unless requested.

    Set ``include_evaluation_material=True`` only for trusted service-level
    storage. The default representation is suitable for student-visible
    output, and intentionally cannot be used to reconstruct hidden answer keys.
    """
    payload = interview_session.model_dump(mode="json")
    if include_evaluation_material:
        by_id = {question.question_id: question for question in interview_session.question_history}
        payload["question_history"] = [
            _question_payload(question, True) for question in interview_session.question_history
        ]
        for turn_data, turn in zip(payload["turn_history"], interview_session.turn_history):
            turn_data["question"] = _question_payload(by_id.get(turn.question.question_id, turn.question), True)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _question_payload(question: InterviewQuestion, include_material: bool) -> dict[str, object]:
    payload = question.model_dump(mode="json")
    if include_material:
        payload["expected_answer_points"] = question.expected_answer_points
        payload["evaluation_rubric"] = question.evaluation_rubric.model_dump(mode="json")
        payload["evaluation_keywords"] = question.evaluation_keywords
    return payload


def _update_performance(
    current: dict[str, CompetencyPerformance],
    question: InterviewQuestion,
    evaluation: AnswerEvaluation,
) -> dict[str, CompetencyPerformance]:
    output = dict(current)
    previous = output.get(question.competency)
    scores = list(previous.scores) if previous else []
    unscored = previous.unscored_attempts if previous else 0
    fallback_attempts = previous.fallback_attempts if previous else 0
    weak_count = previous.repeated_weaknesses if previous else 0
    if evaluation.is_fallback:
        fallback_attempts += 1
    if evaluation.overall_score is None:
        unscored += 1
    else:
        scores.append(evaluation.overall_score)
        if evaluation.overall_score < 55:
            weak_count += 1
    average = sum(scores) / len(scores) if scores else None
    trend = _trend(scores)
    output[question.competency] = CompetencyPerformance(
        competency=question.competency,
        questions_attempted=len(scores) + unscored,
        scores=scores,
        unscored_attempts=unscored,
        fallback_attempts=fallback_attempts,
        average_score=average,
        trend=trend,
        repeated_weaknesses=weak_count,
        confidence=(
            "medium"
            if len(scores) >= 3 and fallback_attempts == 0
            else "low"
        ),
    )
    return output


def _trend(scores: list[float]) -> str:
    if len(scores) < 3:
        return "insufficient_data"
    midpoint = len(scores) // 2
    earlier = sum(scores[:midpoint]) / midpoint
    later = sum(scores[midpoint:]) / len(scores[midpoint:])
    if later - earlier >= 8:
        return "improving"
    if earlier - later >= 8:
        return "declining"
    return "stable"


def _adjust_difficulty(current: Difficulty, score: float | None) -> Difficulty:
    levels: tuple[Difficulty, ...] = ("beginner", "intermediate", "advanced")
    if score is None:
        return current
    index = levels.index(current)
    if score < 45:
        index = max(0, index - 1)
    elif score >= 80:
        index = min(len(levels) - 1, index + 1)
    return levels[index]


def _dimension_average(evaluations: list[AnswerEvaluation], name: str) -> float | None:
    scores = [
        dimension.score
        for evaluation in evaluations
        if (dimension := evaluation.dimension_scores.get(name)) is not None
        and dimension.score is not None
        and dimension.status == "assessed"
    ]
    return round(sum(scores) / len(scores), 2) if scores else None


def _merge(first: list[str], second: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in [*first, *second] if item))


def _key(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


def _now() -> datetime:
    return datetime.now(timezone.utc)
