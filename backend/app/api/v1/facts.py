"""Student-owned profile facts and their immutable revision history."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser
from app.core.errors import AppError
from app.db.repositories.student_data import FactInUseError, ProfileFactRepository
from app.db.session import DbSession
from app.schemas.student_data import (
    ConfirmFactsIn,
    ConfirmFactsOut,
    FactStatus,
    FactType,
    ProfileFactCreate,
    ProfileFactEdit,
    ProfileFactOut,
    ProfileFactRevisionOut,
)

router = APIRouter(prefix="/profile/facts", tags=["profile facts"])


def _student_id(user: CurrentUser) -> uuid.UUID:
    try:
        return uuid.UUID(user.id)
    except ValueError:
        raise AppError(401, "UNAUTHENTICATED", "The access token is invalid.") from None


@router.get("", response_model=list[ProfileFactOut])
async def list_facts(
    user: CurrentUser,
    db: DbSession,
    fact_type: Annotated[FactType | None, Query(alias="type")] = None,
    status: FactStatus | None = None,
) -> list[ProfileFactOut]:
    rows = await ProfileFactRepository(db).list_for_student(
        _student_id(user), fact_type=fact_type, status=status
    )
    return [ProfileFactOut.from_fact(row) for row in rows]


@router.post("", response_model=ProfileFactOut, status_code=201)
async def create_fact(
    body: ProfileFactCreate, user: CurrentUser, db: DbSession
) -> ProfileFactOut:
    if not body.data:
        raise AppError(422, "VALIDATION_ERROR", "Fact data must be a non-empty object.")
    fact = await ProfileFactRepository(db).create(
        _student_id(user), fact_type=body.type, data=body.data, source="student"
    )
    return ProfileFactOut.from_fact(fact)


@router.patch("/{fact_id}", response_model=ProfileFactOut)
async def edit_fact(
    fact_id: uuid.UUID, body: ProfileFactEdit, user: CurrentUser, db: DbSession
) -> ProfileFactOut:
    if not body.data:
        raise AppError(422, "VALIDATION_ERROR", "Fact data must be a non-empty object.")
    fact = await ProfileFactRepository(db).edit_data(_student_id(user), fact_id, body.data)
    if fact is None:
        raise AppError(404, "NOT_FOUND", "Profile fact was not found or is archived.")
    return ProfileFactOut.from_fact(fact)


@router.post("/{fact_id}/archive", response_model=ProfileFactOut)
async def archive_fact(
    fact_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ProfileFactOut:
    fact = await ProfileFactRepository(db).archive(_student_id(user), fact_id)
    if fact is None:
        raise AppError(404, "NOT_FOUND", "Profile fact was not found or is archived.")
    return ProfileFactOut.from_fact(fact)


@router.delete("/{fact_id}", status_code=204)
async def delete_fact(fact_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    try:
        deleted = await ProfileFactRepository(db).delete_uncited(_student_id(user), fact_id)
    except FactInUseError:
        raise AppError(409, "FACT_IN_USE", "A cited fact cannot be deleted; archive it instead.") from None
    if not deleted:
        raise AppError(404, "NOT_FOUND", "Profile fact was not found.")
    return Response(status_code=204)


@router.get("/{fact_id}/revisions", response_model=list[ProfileFactRevisionOut])
async def fact_revisions(
    fact_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> list[ProfileFactRevisionOut]:
    repository = ProfileFactRepository(db)
    if await repository.get(_student_id(user), fact_id) is None:
        raise AppError(404, "NOT_FOUND", "Profile fact was not found.")
    rows = await repository.revisions(_student_id(user), fact_id)
    return [ProfileFactRevisionOut.model_validate(row) for row in rows]


@router.post("/confirm", response_model=ConfirmFactsOut)
async def confirm_facts(
    body: ConfirmFactsIn, user: CurrentUser, db: DbSession
) -> ConfirmFactsOut:
    if len(body.fact_ids) != len(set(body.fact_ids)):
        raise AppError(422, "VALIDATION_ERROR", "fact_ids must not contain duplicates.")
    confirmed = await ProfileFactRepository(db).confirm_many(_student_id(user), body.fact_ids)
    return ConfirmFactsOut(confirmed=confirmed)
