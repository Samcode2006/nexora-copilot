"""Consent, resume upload, and task endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.repositories.student_data import ConsentRepository, ResumeRepository, TaskRepository
from app.db.session import DbSession, get_sessionmaker, set_rls_identity
from app.schemas.student_data import (
    ConsentOut,
    ConsentUpdate,
    ResumeOut,
    ResumeUploadOut,
    TaskOut,
    task_out,
)
from app.services.resume_processing import run_resume_parse

router = APIRouter(tags=["student data"])
_CHUNK_BYTES = 64 * 1024


def _student_id(user: CurrentUser) -> uuid.UUID:
    try:
        return uuid.UUID(user.id)
    except ValueError:
        raise AppError(401, "UNAUTHENTICATED", "The access token is invalid.") from None


def _safe_filename(filename: str | None) -> str:
    normalized = (filename or "").replace("\\", "/")
    name = PurePosixPath(normalized).name
    name = "".join(char for char in name if char.isprintable() and char not in "\r\n\x00")
    name = name.strip().strip(".")[:255]
    if not name:
        raise AppError(422, "VALIDATION_ERROR", "A valid filename is required.")
    return name


async def _background_parse(
    user_id: str,
    task_id: uuid.UUID,
    resume_id: uuid.UUID,
    filename: str,
    content: bytes,
) -> None:
    async with get_sessionmaker()() as session:
        await set_rls_identity(session, user_id)
        await run_resume_parse(
            session=session,
            student_id=uuid.UUID(user_id),
            task_id=task_id,
            resume_id=resume_id,
            content=content,
            filename=filename,
        )


@router.get("/profile/me/consents", response_model=list[ConsentOut])
async def list_consents(user: CurrentUser, db: DbSession) -> list[ConsentOut]:
    rows = await ConsentRepository(db).list_for_student(_student_id(user))
    return [
        ConsentOut(
            consent_type=row.consent_type,
            granted=row.granted_at is not None and row.withdrawn_at is None,
            granted_at=row.granted_at,
            withdrawn_at=row.withdrawn_at,
        )
        for row in rows
    ]


@router.put("/profile/me/consents/{consent_type}", response_model=ConsentOut)
async def update_consent(
    consent_type: str,
    body: ConsentUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ConsentOut:
    if consent_type != "resume_processing":
        raise AppError(422, "VALIDATION_ERROR", "This consent type is not available.")
    repo = ConsentRepository(db)
    if body.granted:
        row = await repo.grant(_student_id(user))
    else:
        row = await repo.withdraw(_student_id(user)) or await repo.get(
            _student_id(user), "resume_processing"
        )
    if row is None:
        raise AppError(404, "NOT_FOUND", "Consent record was not found.")
    return ConsentOut(
        consent_type=row.consent_type,
        granted=row.granted_at is not None and row.withdrawn_at is None,
        granted_at=row.granted_at,
        withdrawn_at=row.withdrawn_at,
    )


@router.post("/resumes", response_model=ResumeUploadOut, status_code=202)
async def upload_resume(
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File()],
) -> ResumeUploadOut:
    settings = get_settings()
    student_id = _student_id(user)
    consent = await ConsentRepository(db).get(student_id, "resume_processing")
    if consent is None or consent.granted_at is None or consent.withdrawn_at is not None:
        raise AppError(
            403,
            "CONSENT_REQUIRED",
            "Grant resume processing consent before uploading a resume.",
            [{"consent_type": "resume_processing"}],
        )

    filename = _safe_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
    if extension not in {"pdf", "docx"}:
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Upload a PDF or DOCX resume.")

    content = bytearray()
    while chunk := await file.read(_CHUNK_BYTES):
        content.extend(chunk)
        if len(content) > settings.resume_max_bytes:
            raise AppError(413, "PAYLOAD_TOO_LARGE", "The resume exceeds the 5 MiB limit.")
    raw = bytes(content)
    if (extension == "pdf" and not raw.startswith(b"%PDF-")) or (
        extension == "docx" and not raw.startswith(b"PK")
    ):
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "The file content does not match PDF or DOCX.")

    repo = TaskRepository(db)
    await repo.lock_resume_parse_admission()
    since = datetime.now(UTC) - timedelta(hours=1)
    parses = await repo.count_since(
        student_id, kind="resume_parse", trigger="explicit", since=since
    )
    if parses >= settings.rate_limit_resume_parses_per_hour:
        raise AppError(
            429,
            "RATE_LIMITED",
            "The resume parsing hourly limit was reached.",
            [{"limit": "resume_parses_per_hour"}],
            headers={"Retry-After": "3600"},
        )
    media_type = (
        "application/pdf"
        if extension == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    resume = await ResumeRepository(db).create(
        student_id,
        filename=filename,
        content_type=media_type,
        size_bytes=len(raw),
    )
    task = await repo.create(
        student_id,
        kind="resume_parse",
        resource_type="resume",
        resource_id=resume.id,
        timeout_seconds=settings.task_timeout_resume_parse_seconds,
    )
    background.add_task(
        _background_parse,
        user.id,
        task.id,
        resume.id,
        filename,
        raw,
    )
    return ResumeUploadOut(resume=resume, task=task_out(task))


@router.get("/resumes", response_model=list[ResumeOut])
async def list_resumes(user: CurrentUser, db: DbSession) -> list[ResumeOut]:
    return await ResumeRepository(db).list_for_student(_student_id(user))


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: uuid.UUID, user: CurrentUser, db: DbSession) -> ResumeOut:
    resume = await ResumeRepository(db).get(_student_id(user), resume_id)
    if resume is None:
        raise AppError(404, "NOT_FOUND", "Resume was not found.")
    return resume


@router.delete("/resumes/{resume_id}", status_code=204)
async def delete_resume(resume_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    student_id = _student_id(user)
    if await TaskRepository(db).has_live_resource(
        student_id, kind="resume_parse", resource_id=resume_id
    ):
        raise AppError(409, "TASK_IN_PROGRESS", "The resume cannot be deleted while it is processing.")
    if not await ResumeRepository(db).delete(student_id, resume_id):
        raise AppError(404, "NOT_FOUND", "Resume was not found.")


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    user: CurrentUser,
    db: DbSession,
    status: Literal["queued", "running", "succeeded", "failed"] | None = Query(default=None),
    kind: str | None = Query(default=None),
) -> list[TaskOut]:
    rows = await TaskRepository(db).list_for_student(
        _student_id(user), status=status, kind=kind
    )
    return [task_out(row) for row in rows]


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, user: CurrentUser, db: DbSession) -> TaskOut:
    task = await TaskRepository(db).get(_student_id(user), task_id)
    if task is None:
        raise AppError(404, "NOT_FOUND", "Task was not found.")
    return task_out(task)
