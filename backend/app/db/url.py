from typing import Any

from sqlalchemy.engine import URL, make_url

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def prepare_async_url(raw: str) -> tuple[URL, dict[str, Any]]:
    """Normalise a Postgres URL for asyncpg and derive connect_args.

    - Ensures the postgresql+asyncpg driver.
    - Drops libpq-style `sslmode` (unsupported by asyncpg) and requires SSL for remote hosts.
    - Supabase transaction pooler (port 6543, pgbouncer) needs the prepared-statement cache off.
    """
    url = make_url(raw)
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    url = url.set(query=query)

    connect_args: dict[str, Any] = {}
    is_local = (url.host or "") in _LOCAL_HOSTS
    if sslmode != "disable" and not is_local:
        connect_args["ssl"] = "require"
    if url.port == 6543:
        connect_args["statement_cache_size"] = 0
    return url, connect_args
