"""API representations for consents, resume metadata, and background tasks."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ConsentOut(BaseModel):
    consent_type: str
    granted: bool
    granted_at: datetime | None
    withdrawn_at: datetime | None


class ConsentUpdate(BaseModel):
    granted: bool


FactType = Literal[
    "education", "skill", "project", "experience", "achievement", "certification"
]
FactStatus = Literal["pending_confirmation", "confirmed", "archived"]


class ProfileFactCreate(BaseModel):
    type: FactType
    data: dict[str, Any]


class ProfileFactEdit(BaseModel):
    data: dict[str, Any]


class ProfileFactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    type: FactType
    data: dict[str, Any]
    status: FactStatus
    source: Literal["student", "resume"]
    revision: int
    ever_cited: bool
    confidence: str | None
    source_ref: dict[str, Any] | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_fact(cls, fact: Any) -> "ProfileFactOut":
        return cls(
            id=fact.id,
            type=fact.fact_type,
            data=fact.data,
            status=fact.status,
            source=fact.source,
            revision=fact.revision,
            ever_cited=fact.ever_cited,
            confidence=fact.confidence,
            source_ref=fact.source_ref,
            archived_at=fact.archived_at,
            created_at=fact.created_at,
            updated_at=fact.updated_at,
        )


class ConfirmFactsIn(BaseModel):
    fact_ids: list[uuid.UUID]


class ConfirmFactsOut(BaseModel):
    confirmed: list[uuid.UUID]


class ProfileFactRevisionOut(BaseModel):
    revision: int
    data: dict[str, Any]
    created_at: datetime


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    extracted_fact_count: int | None = None
    created_at: datetime


class TaskOut(BaseModel):
    id: uuid.UUID
    kind: str
    status: str
    trigger: str
    resource: dict[str, Any]
    attempt: int
    retry_of: uuid.UUID | None
    error: dict[str, Any] | None
    timeout_seconds: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def task_out(task: Any) -> TaskOut:
    error_messages = {
        "AI_TIMEOUT": "Resume processing took too long. Upload the file again.",
        "PARSE_FAILED": "The resume could not be parsed. Check the file and upload again.",
        "CONSENT_REVOKED": "Resume processing consent was withdrawn before processing finished.",
        "INTERNAL_ERROR": "The resume could not be processed. Upload the file again.",
    }
    return TaskOut(
        id=task.id,
        kind=task.kind,
        status=task.status,
        trigger=task.trigger,
        resource={"type": task.resource_type, "id": task.resource_id},
        attempt=task.attempt,
        retry_of=task.retry_of,
        error=(
            {
                "code": task.error_code,
                "message": error_messages.get(task.error_code, "The task failed."),
                "retryable": task.retryable,
            }
            if task.error_code is not None
            else None
        ),
        timeout_seconds=task.timeout_seconds,
        created_at=task.created_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
    )


class ResumeUploadOut(BaseModel):
    resume: ResumeOut
    task: TaskOut


class TaskStatusQuery(BaseModel):
    status: Literal["queued", "running", "succeeded", "failed"] | None = None
    kind: str | None = None
