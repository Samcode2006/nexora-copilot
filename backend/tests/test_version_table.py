"""No-database tests for the alembic_version creation hook (app/db/version_table.py)."""

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.dialects.postgresql import asyncpg as pg_asyncpg

from app.db import version_table as vt


def _table(name: str) -> Table:
    return Table(name, MetaData(), Column("version_num", String(32)))


def test_install_is_idempotent():
    vt.install_version_table_protection()
    vt.install_version_table_protection()
    listeners = list(_table("alembic_version").dispatch.after_create)
    for listener in vt._LISTENERS:
        assert listeners.count(listener) == 1


def test_only_alembic_version_is_targeted():
    assert vt._is_version_table(None, _table("alembic_version"), None)
    assert not vt._is_version_table(None, _table("profiles"), None)
    assert not vt._is_version_table(None, object(), None)


def test_revoke_renders_single_percent_for_asyncpg():
    # asyncpg does not use percent paramstyle, so `%%` must reach Postgres as `%`.
    sql = str(vt._REVOKE_API_ROLES.against(_table("alembic_version")).compile(
        dialect=pg_asyncpg.dialect()
    ))
    assert "format('REVOKE ALL ON TABLE %s FROM %I', 'alembic_version', r)" in sql
    assert "%%" not in sql
    assert "ARRAY['anon', 'authenticated', 'service_role']" in sql


def test_enable_rls_renders_table_name():
    sql = str(vt._ENABLE_RLS.against(_table("alembic_version")).compile(
        dialect=pg_asyncpg.dialect()
    ))
    assert sql.strip() == "ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY"
