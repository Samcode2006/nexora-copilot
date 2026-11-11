"""Real-database tests. Opt in with RUN_DB_TESTS=1 (needs DATABASE_URL + MIGRATION_DATABASE_URL
in the environment/.env and `alembic upgrade head` applied). Creates and removes two throwaway
auth users. Never prints connection strings.
"""
import os
import time
import uuid
from datetime import UTC, datetime

import jwt
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_token_verifier
from app.ai.providers import LLMService
from app.core.config import get_settings
from app.core.security import TokenVerifier
from app.db import session as db_session
from app.db.repositories import (
    ConsentRepository,
    FactInUseError,
    ProfileFactRepository,
    ProfileRepository,
    ResumeRepository,
    TaskRepository,
)
from app.db.session import set_rls_identity
from app.db.url import prepare_async_url
from app.services import resume_processing

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


async def test_deleter_role_is_non_login_and_unavailable_to_runtime(app_sessionmaker):
    async with app_sessionmaker() as s:
        row = (
            await s.execute(
                text(
                    "SELECT rolcanlogin, rolsuper, rolbypassrls, "
                    "pg_has_role('nexora_app', 'nexora_deleter', 'MEMBER') AS runtime_member "
                    "FROM pg_roles WHERE rolname='nexora_deleter'"
                )
            )
        ).one()
        delete_privilege = (
            await s.execute(
                text("SELECT has_table_privilege(current_user, 'profile_fact_revisions', 'DELETE')")
            )
        ).scalar_one()
        deleter_insert_privilege = (
            await s.execute(
                text("SELECT has_table_privilege('nexora_deleter', 'profile_fact_revisions', 'INSERT')")
            )
        ).scalar_one()
    assert row.rolcanlogin is False
    assert row.rolsuper is False
    assert row.rolbypassrls is False
    assert row.runtime_member is False
    assert delete_privilege is False
    assert deleter_insert_privilege is False


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


async def test_phase1_student_tables_are_rls_scoped(app_sessionmaker, users):
    a, b = users
    resume_id = uuid.uuid4()
    fact_id = uuid.uuid4()
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        await s.execute(
            text(
                "INSERT INTO profile_consents (student_id, consent_type, granted_at) "
                "VALUES (:student, 'resume_processing', now())"
            ),
            {"student": a},
        )
        await s.execute(
            text(
                "INSERT INTO resumes (id, student_id, filename, content_type, size_bytes) "
                "VALUES (:id, :student, 'resume.pdf', 'application/pdf', 5242880)"
            ),
            {"id": resume_id, "student": a},
        )
        await s.execute(
            text(
                "INSERT INTO profile_facts (id, student_id, fact_type, data, status, source) "
                "VALUES (:id, :student, 'skill', '{\"name\":\"Python\"}'::jsonb, 'confirmed', 'student')"
            ),
            {"id": fact_id, "student": a},
        )
        visible = (
            await s.execute(
                text("SELECT count(*) FROM profile_consents WHERE student_id IN (:a, :b)"),
                {"a": a, "b": b},
            )
        ).scalar_one()
        assert visible == 1
        visible_tasks = (
            await s.execute(
                text("SELECT count(*) FROM tasks WHERE student_id IN (:a, :b)"),
                {"a": a, "b": b},
            )
        ).scalar_one()
        assert visible_tasks == 0
        await s.execute(
            text(
                "INSERT INTO tasks (id, student_id, kind, resource_type, resource_id, timeout_seconds) "
                "VALUES (:id, :student, 'resume_parse', 'resume', :resource, 60)"
            ),
            {"id": uuid.uuid4(), "student": a, "resource": resume_id},
        )
        visible_tasks = (
            await s.execute(
                text("SELECT count(*) FROM tasks WHERE student_id IN (:a, :b)"),
                {"a": a, "b": b},
            )
        ).scalar_one()
        assert visible_tasks == 1

    # A claim for a different student is rejected even when the UUID is valid.
    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text(
                    "INSERT INTO profile_consents (student_id, consent_type, granted_at) "
                    "VALUES (:student, 'resume_processing', now())"
                ),
                {"student": b},
            )

    async with app_sessionmaker() as s:
        columns = (
            await s.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='resumes'"
                )
            )
        ).scalars().all()
    assert "content" not in columns
    assert "storage_path" not in columns

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text(
                    "INSERT INTO resumes (id, student_id, filename, content_type, size_bytes) "
                    "VALUES (:id, :student, 'too-large.pdf', 'application/pdf', 5242881)"
                ),
                {"id": uuid.uuid4(), "student": a},
            )

    # Remove fixture rows before the shared user fixture attempts Auth cleanup.
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        await s.execute(text("DELETE FROM profile_facts WHERE id=:id"), {"id": fact_id})
        await s.execute(text("DELETE FROM resumes WHERE id=:id"), {"id": resume_id})


async def test_profile_fact_revision_snapshots_are_append_only(app_sessionmaker, users):
    a, _ = users
    fact_id = uuid.uuid4()
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        await s.execute(
            text(
                "INSERT INTO profile_facts (id, student_id, fact_type, data, status, source) "
                "VALUES (:id, :student, 'skill', '{\"name\":\"Python\"}'::jsonb, 'confirmed', 'student')"
            ),
            {"id": fact_id, "student": a},
        )
        revisions = (
            await s.execute(
                text("SELECT revision, data FROM profile_fact_revisions WHERE fact_id=:id"),
                {"id": fact_id},
            )
        ).all()
        assert len(revisions) == 1
        assert revisions[0].revision == 1

        await s.execute(
            text(
                "UPDATE profile_facts SET data=CAST(:data AS jsonb), revision=2 WHERE id=:id"
            ),
            {"id": fact_id, "data": '{"name":"Python 3"}'},
        )
        revisions = (
            await s.execute(
                text(
                    "SELECT revision FROM profile_fact_revisions "
                    "WHERE fact_id=:id ORDER BY revision"
                ),
                {"id": fact_id},
            )
        ).scalars().all()
        assert revisions == [1, 2]

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text("UPDATE profile_fact_revisions SET data='{}'::jsonb WHERE fact_id=:id"),
                {"id": fact_id},
            )

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text("DELETE FROM profile_fact_revisions WHERE fact_id=:id"),
                {"id": fact_id},
            )

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text("UPDATE profile_facts SET ever_cited=true WHERE id=:id"), {"id": fact_id}
            )
            await s.execute(text("DELETE FROM profile_facts WHERE id=:id"), {"id": fact_id})

    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        await s.execute(text("DELETE FROM profile_facts WHERE id=:id"), {"id": fact_id})


async def test_task_live_duplicate_is_rejected_and_state_fields_are_scoped(app_sessionmaker, users):
    a, _ = users
    task_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        await s.execute(
            text(
                "INSERT INTO tasks (id, student_id, kind, resource_type, resource_id, timeout_seconds) "
                "VALUES (:id, :student, 'resume_parse', 'resume', :resource, 60)"
            ),
            {"id": task_id, "student": a, "resource": resource_id},
        )

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text(
                    "INSERT INTO tasks (id, student_id, kind, resource_type, resource_id, timeout_seconds) "
                    "VALUES (:id, :student, 'resume_parse', 'resume', :resource, 60)"
                ),
                {"id": uuid.uuid4(), "student": a, "resource": resource_id},
            )

    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        result = await s.execute(
            text("UPDATE tasks SET status='running', started_at=now() WHERE id=:id"),
            {"id": task_id},
        )
        assert result.rowcount == 1
        result = await s.execute(
            text("UPDATE tasks SET status='succeeded', finished_at=now() WHERE id=:id"),
            {"id": task_id},
        )
        assert result.rowcount == 1

    with pytest.raises(DBAPIError):
        async with app_sessionmaker() as s, s.begin():
            await set_rls_identity(s, str(a))
            await s.execute(
                text("UPDATE tasks SET timeout_seconds=30 WHERE id=:id"), {"id": task_id}
            )


async def test_phase2_repositories_preserve_owner_and_history_rules(app_sessionmaker, users):
    a, _ = users
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        profile_repository = ProfileRepository(s)
        profile = await profile_repository.get_or_create(a, f"{a}@test.invalid")
        assert profile.id == a
        updated_profile = await profile_repository.update_fields(a, {"branch": "CSE"})
        assert updated_profile is not None
        assert updated_profile.branch == "CSE"

        consents = ConsentRepository(s)
        granted = await consents.grant(a)
        assert granted.granted_at is not None and granted.withdrawn_at is None
        withdrawn = await consents.withdraw(a)
        assert withdrawn is not None and withdrawn.withdrawn_at is not None
        regranted = await consents.grant(a)
        assert regranted.withdrawn_at is None
        assert regranted.granted_at >= granted.granted_at

        resumes = ResumeRepository(s)
        resume = await resumes.create(
            a,
            filename="resume.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=100,
        )
        assert await resumes.get(a, resume.id) is not None

        facts = ProfileFactRepository(s)
        fact = await facts.create(
            a,
            fact_type="skill",
            data={"name": "Python"},
            source="student",
        )
        assert fact.status == "confirmed"
        assert [row.revision for row in await facts.revisions(a, fact.id)] == [1]
        fact = await facts.edit_data(a, fact.id, {"name": "Python 3"})
        assert fact is not None and fact.revision == 2
        fact = await facts.archive(a, fact.id)
        assert fact is not None and fact.revision == 3
        assert [row.revision for row in await facts.revisions(a, fact.id)] == [1, 2, 3]

        extracted = await facts.create(
            a,
            fact_type="project",
            data={"title": "Demo"},
            source="resume",
            confidence="high",
            source_ref={"resume_id": str(resume.id), "page": 1, "excerpt": "Demo project"},
        )
        confirmed = await facts.confirm_many(a, [extracted.id])
        assert confirmed == [extracted.id]
        assert [row.revision for row in await facts.revisions(a, extracted.id)] == [1, 2]
        assert await facts.delete_uncited(a, extracted.id) is True

        savepoint = await s.begin_nested()
        cited = await facts.create(
            a,
            fact_type="achievement",
            data={"title": "Award"},
            source="student",
        )
        assert await facts.mark_cited(a, cited.id) is True
        with pytest.raises(FactInUseError):
            await facts.delete_uncited(a, cited.id)
        await savepoint.rollback()

        tasks = TaskRepository(s)
        task = await tasks.create(
            a,
            kind="resume_parse",
            resource_type="resume",
            resource_id=resume.id,
            timeout_seconds=60,
        )
        assert await tasks.count_live_for_student(a, kind="resume_parse") == 1
        assert await tasks.count_since(
            a,
            kind="resume_parse",
            trigger="explicit",
            since=datetime(2000, 1, 1, tzinfo=UTC),
        ) == 1
        assert (await tasks.start(a, task.id)).status == "running"
        assert (await tasks.succeed(a, task.id)).status == "succeeded"

        retryable = await tasks.create(
            a,
            kind="question_generation",
            resource_type="interview",
            resource_id=uuid.uuid4(),
            timeout_seconds=30,
        )
        failed = await tasks.fail(a, retryable.id, error_code="AI_TIMEOUT", retryable=True)
        assert failed is not None and failed.status == "failed"
        retry = await tasks.retry(a, retryable.id)
        assert retry is not None and retry.attempt == 2 and retry.retry_of == retryable.id
        assert await resumes.delete(a, resume.id) is True
        assert await facts.delete_uncited(a, fact.id) is True


async def test_task_recovery_function_is_narrow_and_applies_retry_rules(app_sessionmaker, users):
    a, _ = users
    resume_id, refresh_id, succeeded_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        tasks = TaskRepository(s)
        resume = await tasks.create(
            a,
            kind="resume_parse",
            resource_type="resume",
            resource_id=resume_id,
            timeout_seconds=60,
        )
        refresh = await tasks.create(
            a,
            kind="job_refresh",
            resource_type="student",
            resource_id=refresh_id,
            timeout_seconds=60,
        )
        await tasks.start(a, refresh.id)
        succeeded = await tasks.create(
            a,
            kind="question_generation",
            resource_type="session",
            resource_id=succeeded_id,
            timeout_seconds=60,
        )
        await tasks.start(a, succeeded.id)
        await tasks.succeed(a, succeeded.id)

    async with app_sessionmaker() as s, s.begin():
        assert (await s.execute(text("SELECT nexora_private.recover_tasks(false)"))).scalar_one() == 2

    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        records = (
            await s.execute(
                text(
                    "SELECT id, status, error_code, retryable FROM tasks "
                    "WHERE id = ANY(CAST(:ids AS uuid[])) ORDER BY id"
                ),
                {"ids": [resume.id, refresh.id, succeeded.id]},
            )
        ).all()
        by_id = {row.id: row for row in records}
        assert by_id[resume.id].status == "failed"
        assert by_id[resume.id].error_code == "TASK_INTERRUPTED"
        assert by_id[resume.id].retryable is False
        assert by_id[refresh.id].status == "failed"
        assert by_id[refresh.id].retryable is True
        assert by_id[succeeded.id].status == "succeeded"

    async with app_sessionmaker() as s:
        privileges = (
            await s.execute(
                text(
                    "SELECT has_function_privilege(current_user, "
                    "'nexora_private.recover_tasks(boolean)', 'EXECUTE'), "
                    "has_table_privilege(current_user, 'tasks', 'UPDATE')"
                )
            )
        ).one()
        assert privileges[0] is True
        assert privileges[1] is False


async def test_task_watchdog_only_fails_tasks_past_timeout_and_grace(app_sessionmaker, users):
    a, _ = users
    running_id, queued_id, fresh_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        tasks = TaskRepository(s)
        running = await tasks.create(
            a,
            kind="job_refresh",
            resource_type="student",
            resource_id=running_id,
            timeout_seconds=60,
        )
        await tasks.start(a, running.id)
        queued = await tasks.create(
            a,
            kind="job_refresh",
            resource_type="student",
            resource_id=queued_id,
            timeout_seconds=60,
        )
        fresh = await tasks.create(
            a,
            kind="job_refresh",
            resource_type="student",
            resource_id=fresh_id,
            timeout_seconds=60,
        )

    owner = _engine(get_settings().migration_database_url)
    async with owner.begin() as connection:
        await connection.execute(
            text(
                "UPDATE tasks SET created_at=now()-interval '2 minutes', "
                "started_at=CASE WHEN id=:running THEN now()-interval '2 minutes' "
                "ELSE started_at END WHERE id IN (:running, :queued)"
            ),
            {"running": running.id, "queued": queued.id},
        )
    await owner.dispose()

    async with app_sessionmaker() as s, s.begin():
        await s.execute(
            text("SELECT set_config('nexora.task_watchdog_grace_seconds', '0', true)")
        )
        assert (await s.execute(text("SELECT nexora_private.recover_tasks(true)"))).scalar_one() == 2

    async with app_sessionmaker() as s, s.begin():
        await set_rls_identity(s, str(a))
        rows = (
            await s.execute(
                text("SELECT id, status, error_code FROM tasks WHERE id = ANY(CAST(:ids AS uuid[]))"),
                {"ids": [running.id, queued.id, fresh.id]},
            )
        ).all()
        by_id = {row.id: row for row in rows}
        assert by_id[running.id].error_code == "AI_TIMEOUT"
        assert by_id[queued.id].error_code == "TASK_INTERRUPTED"
        assert by_id[fresh.id].status == "queued"


async def test_resume_task_persists_evidenced_facts_with_success_cas(
    app_sessionmaker, users, monkeypatch
):
    import fitz

    student_id, _ = users
    resume_id: uuid.UUID
    task_id = uuid.uuid4()
    filename = "resume.pdf"
    source = "Skills\nProgramming Languages: Python"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), source)
    content = document.tobytes()
    document.close()

    original_extractor = resume_processing.extract_student_profile

    def deterministic_extractor(text_value: str):
        return original_extractor(text_value, llm_service=LLMService(provider=None))

    monkeypatch.setattr(resume_processing, "extract_student_profile", deterministic_extractor)

    async with app_sessionmaker() as session, session.begin():
        await set_rls_identity(session, str(student_id))
        await ConsentRepository(session).grant(student_id)
        resume = await ResumeRepository(session).create(
            student_id,
            filename=filename,
            content_type="application/pdf",
            size_bytes=len(content),
        )
        resume_id = resume.id
        task = await TaskRepository(session).create(
            student_id,
            kind="resume_parse",
            resource_type="resume",
            resource_id=resume_id,
            timeout_seconds=60,
        )
        task_id = task.id

    async with app_sessionmaker() as session:
        await set_rls_identity(session, str(student_id))
        await resume_processing.run_resume_parse(
            session=session,
            student_id=student_id,
            task_id=task_id,
            resume_id=resume_id,
            content=content,
            filename=filename,
        )

    async with app_sessionmaker() as session, session.begin():
        await set_rls_identity(session, str(student_id))
        finished = await TaskRepository(session).get(student_id, task_id)
        facts = await ProfileFactRepository(session).list_for_student(
            student_id, fact_type="skill", status="pending_confirmation"
        )
        assert finished is not None and finished.status == "succeeded"
        assert any(
            fact.source == "resume"
            and fact.source_ref is not None
            and fact.source_ref.get("resume_id") == str(resume_id)
            for fact in facts
        )
        repository = ProfileFactRepository(session)
        for fact in facts:
            assert await repository.delete_uncited(student_id, fact.id)
