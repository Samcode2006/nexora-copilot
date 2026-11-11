import assert from "node:assert/strict";
import test from "node:test";
import { withViteSsr } from "./helpers/loadTs.mjs";

test("executeApiRequest attaches Bearer token and JSON Content-Type", async () => {
  await withViteSsr(async (load) => {
    const { executeApiRequest } = await load("/src/lib/apiClientCore.ts");

    let capturedUrl = "";
    let capturedInit = null;

    const result = await executeApiRequest(
      "api/v1/profile/me",
      {
        method: "PATCH",
        body: JSON.stringify({ batch_year: 2027 }),
      },
      {
        baseUrl: "http://localhost:8000///",
        getToken: async () => "eyJhbGciOiJFUzI1NiJ9.payload.sig",
        fetchImpl: async (url, init) => {
          capturedUrl = url;
          capturedInit = init;
          return new Response(JSON.stringify({ id: "u-1", batch_year: 2027 }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        },
      },
    );

    assert.equal(capturedUrl, "http://localhost:8000/api/v1/profile/me");
    const headers = new Headers(capturedInit.headers);
    assert.equal(headers.get("Authorization"), "Bearer eyJhbGciOiJFUzI1NiJ9.payload.sig");
    assert.equal(headers.get("Content-Type"), "application/json");
    assert.deepEqual(result, { id: "u-1", batch_year: 2027 });
  });
});

test("executeApiRequest omits Authorization when signed out and respects FormData", async () => {
  await withViteSsr(async (load) => {
    const { executeApiRequest } = await load("/src/lib/apiClientCore.ts");

    let capturedHeaders = null;
    const formData = new FormData();
    formData.append("file", new Blob(["dummy"]), "resume.pdf");

    const result = await executeApiRequest(
      "/api/v1/resumes",
      { method: "POST", body: formData },
      {
        baseUrl: "http://localhost:8000",
        getToken: async () => undefined,
        fetchImpl: async (_url, init) => {
          capturedHeaders = new Headers(init.headers);
          return new Response(null, { status: 204 });
        },
      },
    );

    assert.equal(capturedHeaders.has("Authorization"), false);
    assert.equal(capturedHeaders.has("Content-Type"), false);
    assert.equal(result, undefined);
  });
});

test("executeApiRequest parses standard backend error envelope into ApiError", async () => {
  await withViteSsr(async (load) => {
    const { executeApiRequest, ApiError } = await load("/src/lib/apiClientCore.ts");

    await assert.rejects(
      () =>
        executeApiRequest(
          "/api/v1/applications",
          { method: "POST" },
          {
            baseUrl: "http://localhost:8000",
            getToken: async () => "tok",
            fetchImpl: async () =>
              new Response(
                JSON.stringify({
                  error: {
                    code: "APPLICATION_EXISTS",
                    message: "You already saved this job.",
                    details: [{ application_id: "a12b" }],
                  },
                }),
                { status: 409, headers: { "Content-Type": "application/json" } },
              ),
          },
        ),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 409);
        assert.equal(err.code, "APPLICATION_EXISTS");
        assert.equal(err.message, "You already saved this job.");
        assert.deepEqual(err.details, [{ application_id: "a12b" }]);
        return true;
      },
    );
  });
});

test("executeApiRequest falls back cleanly when error response is non-JSON", async () => {
  await withViteSsr(async (load) => {
    const { executeApiRequest, ApiError } = await load("/src/lib/apiClientCore.ts");

    await assert.rejects(
      () =>
        executeApiRequest(
          "/api/v1/profile/me",
          {},
          {
            baseUrl: "http://localhost:8000",
            getToken: async () => undefined,
            fetchImpl: async () => new Response("Bad Gateway", { status: 502 }),
          },
        ),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 502);
        assert.equal(err.code, "HTTP_ERROR");
        assert.equal(err.message, "Request failed with status 502");
        assert.deepEqual(err.details, []);
        return true;
      },
    );
  });
});

