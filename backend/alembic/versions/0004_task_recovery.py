"""Add a narrowly scoped maintenance function for task recovery.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_maintenance') THEN
                RAISE EXCEPTION 'Role nexora_maintenance does not exist; migration 0004 aborted.'
                    USING HINT = 'Run SECTION 1 of docs/db-role.sql, then re-run: alembic upgrade head';
            END IF;
            IF EXISTS (
                SELECT 1 FROM pg_roles
                WHERE rolname = 'nexora_maintenance'
                  AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication
                       OR rolbypassrls OR rolcanlogin OR rolinherit)
            ) THEN
                RAISE EXCEPTION 'Role nexora_maintenance is misconfigured; migration 0004 aborted.'
                    USING HINT = 'It must be NOLOGIN, NOINHERIT, NOSUPERUSER, NOCREATEDB, '
                                 'NOCREATEROLE, NOREPLICATION and NOBYPASSRLS.';
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE, CREATE ON SCHEMA nexora_private TO nexora_maintenance")
    op.execute("GRANT SELECT ON tasks TO nexora_maintenance")
    op.execute(
        "GRANT UPDATE (status, error_code, retryable, finished_at) "
        "ON tasks TO nexora_maintenance"
    )
    op.execute(
        "CREATE POLICY tasks_maintenance_select ON tasks FOR SELECT "
        "TO nexora_maintenance USING (true)"
    )
    op.execute(
        "CREATE POLICY tasks_maintenance_update ON tasks FOR UPDATE "
        "TO nexora_maintenance USING (true) WITH CHECK (true)"
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.recover_tasks(p_overdue_only boolean)
        RETURNS integer
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        DECLARE
            changed integer;
            grace integer;
        BEGIN
            grace := COALESCE(
                NULLIF(current_setting('nexora.task_watchdog_grace_seconds', true), '')::integer,
                30
            );
            IF grace < 0 THEN
                RAISE EXCEPTION 'task watchdog grace cannot be negative'
                    USING ERRCODE = '22023';
            END IF;
            UPDATE public.tasks AS t
            SET status = 'failed',
                error_code = CASE
                    WHEN p_overdue_only AND t.started_at IS NOT NULL THEN 'AI_TIMEOUT'
                    ELSE 'TASK_INTERRUPTED'
                END,
                retryable = (t.kind <> 'resume_parse'),
                finished_at = pg_catalog.now()
            WHERE t.status IN ('queued', 'running')
              AND (
                    NOT p_overdue_only
                    OR COALESCE(t.started_at, t.created_at)
                       + pg_catalog.make_interval(secs => t.timeout_seconds + grace)
                       <= pg_catalog.now()
              );
            GET DIAGNOSTICS changed = ROW_COUNT;
            RETURN changed;
        END
        $function$
        """
    )
    op.execute("GRANT nexora_maintenance TO postgres WITH SET TRUE, INHERIT FALSE")
    op.execute("ALTER FUNCTION nexora_private.recover_tasks(boolean) OWNER TO nexora_maintenance")
    op.execute("REVOKE nexora_maintenance FROM postgres")
    op.execute("REVOKE CREATE ON SCHEMA nexora_private FROM nexora_maintenance")
    op.execute("REVOKE ALL ON FUNCTION nexora_private.recover_tasks(boolean) FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA nexora_private TO nexora_app")
    op.execute("GRANT EXECUTE ON FUNCTION nexora_private.recover_tasks(boolean) TO nexora_app")


def downgrade() -> None:
    op.execute("REVOKE EXECUTE ON FUNCTION nexora_private.recover_tasks(boolean) FROM nexora_app")
    op.execute("GRANT nexora_maintenance TO postgres WITH SET TRUE, INHERIT FALSE")
    op.execute("ALTER FUNCTION nexora_private.recover_tasks(boolean) OWNER TO postgres")
    op.execute("REVOKE nexora_maintenance FROM postgres")
    op.execute("DROP FUNCTION nexora_private.recover_tasks(boolean)")
    op.execute("DROP POLICY IF EXISTS tasks_maintenance_update ON tasks")
    op.execute("DROP POLICY IF EXISTS tasks_maintenance_select ON tasks")
    op.execute("REVOKE UPDATE (status, error_code, retryable, finished_at) ON tasks FROM nexora_maintenance")
    op.execute("REVOKE SELECT ON tasks FROM nexora_maintenance")
    op.execute("REVOKE USAGE, CREATE ON SCHEMA nexora_private FROM nexora_maintenance")
    op.execute("REVOKE USAGE ON SCHEMA nexora_private FROM nexora_app")
