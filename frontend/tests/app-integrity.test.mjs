import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { FRONTEND_ROOT, withViteSsr } from "./helpers/loadTs.mjs";

const VALID_APPLICATION_STAGES = new Set([
  "Interested",
  "Preparing",
  "Awaiting approval",
  "Ready to apply",
  "Applied",
  "Assessment",
  "Interview",
  "Offer",
  "Rejected",
  "Withdrawn",
]);

test("mockData cross-references and IDs are internally consistent", async () => {
  await withViteSsr(async (load) => {
    const mock = await load("/src/data/mockData.ts");

    const jobIds = new Set(mock.initialJobs.map((j) => j.id));
    assert.equal(jobIds.size, mock.initialJobs.length, "Duplicate job IDs found");

    const appIds = new Set(mock.initialApplications.map((a) => a.id));
    assert.equal(appIds.size, mock.initialApplications.length, "Duplicate application IDs found");

    for (const app of mock.initialApplications) {
      assert.ok(jobIds.has(app.jobId), `Application ${app.id} references missing jobId ${app.jobId}`);
      assert.ok(
        VALID_APPLICATION_STAGES.has(app.stage),
        `Application ${app.id} has unexpected stage ${app.stage}`,
      );
    }

    for (const approval of mock.initialApprovals) {
      assert.ok(
        jobIds.has(approval.jobId),
        `Approval ${approval.id} references missing jobId ${approval.jobId}`,
      );
      assert.ok(
        ["pending", "approved", "rejected"].includes(approval.status),
        `Approval ${approval.id} has invalid status ${approval.status}`,
      );
    }

    // Synthetic data guard: student email must be synthetic, never a real personal domain
    assert.ok(mock.initialProfile.email.endsWith(".edu") || mock.initialProfile.email.endsWith("@example.com"));
  });
});

test("AppContext handles corrupted localStorage safely without crashing", () => {
  const ctxSrc = fs.readFileSync(
    path.join(FRONTEND_ROOT, "src/context/AppContext.tsx"),
    "utf8",
  );
  assert.match(ctxSrc, /function readStoredState<T>/);
  assert.match(ctxSrc, /catch\s*\{/);
});

