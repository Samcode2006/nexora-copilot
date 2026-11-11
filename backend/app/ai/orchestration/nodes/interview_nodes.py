"""Interview question and separate answer-evaluation nodes."""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.interview_intelligence.schemas import AnswerEvaluation, InterviewQuestion
from app.ai.orchestration.errors import WorkflowErrorCode, WorkflowStage
from app.ai.orchestration.nodes._shared import (
    begin_stage,
    complete_stage,
    failed_stage,
    terminal_stage,
)
from app.ai.orchestration.schemas import (
    AnswerEvaluationInput,
    InterviewPreparationInput,
)
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState


def validate_interview_input_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.INPUT_VALIDATION
    begin_stage(state, services, stage)
    try:
        request = InterviewPreparationInput.model_validate(state["runtime_input"])
    except (ValidationError, TypeError, ValueError) as exc:
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.INVALID_INPUT,
            expected_exceptions=(ValidationError, TypeError, ValueError),
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={
            "student_profile": request.student_profile,
            "selected_job": request.job_listing,
            "job_matches": (
                {request.job_listing.job_id: request.job_match}
                if request.job_match is not None
                else {}
            ),
        },
        input_item_count=1,
    )


def generate_interview_questions_node(
    state: WorkflowState, *, services: OrchestrationServices
) -> dict:
    stage = WorkflowStage.INTERVIEW_QUESTION_GENERATION
    begin_stage(state, services, stage, input_item_count=1)
    try:
        request = InterviewPreparationInput.model_validate(state["runtime_input"])
        questions = services.generate_interview_questions_fn(
            request.student_profile,
            request.job_listing,
            request.interview_type,
            request.difficulty,
            request.question_count,
            job_match=request.job_match,
            llm_service=services.llm_service,
        )
        if isinstance(questions, (str, bytes)) or not isinstance(questions, list):
            raise TypeError("Question service returned an invalid collection.")
        validated = [InterviewQuestion.model_validate(question) for question in questions]
        if len(validated) != request.question_count:
            raise ValueError("Question service returned an incomplete result.")
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.INTERVIEW_QUESTION_GENERATION_FAILURE,
            expected_exceptions=(ValidationError, TypeError, ValueError),
            input_item_count=1,
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"interview_questions": validated},
        input_item_count=1,
        output_item_count=len(validated),
    )


def finish_interview_preparation_node(
    state: WorkflowState, *, services: OrchestrationServices
) -> dict:
    return terminal_stage(
        state,
        services,
        output_item_count=len(state["interview_questions"]),
    )


def validate_answer_input_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.INPUT_VALIDATION
    begin_stage(state, services, stage)
    try:
        request = AnswerEvaluationInput.model_validate(state["runtime_input"])
    except (ValidationError, TypeError, ValueError) as exc:
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.INVALID_INPUT,
            expected_exceptions=(ValidationError, TypeError, ValueError),
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={
            "student_profile": request.student_profile,
            "selected_job": request.job_listing,
        },
        input_item_count=1,
    )


def evaluate_interview_answer_node(
    state: WorkflowState, *, services: OrchestrationServices
) -> dict:
    stage = WorkflowStage.ANSWER_EVALUATION
    begin_stage(state, services, stage, input_item_count=1)
    try:
        request = AnswerEvaluationInput.model_validate(state["runtime_input"])
        result = services.evaluate_interview_answer_fn(
            request.question,
            request.answer,
            request.student_profile,
            request.job_listing,
            llm_service=services.llm_service,
        )
        result = AnswerEvaluation.model_validate(result)
        if result.question_id != request.question.question_id:
            raise ValueError("Evaluation result refers to another question.")
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.ANSWER_EVALUATION_FAILURE,
            expected_exceptions=(ValidationError, TypeError, ValueError),
            input_item_count=1,
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"answer_evaluation": result},
        input_item_count=1,
        output_item_count=1,
    )


def finish_answer_evaluation_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    return terminal_stage(
        state,
        services,
        output_item_count=1 if state["answer_evaluation"] is not None else 0,
    )
