"""Baseline: schema usage grants for the restricted app role.

The role itself is created once, manually, by the project owner (see docs/db-role.sql)
so that no password is ever stored in Git. This migration fails if the role is missing,
so migrations can never be applied without the grants the API needs.

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Self-contained on purpose: migrations must not import app code that may change later.
REQUIRE_APP_ROLE = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_app') THEN
        RAISE EXCEPTION 'Role nexora_app does not exist; migration % aborted.', '0001'
            USING HINT = 'Run SECTION 1 of docs/db-role.sql in the Supabase SQL Editor, '
                         'then re-run: alembic upgrade head';
    END IF;
END
$$;
"""


def upgrade() -> None:
    op.execute(REQUIRE_APP_ROLE)
    op.execute("GRANT USAGE ON SCHEMA public TO nexora_app")


def downgrade() -> None:
    # Tolerant on purpose: rolling back must still work if the role was dropped.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora_app') THEN
                REVOKE USAGE ON SCHEMA public FROM nexora_app;
            END IF;
        END
        $$;
        """
    )
