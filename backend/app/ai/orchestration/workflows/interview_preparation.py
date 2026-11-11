"""Interview question generation and explicit answer-evaluation graphs."""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.ai.orchestration.errors import WorkflowType
from app.ai.orchestration.nodes.interview_nodes import (
    evaluate_interview_answer_node,
    finish_answer_evaluation_node,
    finish_interview_preparation_node,
    generate_interview_questions_node,
    validate_answer_input_node,
    validate_interview_input_node,
)
from app.ai.orchestration.schemas import (
    AnswerEvaluationInput,
    AnswerEvaluationResult,
    InterviewPreparationInput,
    InterviewPreparationResult,
)
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState
from app.ai.orchestration.workflows._runtime import (
    common_output_fields,
    initial_state,
    invalid_input_state,
    invoke_graph,
    resolve_services,
    route_failed,
)


def build_interview_preparation_graph(services: OrchestrationServices):
    graph = StateGraph(WorkflowState)
    graph.add_node("validate_input", partial(validate_interview_input_node, services=services))
    graph.add_node(
        "generate_questions",
        partial(generate_interview_questions_node, services=services),
    )
    graph.add_node(
        "finish",
        partial(finish_interview_preparation_node, services=services),
    )
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_failed,
        {"finish": "finish", "continue": "generate_questions"},
    )
    graph.add_conditional_edges(
        "generate_questions",
        route_failed,
        {"finish": "finish", "continue": "finish"},
    )
    graph.add_edge("finish", END)
    return graph.compile()


def build_answer_evaluation_graph(services: OrchestrationServices):
    graph = StateGraph(WorkflowState)
    graph.add_node("validate_input", partial(validate_answer_input_node, services=services))
    graph.add_node(
        "evaluate_answer",
        partial(evaluate_interview_answer_node, services=services),
    )
    graph.add_node(
        "finish",
        partial(finish_answer_evaluation_node, services=services),
    )
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_failed,
        {"finish": "finish", "continue": "evaluate_answer"},
    )
    graph.add_conditional_edges(
        "evaluate_answer",
        route_failed,
        {"finish": "finish", "continue": "finish"},
    )
    graph.add_edge("finish", END)
    return graph.compile()


def prepare_interview(
    input_data,
    *,
    services: OrchestrationServices | None = None,
    checkpoint_store=None,
) -> InterviewPreparationResult:
    """Generate questions only. Answer evaluation is a separate invocation."""
    dependencies = resolve_services(services, checkpoint_store)
    try:
        request = InterviewPreparationInput.model_validate(input_data)
    except (ValidationError, TypeError, ValueError):
        state = invalid_input_state(WorkflowType.INTERVIEW_PREPARATION, dependencies)
        return InterviewPreparationResult(
            **common_output_fields(state),
        )

    state = initial_state(WorkflowType.INTERVIEW_PREPARATION, request, dependencies)
    final = invoke_graph(build_interview_preparation_graph(dependencies), state, dependencies)
    return InterviewPreparationResult(
        **common_output_fields(final),
        job_id=request.job_listing.job_id,
        questions=final["interview_questions"],
    )


def evaluate_answer(
    input_data,
    *,
    services: OrchestrationServices | None = None,
    checkpoint_store=None,
) -> AnswerEvaluationResult:
    """Evaluate one explicitly supplied answer in its own graph invocation."""
    dependencies = resolve_services(services, checkpoint_store)
    try:
        request = AnswerEvaluationInput.model_validate(input_data)
    except (ValidationError, TypeError, ValueError):
        state = invalid_input_state(WorkflowType.ANSWER_EVALUATION, dependencies)
        return AnswerEvaluationResult(
            **common_output_fields(state),
        )

    state = initial_state(WorkflowType.ANSWER_EVALUATION, request, dependencies)
    final = invoke_graph(build_answer_evaluation_graph(dependencies), state, dependencies)
    return AnswerEvaluationResult(
        **common_output_fields(final),
        question_id=request.question.question_id,
        evaluation=final["answer_evaluation"],
    )
