"""Profile reads and writes scoped to the verified student's identifier."""

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.profile import Profile

EDITABLE_FIELDS = frozenset(
    {"full_name", "batch_year", "cgpa", "backlogs", "branch", "eligible_locations"}
)


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, student_id: uuid.UUID) -> Profile | None:
        result = await self._session.execute(select(Profile).where(Profile.id == student_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, student_id: uuid.UUID, email: str | None) -> Profile:
        await self._session.execute(
            pg_insert(Profile)
            .values(id=student_id, email=email)
            .on_conflict_do_nothing(index_elements=[Profile.id])
        )
        profile = await self.get(student_id)
        if profile is None:  # Defensive: RLS/foreign-key issues must not look like a blank profile.
            raise RuntimeError("Profile upsert completed without a visible profile row.")
        return profile

    async def update_fields(
        self, student_id: uuid.UUID, fields: Mapping[str, Any]
    ) -> Profile | None:
        unknown = set(fields) - EDITABLE_FIELDS
        if unknown:
            raise ValueError(f"Unsupported profile fields: {', '.join(sorted(unknown))}")
        if not fields:
            return await self.get(student_id)

        result = await self._session.execute(
            update(Profile)
            .where(Profile.id == student_id)
            .values(**fields, updated_at=func.now())
            .returning(Profile)
        )
        return result.scalar_one_or_none()
