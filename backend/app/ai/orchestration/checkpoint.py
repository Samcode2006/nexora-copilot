"""Allowlisted in-memory metadata checkpoints; never resumable graph state."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from threading import RLock

from pydantic import ConfigDict, Field

from app.ai.orchestration.errors import (
    StrictModel,
    WorkflowErrorCategory,
    WorkflowErrorCode,
    WorkflowStage,
    WorkflowStatus,
    WorkflowType,
)


class MetadataCheckpointRecord(StrictModel):
    """Only explicitly approved operational metadata can be stored here."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(min_length=1, max_length=64)
    workflow_type: WorkflowType
    current_stage: WorkflowStage
    status: WorkflowStatus
    completed_stages: tuple[WorkflowStage, ...] = ()
    error_categories: tuple[WorkflowErrorCategory, ...] = ()
    error_codes: tuple[WorkflowErrorCode, ...] = ()
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    input_item_count: int | None = Field(default=None, ge=0)
    output_item_count: int | None = Field(default=None, ge=0)


class InMemoryMetadataCheckpointStore:
    """Bounded, thread-safe metadata store that cannot resume graph execution."""

    def __init__(self, *, max_records: int = 1_000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be positive")
        self._max_records = max_records
        self._records: OrderedDict[str, MetadataCheckpointRecord] = OrderedDict()
        self._lock = RLock()

    def save(self, record: MetadataCheckpointRecord) -> MetadataCheckpointRecord:
        snapshot = MetadataCheckpointRecord.model_validate(record.model_dump())
        with self._lock:
            self._records.pop(snapshot.workflow_id, None)
            self._records[snapshot.workflow_id] = snapshot
            while len(self._records) > self._max_records:
                self._records.popitem(last=False)
        return snapshot.model_copy(deep=True)

    def get(self, workflow_id: str) -> MetadataCheckpointRecord | None:
        with self._lock:
            record = self._records.get(workflow_id)
            return record.model_copy(deep=True) if record is not None else None

    def cleanup(self, workflow_id: str) -> bool:
        """Remove one workflow's metadata; this does not affect graph state."""
        with self._lock:
            return self._records.pop(workflow_id, None) is not None

    def clear(self) -> int:
        """Remove all metadata and return the number of removed records."""
        with self._lock:
            removed = len(self._records)
            self._records.clear()
            return removed

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


_DEFAULT_CHECKPOINT_STORE = InMemoryMetadataCheckpointStore()


def default_checkpoint_store() -> InMemoryMetadataCheckpointStore:
    return _DEFAULT_CHECKPOINT_STORE
