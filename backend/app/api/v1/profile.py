import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.core.errors import AppError
from app.core.security import unauthenticated
from app.db.models.profile import Profile
from app.db.repositories.profile import ProfileRepository
from app.db.session import DbSession
from app.schemas.profile import ProfileOut, ProfilePatch

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(user: CurrentUser, db: DbSession) -> Profile:
    """Return the caller's profile, creating an empty one on first use.

    The student id comes only from the verified token. RLS is a second layer.
    """
    try:
        uid = uuid.UUID(user.id)
    except ValueError:
        raise unauthenticated() from None

    return await ProfileRepository(db).get_or_create(uid, user.email)


@router.patch("/me", response_model=ProfileOut)
async def update_my_profile(
    body: ProfilePatch, user: CurrentUser, db: DbSession
) -> Profile:
    try:
        uid = uuid.UUID(user.id)
    except ValueError:
        raise unauthenticated() from None
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise AppError(422, "VALIDATION_ERROR", "At least one profile field is required.")
    profile = await ProfileRepository(db).update_fields(uid, fields)
    if profile is None:
        raise AppError(404, "NOT_FOUND", "Profile was not found.")
    return profile
