import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.db.models import profile, student_data  # noqa: F401  (register models)
from app.db.url import prepare_async_url
from app.db.version_table import install_version_table_protection

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Must run before Alembic creates `alembic_version` (see app/db/version_table.py).
install_version_table_protection()

target_metadata = Base.metadata


def _migration_url():
    raw = get_settings().migration_database_url
    if not raw:
        raise RuntimeError("MIGRATION_DATABASE_URL is required to run migrations.")
    return prepare_async_url(raw)


def run_migrations_offline() -> None:
    url, _ = _migration_url()
    context.configure(
        url=url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    url, connect_args = _migration_url()
    engine = create_async_engine(url, connect_args=connect_args, poolclass=NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_do_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
