"""Deterministic next-question selection for a single interview session."""

from __future__ import annotations

from app.ai.providers import LLMService

from .question_generator import available_competencies, generate_interview_questions
from .schemas import InterviewSession, QuestionSelection


def select_next_question(
    interview_session: InterviewSession,
    *,
    llm_service: LLMService | None = None,
) -> QuestionSelection | None:
    """Select a targeted next question and explain the decision.

    One weak attempt can trigger one same-competency reinforcement. After that,
    the engine prefers unasked job competencies, so one difficult answer does
    not trap the student in a loop.
    """
    session = interview_session
    if session.status != "in_progress":
        return None
    if len(session.question_history) >= session.total_planned_questions:
        return None
    if not session.question_history:
        return None

    previous_question = session.question_history[-1]
    previous_evaluation = session.evaluation_history[-1] if session.evaluation_history else None
    weak_score = previous_evaluation.overall_score if previous_evaluation else None
    reinforcement = bool(
        weak_score is not None
        and weak_score < 55
        and not session.focus_reinforcement_used
    )

    available = available_competencies(
        session.student_profile,
        session.job_listing,
        session.interview_type,
        job_match=session.job_match,
    )
    attempted = [question.competency for question in session.question_history]
    if reinforcement:
        target = previous_question.competency
        reason = (
            f"The previous response scored {weak_score:.0f}/100. One focused follow-up will "
            f"check {target.replace('_', ' ')} at the current adjusted difficulty; further "
            "weaknesses will be balanced with other role competencies."
        )
    else:
        target = _choose_unasked_target(session, available, attempted)
        if target is None:
            target = _choose_review_target(session, available, previous_question.competency)
        if target is None:
            target = available[len(session.question_history) % len(available)] if available else previous_question.competency
        if target != previous_question.competency:
            reason = f"Move to {target.replace('_', ' ')} to cover another relevant competency without repeating the last question."
        elif weak_score is not None and weak_score >= 80:
            reason = f"The previous response was strong ({weak_score:.0f}/100); continue with a related competency at the adjusted difficulty."
        else:
            reason = f"Continue role-specific practice on {target.replace('_', ' ')} using a distinct question."

    history_texts = [question.question_text for question in session.question_history]
    generated = generate_interview_questions(
        session.student_profile,
        session.job_listing,
        session.interview_type,
        session.current_difficulty,
        1,
        job_match=session.job_match,
        llm_service=llm_service,
        focus_competency=target,
        exclude_question_texts=history_texts,
        variant_offset=len(session.question_history),
    )
    if not generated:
        return None
    question_updates = {"selection_reason": reason}
    if reinforcement:
        # Keep the same tracked competency label even if the generated wording
        # uses a more specific synonym for its standardized target.
        question_updates["competency"] = target
    question = generated[0].model_copy(update=question_updates)
    return QuestionSelection(
        question=question,
        selection_reason=reason,
        targeted_competency=question.competency,
        reinforcement=reinforcement,
    )


def _choose_unasked_target(
    session: InterviewSession,
    available: list[str],
    attempted: list[str],
) -> str | None:
    canonical_attempted = {_key(item) for item in attempted}
    ordered: list[str] = []
    # A match's unobserved required skills are especially useful practice areas.
    if session.job_match is not None:
        for skill in session.job_match.missing_required_skills:
            slug = _competency_for_skill(skill)
            ordered.extend(item for item in available if _key(item) == _key(slug))
    for skill in session.job_listing.required_skills:
        slug = _competency_for_skill(skill)
        ordered.extend(item for item in available if _key(item) == _key(slug))
    for skill in session.job_listing.preferred_skills:
        slug = _competency_for_skill(skill)
        ordered.extend(item for item in available if _key(item) == _key(slug))
    ordered.extend(available)
    for candidate in ordered:
        if _key(candidate) not in canonical_attempted:
            return candidate
    return None


def _choose_review_target(
    session: InterviewSession,
    available: list[str],
    last_competency: str,
) -> str | None:
    for competency in session.repeated_weaknesses:
        if _key(competency) == _key(last_competency):
            continue
        performance = session.competency_performance.get(competency)
        if performance and performance.average_score is not None and performance.average_score < 70:
            candidate = next((item for item in available if _key(item) == _key(competency)), None)
            if candidate:
                return candidate
    return None


def _competency_for_skill(value: str) -> str:
    normalized = _key(value)
    aliases = {
        "python": "python_fundamentals",
        "python basics": "python_fundamentals",
        "python fundamentals": "python_fundamentals",
        "rest api": "api_design",
        "apis": "api_design",
        "fastapi": "api_development",
        "django": "api_development",
        "flask": "api_development",
        "aws": "cloud_fundamentals",
        "azure": "cloud_fundamentals",
        "gcp": "cloud_fundamentals",
        "postgres": "sql_databases",
        "postgresql": "sql_databases",
        "mysql": "sql_databases",
        "mongodb": "nosql_databases",
        "data structures": "data_structures",
    }
    if normalized in aliases:
        return aliases[normalized]
    return "_".join(normalized.split())


def _key(value: str) -> str:
    normalized = " ".join(value.casefold().replace("-", " ").replace("_", " ").split())
    return {
        "python basics": "python fundamentals",
        "python fundamentals": "python fundamentals",
    }.get(normalized, normalized)
