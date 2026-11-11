import uuid

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.api.deps import CurrentUser
from app.core.security import unauthenticated
from app.db.models.profile import Profile
from app.db.session import DbSession
from app.schemas.profile import ProfileOut

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

    await db.execute(
        pg_insert(Profile)
        .values(id=uid, email=user.email)
        .on_conflict_do_nothing(index_elements=[Profile.id])
    )
    return (await db.execute(select(Profile).where(Profile.id == uid))).scalar_one()
