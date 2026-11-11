"""Multi-job resume and cover-letter tailoring graph."""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.ai.orchestration.errors import WorkflowType
from app.ai.orchestration.nodes.tailoring_nodes import (
    finish_tailoring_node,
    generate_cover_letters_node,
    tailor_selected_jobs_node,
    validate_tailoring_input_node,
)
from app.ai.orchestration.schemas import ResumeTailoringInput, ResumeTailoringResult
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


def build_resume_tailoring_graph(services: OrchestrationServices):
    graph = StateGraph(WorkflowState)
    graph.add_node("validate_input", partial(validate_tailoring_input_node, services=services))
    graph.add_node("tailor_resumes", partial(tailor_selected_jobs_node, services=services))
    graph.add_node(
        "generate_cover_letters", partial(generate_cover_letters_node, services=services)
    )
    graph.add_node("finish", partial(finish_tailoring_node, services=services))
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_failed,
        {"finish": "finish", "continue": "tailor_resumes"},
    )
    graph.add_edge("tailor_resumes", "generate_cover_letters")
    graph.add_edge("generate_cover_letters", "finish")
    graph.add_edge("finish", END)
    return graph.compile()


def tailor_resume_workflow(
    input_data,
    *,
    services: OrchestrationServices | None = None,
    checkpoint_store=None,
) -> ResumeTailoringResult:
    """Tailor multiple jobs independently and preserve successful partial results."""
    dependencies = resolve_services(services, checkpoint_store)
    try:
        request = ResumeTailoringInput.model_validate(input_data)
    except (ValidationError, TypeError, ValueError):
        state = invalid_input_state(WorkflowType.RESUME_TAILORING, dependencies)
        return ResumeTailoringResult(**common_output_fields(state))

    state = initial_state(WorkflowType.RESUME_TAILORING, request, dependencies)
    final = invoke_graph(build_resume_tailoring_graph(dependencies), state, dependencies)
    return ResumeTailoringResult(
        **common_output_fields(final),
        outcomes=final["tailoring_outcomes"],
    )
