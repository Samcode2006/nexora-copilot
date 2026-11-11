# NEXORA AI Hardening Integration Report

- **Date:** 2026-11-11
- **Project:** NEXORA
- **Branch:** `feat/ai-hardening`
- **Base:** `8d007edd6769afb9d50b49731c4e1606aaa0f643` (`main`)
- **Integration workspace:** `C:\Users\LENOVO\OneDrive\Documents\ChatGPT\Nexora-AI-Hardening`
- **Original AI workspace:** `C:\Users\LENOVO\OneDrive\Documents\ChatGPT\Nexora`

## 1. Summary

Integrated the five AI hardening batches into the backend feature branch using targeted edits. The branch began clean at the requested base. The original AI workspace had no commits, so the comparison used its file contents directly against the integration checkout.

The integration preserves the backend's `app.ai` package path, configuration, existing application fixtures, and backend Ruff configuration. It does not add routes, database access, persistence, backend adapters, or task execution. Public AI service signatures and Pydantic field declarations remain unchanged.

All work remains uncommitted and unpushed on `feat/ai-hardening`. No branch switch, merge, or rebase was performed. The separate `Nexora-Git` `main` checkout was left untouched. The pull request remains for Samarth's review and approval.

## 2. Batch summary

1. **Cover-letter evidence and interview serialization:** added one canonical neutral closing, model validation for that closing, and full question/answer/evaluation history alignment validation. Extended tests for invalid closing text, trusted session serialization, reconstruction, and resumption behavior.
2. **Resume parser:** changed the default limit to exactly 5,000,000 bytes, retained explicit per-call overrides, and added inclusive-boundary tests.
3. **Offline end-to-end workflows:** added deterministic tests spanning parsing/profile extraction, job discovery/normalization/matching, resume and cover-letter generation, and interview generation/evaluation/reconstruction. Network access is blocked in the workflow tests.
4. **Provider reliability:** added bounded LLM retries, a 60-second native Gemini request timeout, safe provider failure categories and diagnostics, safer fallback metadata, bounded/sanitized Remotive failures, and embedding keyword-fallback diagnostics.
5. **Quality and docs:** kept the backend Ruff configuration, updated the AI service contracts and Phase 1–6 integration audit, and added this integration report. During final validation, installed the already-declared PyJWT runtime dependency and Ruff dev dependency at their pinned versions. Ruff ran and reported 20 lint findings; details are recorded below.

## 3. Reconciliation of all 37 differing shared AI paths

The original workspace used `backend.app` imports in several places, while the integration branch's supported import root is `app`. Source-workspace import rewrites and broad file copies were not transferred. Paths not needing behavior changes below retain the integration branch's implementation.

| Shared path | Reconciliation |
| --- | --- |
| `backend/app/__init__.py` | Kept the integration branch package initializer. No new `backend.app` import root was introduced. |
| `backend/app/ai/__init__.py` | Kept the branch's `app.ai` export structure. |
| `backend/app/ai/interview_intelligence/__init__.py` | Kept existing exports and public service imports. |
| `backend/app/ai/interview_intelligence/adaptive_engine.py` | Kept the backend implementation; offline and interview regression tests exercise it. |
| `backend/app/ai/interview_intelligence/evaluation.py` | Kept the backend implementation and existing evaluation contract. |
| `backend/app/ai/interview_intelligence/interview_service.py` | Preserved function signatures and serialization behavior; retained the clearer trusted-storage/privacy boundary and Python UTC cleanup. |
| `backend/app/ai/interview_intelligence/prompts.py` | Kept the integration implementation; no provider-independent prompt change was needed. |
| `backend/app/ai/interview_intelligence/question_generator.py` | Kept the integration implementation; existing validation and deterministic generation are covered by the AI tests. |
| `backend/app/ai/interview_intelligence/rubrics.py` | Kept existing rubric definitions and weights. |
| `backend/app/ai/interview_intelligence/schemas.py` | Strengthened session validation so each turn's complete question, answer, and evaluation must equal its parallel history entry. No fields or JSON shape changed. |
| `backend/app/ai/job_intelligence/__init__.py` | Kept current exports under `app.ai`. |
| `backend/app/ai/job_intelligence/discovery.py` | Kept the backend implementation; no hardening behavior required a discovery API change. |
| `backend/app/ai/job_intelligence/normalizer.py` | Kept the backend normalization implementation; end-to-end tests cover normalized results. |
| `backend/app/ai/job_intelligence/providers.py` | Merged finite configuration checks, bounded transient retries, sanitized errors, and minimal diagnostics. Existing provider constructor and search signatures remain unchanged. |
| `backend/app/ai/job_intelligence/schemas.py` | Kept the existing job schema fields and validation contract. |
| `backend/app/ai/job_matching/__init__.py` | Kept current matching exports. |
| `backend/app/ai/job_matching/eligibility.py` | Kept the backend eligibility implementation. |
| `backend/app/ai/job_matching/embeddings.py` | Added safe diagnostics for optional package/model failures while preserving the existing exception constructor and embedding-provider API. |
| `backend/app/ai/job_matching/evidence.py` | Kept the backend evidence-reference implementation. |
| `backend/app/ai/job_matching/schemas.py` | Kept existing matching model fields and output structure. |
| `backend/app/ai/job_matching/scoring.py` | Added sanitized embedding diagnostics and retained deterministic keyword rescoring and `keyword_fallback` metadata. Existing scoring outputs remain unchanged. |
| `backend/app/ai/providers/__init__.py` | Kept current provider exports and import structure. |
| `backend/app/ai/providers/base.py` | Added internal error category/retry metadata helpers without changing public error constructors or result fields. |
| `backend/app/ai/providers/gemini.py` | Added native-client timeout and safe classification while retaining SDK-independent injected-client requests through plain-dict config. See Gemini compatibility below. |
| `backend/app/ai/providers/service.py` | Added safe fallback reasons/diagnostics and capped provider attempts at three. Programming errors continue to surface. `LLMService` signatures are unchanged. |
| `backend/app/ai/resume_intelligence/__init__.py` | Kept current parser/profile exports. |
| `backend/app/ai/resume_intelligence/parser.py` | Set the default to 5,000,000 bytes and made the limit message exact; explicit overrides remain supported. Signature unchanged. |
| `backend/app/ai/resume_intelligence/profile_extractor.py` | Kept the backend evidence extraction implementation; the new end-to-end suite exercises it. |
| `backend/app/ai/resume_intelligence/profile_schemas.py` | Kept existing profile/evidence model fields. |
| `backend/app/ai/resume_intelligence/schemas.py` | Kept existing parsed-resume model fields. |
| `backend/app/ai/resume_tailoring/__init__.py` | Kept current tailoring exports. |
| `backend/app/ai/resume_tailoring/cover_letter.py` | Switched generation to the canonical closing constant; existing function signature and evidence flow remain. |
| `backend/app/ai/resume_tailoring/generation.py` | Kept the feature-owned fallback boundary and sanitized unexpected provider failures. Public function signatures remain. |
| `backend/app/ai/resume_tailoring/prompts.py` | Kept the backend prompt implementation; no API change was needed. |
| `backend/app/ai/resume_tailoring/schemas.py` | Added the canonical constant and a private field validator enforcing it. Public fields and serialized shape are unchanged. |
| `backend/app/ai/resume_tailoring/tailoring.py` | Kept existing resume tailoring and evidence validation behavior. |
| `backend/app/ai/resume_tailoring/validation.py` | Kept existing evidence validation; no adapter or persistence logic was added. |

## 4. Accounting for all six original-only candidates

| Original-only candidate | Decision | Reason |
| --- | --- | --- |
| `backend/tests/test_ai_offline_workflows.py` | Added | Adapted imports to `app.ai`; retains deterministic fixtures and blocks network access. |
| `backend/tests/test_ai_provider_reliability.py` | Added | Adapted imports to `app.ai`; provider transports and SDK clients are mocked. |
| `docs/AI_HARDENING_BATCH_1_AUDIT.md` | Excluded as a separate file | Its findings are reflected in the updated service contracts and this integration report; the source-workspace audit is not presented as a new backend audit. |
| `docs/AI_HARDENING_FINAL_REPORT.md` | Excluded as a separate file | Its test results predate this branch integration. This report records the integration branch's actual checks and limitations. |
| `docs/AI_OFFLINE_TEST_AUDIT.md` | Excluded as a separate file | The Phase 1–6 audit follow-up and this report cover the offline scope and current results. |
| `docs/AI_PROVIDER_RELIABILITY_AUDIT.md` | Excluded as a separate file | Provider changes and validation are documented in the service contracts and this report; the source audit's environment-specific results are not copied as current results. |

The original workspace also contained `.pytest_cache`, `.ruff_cache`, `nexora_ai.egg-info`, a standalone root `pyproject.toml`, and `backend/__init__.py`. These were not transferred. In particular, the standalone root project metadata and generated egg-info were explicitly excluded; the extra package stub would also conflict with the backend's `app.ai` import root. Existing target-only files were preserved.

## 5. Changes merged and intentionally excluded

Merged changes are limited to the five batches summarized above, including targeted edits to existing AI tests and fixture support. Existing backend tests were not replaced. Two assertions in `test_llm_provider.py` were updated to require sanitized failure text instead of raw provider details; the injected-client tests remain.

The four source-workspace audit documents were intentionally not copied as separate files. Their useful findings are reflected in `AI_SERVICE_CONTRACTS.md`, the Phase 1–6 audit follow-up, and this integration-specific report. No source-workspace project metadata, generated package output, or cache files were transferred. No target-only files were removed or overwritten.

## 6. Conflicts found and resolution

- **Import namespace:** source-workspace files used `backend.app`; the branch uses `app.ai`. New tests were adapted and target package exports were retained.
- **Gemini injected-client behavior:** the source reliability change used `google.genai.types.GenerateContentConfig` during every request. That would require the optional SDK even with an injected client. The integration keeps a plain dictionary request config and imports SDK types only while constructing a native client for the timeout.
- **Provider exception APIs:** source code added constructor parameters to provider error classes. To avoid changing public constructor signatures, the merge attaches category/retry/diagnostic metadata through private helper functions while keeping existing exception constructors.
- **Programming errors:** the backend's Gemini implementation and tests require programming errors such as `TypeError` to surface. The shared service keeps that behavior and sanitizes other unexpected provider failures into explicit fallbacks.
- **Backend test fixtures:** the original AI `conftest.py` omitted backend application fixtures. Its three AI-only fixtures were merged into the existing backend `conftest.py`; its app/client and environment fixtures remain.
- **Fallback message assertions:** two pre-existing assertions expected raw provider details. They now assert the safe category messages required by the reliability batch.

A static comparison against the base found **zero public service/method signature changes** and **zero Pydantic field declaration changes**. The two requested model validators change accepted-value invariants only; public field shapes remain intact.

## 7. Gemini compatibility preservation

`GeminiProvider.__init__(..., client=...)` remains unchanged. When a client is injected, the constructor does not import or construct the Google SDK client. `generate_structured` uses the provider-neutral dict config, so an injected client still works when `google-genai` is unavailable. The optional SDK and `HttpOptions(timeout=60_000)` are loaded only when the provider creates its own native client.

The existing `test_injected_client_works_without_google_sdk` regression test was preserved and passed in the AI test run. No live Gemini call was made.

## 8. Import, fixture, and ownership compatibility

- Preserved `app.ai` and all existing `app.ai.*` package exports.
- Confirmed no AI source imports FastAPI routes or SQLAlchemy/database modules.
- Preserved the backend `app` and `client` fixtures and test environment setup; added `sample_resume_text`, `offline_job_provider`, and `run_pipeline_stage` fixtures alongside them.
- Kept AI services independent of routes, database persistence, backend adapters, and task execution.
- Left `backend/pyproject.toml` unchanged; the standalone root `pyproject.toml` was not transferred.

## 9. Dependency setup and final test results

backend/pyproject.toml declares pyjwt[crypto]==2.15.1 as a runtime dependency and ruff==0.17.4 in the dev extra. The repository has no backend Python lockfile; the frontend has package-lock.json. Backend installation instructions use pip extras, including python -m pip install -e ".[dev,gemini]" from backend/. Installed only the already-declared missing packages, at their pinned versions:

Command: python -m pip install "pyjwt[crypto]==2.15.1" "ruff==0.17.4"

The backend configuration was not changed. Tests ran from backend/ with GEMINI_API_KEY empty, JOBS_PROVIDER=mock, and JOB_MATCH_EMBEDDINGS=keyword. No live Gemini or Remotive calls were made.

| Exact command | Result |
| --- | --- |
| python -m pytest -q tests | **224 passed, 5 skipped, 1 warning** (1.57s). The warning is from google-genai's deprecated _UnionGenericAlias. |
| python -m pytest -q tests/test_ai_pipeline_offline.py tests/test_ai_offline_workflows.py tests/test_ai_provider_reliability.py tests/test_resume_parser.py tests/test_profile_extractor.py tests/test_job_discovery.py tests/test_job_matching.py tests/test_resume_tailoring.py tests/test_interview_intelligence.py tests/test_llm_provider.py | **199 passed, 1 warning** (1.38s). |
| python -m pytest -q tests/test_ai_offline_workflows.py | **6 passed** (0.39s). |
| python -m pytest -q tests/test_ai_provider_reliability.py | **31 passed, 1 warning** (0.75s). |
| python -m pytest -q tests/test_llm_provider.py::test_injected_client_works_without_google_sdk | **1 passed** (0.02s). |
| python -m compileall -q app tests | Passed. |
| git diff --check | Passed; Git emitted only LF-to-CRLF working-copy notices. |
| python -m ruff check --config pyproject.toml . | **20 findings; nonzero exit.** All findings are present in main at the selected base; none were introduced by the AI hardening changes. See Section 10. |

The workflow tests block socket connections and urllib access; reliability tests use injected transports and fake clients. The full backend suite ran without failures. The five skips are from existing skip conditions.

## 10. Ruff baseline, classification, and targeted cleanup

Ruff was run with backend/pyproject.toml against both the current tree and an isolated temporary archive of main at 8d007edd6769afb9d50b49731c4e1606aaa0f643. A machine-readable comparison keyed by relative path, rule, and message found **31 findings on main, 20 in the current tree, 20 current findings matching main, 0 introduced findings, and 11 baseline findings no longer reported**. Ruff's baseline summary was 15 automatically fixable and 9 with unsafe fixes available; the current summary is 7 automatically fixable and 8 with unsafe fixes available.

The original 20 current findings are all pre-existing. Findings on unchanged files/lines are unrelated to this integration and remain out of scope. The two findings located in modified files refer to declarations already present at the base: LLMResult's Generic[T] declaration (base line 31; current line 65 after helper additions) and generate_draft's TypeVar-based signature (line 23 in both versions). Neither was created by the nearby integration changes.

| Current finding | Classification |
| --- | --- |
| BLE001 — app/ai/interview_intelligence/evaluation.py:120 | Unrelated backend issue; pre-existing in main. |
| B033 — app/ai/interview_intelligence/question_generator.py:41 | Unrelated backend issue; pre-existing in main. |
| TRY004 — app/ai/interview_intelligence/question_generator.py:106 | Unrelated backend issue; pre-existing in main. |
| F841 — app/ai/interview_intelligence/question_generator.py:130 | Unrelated backend issue; pre-existing in main. |
| BLE001 — app/ai/interview_intelligence/question_generator.py:272 | Unrelated backend issue; pre-existing in main. |
| FLY002 — app/ai/interview_intelligence/question_generator.py:657 | Unrelated backend issue; pre-existing in main. |
| F401 — app/ai/job_intelligence/discovery.py:6 | Unrelated backend issue; pre-existing in main. |
| F401 — app/ai/job_intelligence/discovery.py:7 | Unrelated backend issue; pre-existing in main. |
| SIM103 — app/ai/job_intelligence/discovery.py:112 | Unrelated backend issue; pre-existing in main. |
| SIM101 — app/ai/job_intelligence/normalizer.py:165 | Unrelated backend issue; pre-existing in main. |
| UP046 — app/ai/providers/base.py:65 | Pre-existing in main; the LLMResult generic declaration is unchanged. |
| RUF022 — app/ai/resume_intelligence/__init__.py:17 | Unrelated backend issue; pre-existing in main. |
| SIM102 — app/ai/resume_intelligence/profile_extractor.py:192 | Unrelated backend issue; pre-existing in main. |
| UP046 — app/ai/resume_intelligence/profile_schemas.py:20 | Unrelated backend issue; pre-existing in main. |
| I001 — app/ai/resume_tailoring/__init__.py:3 | Unrelated backend issue; pre-existing in main. |
| UP047 — app/ai/resume_tailoring/generation.py:23 | Pre-existing in main; the generate_draft generic signature is unchanged. |
| I001 — app/ai/resume_tailoring/tailoring.py:3 | Unrelated backend issue; pre-existing in main. |
| UP047 — tests/test_ai_pipeline_offline.py:81 | Unrelated backend issue; pre-existing in main. |
| BLE001 — tests/test_ai_pipeline_offline.py:84 | Unrelated backend issue; pre-existing in main. |
| I001 — tests/test_job_discovery.py:1 | Unrelated backend issue; pre-existing in main. |

No Ruff finding was classified as introduced by AI hardening or caused by the integration. Therefore no source cleanup was appropriate under the instruction to leave pre-existing and unrelated findings out of scope. No unsafe automatic fixes were applied, and no source code was changed during this targeted cleanup step.

Eleven findings from the main baseline are no longer reported after the integration changes:

- interview_service.py: I001 import ordering and UP017; the integration sorted imports and switched to datetime.UTC.
- job_matching/scoring.py: two F841 findings and TRY203; the integration uses the caught error for safe diagnostics, removes an unused local, and removes a redundant catch-and-reraise.
- resume_tailoring/cover_letter.py: I001; imports were ordered while adding the canonical closing.
- resume_tailoring/generation.py: BLE001; the broad feature fallback is explicitly marked as intentional.
- resume_tailoring/schemas.py: I001; imports were ordered while adding the closing validator.
- tests/test_interview_intelligence.py: F401 and SIM114; an unused import was removed and equivalent branches were combined.
- tests/test_resume_tailoring.py: F401; an unused draft import was replaced by the schemas used by the new tests.

## 11. Final worktree and diff review

The branch remains feat/ai-hardening at base 8d007edd6769afb9d50b49731c4e1606aaa0f643. The worktree contains 19 modified tracked files and three untracked integration deliverables: backend/tests/test_ai_offline_workflows.py, backend/tests/test_ai_provider_reliability.py, and this report. The tracked diff summary is **19 files changed, 840 insertions, 104 deletions**; git diff --stat excludes untracked files until staged. No files were staged, committed, or pushed.

The final review covered the complete tracked source, test, and documentation diffs and all three untracked deliverables. The two new test modules use deterministic fixtures/fakes; the offline workflow test blocks socket and URL access. No unexpected changes were identified. backend/pyproject.toml is unchanged. The status contains no dependency files, .env files, bytecode, caches, nexora_ai.egg-info, or unrelated generated artifacts. A credential-pattern scan of changed and new files found no credential patterns; the reliability tests intentionally contain a synthetic redaction sentinel. git diff --check passed.

## 12. Remaining limitations

- Ruff still exits nonzero for the 20 pre-existing findings listed above. They were not changed because they are not attributable to this integration.
- Five backend tests were skipped by existing conditions; all executed tests passed.
- Provider reliability is tested with deterministic fakes. Live Gemini, Remotive availability, and native provider behavior were not exercised.
- Interview serialization remains a trusted service-level primitive, not an authorization mechanism or privacy-redacted API response. Backend response projection and persistence remain backend-owned.
- AI services remain synchronous and do not implement backend task scheduling.

## 13. Recommended PR description

**Title:** Harden AI evidence, parsing, offline workflows, and provider reliability

**Description:**

- Enforce the canonical evidence-safe cover-letter closing and stronger interview session history invariants.
- Set the resume parser default limit to 5,000,000 bytes while preserving explicit overrides.
- Add deterministic offline coverage across resume, job, tailoring, and interview workflows.
- Bound provider retries, configure a native Gemini timeout, sanitize diagnostics/fallback metadata, and preserve SDK-independent injected clients.
- Update AI service contracts and integration audit documentation without changing backend-owned APIs, routes, persistence, or configuration.

**Validation note:** the full backend suite passed (224 passed, 5 skipped); the complete AI selection passed (199 passed), including offline workflow and provider reliability tests. Compilation and git diff --check passed. Ruff reports 20 findings, all confirmed in the main baseline; the integration introduced none.