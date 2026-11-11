import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import AnonDbSession

logger = logging.getLogger("nexora")

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(db: AnonDbSession) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any failure means "unavailable"; no detail leaked
        logger.error("DB health check failed: %s", type(exc).__name__)
        raise AppError(503, "DB_UNAVAILABLE", "Database is unavailable.") from None
    return {"status": "ok"}
