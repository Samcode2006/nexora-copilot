"""Resume parsing and profile-extraction graph."""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.ai.orchestration.errors import WorkflowType
from app.ai.orchestration.nodes.resume_nodes import (
    extract_profile_node,
    finish_resume_node,
    parse_resume_node,
    validate_resume_input_node,
    validate_resume_result_node,
)
from app.ai.orchestration.schemas import ResumeProcessingInput, ResumeProcessingResult
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


def build_resume_processing_graph(services: OrchestrationServices):
    graph = StateGraph(WorkflowState)
    graph.add_node("validate_input", partial(validate_resume_input_node, services=services))
    graph.add_node("parse_resume", partial(parse_resume_node, services=services))
    graph.add_node("extract_profile", partial(extract_profile_node, services=services))
    graph.add_node("validate_result", partial(validate_resume_result_node, services=services))
    graph.add_node("finish", partial(finish_resume_node, services=services))
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_failed,
        {"finish": "finish", "continue": "parse_resume"},
    )
    graph.add_conditional_edges(
        "parse_resume",
        route_failed,
        {"finish": "finish", "continue": "extract_profile"},
    )
    graph.add_conditional_edges(
        "extract_profile",
        route_failed,
        {"finish": "finish", "continue": "validate_result"},
    )
    graph.add_edge("validate_result", "finish")
    graph.add_edge("finish", END)
    return graph.compile()


def process_resume(
    input_data,
    *,
    services: OrchestrationServices | None = None,
    checkpoint_store=None,
) -> ResumeProcessingResult:
    """Parse one PDF/DOCX resume and extract a profile; runtime state is ephemeral."""
    dependencies = resolve_services(services, checkpoint_store)
    try:
        request = ResumeProcessingInput.model_validate(input_data)
    except (ValidationError, TypeError, ValueError):
        state = invalid_input_state(WorkflowType.RESUME_PROCESSING, dependencies)
        return ResumeProcessingResult(**common_output_fields(state))

    state = initial_state(WorkflowType.RESUME_PROCESSING, request, dependencies)
    final = invoke_graph(build_resume_processing_graph(dependencies), state, dependencies)
    result = ResumeProcessingResult(
        **common_output_fields(final),
        parsed_resume=final["parsed_resume"],
        student_profile=final["student_profile"],
    )
    return result
