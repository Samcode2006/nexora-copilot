"""profiles table with RLS (first vertical slice).

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Same value auth.uid() returns on Supabase; avoids needing extra grants on the auth schema.
CURRENT_UID = "NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid"

# Checked here as well as in 0001: a database may already be at 0001 from before 0001
# failed fast. Self-contained on purpose (no app imports in migrations).
REQUIRE_APP_ROLE = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_app') THEN
        RAISE EXCEPTION 'Role nexora_app does not exist; migration % aborted.', '0002'
            USING HINT = 'Run SECTION 1 of docs/db-role.sql in the Supabase SQL Editor, '
                         'then re-run: alembic upgrade head';
    END IF;
END
$$;
"""


def upgrade() -> None:
    # Fail before creating anything.
    op.execute(REQUIRE_APP_ROLE)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("batch_year", sa.Integer(), nullable=True),
        sa.Column("cgpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("backlogs", sa.Integer(), nullable=True),
        sa.Column("branch", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("batch_year IS NULL OR batch_year BETWEEN 2000 AND 2100", name="ck_profiles_batch_year"),
        sa.CheckConstraint("cgpa IS NULL OR cgpa BETWEEN 0 AND 10", name="ck_profiles_cgpa"),
        sa.CheckConstraint("backlogs IS NULL OR backlogs >= 0", name="ck_profiles_backlogs"),
    )

    op.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY profiles_select_own ON profiles FOR SELECT USING (id = {CURRENT_UID})")
    op.execute(f"CREATE POLICY profiles_insert_own ON profiles FOR INSERT WITH CHECK (id = {CURRENT_UID})")
    op.execute(
        f"CREATE POLICY profiles_update_own ON profiles FOR UPDATE "
        f"USING (id = {CURRENT_UID}) WITH CHECK (id = {CURRENT_UID})"
    )
    # Defence in depth: block direct API-role access through Supabase's PostgREST.
    op.execute("REVOKE ALL ON profiles FROM anon, authenticated")

    op.execute("GRANT SELECT, INSERT, UPDATE ON profiles TO nexora_app")


def downgrade() -> None:
    op.drop_table("profiles")
