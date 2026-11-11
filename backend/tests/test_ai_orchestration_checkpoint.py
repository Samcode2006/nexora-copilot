from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.ai.orchestration.checkpoint import (
    InMemoryMetadataCheckpointStore,
    MetadataCheckpointRecord,
)
from app.ai.orchestration.errors import WorkflowStage, WorkflowStatus, WorkflowType


def _record(workflow_id: str) -> MetadataCheckpointRecord:
    now = datetime.now(UTC)
    return MetadataCheckpointRecord(
        workflow_id=workflow_id,
        workflow_type=WorkflowType.JOB_MATCHING,
        current_stage=WorkflowStage.COMPLETE,
        status=WorkflowStatus.SUCCEEDED,
        started_at=now,
        updated_at=now,
        completed_at=now,
        input_item_count=1,
        output_item_count=2,
    )


def test_checkpoint_allowlist_rejects_runtime_payload_fields() -> None:
    payload = _record("wf-allowlist").model_dump()
    payload["raw_resume_bytes"] = b"private"
    payload["student_profile"] = {"email": "private@example.test"}

    with pytest.raises(ValidationError):
        MetadataCheckpointRecord.model_validate(payload)


def test_checkpoint_cleanup_removes_metadata() -> None:
    store = InMemoryMetadataCheckpointStore()
    store.save(_record("wf-cleanup"))

    assert store.cleanup("wf-cleanup") is True
    assert store.get("wf-cleanup") is None
    assert store.cleanup("wf-cleanup") is False


def test_checkpoint_store_is_bounded_and_evicts_oldest_record() -> None:
    store = InMemoryMetadataCheckpointStore(max_records=2)
    store.save(_record("wf-1"))
    store.save(_record("wf-2"))
    store.save(_record("wf-3"))

    assert len(store) == 2
    assert store.get("wf-1") is None
    assert store.get("wf-2") is not None
    assert store.get("wf-3") is not None


def test_checkpoint_copy_does_not_expose_mutable_store_record() -> None:
    store = InMemoryMetadataCheckpointStore()
    saved = store.save(_record("wf-copy"))
    copy = store.get("wf-copy")

    assert saved is not None and copy is not None
    assert saved is not copy
    assert copy.workflow_id == "wf-copy"
