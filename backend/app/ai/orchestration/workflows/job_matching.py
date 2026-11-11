"""Job discovery, normalization, and ranking graph."""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.ai.orchestration.errors import WorkflowType
from app.ai.orchestration.nodes.job_nodes import (
    discover_jobs_node,
    finish_job_matching_node,
    match_discovered_jobs_node,
    normalize_discovered_jobs_node,
    validate_job_search_input_node,
)
from app.ai.orchestration.schemas import JobMatchingInput, JobMatchingResult
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState
from app.ai.orchestration.workflows._runtime import (
    common_output_fields,
    initial_state,
    invalid_input_state,
    invoke_graph,
    resolve_services,
    route_failed,
    route_failed_or_empty_jobs,
)


def build_job_matching_graph(services: OrchestrationServices):
    graph = StateGraph(WorkflowState)
    graph.add_node("validate_input", partial(validate_job_search_input_node, services=services))
    graph.add_node("discover_jobs", partial(discover_jobs_node, services=services))
    graph.add_node("normalize_jobs", partial(normalize_discovered_jobs_node, services=services))
    graph.add_node("match_jobs", partial(match_discovered_jobs_node, services=services))
    graph.add_node("finish", partial(finish_job_matching_node, services=services))
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        route_failed,
        {"finish": "finish", "continue": "discover_jobs"},
    )
    graph.add_conditional_edges(
        "discover_jobs",
        route_failed,
        {"finish": "finish", "continue": "normalize_jobs"},
    )
    graph.add_conditional_edges(
        "normalize_jobs",
        route_failed_or_empty_jobs,
        {"finish": "finish", "continue": "match_jobs"},
    )
    graph.add_edge("match_jobs", "finish")
    graph.add_edge("finish", END)
    return graph.compile()


def match_jobs_workflow(
    input_data,
    *,
    services: OrchestrationServices | None = None,
    checkpoint_store=None,
) -> JobMatchingResult:
    """Discover, normalize, and rank jobs without persistence or invented listings."""
    dependencies = resolve_services(services, checkpoint_store)
    try:
        request = JobMatchingInput.model_validate(input_data)
    except (ValidationError, TypeError, ValueError):
        state = invalid_input_state(WorkflowType.JOB_MATCHING, dependencies)
        return JobMatchingResult(**common_output_fields(state))

    state = initial_state(WorkflowType.JOB_MATCHING, request, dependencies)
    final = invoke_graph(build_job_matching_graph(dependencies), state, dependencies)
    return JobMatchingResult(
        **common_output_fields(final),
        jobs=final["normalized_jobs"],
        matches=final["ranked_matches"],
    )
