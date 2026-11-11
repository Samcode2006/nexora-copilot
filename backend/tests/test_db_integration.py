"""Real-database tests. Opt in with RUN_DB_TESTS=1 (needs DATABASE_URL + MIGRATION_DATABASE_URL
in the environment/.env and `alembic upgrade head` applied). Creates and removes two throwaway
auth users. Never prints connection strings.
"""
import os
import time
import uuid

import jwt
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_token_verifier
from app.core.config import get_settings
from app.core.security import TokenVerifier
from app.db import session as db_session
from app.db.session import set_rls_identity
from app.db.url import prepare_async_url

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 (with DATABASE_URL and MIGRATION_DATABASE_URL) to run DB tests.",
)

SECRET = "db-test-hs256-secret-with-at-least-32-bytes!"


def _engine(raw: str):
    url, args = prepare_async_url(raw)
    return create_async_engine(url, connect_args=args, poolclass=NullPool)


@pytest.fixture
async def users():
    s = get_settings()
    assert s.migration_database_url, "MIGRATION_DATABASE_URL required for DB tests"
    a, b = uuid.uuid4(), uuid.uuid4()
    owner = _engine(s.migration_database_url)
    async with owner.begin() as c:
        for uid in (a, b):
            await c.execute(
                text("INSERT INTO auth.users (id, email) VALUES (:id, :e)"),
                {"id": uid, "e": f"{uid}@test.invalid"},
            )
    yield a, b
    async with owner.begin() as c:
        await c.execute(text("DELETE FROM auth.users WHERE id IN (:a, :b)"), {"a": a, "b": b})
    await owner.dispose()


@pytest.fixture
def app_sessionmaker(monkeypatch):
    engine = _engine(get_settings().database_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db_session, "get_sessionmaker", lambda: maker)
    return maker


def _token(uid: uuid.UUID) -> str:
    s = get_settings()
    return jwt.encode(
        {
            "sub": str(uid),
            "email": f"{uid}@test.invalid",
            "aud": s.supabase_jwt_audience,
            "iss": s.jwt_issuer,
            "exp": int(time.time()) + 300,
        },
        SECRET,
        algorithm="HS256",
    )


async def test_app_role_is_restricted(app_sessionmaker):
    async with app_sessionmaker() as s:
        row = (
            await s.execute(
                text(
                    "SELECT current_user, rolsuper, rolbypassrls FROM pg_roles "
                    "WHERE rolname = current_user"
                )
            )
        ).one()
    assert row.rolsuper is False
    assert row.rolbypassrls is False
    assert row.current_user.startswith("nexora_app")


async def test_db_health(app_sessionmaker, client):
    r = await client.get("/api/v1/health/db")
    assert r.status_code == 200


async def test_profile_me_returns_own_profile_only(app, client, app_sessionmaker, users):
    a, b = users
    s = get_settings().model_copy(update={"supabase_jwt_secret": SECRET})
    app.dependency_overrides[get_token_verifier] = lambda: TokenVerifier(s)

    ra = await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {_token(a)}"})
    rb = await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {_token(b)}"})
    ra2 = await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {_token(a)}"})
    assert ra.status_code == rb.status_code == ra2.status_code == 200
    assert ra.json()["id"] == str(a)
    assert rb.json()["id"] == str(b)
    assert ra2.json()["id"] == str(a)  # idempotent upsert


async def test_rls_isolates_rows(app_sessionmaker, users, app, client):
    a, b = users
    s = get_settings().model_copy(update={"supabase_jwt_secret": SECRET})
    app.dependency_overrides[get_token_verifier] = lambda: TokenVerifier(s)
    for uid in (a, b):  # make sure both profiles exist
        await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {_token(uid)}"})

    async def visible(session: AsyncSession, uid):
        if uid is not None:
            await set_rls_identity(session, str(uid))
        return {
            str(r[0])
            for r in (
                await session.execute(
                    text("SELECT id FROM profiles WHERE id IN (:a, :b)"), {"a": a, "b": b}
                )
            ).all()
        }

    async with app_sessionmaker() as s1, s1.begin():
        assert await visible(s1, a) == {str(a)}
    async with app_sessionmaker() as s2, s2.begin():
        assert await visible(s2, b) == {str(b)}
    async with app_sessionmaker() as s3, s3.begin():
        assert await visible(s3, None) == set()  # no identity => no rows

    # Cannot write another student's row, and cannot update another's row.
    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s4, s4.begin():
            await set_rls_identity(s4, str(a))
            await s4.execute(text("INSERT INTO profiles (id) VALUES (:b)"), {"b": uuid.uuid4()})
    async with app_sessionmaker() as s5, s5.begin():
        await set_rls_identity(s5, str(a))
        res = await s5.execute(text("UPDATE profiles SET full_name='x' WHERE id = :b"), {"b": b})
        assert res.rowcount == 0


async def test_alembic_version_protected():
    """alembic_version: RLS on, no API-role or nexora_app privileges, owner can read/update."""
    owner = _engine(get_settings().migration_database_url)
    async with owner.connect() as c:
        rls = (
            await c.execute(
                text("SELECT relrowsecurity FROM pg_class WHERE oid = 'public.alembic_version'::regclass")
            )
        ).scalar_one()
        leaks = (
            await c.execute(
                text(
                    "SELECT r || ':' || p"
                    " FROM unnest(ARRAY['anon','authenticated','service_role','nexora_app']) r"
                    " CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE',"
                    "'TRUNCATE','REFERENCES','TRIGGER']) p"
                    " WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r)"
                    " AND has_table_privilege(r, 'public.alembic_version', p)"
                )
            )
        ).scalars().all()
        version = (await c.execute(text("SELECT version_num FROM alembic_version"))).scalar_one()
        updated = (
            await c.execute(text("UPDATE alembic_version SET version_num = version_num"))
        ).rowcount
        await c.rollback()  # ends the autobegun transaction; the version table is untouched
    await owner.dispose()

    assert rls is True
    assert leaks == []
    assert version
    assert updated == 1
