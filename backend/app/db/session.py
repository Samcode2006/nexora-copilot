import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.db.url import prepare_async_url


@lru_cache
def get_engine() -> AsyncEngine:
    url, connect_args = prepare_async_url(get_settings().database_url)
    return create_async_engine(
        url,
        connect_args=connect_args,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def set_rls_identity(session: AsyncSession, user_id: str) -> None:
    """Expose the verified user to Postgres for RLS. `true` = local to this transaction."""
    claims = json.dumps({"sub": user_id, "role": "authenticated"})
    await session.execute(
        text(
            "SELECT set_config('request.jwt.claim.sub', :sub, true),"
            " set_config('request.jwt.claims', :claims, true)"
        ),
        {"sub": user_id, "claims": claims},
    )


async def get_db(user: CurrentUser) -> AsyncIterator[AsyncSession]:
    """Per-request transaction scoped to the authenticated student (commit/rollback automatic)."""
    async with get_sessionmaker()() as session, session.begin():
        await set_rls_identity(session, user.id)
        yield session


async def get_db_anonymous() -> AsyncIterator[AsyncSession]:
    """For unauthenticated infrastructure checks only. Never use for student data."""
    async with get_sessionmaker()() as session, session.begin():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
AnonDbSession = Annotated[AsyncSession, Depends(get_db_anonymous)]
