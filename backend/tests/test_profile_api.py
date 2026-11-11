"""API-level tests for /profile/me that need no database (auth + wiring)."""


async def test_profile_me_requires_token(client):
    r = await client.get("/api/v1/profile/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_profile_me_rejects_bad_token(client):
    r = await client.get("/api/v1/profile/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


async def test_profile_me_ignores_client_supplied_id(client):
    # No student id parameter exists; unknown params must not grant access.
    r = await client.get("/api/v1/profile/me?id=11111111-1111-1111-1111-111111111111")
    assert r.status_code == 401


async def test_profile_in_openapi(client):
    paths = (await client.get("/api/v1/openapi.json")).json()["paths"]
    assert "/api/v1/profile/me" in paths


async def test_student_data_and_fact_routes_in_openapi(client):
    paths = (await client.get("/api/v1/openapi.json")).json()["paths"]
    assert "/api/v1/profile/me/consents" in paths
    assert "/api/v1/profile/facts" in paths
    assert "/api/v1/resumes" in paths
    assert "/api/v1/tasks/{task_id}" in paths
