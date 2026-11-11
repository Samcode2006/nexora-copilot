"""Protect Alembic's version table from the moment it is created.

Alembic creates ``alembic_version`` itself, before any migration runs
(``upgrade``/``downgrade`` on an empty database), or without running any
migration at all (``stamp``, ``ensure_version``). On Supabase, default
privileges can give new ``public`` tables to the Data API roles, so a
protection placed in migration 0001 would be too late or never run.

Every creation path goes through SQLAlchemy ``Table.create``, which fires
``after_create`` right after ``CREATE TABLE`` on the same connection and in the
same transaction. These listeners run there, so the table is never committed
without the protection. The table owner (the migration role) is unaffected:
owners bypass RLS unless it is forced, and owner privileges are not revoked.
``nexora_app`` is given nothing.

``service_role`` is revoked as well: it has BYPASSRLS on Supabase, so RLS alone
would not stop it, and nothing in NEXORA needs it to touch migration state.
"""

from sqlalchemy import DDL, Table, event

VERSION_TABLE = "alembic_version"

_ENABLE_RLS = DDL("ALTER TABLE %(fullname)s ENABLE ROW LEVEL SECURITY")

# Guarded per role so the same code also runs on plain Postgres without the
# Supabase roles. `%%` is a literal `%` for format() after DDL substitution.
_REVOKE_API_ROLES = DDL(
    """
DO $$
DECLARE
    r text;
BEGIN
    FOREACH r IN ARRAY ARRAY['anon', 'authenticated', 'service_role'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('REVOKE ALL ON TABLE %%s FROM %%I', '%(fullname)s', r);
        END IF;
    END LOOP;
END
$$
"""
)


def _is_version_table(ddl, target, bind, **kw) -> bool:
    return isinstance(target, Table) and target.name == VERSION_TABLE


_LISTENERS = (
    _ENABLE_RLS.execute_if(callable_=_is_version_table),
    _REVOKE_API_ROLES.execute_if(callable_=_is_version_table),
)


def install_version_table_protection() -> None:
    """Register the listeners once per process (safe to call repeatedly)."""
    for listener in _LISTENERS:
        if not event.contains(Table, "after_create", listener):
            event.listen(Table, "after_create", listener)
