import os

# Test environment: set BEFORE the app is imported. Real env vars override any .env file.
os.environ["SUPABASE_URL"] = "https://testref.supabase.co"
os.environ["SUPABASE_JWT_AUDIENCE"] = "authenticated"
os.environ["SUPABASE_JWT_SECRET"] = "test-hs256-secret-with-at-least-32-bytes!!"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
if os.environ.get("RUN_DB_TESTS") != "1":
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://u:p@127.0.0.1:1/none"
    os.environ.pop("MIGRATION_DATABASE_URL", None)

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
