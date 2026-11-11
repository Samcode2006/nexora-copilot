"""Repositories for consent, resume metadata, facts and background tasks."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import case, delete, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student_data import (
    ProfileConsent,
    ProfileFact,
    ProfileFactRevision,
    Resume,
    Task,
)


class FactInUseError(ValueError):
    """Raised when a fact has already been referenced by evidence."""


class ConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_student(self, student_id: uuid.UUID) -> list[ProfileConsent]:
        result = await self._session.execute(
            select(ProfileConsent)
            .where(ProfileConsent.student_id == student_id)
            .order_by(ProfileConsent.consent_type)
        )
        return list(result.scalars().all())

    async def get(
        self, student_id: uuid.UUID, consent_type: Literal["resume_processing"]
    ) -> ProfileConsent | None:
        result = await self._session.execute(
            select(ProfileConsent).where(
                ProfileConsent.student_id == student_id,
                ProfileConsent.consent_type == consent_type,
            )
        )
        return result.scalar_one_or_none()

    async def grant(self, student_id: uuid.UUID) -> ProfileConsent:
        now = func.now()
        stmt = pg_insert(ProfileConsent).values(
            student_id=student_id,
            consent_type="resume_processing",
            granted_at=now,
            withdrawn_at=None,
        )
        # Use the existing grant time when consent is still active; a re-grant
        # after withdrawal starts a new current consent period.
        stmt = stmt.on_conflict_do_update(
            index_elements=[ProfileConsent.student_id, ProfileConsent.consent_type],
            set_={
                "granted_at": case(
                    (ProfileConsent.withdrawn_at.is_not(None), now),
                    else_=ProfileConsent.granted_at,
                ),
                "withdrawn_at": None,
            },
        ).returning(ProfileConsent).execution_options(populate_existing=True)
        return (await self._session.execute(stmt)).scalar_one()

    async def withdraw(self, student_id: uuid.UUID) -> ProfileConsent | None:
        result = await self._session.execute(
            update(ProfileConsent)
            .where(
                ProfileConsent.student_id == student_id,
                ProfileConsent.consent_type == "resume_processing",
                ProfileConsent.granted_at.is_not(None),
                ProfileConsent.withdrawn_at.is_(None),
            )
            .values(withdrawn_at=func.now())
            .returning(ProfileConsent)
        )
        return result.scalar_one_or_none()


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        student_id: uuid.UUID,
        *,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> Resume:
        result = await self._session.execute(
            insert(Resume)
            .values(
                id=uuid.uuid4(),
                student_id=student_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
            )
            .returning(Resume)
        )
        return result.scalar_one()

    async def get(self, student_id: uuid.UUID, resume_id: uuid.UUID) -> Resume | None:
        result = await self._session.execute(
            select(Resume).where(Resume.student_id == student_id, Resume.id == resume_id)
        )
        return result.scalar_one_or_none()

    async def list_for_student(self, student_id: uuid.UUID) -> list[Resume]:
        result = await self._session.execute(
            select(Resume)
            .where(Resume.student_id == student_id)
            .order_by(Resume.created_at.desc(), Resume.id)
        )
        return list(result.scalars().all())

    async def delete(self, student_id: uuid.UUID, resume_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Resume)
            .where(Resume.student_id == student_id, Resume.id == resume_id)
            .returning(Resume.id)
        )
        return result.scalar_one_or_none() is not None


class ProfileFactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        student_id: uuid.UUID,
        *,
        fact_type: str,
        data: dict[str, Any],
        source: Literal["student", "resume"],
        confidence: str | None = None,
        source_ref: dict[str, Any] | None = None,
    ) -> ProfileFact:
        result = await self._session.execute(
            insert(ProfileFact)
            .values(
                id=uuid.uuid4(),
                student_id=student_id,
                fact_type=fact_type,
                data=data,
                status="confirmed" if source == "student" else "pending_confirmation",
                source=source,
                confidence=confidence,
                source_ref=source_ref,
            )
            .returning(ProfileFact)
        )
        # The database trigger writes revision 1 in this transaction.
        return result.scalar_one()

    async def get(self, student_id: uuid.UUID, fact_id: uuid.UUID) -> ProfileFact | None:
        result = await self._session.execute(
            select(ProfileFact).where(ProfileFact.student_id == student_id, ProfileFact.id == fact_id)
        )
        return result.scalar_one_or_none()

    async def list_for_student(
        self,
        student_id: uuid.UUID,
        *,
        fact_type: str | None = None,
        status: str | None = None,
    ) -> list[ProfileFact]:
        statement = select(ProfileFact).where(ProfileFact.student_id == student_id)
        if fact_type is not None:
            statement = statement.where(ProfileFact.fact_type == fact_type)
        if status is not None:
            statement = statement.where(ProfileFact.status == status)
        else:
            statement = statement.where(ProfileFact.status != "archived")
        result = await self._session.execute(
            statement.order_by(ProfileFact.updated_at.desc(), ProfileFact.id)
        )
        return list(result.scalars().all())

    async def edit_data(
        self, student_id: uuid.UUID, fact_id: uuid.UUID, data: dict[str, Any]
    ) -> ProfileFact | None:
        result = await self._session.execute(
            update(ProfileFact)
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.id == fact_id,
                ProfileFact.status != "archived",
            )
            .values(data=data, revision=ProfileFact.revision + 1, updated_at=func.now())
            .returning(ProfileFact)
        )
        return result.scalar_one_or_none()

    async def confirm_many(
        self, student_id: uuid.UUID, fact_ids: list[uuid.UUID]
    ) -> list[uuid.UUID]:
        if not fact_ids:
            return []
        result = await self._session.execute(
            update(ProfileFact)
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.id.in_(set(fact_ids)),
                ProfileFact.status == "pending_confirmation",
            )
            .values(
                status="confirmed",
                revision=ProfileFact.revision + 1,
                updated_at=func.now(),
            )
            .returning(ProfileFact.id)
        )
        return list(result.scalars().all())

    async def archive(self, student_id: uuid.UUID, fact_id: uuid.UUID) -> ProfileFact | None:
        result = await self._session.execute(
            update(ProfileFact)
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.id == fact_id,
                ProfileFact.status != "archived",
            )
            .values(
                status="archived",
                archived_at=func.now(),
                revision=ProfileFact.revision + 1,
                updated_at=func.now(),
            )
            .returning(ProfileFact)
        )
        return result.scalar_one_or_none()

    async def mark_cited(self, student_id: uuid.UUID, fact_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(ProfileFact)
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.id == fact_id,
                ProfileFact.ever_cited.is_(False),
            )
            .values(ever_cited=True)
            .returning(ProfileFact.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete_uncited(self, student_id: uuid.UUID, fact_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(ProfileFact)
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.id == fact_id,
                ProfileFact.ever_cited.is_(False),
            )
            .returning(ProfileFact.id)
        )
        if result.scalar_one_or_none() is not None:
            return True
        fact = await self.get(student_id, fact_id)
        if fact is not None and fact.ever_cited:
            raise FactInUseError("A cited profile fact cannot be deleted.")
        return False

    async def revisions(
        self, student_id: uuid.UUID, fact_id: uuid.UUID
    ) -> list[ProfileFactRevision]:
        result = await self._session.execute(
            select(ProfileFactRevision)
            .where(
                ProfileFactRevision.student_id == student_id,
                ProfileFactRevision.fact_id == fact_id,
            )
            .order_by(ProfileFactRevision.revision)
        )
        return list(result.scalars().all())


class TaskRepository:
    LIVE_STATES = ("queued", "running")

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_resume_parse_admission(self) -> None:
        """Serialize rate/capacity checks through the enclosing request transaction."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('nexora:resume-parse-admission'))")
        )

    async def create(
        self,
        student_id: uuid.UUID,
        *,
        kind: str,
        resource_type: str,
        resource_id: uuid.UUID,
        timeout_seconds: int,
        trigger: Literal["explicit", "automatic"] = "explicit",
        retry_of: uuid.UUID | None = None,
        attempt: int = 1,
    ) -> Task:
        result = await self._session.execute(
            insert(Task)
            .values(
                id=uuid.uuid4(),
                student_id=student_id,
                kind=kind,
                status="queued",
                trigger=trigger,
                retry_of=retry_of,
                attempt=attempt,
                resource_type=resource_type,
                resource_id=resource_id,
                timeout_seconds=timeout_seconds,
            )
            .returning(Task)
        )
        return result.scalar_one()

    async def get(self, student_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        result = await self._session.execute(
            select(Task).where(Task.student_id == student_id, Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_for_student(
        self,
        student_id: uuid.UUID,
        *,
        status: str | None = None,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[Task]:
        statement = select(Task).where(Task.student_id == student_id)
        if status is not None:
            statement = statement.where(Task.status == status)
        if kind is not None:
            statement = statement.where(Task.kind == kind)
        result = await self._session.execute(
            statement.order_by(Task.created_at.desc(), Task.id).limit(min(max(limit, 1), 100))
        )
        return list(result.scalars().all())

    async def count_since(
        self,
        student_id: uuid.UUID,
        *,
        kind: str,
        trigger: str | None,
        since: datetime,
    ) -> int:
        statement = select(func.count()).select_from(Task).where(
            Task.student_id == student_id,
            Task.kind == kind,
            Task.created_at >= since,
        )
        if trigger is not None:
            statement = statement.where(Task.trigger == trigger)
        return int((await self._session.execute(statement)).scalar_one())

    async def count_live_for_student(self, student_id: uuid.UUID, *, kind: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Task).where(
                Task.student_id == student_id,
                Task.kind == kind,
                Task.status.in_(self.LIVE_STATES),
            )
        )
        return int(result.scalar_one())

    async def count_live(self, *, kind: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Task).where(
                Task.kind == kind,
                Task.status.in_(self.LIVE_STATES),
            )
        )
        return int(result.scalar_one())

    async def has_live_resource(
        self, student_id: uuid.UUID, *, kind: str, resource_id: uuid.UUID
    ) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(Task).where(
                Task.student_id == student_id,
                Task.kind == kind,
                Task.resource_id == resource_id,
                Task.status.in_(self.LIVE_STATES),
            )
        )
        return bool(result.scalar_one())

    async def start(self, student_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        result = await self._session.execute(
            update(Task)
            .where(
                Task.student_id == student_id,
                Task.id == task_id,
                Task.status == "queued",
            )
            .values(status="running", started_at=func.now())
            .returning(Task)
        )
        return result.scalar_one_or_none()

    async def succeed(self, student_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        result = await self._session.execute(
            update(Task)
            .where(
                Task.student_id == student_id,
                Task.id == task_id,
                Task.status == "running",
            )
            .values(status="succeeded", finished_at=func.now())
            .returning(Task)
        )
        return result.scalar_one_or_none()

    async def fail(
        self,
        student_id: uuid.UUID,
        task_id: uuid.UUID,
        *,
        error_code: str,
        retryable: bool,
    ) -> Task | None:
        result = await self._session.execute(
            update(Task)
            .where(
                Task.student_id == student_id,
                Task.id == task_id,
                Task.status.in_(self.LIVE_STATES),
            )
            .values(
                status="failed",
                error_code=error_code,
                retryable=retryable,
                finished_at=func.now(),
            )
            .returning(Task)
        )
        return result.scalar_one_or_none()

    async def retry(self, student_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        previous = await self.get(student_id, task_id)
        if previous is None or previous.status != "failed" or previous.retryable is not True:
            return None
        return await self.create(
            student_id,
            kind=previous.kind,
            resource_type=previous.resource_type,
            resource_id=previous.resource_id,
            timeout_seconds=previous.timeout_seconds,
            trigger=previous.trigger,  # type: ignore[arg-type]
            retry_of=previous.id,
            attempt=previous.attempt + 1,
        )
