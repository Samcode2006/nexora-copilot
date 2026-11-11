# NEXORA: Team Start Here

NEXORA is an approval-first AI placement co-pilot for students. This is a hackathon MVP, so keep it small, keep the trust rules intact, and use free tools.

## 1. Architecture

```
Browser (React + TS + Vite)
  ├── Supabase Auth (sign-up / sign-in only; publishable key)
  └── FastAPI  /api/v1  (Bearer = Supabase access token)
        ├── verifies JWT (ES256, project JWKS) → student = token `sub`
        ├── business rules: eligibility, evidence, approval, stage transitions
        ├── app/ai/*  (Member 3 modules, in-process; mock + real)
        └── PostgreSQL on Supabase, as restricted role `nexora_app`
              └── RLS on every student table (second layer: guards against query bugs,
                  not against a compromised backend; contract section 17.2.1)
```

- The browser uses Supabase **only for login**. All NEXORA data goes through FastAPI.
- The student is always taken from the verified token, never from request data.
- Secret and service keys never reach the frontend.
- Background work uses FastAPI BackgroundTasks. There are no microservices, queues or Kubernetes.

**Credentials at a glance**

| Who | Uses | Never has |
|---|---|---|
| **Frontend** (M2's code) | Supabase Auth with the project URL and the **publishable key**. The student's access token is sent to FastAPI as a Bearer token. | Any database credential, secret key or `service_role` key |
| **FastAPI backend** (shared runtime run by M1) | The restricted **`nexora_app`** database role (`DATABASE_URL`) | The `service_role` key (not configured or used in the MVP), and the migration-owner credentials |
| **Member 1 only** | The `nexora_app` credentials for the backend runtime, and the migration-owner credentials (`MIGRATION_DATABASE_URL`) for `alembic upgrade head` | The `service_role` key (not used in the MVP) |
| **Members 2 and 3** | M2: the public Supabase URL and publishable key. M3: mock-mode settings. | **No database credentials of any kind** |

## 2. Repository structure

```
.env.example              backend env names (copy to .env, never commit .env)
PROGRESS.md               backend task log and verification status
docs/
  TEAM_START_HERE.md      this file
  api-contract-proposed.md  API + AI-module contract (v0.6)
  openapi.json            (planned) OpenAPI snapshot for frontend type generation
  db-role.sql             one-time DB role setup + checks (owner runs it)
  frontend-auth-checklist.md
fixtures/api/             (planned) shared synthetic JSON fixtures (contract section 15)
backend/
  app/main.py             FastAPI app
  app/core/               config, JWT verification, error format
  app/api/                deps (current user), v1 routers
  app/db/                 async engine/session (RLS identity), models, version-table hook
  app/schemas/            Pydantic request/response models
  alembic/                migrations (Member 1 owns)
  tests/                  pytest (DB tests opt-in with RUN_DB_TESTS=1)
frontend/
  src/lib/supabaseClient.ts  Auth client (publishable key only)
  src/lib/api.ts          fetch wrapper: adds Bearer token, parses error envelope
  src/auth/               AuthProvider / useAuth
  .env.example            copy to .env.local (git-ignored)
```

## 3. Setup

**Backend** (Python 3.12+, tested with 3.14), from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```
On macOS/Linux, use `.venv/bin/python` instead.

The editable install contains only the `app` package, and it pulls in every pinned runtime and dev dependency. `tests/` and the `alembic/` migrations folder aren't installed.

1. Copy `.env.example` to `.env` **at the repository root**.
   - **M2 and M3:** set only `APP_ENV`, `CORS_ORIGINS` and a placeholder `SUPABASE_URL` (for example `https://example.supabase.co`). Leave `SUPABASE_JWT_SECRET` and `MIGRATION_DATABASE_URL` empty, and use the placeholder `DATABASE_URL` below. You never receive real database credentials.
   - **M1:** also sets the real `DATABASE_URL` (the restricted `nexora_app` role) and `MIGRATION_DATABASE_URL` (migration owner). Leave `SUPABASE_JWT_SECRET` empty: the project signs tokens with ES256.
2. `DATABASE_URL` must be set for the app to start. A placeholder such as `postgresql://u:p@127.0.0.1:1/x` is enough for working on endpoints that don't use the database, and for AI modules with `AI_PROVIDER=mock`.

**Development database and backend (D-16, O-8):**
- There is one shared development Supabase project, available after M1 finishes the security setup.
- **Only the shared backend runtime, run by M1, holds application database credentials.** Migration-owner credentials are private to M1.
- **M2 and M3 never receive database credentials.**
  - **M2** points the frontend at the shared backend URL (`VITE_API_BASE_URL`). Until that URL exists (contract R-2), M2 uses the fixture mock mode. That mode becomes usable only after M2-2 has built it (section 7); until then M2 builds it as part of M2-2.
  - **M3** develops AI modules against deterministic mocks, with `AI_PROVIDER=mock` and a placeholder `DATABASE_URL`, and integrates through PRs.
- The `service_role` key never goes in the frontend or the repository, and is never shared. **No service-role key is configured or used in the MVP backend** (contract R-3). **Deleting a student's data and removing their login are both manual steps run by M1 as the migration owner** after verifying the request (contract sections 18.1 and 18.6). The backend cannot delete accounts, and the runtime role cannot execute any deletion function.
- **Resume uploads (contract section 5, R-3).** The backend reads an upload into memory, parses it and discards it. Resume files are **not retained** in the MVP: nothing is written to disk, a temp folder or Supabase Storage. Supabase Storage integration and the `retain_resume_file` option are deferred, so don't create a Storage bucket or add file-retention code.
- Use **synthetic data only**. Never load real student data or real resumes.

| Task | Command (from `backend/`) |
|---|---|
| Run | `.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`. Docs at http://localhost:8000/docs |
| Test | `.\.venv\Scripts\python -m pytest -q` |
| Lint | `.\.venv\Scripts\python -m ruff check app tests alembic` |

Only Member 1 runs migrations (`alembic upgrade head`), and only after `docs/db-role.sql` Section 1 has been run **and the M1-7 conditions in section 7 are met**.

**Frontend** (Node 20.19+ or 22.12+, required by Vite 8), from `frontend/`:

1. Run `npm install`.
2. Copy `.env.example` to `.env.local` and fill in `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`. Only the publishable key goes here, never a secret or `service_role` key.
3. Set `VITE_API_BASE_URL` to the shared backend URL once M1 has shared one (contract R-2). Until then, leave it unset. The fixture mock mode exists only after M2-2 has built it; before that there is no backend to call, and M2 builds the mock client as part of M2-2. The default, `http://localhost:8000`, only works if you run the backend yourself with the placeholder `DATABASE_URL`.

| Task | Command (from `frontend/`) |
|---|---|
| Run | `npm run dev` (http://localhost:5173) |
| Check | `npm run lint`, then `npm run build` |

## 4. API contract and tooling

- **The contract** is `docs/api-contract-proposed.md` (v0.6). Decisions D-1 to D-16, O-1 to O-9, R-3, R-4, R-8 and F-1 to F-5 are final; see its decision log (contract section 21).
- **Remaining questions** R-1, R-2, R-5, R-6, R-7, R-9 and R-10 (contract section 22) must be answered before anyone builds the behaviour they affect.
- **Database designs not yet proven** (contract section 22.3): the sealed child-row triggers, the stage-guard triggers, the operator deletion function, and task recovery. Only simplified stand-ins have been run (marked "ran" in the contract); M1 proves the real versions on a disposable Postgres before anything is merged.
- **Source of truth:** once endpoints exist, the backend's `/api/v1/openapi.json` (snapshot in `docs/openapi.json`).
- **Changing the contract** means updating that file in the same pull request as the code change.

**Tooling (D-15, contract section 15).** The folders and the export module are created on day one.

| Purpose | Command |
|---|---|
| Backend contract tests | `.\.venv\Scripts\python -m pytest -q tests/contract` (from `backend/`) |
| AI mock tests | `.\.venv\Scripts\python -m pytest -q tests/ai` (from `backend/`) |
| Refresh the OpenAPI snapshot | `.\.venv\Scripts\python -m app.tools.export_openapi > ..\docs\openapi.json` (from `backend/`) |
| Frontend types | `npx openapi-typescript ../docs/openapi.json -o src/lib/api-types.ts` (from `frontend/`) |

**Fixtures** live in `fixtures/api/<area>/<name>.json`. They are synthetic and deterministic, taken from the contract examples, and used by the backend contract tests, the frontend mocks and the mock job source.

**Deferred for the MVP:** Today view, DOCX export, email reminders, live job sources (until the mock workflow works), keeping uploaded resume files, Supabase Storage and the `retain_resume_file` option, any service-role key in the backend, and automated or self-service account deletion (deletion is operator-run in the MVP). PDF export comes only after all Must flows work.

## 5. Ownership

| Member | Owns | Must review |
|---|---|---|
| **M1: Technical and backend lead** | FastAPI routes, DB schema, migrations, RLS, auth, Evidence Ledger rules, approval gate, stage transitions, task runner with startup recovery and watchdog, maintenance functions, the operator runbook for deletion requests (verify, delete data, remove login), backend tests | Any change to schema, auth, approval, transitions, security |
| **M2: Frontend and student experience** | React app shell, routing, API client, all screens (onboarding, profile, jobs, fit, editor, evidence, approval, tracker, reminders, interviews, delete-my-data and account-closed), accessibility | Changes to `frontend/src/lib/api.ts` and shared UI |
| **M3: AI, integrations and background workflows** | `backend/app/ai/` implementations and mocks: resume parser (in memory only), mock job source and normalization, eligibility and fit scoring, document generation, evidence mapping, interview coach; AI mock tests | Changes to the AI interface types (contract section 14) |

The full per-endpoint table is in contract section 20.

## 6. Git and pull-request rules

- **Branches:** `main` is protected; nobody pushes to it directly. The repository owner still needs to turn on branch protection.
  - Use `<type>/<area>-<topic>`, where type is `feat`, `fix`, `chore` or `docs`, and area is `backend`, `frontend` or `ai`.
  - Examples: `feat/backend-applications`, `feat/frontend-onboarding`, `feat/ai-mock-job-source`, `fix/backend-deleted-user-401`.
- **Pull requests:** one topic per PR. Keep PRs small, around 400 changed lines where possible.
- **Before opening a PR,** rebase on `main` and run the tests and lint for every part you touched. There is no CI yet.
- **Review:** at least **one approval from another member**. The owner listed in the ownership table (section 5 of this guide) must also review changes in their area.
- **Merging:** squash-merge. Write the commit title as `type(area): summary`, for example `feat(backend): add applications state machine`.
- **Test data:** synthetic only, in fixtures, tests and the shared dev project.
- **Secrets:** never commit `.env`, `.env.local`, keys, passwords or connection strings.
  - Stage files by name. Don't run `git add .` without checking `git status` first.
  - If a secret gets committed, tell M1 immediately so it can be rotated.
- **Migrations** come only from M1, or with M1's review. Never edit a migration that has already been applied; add a new one.
- **Contract:** a PR that changes request or response shapes also updates the contract.
- **Trust rules:** no automatic application submission, and no outbound message without explicit student approval. Reviewers reject anything that breaks this.

## 7. First-day deliverables

| ID | Owner | Deliverable |
|---|---|---|
| ALL-1 | Everyone | Read the PRD and contract v0.6. Answer the remaining questions R-1, R-2, R-5, R-6, R-7, R-9 and R-10 (contract section 22) in one review meeting. |
| M1-1 | M1 | `feat/backend-foundation` already has local commit `108219b` (repo hygiene, `.env.example`, `PROGRESS.md`, frontend scaffold; it holds **no backend code**), which has not been pushed. The backend, `docs/`, the frontend auth code and other changes are still uncommitted. M1 runs `git status`, reviews `108219b` and the remaining changes (including the deleted scaffold assets and the untracked `.vscode/`), commits the rest in reviewable commits staged by file name without repeating what `108219b` already holds, and pushes and opens the first PR only when ready. |
| M1-2 | M1 | Security tasks SEC-1 (anonymous tokens), SEC-2 (role claim), SEC-3 (deleted user → 401) from contract section 19 |
| M1-3 | M1 | `backend/app/ai/interfaces.py` with the contract section 14 types and protocols (review with M3), plus stub routes that return the contract examples |
| M1-4 | M1 | Tooling skeleton: `fixtures/api/`, `tests/contract/`, `app.tools.export_openapi`, first `docs/openapi.json` |
| M1-5 | M1 | Prove the database designs on a **disposable PostgreSQL 17** against the real migrations. Acceptance criteria are listed below this table. |
| M1-6 | M1 | Shared Supabase project **security setup, with no migration**: create the `nexora_app` role (`docs/db-role.sql` Section 1), SEC-10 (turn off automatic exposure of new tables; keep `nexora_private` out of the exposed schemas), SEC-11 (credential hygiene), set and verify the 900 s token lifetime (SEC-9). Propose where the shared backend runs (contract R-2) and share its URL with M2. Keep database credentials with M1 only. |
| M1-7 | M1 | **First live migration** (`alembic upgrade head`). **Blocked** until all four conditions below are met. Finishing M1-6 does not unblock it. |
| M2-1 | M2 | App shell and routing on the existing scaffold; keep the auth flow in `src/auth` and `src/lib/api.ts` |
| M2-2 | M2 | Add `openapi-typescript` (pinned); build the typed API client **and its fixture-based mock mode** (reading `fixtures/api/`, created by M1-4); profile and onboarding screens against `GET/PATCH /profile/me`. Fixture mode does not exist until this task delivers it. |
| M3-1 | M3 | Mock `JobSource` serving about 20 varied synthetic jobs from `fixtures/api/jobs/`, plus `normalize` (canonical branch values; `location_restriction` only when explicit) |
| M3-2 | M3 | `evaluate_eligibility` with one test per reason code and the `unknown` rules (contract section 6) |
| M3-3 | M3 | Mock `ResumeParser` (in memory only, never writing the bytes anywhere) and the AI mock test suite (`tests/ai`). A live job source comes only after the mock workflow works and its terms are checked (D-11). |

**M1-5 acceptance criteria.** Every item must pass on a disposable PostgreSQL 17 using the real migrations. Test IDs are defined in the contract (v0.6).
1. **Original matrices:** stage guard G1–G17 (contract section 17.4), task recovery T1–T9 (section 18.9), rate limits RL1–RL9 (section 16.1).
2. **Additional tests that came out of the v0.5 review.** They are *not* covered by G1–G17 or by the earlier D1–D18. The contract defines them as the W series, G18–G22, and the rewritten D1–D19.
   - **Late child-row inserts into `approval_items`:** run as `nexora_app` against an existing approved application. Tests W1, W2 (section 17.2.2), G18 and G21 (section 17.4).
   - **Late child-row inserts into `evidence_validation_claims` and `evidence_claim_sources`:** run as `nexora_app` against finalized validations. Tests W3, W4, G19, G20 and G21. The seal-count tests W8–W12 and the monitoring query W18 belong here too, as does `submission_items` (W5).
   - **Cross-student deletion authorization attempts, including forged identity settings:** a runtime session that forges the identity setting and inserts its own deletion request must not be able to delete anyone's data. Tests D1, D2, D6, D19 (section 18.9) and W15 (forged identity against child rows).
   - **Cross-student exposure through stalled-deletion maintenance functions:** the functions `nexora_app` can execute must be exactly `recover_tasks` and `purge_expired_idempotency_keys`, and none may return student or request identifiers. The functions removed in v0.6 (`list_stalled_deletions`, `mark_deletion_failed`) must not be executable by it. Test D3 (an allow-list, so it covers this).
3. **Evidence status:** some of these tests were run only against simplified stand-in tables (the contract marks each one "ran" or "not run"). Those stand-in runs do not count toward M1-5. Only a pass against the real migrations does.

**M1-7 conditions.** The first live migration stays blocked until **all** of these hold:
1. The append-only child-row integrity concerns from the v0.5 review are resolved in the contract (section 17.2.2 and the stage-guard extension in section 17.4) and the team has accepted them (ALL-1).
2. The account-deletion authorization and maintenance-function concerns are resolved in the contract (sections 18.1, 18.4 and 18.7, operator-run deletion) and the team has accepted them (ALL-1; contract R-5, R-6 and R-10).
3. The M1-5 test matrix passes on the disposable PostgreSQL 17.
4. The Supabase-specific ownership and exposure checks pass (contract section 22.3): function ownership transfer, the `session_user` check through the pooler, `nexora_private` not exposed through the Data API, and statement timeouts through the pooler. M1 decides how to run them without applying the NEXORA migrations (for example in a throwaway scratch schema that is dropped afterwards).
