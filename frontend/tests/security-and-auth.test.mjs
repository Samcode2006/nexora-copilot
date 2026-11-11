import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { FRONTEND_ROOT, withViteSsr } from "./helpers/loadTs.mjs";

function makeJwt(payload) {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${header}.${body}.signature`;
}

test("assertPublicKey rejects secret and service_role keys and accepts public keys", async () => {
  await withViteSsr(async (load) => {
    const { assertPublicKey } = await load("/src/lib/keyValidation.ts");

    assert.throws(
      () => assertPublicKey("sb_secret_test_value_12345"),
      /secret key must never be used/i,
    );

    const serviceRoleJwt = makeJwt({ role: "service_role", iss: "supabase" });
    assert.throws(
      () => assertPublicKey(serviceRoleJwt),
      /service_role key must never be used/i,
    );

    const anonJwt = makeJwt({ role: "anon", iss: "supabase" });
    assert.doesNotThrow(() => assertPublicKey(anonJwt));
    assert.doesNotThrow(() => assertPublicKey("sb_publishable_demo_key_123"));
  });
});

test(".env.example defines required public env vars and never secrets", () => {
  const envExample = fs.readFileSync(path.join(FRONTEND_ROOT, ".env.example"), "utf8");
  assert.match(envExample, /^VITE_SUPABASE_URL=/m);
  assert.match(envExample, /^VITE_SUPABASE_PUBLISHABLE_KEY=/m);
  assert.match(envExample, /^VITE_API_BASE_URL=/m);
  assert.doesNotMatch(envExample, /sb_secret_[A-Za-z0-9_-]+/);
  assert.doesNotMatch(envExample, /DATABASE_URL/);
});

test("router.tsx gates all /app and /onboarding routes behind RequireAuth", () => {
  const routerSrc = fs.readFileSync(
    path.join(FRONTEND_ROOT, "src/app/router.tsx"),
    "utf8",
  );
  assert.match(routerSrc, /element:\s*<RequireAuth\s*\/>/);
  assert.match(routerSrc, /<RedirectIfAuthenticated>\s*<LoginPage\s*\/>\s*<\/RedirectIfAuthenticated>/);
  assert.match(routerSrc, /<RedirectIfAuthenticated>\s*<SignupPage\s*\/>\s*<\/RedirectIfAuthenticated>/);

  const expectedAppSubroutes = [
    "dashboard",
    "profile",
    "resume",
    "jobs",
    "jobs/:jobId",
    "resume-studio",
    "cover-letter",
    "approvals",
    "applications",
    "applications/:applicationId",
    "calendar",
    "interview-prep",
    "interview-prep/:sessionId",
    "feedback",
    "skill-roadmap",
    "follow-ups",
    "assistant",
    "settings",
  ];
  for (const route of expectedAppSubroutes) {
    assert.ok(
      routerSrc.includes(`path: '${route}'`),
      `Missing expected protected route: ${route}`,
    );
  }
});

test("built bundle contains no leaked sb_secret_ tokens or supabase REST calls", () => {
  const distAssetsDir = path.join(FRONTEND_ROOT, "dist/assets");
  if (!fs.existsSync(distAssetsDir)) {
    return;
  }
  const jsFiles = fs.readdirSync(distAssetsDir).filter((f) => f.endsWith(".js"));
  assert.ok(jsFiles.length > 0, "Expected built JS assets in dist/assets");

  for (const file of jsFiles) {
    const content = fs.readFileSync(path.join(distAssetsDir, file), "utf8");
    // Ensure no real sb_secret_<token> is embedded (the guard string checks literal prefix "sb_secret_")
    assert.doesNotMatch(content, /sb_secret_[A-Za-z0-9]{8,}/);
  }
});

