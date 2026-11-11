"""In-memory resume processing and persistence orchestration."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.resume_intelligence import ResumeParseError, extract_student_profile, parse_resume
from app.core.config import Settings, get_settings
from app.db.repositories.student_data import (
    ConsentRepository,
    ProfileFactRepository,
    TaskRepository,
)
from app.db.session import set_rls_identity


def _evidence(value: Any) -> list[Any]:
    """Collect evidence models recursively for provenance and confidence."""
    if hasattr(value, "source_text") and hasattr(value, "value"):
        return [value]
    if isinstance(value, BaseModel):
        return [item for name in type(value).model_fields for item in _evidence(getattr(value, name))]
    if isinstance(value, list):
        return [item for child in value for item in _evidence(child)]
    return []


def _plain(value: Any) -> Any:
    if hasattr(value, "source_text") and hasattr(value, "value"):
        return value.value
    if isinstance(value, BaseModel):
        return {name: _plain(getattr(value, name)) for name in type(value).model_fields}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _fact_drafts(profile: Any, resume_id: uuid.UUID) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    groups = (
        ("education", "education"),
        ("skills", "skill"),
        ("projects", "project"),
        ("experience", "experience"),
        ("internships", "experience"),
        ("certifications", "certification"),
        ("awards", "achievement"),
        ("achievements", "achievement"),
    )
    for field, fact_type in groups:
        value = getattr(profile, field)
        items = [value] if field == "skills" else value
        for item in items:
            evidence = _evidence(item)
            if not evidence:
                continue
            excerpts = list(dict.fromkeys(str(entry.source_text) for entry in evidence if entry.source_text))
            confidence = "high" if all(entry.confidence == "high" for entry in evidence) else "low"
            drafts.append(
                {
                    "fact_type": fact_type,
                    "data": _plain(item),
                    "confidence": confidence,
                    "source_ref": {
                        "resume_id": str(resume_id),
                        "page": None,
                        "excerpt": "\n".join(excerpts)[:4000],
                    },
                }
            )
    return drafts


async def run_resume_parse(
    *,
    session: AsyncSession,
    student_id: uuid.UUID,
    task_id: uuid.UUID,
    resume_id: uuid.UUID,
    content: bytes,
    filename: str,
    settings: Settings | None = None,
) -> None:
    """Run one parse task; results and success CAS share one transaction."""
    settings = settings or get_settings()
    tasks = TaskRepository(session)
    consent = await ConsentRepository(session).get(student_id, "resume_processing")
    if consent is None or consent.granted_at is None or consent.withdrawn_at is not None:
        await tasks.fail(student_id, task_id, error_code="CONSENT_REVOKED", retryable=False)
        await session.commit()
        return
    started = await tasks.start(student_id, task_id)
    if started is None:
        return
    await session.commit()

    try:
        async with asyncio.timeout(started.timeout_seconds):
            parsed = await run_in_threadpool(
                parse_resume,
                content,
                filename,
                max_file_bytes=settings.resume_max_bytes,
            )
            profile = await run_in_threadpool(extract_student_profile, parsed.text)
            drafts = _fact_drafts(profile, resume_id)
        async with session.begin():
            await set_rls_identity(session, str(student_id))
            consent = await ConsentRepository(session).get(student_id, "resume_processing")
            if consent is None or consent.granted_at is None or consent.withdrawn_at is not None:
                await TaskRepository(session).fail(
                    student_id, task_id, error_code="CONSENT_REVOKED", retryable=False
                )
                return
            facts = ProfileFactRepository(session)
            for draft in drafts:
                await facts.create(student_id, source="resume", **draft)
            finished = await TaskRepository(session).succeed(student_id, task_id)
            if finished is None:
                raise RuntimeError("Resume parse task was no longer running at completion.")
    except TimeoutError:
        await session.rollback()
        async with session.begin():
            await set_rls_identity(session, str(student_id))
            await TaskRepository(session).fail(
                student_id, task_id, error_code="AI_TIMEOUT", retryable=False
            )
    except ResumeParseError:
        await session.rollback()
        async with session.begin():
            await set_rls_identity(session, str(student_id))
            await TaskRepository(session).fail(
                student_id, task_id, error_code="PARSE_FAILED", retryable=False
            )
    except Exception:
        await session.rollback()
        async with session.begin():
            await set_rls_identity(session, str(student_id))
            await TaskRepository(session).fail(
                student_id, task_id, error_code="INTERNAL_ERROR", retryable=False
            )
        raise

