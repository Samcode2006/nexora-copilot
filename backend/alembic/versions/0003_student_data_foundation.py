"""Student-owned consent, resume metadata, profile facts and task records.

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

CURRENT_UID = "NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid"
REQUIRE_APP_ROLE = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_app') THEN
        RAISE EXCEPTION 'Role nexora_app does not exist; migration % aborted.', '0003'
            USING HINT = 'Run SECTION 1 of docs/db-role.sql in the Supabase SQL Editor, '
                         'then re-run: alembic upgrade head';
    END IF;
END
$$;
"""
REQUIRE_DELETER_ROLE = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_deleter') THEN
        RAISE EXCEPTION 'Role nexora_deleter does not exist; migration % aborted.', '0003'
            USING HINT = 'Run SECTION 1 of docs/db-role.sql in the Supabase SQL Editor, '
                         'then re-run: alembic upgrade head';
    END IF;
END
$$;
"""


def _protect_student_table(table: str, *, update: bool = False, delete: bool = False) -> None:
    """Apply the common public-schema/RLS/grant boundary to a student table."""
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_select_own ON {table} FOR SELECT "
        f"USING (student_id = {CURRENT_UID})"
    )
    op.execute(
        f"CREATE POLICY {table}_insert_own ON {table} FOR INSERT "
        f"WITH CHECK (student_id = {CURRENT_UID})"
    )
    if update:
        op.execute(
            f"CREATE POLICY {table}_update_own ON {table} FOR UPDATE "
            f"USING (student_id = {CURRENT_UID}) WITH CHECK (student_id = {CURRENT_UID})"
        )
    if delete:
        op.execute(
            f"CREATE POLICY {table}_delete_own ON {table} FOR DELETE "
            f"USING (student_id = {CURRENT_UID})"
        )
    op.execute(f"REVOKE ALL ON {table} FROM PUBLIC, anon, authenticated, service_role")


def upgrade() -> None:
    # Fail before touching the schema if the restricted runtime role is absent.
    op.execute(REQUIRE_APP_ROLE)
    op.execute(REQUIRE_DELETER_ROLE)

    # Close any Supabase default-privilege exposure inherited by the original
    # profile table, then re-apply only the backend runtime grant.
    op.execute("REVOKE ALL ON profiles FROM PUBLIC, anon, authenticated, service_role")
    op.execute("GRANT SELECT, INSERT, UPDATE ON profiles TO nexora_app")

    op.add_column("profiles", sa.Column("eligible_locations", postgresql.ARRAY(sa.Text())))
    op.create_check_constraint(
        "ck_profiles_eligible_locations_count",
        "profiles",
        "eligible_locations IS NULL OR cardinality(eligible_locations) BETWEEN 1 AND 20",
    )

    op.create_table(
        "profile_consents",
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consent_type", sa.Text(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("student_id", "consent_type", name="pk_profile_consents"),
        sa.ForeignKeyConstraint(
            ["student_id"], ["auth.users.id"], ondelete="CASCADE", name="fk_profile_consents_user"
        ),
        sa.CheckConstraint(
            "consent_type = 'resume_processing'", name="ck_profile_consents_supported_type"
        ),
        sa.CheckConstraint(
            "withdrawn_at IS NULL OR granted_at IS NOT NULL",
            name="ck_profile_consents_withdrawal_requires_grant",
        ),
    )

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_resumes"),
        sa.UniqueConstraint("id", "student_id", name="uq_resumes_id_student"),
        sa.ForeignKeyConstraint(
            ["student_id"], ["auth.users.id"], ondelete="CASCADE", name="fk_resumes_user"
        ),
        sa.CheckConstraint("length(filename) BETWEEN 1 AND 255", name="ck_resumes_filename_length"),
        sa.CheckConstraint(
            "content_type IN ('application/pdf', "
            "'application/vnd.openxmlformats-officedocument.wordprocessingml.document')",
            name="ck_resumes_content_type",
        ),
        sa.CheckConstraint("size_bytes BETWEEN 1 AND 5242880", name="ck_resumes_size_bytes"),
    )
    op.create_index("ix_resumes_student_created", "resumes", ["student_id", "created_at"])

    op.create_table(
        "profile_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fact_type", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ever_cited", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Text()),
        sa.Column("source_ref", postgresql.JSONB()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_profile_facts"),
        sa.UniqueConstraint("id", "student_id", name="uq_profile_facts_id_student"),
        sa.ForeignKeyConstraint(
            ["student_id"], ["auth.users.id"], ondelete="CASCADE", name="fk_profile_facts_user"
        ),
        sa.CheckConstraint(
            "fact_type IN ('education','skill','project','experience','achievement','certification')",
            name="ck_profile_facts_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending_confirmation','confirmed','archived')",
            name="ck_profile_facts_status",
        ),
        sa.CheckConstraint("source IN ('student','resume')", name="ck_profile_facts_source"),
        sa.CheckConstraint("revision >= 1", name="ck_profile_facts_revision"),
        sa.CheckConstraint("jsonb_typeof(data) = 'object'", name="ck_profile_facts_data_object"),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence IN ('high','medium','low')",
            name="ck_profile_facts_confidence",
        ),
        sa.CheckConstraint(
            "(status = 'archived') = (archived_at IS NOT NULL)",
            name="ck_profile_facts_archive_timestamp",
        ),
        sa.CheckConstraint(
            "source <> 'resume' OR (confidence IS NOT NULL AND source_ref IS NOT NULL)",
            name="ck_profile_facts_resume_provenance",
        ),
    )
    op.create_index(
        "ix_profile_facts_student_status_type",
        "profile_facts",
        ["student_id", "status", "fact_type"],
    )

    op.create_table(
        "profile_fact_revisions",
        sa.Column("fact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("fact_id", "revision", name="pk_profile_fact_revisions"),
        sa.UniqueConstraint(
            "fact_id", "revision", "student_id", name="uq_profile_fact_revisions_fact_rev_student"
        ),
        sa.ForeignKeyConstraint(
            ["fact_id", "student_id"],
            ["profile_facts.id", "profile_facts.student_id"],
            ondelete="CASCADE",
            name="fk_profile_fact_revisions_fact_student",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["auth.users.id"], ondelete="NO ACTION", name="fk_profile_fact_revisions_user"
        ),
        sa.CheckConstraint("revision >= 1", name="ck_profile_fact_revisions_revision"),
        sa.CheckConstraint(
            "jsonb_typeof(data) = 'object'", name="ck_profile_fact_revisions_data_object"
        ),
    )
    op.create_index(
        "ix_profile_fact_revisions_student_created",
        "profile_fact_revisions",
        ["student_id", "created_at"],
    )

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("trigger", sa.Text(), nullable=False, server_default="explicit"),
        sa.Column("retry_of", postgresql.UUID(as_uuid=True)),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_code", sa.Text()),
        sa.Column("retryable", sa.Boolean()),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
        sa.UniqueConstraint("id", "student_id", name="uq_tasks_id_student"),
        sa.ForeignKeyConstraint(
            ["student_id"], ["auth.users.id"], ondelete="CASCADE", name="fk_tasks_user"
        ),
        sa.ForeignKeyConstraint(
            ["retry_of", "student_id"], ["tasks.id", "tasks.student_id"],
            ondelete="CASCADE", name="fk_tasks_retry_same_student",
        ),
        sa.CheckConstraint(
            "kind IN ('resume_parse','job_refresh','document_generation','evidence_validation',"
            "'question_generation','answer_evaluation')",
            name="ck_tasks_kind",
        ),
        sa.CheckConstraint("status IN ('queued','running','succeeded','failed')", name="ck_tasks_status"),
        sa.CheckConstraint("trigger IN ('explicit','automatic')", name="ck_tasks_trigger"),
        sa.CheckConstraint("attempt >= 1", name="ck_tasks_attempt"),
        sa.CheckConstraint(
            "(attempt = 1 AND retry_of IS NULL) OR (attempt > 1 AND retry_of IS NOT NULL)",
            name="ck_tasks_retry_shape",
        ),
        sa.CheckConstraint("timeout_seconds > 0", name="ck_tasks_timeout_seconds"),
        sa.CheckConstraint(
            "(status IN ('queued','running') AND error_code IS NULL AND retryable IS NULL) OR "
            "(status = 'succeeded' AND error_code IS NULL AND retryable IS NULL) OR "
            "(status = 'failed' AND error_code IS NOT NULL AND retryable IS NOT NULL)",
            name="ck_tasks_error_state",
        ),
        sa.CheckConstraint(
            "(status = 'queued' AND started_at IS NULL AND finished_at IS NULL) OR "
            "(status = 'running' AND started_at IS NOT NULL AND finished_at IS NULL) OR "
            "(status = 'succeeded' AND finished_at IS NOT NULL AND started_at IS NOT NULL) OR "
            "(status = 'failed' AND finished_at IS NOT NULL)",
            name="ck_tasks_timestamps",
        ),
    )
    op.create_index(
        "ix_tasks_student_kind_trigger_created",
        "tasks",
        ["student_id", "kind", "trigger", "created_at"],
    )
    op.create_index(
        "uq_tasks_one_live_resource",
        "tasks",
        ["student_id", "kind", "resource_type", "resource_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued','running')"),
    )

    # Keep RLS identity and grants consistent across every student-owned table.
    for table in ("profile_consents", "resumes", "profile_facts", "profile_fact_revisions", "tasks"):
        _protect_student_table(
            table,
            update=table in {"profile_consents", "profile_facts", "tasks"},
            delete=table in {"resumes", "profile_facts"},
        )

    op.execute("GRANT SELECT, INSERT, UPDATE ON profile_consents TO nexora_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON resumes TO nexora_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON profile_facts TO nexora_app")
    op.execute("GRANT SELECT, INSERT ON profile_fact_revisions TO nexora_app")
    op.execute("GRANT SELECT, INSERT ON tasks TO nexora_app")
    op.execute(
        "GRANT UPDATE (status, error_code, retryable, started_at, finished_at) "
        "ON tasks TO nexora_app"
    )

    # Private schema is not part of the Data API. Trigger functions remain
    # SECURITY INVOKER so row policies and the actual runtime role still apply.
    op.execute("CREATE SCHEMA IF NOT EXISTS nexora_private")
    op.execute(
        "REVOKE ALL ON SCHEMA nexora_private FROM PUBLIC, anon, authenticated, service_role, nexora_app"
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.reject_immutable_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        BEGIN
            IF TG_OP = 'DELETE' AND current_user = 'nexora_deleter' THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'immutable records cannot be changed by this role'
                USING ERRCODE = 'NX001';
        END
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.validate_profile_fact_revision()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.revision <> 1 THEN
                    RAISE EXCEPTION 'a new profile fact must start at revision 1'
                        USING ERRCODE = 'NX002';
                END IF;
                RETURN NEW;
            END IF;

            IF OLD.ever_cited AND NOT NEW.ever_cited THEN
                RAISE EXCEPTION 'ever_cited cannot be reset'
                    USING ERRCODE = 'NX002';
            END IF;
            IF OLD.status = 'archived' AND (
                NEW.fact_type IS DISTINCT FROM OLD.fact_type OR
                NEW.data IS DISTINCT FROM OLD.data OR
                NEW.status IS DISTINCT FROM OLD.status OR
                NEW.source IS DISTINCT FROM OLD.source OR
                NEW.confidence IS DISTINCT FROM OLD.confidence OR
                NEW.source_ref IS DISTINCT FROM OLD.source_ref OR
                NEW.archived_at IS DISTINCT FROM OLD.archived_at
            ) THEN
                RAISE EXCEPTION 'archived profile facts are terminal'
                    USING ERRCODE = 'NX002';
            END IF;

            IF NEW.fact_type IS DISTINCT FROM OLD.fact_type OR
               NEW.source IS DISTINCT FROM OLD.source OR
               NEW.confidence IS DISTINCT FROM OLD.confidence OR
               NEW.source_ref IS DISTINCT FROM OLD.source_ref THEN
                RAISE EXCEPTION 'profile fact type and provenance cannot be changed'
                    USING ERRCODE = 'NX002';
            END IF;

            IF NEW.data IS DISTINCT FROM OLD.data OR
               NEW.status IS DISTINCT FROM OLD.status OR
               NEW.archived_at IS DISTINCT FROM OLD.archived_at THEN
                IF NEW.revision <> OLD.revision + 1 THEN
                    RAISE EXCEPTION 'fact content changes must increment revision by one'
                        USING ERRCODE = 'NX002';
                END IF;
            ELSIF NEW.revision <> OLD.revision THEN
                RAISE EXCEPTION 'revision can change only with fact content'
                    USING ERRCODE = 'NX002';
            END IF;
            RETURN NEW;
        END
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.validate_profile_fact_revision_snapshot()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        DECLARE
            current_revision integer;
            current_data jsonb;
        BEGIN
            SELECT revision, data INTO current_revision, current_data
            FROM public.profile_facts
            WHERE id = NEW.fact_id AND student_id = NEW.student_id;
            IF NOT FOUND OR current_revision <> NEW.revision OR current_data <> NEW.data THEN
                RAISE EXCEPTION 'revision snapshot must match the current profile fact'
                    USING ERRCODE = 'NX002';
            END IF;
            RETURN NEW;
        END
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.snapshot_profile_fact_revision()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        BEGIN
            IF TG_OP = 'INSERT' OR NEW.revision IS DISTINCT FROM OLD.revision THEN
                INSERT INTO public.profile_fact_revisions (fact_id, student_id, revision, data)
                VALUES (NEW.id, NEW.student_id, NEW.revision, NEW.data);
            END IF;
            RETURN NEW;
        END
        $function$
        """
    )

    for table in ("profile_fact_revisions",):
        op.execute(
            f"CREATE TRIGGER {table}_reject_update_delete BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION nexora_private.reject_immutable_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_reject_truncate BEFORE TRUNCATE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION nexora_private.reject_immutable_mutation()"
        )
    op.execute(
        "CREATE TRIGGER profile_fact_revisions_snapshot_guard BEFORE INSERT "
        "ON profile_fact_revisions FOR EACH ROW "
        "EXECUTE FUNCTION nexora_private.validate_profile_fact_revision_snapshot()"
    )
    op.execute(
        "CREATE TRIGGER profile_facts_revision_guard BEFORE INSERT OR UPDATE ON profile_facts "
        "FOR EACH ROW EXECUTE FUNCTION nexora_private.validate_profile_fact_revision()"
    )
    op.execute(
        "CREATE TRIGGER profile_facts_revision_snapshot AFTER INSERT OR UPDATE ON profile_facts "
        "FOR EACH ROW EXECUTE FUNCTION nexora_private.snapshot_profile_fact_revision()"
    )
    op.execute(
        """
        CREATE FUNCTION nexora_private.delete_uncited_fact_revisions()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $function$
        BEGIN
            IF OLD.ever_cited THEN
                RAISE EXCEPTION 'a cited profile fact cannot be deleted'
                    USING ERRCODE = 'NX005';
            END IF;
            DELETE FROM public.profile_fact_revisions
            WHERE fact_id = OLD.id AND student_id = OLD.student_id;
            RETURN OLD;
        END
        $function$
        """
    )
    op.execute(
        "CREATE TRIGGER profile_facts_delete_revisions BEFORE DELETE ON profile_facts "
        "FOR EACH ROW EXECUTE FUNCTION nexora_private.delete_uncited_fact_revisions()"
    )
    op.execute(
        "CREATE POLICY profile_fact_revisions_delete_deleter ON profile_fact_revisions "
        "FOR DELETE TO nexora_deleter USING (true)"
    )
    op.execute("GRANT USAGE ON SCHEMA public TO nexora_deleter")
    op.execute("GRANT DELETE ON profile_fact_revisions TO nexora_deleter")
    op.execute("GRANT USAGE, CREATE ON SCHEMA nexora_private TO nexora_deleter")
    op.execute("GRANT nexora_deleter TO postgres WITH SET TRUE, INHERIT FALSE")
    op.execute(
        "ALTER FUNCTION nexora_private.delete_uncited_fact_revisions() OWNER TO nexora_deleter"
    )
    op.execute("REVOKE CREATE ON SCHEMA nexora_private FROM nexora_deleter")
    op.execute("REVOKE nexora_deleter FROM postgres")

    # The operator role can delete only through the guarded trigger path.
    op.execute(
        "REVOKE ALL ON profile_fact_revisions FROM "
        "PUBLIC, anon, authenticated, service_role, nexora_app, nexora_deleter"
    )
    op.execute("GRANT SELECT, INSERT ON profile_fact_revisions TO nexora_app")
    op.execute("GRANT SELECT, DELETE ON profile_fact_revisions TO nexora_deleter")
    op.execute("GRANT USAGE ON SCHEMA nexora_private TO nexora_deleter")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS profile_facts_delete_revisions ON profile_facts")
    op.execute(
        "GRANT nexora_deleter TO postgres WITH SET TRUE, INHERIT FALSE"
    )
    op.execute("GRANT CREATE ON SCHEMA nexora_private TO nexora_deleter")
    op.execute(
        "ALTER FUNCTION nexora_private.delete_uncited_fact_revisions() OWNER TO postgres"
    )
    op.execute("REVOKE CREATE ON SCHEMA nexora_private FROM nexora_deleter")
    op.execute("REVOKE nexora_deleter FROM postgres")
    op.execute("DROP FUNCTION IF EXISTS nexora_private.delete_uncited_fact_revisions()")
    op.execute("DROP TRIGGER IF EXISTS profile_facts_revision_snapshot ON profile_facts")
    op.execute("DROP TRIGGER IF EXISTS profile_facts_revision_guard ON profile_facts")
    op.execute("DROP FUNCTION IF EXISTS nexora_private.snapshot_profile_fact_revision()")
    op.execute(
        "DROP TRIGGER IF EXISTS profile_fact_revisions_snapshot_guard ON profile_fact_revisions"
    )
    op.execute("DROP FUNCTION IF EXISTS nexora_private.validate_profile_fact_revision_snapshot()")
    op.execute("DROP FUNCTION IF EXISTS nexora_private.validate_profile_fact_revision()")
    op.execute(
        "DROP TRIGGER IF EXISTS profile_fact_revisions_reject_truncate ON profile_fact_revisions"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS profile_fact_revisions_reject_update_delete ON profile_fact_revisions"
    )
    op.execute("DROP FUNCTION IF EXISTS nexora_private.reject_immutable_mutation()")
    op.execute("DROP POLICY IF EXISTS profile_fact_revisions_delete_deleter ON profile_fact_revisions")
    op.execute("REVOKE DELETE ON profile_fact_revisions FROM nexora_deleter")
    for table in ("tasks", "profile_fact_revisions", "profile_facts", "resumes", "profile_consents"):
        op.drop_table(table)
    op.drop_constraint("ck_profiles_eligible_locations_count", "profiles", type_="check")
    op.drop_column("profiles", "eligible_locations")
