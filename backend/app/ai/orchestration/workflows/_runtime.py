"""Shared invocation helpers. No graph state is persisted or returned to the store."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from app.ai.orchestration.checkpoint import MetadataCheckpointRecord
from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStage,
    WorkflowStatus,
    WorkflowType,
    make_issue,
)
from app.ai.orchestration.nodes._shared import complete_stage, terminal_stage
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState


def resolve_services(
    services: OrchestrationServices | None,
    checkpoint_store=None,
) -> OrchestrationServices:
    resolved = services or OrchestrationServices()
    if checkpoint_store is not None:
        resolved = replace(resolved, checkpoint_store=checkpoint_store)
    return resolved


def initial_state(
    workflow_type: WorkflowType,
    runtime_input,
    services: OrchestrationServices,
) -> WorkflowState:
    now = datetime.now(UTC)
    workflow_id = str(uuid4())
    state: WorkflowState = {
        "workflow_id": workflow_id,
        "workflow_type": workflow_type,
        "status": WorkflowStatus.RUNNING,
        "current_stage": WorkflowStage.INPUT_VALIDATION,
        "started_at": now,
        "completed_at": None,
        "runtime_input": runtime_input,
        "raw_resume_bytes": None,
        "parsed_resume": None,
        "student_profile": None,
        "search_criteria": None,
        "discovered_jobs": [],
        "normalized_jobs": [],
        "ranked_matches": [],
        "selected_job": None,
        "selected_jobs": [],
        "job_matches": {},
        "tailoring_preferences": None,
        "tailoring_outcomes": [],
        "interview_questions": [],
        "answer_evaluation": None,
        "errors": [],
        "completed_stages": [],
        "partial_success": None,
    }
    services.checkpoint_store.save(
        MetadataCheckpointRecord(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            current_stage=WorkflowStage.INPUT_VALIDATION,
            status=WorkflowStatus.RUNNING,
            started_at=now,
            updated_at=now,
        )
    )
    return state


def invalid_input_state(
    workflow_type: WorkflowType,
    services: OrchestrationServices,
) -> WorkflowState:
    state = initial_state(workflow_type, None, services)
    issue = make_issue(WorkflowErrorCode.INVALID_INPUT)
    changes = complete_stage(
        state,
        services,
        WorkflowStage.INPUT_VALIDATION,
        updates={"errors": [issue], "status": WorkflowStatus.FAILED},
    )
    state.update(changes)
    changes = terminal_stage(state, services, status=WorkflowStatus.FAILED)
    state.update(changes)
    return state


def route_failed(state: WorkflowState) -> str:
    return "finish" if state["status"] == WorkflowStatus.FAILED else "continue"


def route_failed_or_empty_jobs(state: WorkflowState) -> str:
    if state["status"] == WorkflowStatus.FAILED or not state["normalized_jobs"]:
        return "finish"
    return "continue"


def invoke_graph(graph, state: WorkflowState, services: OrchestrationServices) -> WorkflowState:
    try:
        return graph.invoke(state)
    except Exception:  # noqa: BLE001 - prevent internal exception details from escaping the workflow.
        issue = make_issue(WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR)
        state["errors"] = [*state["errors"], issue]
        state["status"] = WorkflowStatus.FAILED
        state.update(terminal_stage(state, services, status=WorkflowStatus.FAILED))
        return state


def common_output_fields(state: WorkflowState) -> dict:
    return {
        "workflow_id": state["workflow_id"],
        "status": state["status"],
        "completed_stages": state["completed_stages"],
        "errors": state["errors"],
        "partial_success": state["partial_success"],
    }
