"""Sanitized stage transitions shared by independently testable nodes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.ai.orchestration.checkpoint import MetadataCheckpointRecord
from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowIssue,
    WorkflowStage,
    WorkflowStatus,
)
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState


def utcnow() -> datetime:
    return datetime.now(UTC)


def _save_metadata(
    state: WorkflowState,
    services: OrchestrationServices,
    *,
    stage: WorkflowStage,
    status: WorkflowStatus,
    completed_stages: Iterable[WorkflowStage],
    errors: Iterable[WorkflowIssue],
    completed_at: datetime | None = None,
    input_item_count: int | None = None,
    output_item_count: int | None = None,
) -> None:
    issues = tuple(errors)
    record = MetadataCheckpointRecord(
        workflow_id=state["workflow_id"],
        workflow_type=state["workflow_type"],
        current_stage=stage,
        status=status,
        completed_stages=tuple(completed_stages),
        error_categories=tuple(dict.fromkeys(issue.category for issue in issues)),
        error_codes=tuple(dict.fromkeys(issue.code for issue in issues)),
        started_at=state["started_at"],
        updated_at=utcnow(),
        completed_at=completed_at,
        input_item_count=input_item_count,
        output_item_count=output_item_count,
    )
    services.checkpoint_store.save(record)


def begin_stage(
    state: WorkflowState,
    services: OrchestrationServices,
    stage: WorkflowStage,
    *,
    input_item_count: int | None = None,
) -> None:
    _save_metadata(
        state,
        services,
        stage=stage,
        status=state["status"],
        completed_stages=state["completed_stages"],
        errors=state["errors"],
        input_item_count=input_item_count,
    )


def complete_stage(
    state: WorkflowState,
    services: OrchestrationServices,
    stage: WorkflowStage,
    *,
    updates: dict[str, Any] | None = None,
    input_item_count: int | None = None,
    output_item_count: int | None = None,
) -> dict[str, Any]:
    changes = dict(updates or {})
    completed = list(changes.get("completed_stages", state["completed_stages"]))
    if stage not in completed:
        completed.append(stage)
    changes["current_stage"] = stage
    changes["completed_stages"] = completed
    merged_status = changes.get("status", state["status"])
    merged_errors = changes.get("errors", state["errors"])
    merged_completed_at = changes.get("completed_at", state["completed_at"])
    _save_metadata(
        state,
        services,
        stage=stage,
        status=merged_status,
        completed_stages=completed,
        errors=merged_errors,
        completed_at=merged_completed_at,
        input_item_count=input_item_count,
        output_item_count=output_item_count,
    )
    return changes


def failed_stage(
    state: WorkflowState,
    services: OrchestrationServices,
    stage: WorkflowStage,
    exc: Exception,
    *,
    expected_code: WorkflowErrorCode,
    expected_exceptions: tuple[type[BaseException], ...],
    input_item_count: int | None = None,
) -> dict[str, Any]:
    from app.ai.orchestration.errors import make_issue

    code = (
        expected_code
        if isinstance(exc, expected_exceptions)
        else WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR
    )
    issues = [*state["errors"], make_issue(code)]
    return complete_stage(
        state,
        services,
        stage,
        updates={"errors": issues, "status": WorkflowStatus.FAILED},
        input_item_count=input_item_count,
    )


def terminal_stage(
    state: WorkflowState,
    services: OrchestrationServices,
    *,
    status: WorkflowStatus | None = None,
    output_item_count: int | None = None,
) -> dict[str, Any]:
    final_status = status or state["status"]
    if final_status == WorkflowStatus.RUNNING:
        final_status = WorkflowStatus.SUCCEEDED
    completed_at = utcnow()
    return complete_stage(
        state,
        services,
        WorkflowStage.COMPLETE,
        updates={"status": final_status, "completed_at": completed_at},
        output_item_count=output_item_count,
    )
