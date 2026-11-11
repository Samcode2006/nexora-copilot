from fastapi import APIRouter

from app.core.errors import AppError


def _assert_envelope(body: dict, code: str):
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    assert isinstance(body["error"]["details"], list)


async def test_404_envelope(client):
    r = await client.get("/api/v1/nope")
    assert r.status_code == 404
    _assert_envelope(r.json(), "NOT_FOUND")


async def test_422_envelope(app, client):
    router = APIRouter()

    @router.get("/api/v1/_t422")
    async def _t(n: int):
        return {"n": n}

    app.include_router(router)
    r = await client.get("/api/v1/_t422?n=abc")
    assert r.status_code == 422
    _assert_envelope(r.json(), "VALIDATION_ERROR")
    assert r.json()["error"]["details"]


async def test_500_envelope_no_leak(app, client):
    router = APIRouter()

    @router.get("/api/v1/_t500")
    async def _t():
        raise RuntimeError("secret-internal-detail")

    app.include_router(router)
    r = await client.get("/api/v1/_t500")
    assert r.status_code == 500
    _assert_envelope(r.json(), "INTERNAL_ERROR")
    assert "secret-internal-detail" not in r.text


async def test_app_error_envelope(app, client):
    router = APIRouter()

    @router.get("/api/v1/_tapp")
    async def _t():
        raise AppError(409, "CONFLICT", "Nope.")

    app.include_router(router)
    r = await client.get("/api/v1/_tapp")
    assert r.status_code == 409
    _assert_envelope(r.json(), "CONFLICT")


async def test_cors_restricted(client):
    ok = await client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = await client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in bad.headers
