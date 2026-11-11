import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.formparsers import MultiPartParser

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.db.session import get_sessionmaker

logger = logging.getLogger("nexora.tasks")


async def _recover_tasks(*, overdue_only: bool, grace_seconds: int) -> int:
    async with get_sessionmaker()() as session, session.begin():
        await session.execute(
            text("SELECT set_config('nexora.task_watchdog_grace_seconds', :grace, true)"),
            {"grace": str(grace_seconds)},
        )
        result = await session.execute(
            text("SELECT nexora_private.recover_tasks(:overdue_only)"),
            {"overdue_only": overdue_only},
        )
        return int(result.scalar_one())


async def _task_watchdog(*, interval_seconds: int, grace_seconds: int, recovered: bool) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            changed = await _recover_tasks(
                overdue_only=recovered,
                grace_seconds=grace_seconds,
            )
            if not recovered:
                recovered = True
            if changed:
                logger.info("Recovered %d background task(s).", changed)
        except Exception as exc:  # noqa: BLE001 - keep liveness when DB is briefly unavailable
            logger.warning("Task recovery failed (%s).", type(exc).__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    recovered = False
    try:
        count = await _recover_tasks(
            overdue_only=False,
            grace_seconds=settings.task_watchdog_grace_seconds,
        )
        recovered = True
        if count:
            logger.info("Marked %d interrupted background task(s) failed at startup.", count)
    except Exception as exc:  # noqa: BLE001 - health endpoints must remain available
        logger.warning("Startup task recovery failed (%s); watchdog will retry.", type(exc).__name__)

    watchdog = asyncio.create_task(
        _task_watchdog(
            interval_seconds=settings.task_watchdog_interval_seconds,
            grace_seconds=settings.task_watchdog_grace_seconds,
            recovered=recovered,
        )
    )
    try:
        yield
    finally:
        watchdog.cancel()
        try:
            await watchdog
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    # Starlette defaults to a 1 MiB disk-spooling threshold. Valid resume uploads
    # must remain memory-only under the MVP retention contract.
    MultiPartParser.spool_max_size = settings.resume_max_bytes + 64 * 1024
    app = FastAPI(
        title="NEXORA API",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.add_middleware(
        ResumeBodyLimitMiddleware,
        max_bytes=settings.resume_max_bytes + 64 * 1024,
        max_concurrent=settings.resume_parse_max_concurrency,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router)
    return app


class ResumeBodyLimitMiddleware:
    """Bound multipart request bytes before Starlette parses or spools a file."""

    def __init__(self, app, *, max_bytes: int, max_concurrent: int) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self._upload_slots = asyncio.Semaphore(max_concurrent)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST" or scope.get("path") != "/api/v1/resumes":
            await self.app(scope, receive, send)
            return

        if self._upload_slots.locked():
            body = (
                b'{"error":{"code":"RATE_LIMITED",'
                b'"message":"Resume parsing is at capacity. Try again shortly.","details":[]}}'
            )
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [(b"content-type", b"application/json"), (b"retry-after", b"2")],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await self._upload_slots.acquire()
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _ResumeBodyTooLarge
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _ResumeBodyTooLarge:
            body = (
                b'{"error":{"code":"PAYLOAD_TOO_LARGE",'
                b'"message":"The resume exceeds the 5 MiB limit.","details":[]}}'
            )
            await send(
                {"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json")]}
            )
            await send({"type": "http.response.body", "body": body})
        finally:
            self._upload_slots.release()


class _ResumeBodyTooLarge(Exception):
    pass


app = create_app()
