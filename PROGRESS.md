# NEXORA Backend Progress

Owner: Technical Lead & Backend Lead. Branch: `feat/backend-foundation`.
Rule: no secrets in this file. Update after every task.

## Verification levels
- **Implemented**: code or docs written.
- **Locally tested**: automated tests, lint, build or offline checks pass on this machine, with no database.
- **Local Postgres tested**: run against a disposable Docker PostgreSQL 17 with Supabase-like stubs (see 2026-11-10 log). Not Supabase.
- **Live verified**: confirmed against the real Supabase project (Auth, database or JWKS).

## Task tracker

| # | Task | Implemented | Locally tested | Local Postgres tested | Live verified |
|---|---|---|---|---|---|
| 0 | Repo hygiene, GitHub connection, progress tracker | yes | yes | n/a | n/a |
| 1 | Supabase configuration checklist (owner) | n/a | n/a | n/a | **no, waiting on owner** |
| 2 | FastAPI skeleton and health endpoint | yes | yes | yes (`/health/db`) | n/a |
| 3 | Config, CORS, standard error format | yes | yes | n/a | n/a |
| 4 | Supabase JWT verification (JWKS ES256/RS256, legacy HS256) | yes | yes (local keys, fake JWKS) | n/a | no |
| 5 | DB session, RLS identity propagation, Alembic (fail-fast on missing role), `docs/db-role.sql` | yes | yes | **yes** | no |
| 6 | `GET /api/v1/profile/me` | yes | yes | **yes** (HS256 test tokens) | no |
| F1 | Frontend Supabase Auth + Bearer token to FastAPI | yes | yes (tsc, eslint, build, bundle scan) | n/a | no (browser checklist not run) |

Review checkpoint: stopped after Task 6.

### Later (not started)
| # | Task |
|---|---|
| 7 | Schema v1 and RLS (agree names with Members 2 and 3 first) |
| 8 | Profile, facts, preferences and consent APIs |
| 9 | Evidence Ledger model and validation |
| 10 | Documents and versioning |
| 11 | Approval gate (append-only approvals) |
| 12 | Applications and stage transitions |
| 13 | Delete-my-data (adds DELETE grants) |
| 14 | API contracts and docs for Members 2 and 3 |
| 15 | End-to-end tests and hardening |

## Live verification still needed
The SQL logic is proven on local Postgres 17. These items depend on Supabase itself and are still open.

| Item | Why local testing does not cover it | How | Covers |
|---|---|---|---|
| `postgres` can create the FK to `auth.users` | The stub granted `postgres` `REFERENCES` (and `INSERT`/`DELETE` for tests) on `auth.users`; Supabase's real grants may differ | `alembic upgrade head` succeeds | Tasks 5, 6 |
| `RUN_DB_TESTS=1` user fixture | It inserts into `auth.users` as `postgres`; Supabase may not allow that | run pytest; if setup fails, switch the fixture to the Auth admin API | Tasks 5, 6 |
| Pooler login as `nexora_app.<project-ref>` over SSL | Local test used direct TCP without SSL | `/api/v1/health/db` | Task 5 |
| Project Postgres version | Section 4 uses the Postgres 16+ grant line; local was 17 | `SHOW server_version;` | Task 5 |
| SQL Editor runs Section 1 all-or-nothing | Emulated locally with `psql -1` | Section 1 error leaves no partial changes | Task 5 |
| "Automatically expose new tables" setting turned OFF (owner action in dashboard) | Dashboard setting; live default privileges currently grant new `public` tables to API roles | read-only check of `pg_default_acl` for `postgres` in `public` | Task 5 |
| `alembic_version` protected on the live DB | Hook proven on local Postgres 17 with the same default privileges as the live project | SQL 3h (no rows) and 3i (`relrowsecurity = true`) after the first migration; `RUN_DB_TESTS=1` `test_alembic_version_protected` | Task 5 |
| `pg_net` enabled or not | Not present locally | SQL 3c shows only `public` | Task 5 |
| Real Supabase token accepted, JWKS reachable | Local tests used HS256 test tokens and a fake JWKS | sign in on frontend, "Load my profile" | Tasks 4, 6, F1 |
| Frontend sign-up/in/out, session restore | Needs a browser and Supabase Auth | `docs/frontend-auth-checklist.md` | F1 |

## Decisions (no values)
- Auth: Supabase JWT verified in FastAPI; supports asymmetric (JWKS) and legacy HS256 by token `alg`.
- DB: SQLAlchemy async + asyncpg, Alembic; app role `nexora_app`; RLS as second layer.
- RLS policies read `request.jwt.claim.sub` directly (same value as `auth.uid()`), so the app role needs no grants on the `auth` schema.
- Migrations that grant to `nexora_app` must first check that it exists and raise an error if not (no silent skips).
- `alembic_version` is protected by an SQLAlchemy `after_create` hook installed in `alembic/env.py` (`app/db/version_table.py`), not by a migration: Alembic creates the table before migration 0001 runs, and `stamp`/`ensure_version` create it without running any migration.
- `nexora_app` is NOT granted to `postgres` permanently. The SQL Editor RLS test grants it inside a rolled-back transaction.
- Frontend uses Supabase for authentication only; all NEXORA data goes through FastAPI.
- Local briefs (`NEXORA_*.md`) are git-ignored by choice.
- Signing type: confirmed asymmetric ES256 via the project JWKS (2026-11-10). Pooler mode: session pooler (5432) planned, not yet configured.

## Owner actions needed (Task 1)
1. Fill `.env` (key names are in `.env.example`).
2. Confirm in Supabase: JWT signing key type, project region, pooler mode (session 5432 recommended), Postgres version (`SHOW server_version;`).
3. Run `docs/db-role.sql` section 1 in the SQL Editor (password replaced in the editor only, not saved as a snippet).
4. Put the `nexora_app` URL in `DATABASE_URL` and the owner URL in `MIGRATION_DATABASE_URL`.
5. From `backend/`: `.\.venv\Scripts\python -m alembic upgrade head`.
6. Run `docs/db-role.sql` sections 2, 3 and 4.
7. From `backend/`: `$env:RUN_DB_TESTS='1'; .\.venv\Scripts\python -m pytest -q`.

## Log

### 2026-11-10 Task 0
- Found existing local repo with `.env` and briefs staged. Added root `.gitignore`, unstaged them (index only, files untouched).
- Added `origin` (remote `main` had only `LICENSE`), based local work on it, created `feat/backend-foundation`.
- Commit `108219b`: `.gitignore`, `.env.example`, `PROGRESS.md`, `frontend/`. `.env`, `node_modules`, briefs not staged. Not pushed.

### 2026-11-10 Tasks 2-3
- Files: `backend/pyproject.toml`, `app/main.py`, `app/core/{config,errors}.py`, `app/api/v1/{router,health}.py`, tests.
- Locally tested: uvicorn boots; `/api/v1/health` ok; OpenAPI served; error envelope for 404/422/500/AppError; CORS restricted; startup fails fast when required env is missing.

### 2026-11-10 Task 4
- Files: `app/core/security.py`, `app/api/deps.py`, `tests/test_security.py`.
- Locally tested with generated keys and a fake JWKS: valid ES256/RS256/HS256; expired, wrong aud/iss, missing sub/exp, bad signature, `alg=none`, garbage, HS256-with-public-key confusion and malformed headers all return a generic 401.
- Not live verified: real Supabase token, live JWKS endpoint.

### 2026-11-10 Tasks 5-6
- Files: `app/db/{url,base,session}.py`, `app/db/models/profile.py`, `app/schemas/profile.py`, `app/api/v1/profile.py`, `/api/v1/health/db`, `alembic/` (0001 schema grant, 0002 profiles + RLS + grants), `docs/db-role.sql`, `tests/test_db_integration.py` (opt-in).
- Locally tested: `/health/db` returns a 503 envelope with no leak when the DB is unreachable; `alembic upgrade head --sql` renders the table, RLS, policies, `REVOKE ... FROM anon, authenticated` and the conditional `nexora_app` grants; `/profile/me` returns 401 without or with a bad token.
- Not live verified: migrations, role attributes, grants, RLS isolation, `/profile/me` with a real token.

### 2026-11-10 Frontend Supabase Auth (F1)
- Already done by owner: `@supabase/supabase-js@2.119.0`, `src/lib/supabaseClient.ts`, `.env.local` (keys set, git-ignored).
- Added: `src/auth/AuthContext.ts`, `src/auth/AuthProvider.tsx`, `src/lib/api.ts`, `src/vite-env.d.ts`, `frontend/.env.example`, `docs/frontend-auth-checklist.md`.
- Changed: `supabaseClient.ts` (refuses secret/service_role keys), `main.tsx` (`<AuthProvider>`), `App.tsx` (minimal auth harness).
- Locally tested: `tsc -b`, `eslint`, `vite build`; bundle contains no `sb_secret_` value. Owner approved the implementation.

### 2026-11-10 `docs/db-role.sql` revised (nothing executed)
- Removed the permanent `GRANT nexora_app TO postgres` and its misleading comment. The SQL Editor RLS test now grants it inside a transaction that is rolled back.
- Script is safe to repeat: creates the role only if missing, never resets the password, stops if an existing role has elevated attributes, rejects the unreplaced placeholder.
- Documents the required order (role before Alembic) and adds a post-migration section that repairs grants and revokes `alembic_version` from anon/authenticated.
- Added read-only checks, including effective privileges inherited through PUBLIC.
- Test status unchanged: 21 passed, 4 skipped; `ruff check` clean.

### 2026-11-10 Migrations fail fast on missing `nexora_app` (nothing executed against Supabase)
- `0001`: raises `Role nexora_app does not exist; migration 0001 aborted.` (with a HINT pointing to `docs/db-role.sql` Section 1) instead of a NOTICE; the schema `USAGE` grant is now unconditional. Downgrade stays tolerant of a dropped role.
- `0002`: same check as the first statement of `upgrade()`, before any table is created; the `profiles` grant is now unconditional. The check is repeated because a database may already be at 0001 from the old, non-failing version.
- Migrations run in one transaction (transactional DDL), so a failure applies nothing.
- `docs/db-role.sql` Section 1 now rejects an existing role that is NOLOGIN or has an expired VALID UNTIL, in addition to elevated attributes, and lists every problem found. It still changes nothing on an existing role. Section 2 is kept and labelled as recovery for databases migrated by the old version. Check 3a shows `rolvaliduntil`.
- Locally tested: `alembic upgrade head --sql` and `alembic downgrade 0002:base --sql` render as expected; 21 passed, 4 skipped (DB tests need `RUN_DB_TESTS=1`); `ruff check` clean.
- Not tested at the time: the fail-fast path and the Section 1 checks (covered by the next entry).

### 2026-11-10 Disposable local Postgres test (Docker; Supabase not touched)
- Environment: `postgres:17` (17.11) container `nexora-pgtest`, data on tmpfs (no volume), port bound to `127.0.0.1:55432` only. Every Alembic/pytest call refused to run unless both DB URLs pointed at that port. Throwaway passwords lived only in a temp folder, deleted afterwards.
- Supabase-like stubs: bootstrap superuser `supabase_admin`; `postgres` as a NON-superuser with CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS, owning database `nexora_test`; `anon`, `authenticated`, `service_role`, `supabase_auth_admin`; `auth.users` owned by `supabase_auth_admin`; legacy default privileges giving new `public` tables to API roles.
- Results: 68 checks passed. 1 failure was a harness string-comparison bug (`t` vs `true`), re-run and passed.
  - Migrations without `nexora_app`: fresh DB fails at 0001, DB stamped at 0001 fails at 0002; both leave nothing applied (no tables, version unchanged).
  - Section 1 rejects an existing role that is NOLOGIN, NOLOGIN+BYPASSRLS (both listed), or has an expired VALID UNTIL; role left unchanged. Rejects the unreplaced placeholder and a short password; no role created.
  - Section 1 creates the role with the expected attributes (login only, limit 20, `statement_timeout=15s`, no memberships). Re-running is a no-op and does not change the password (original password still logs in over SCRAM).
  - Migrations succeed once the role exists; Section 3 runs cleanly and every expectation holds (schemas = `public`; no `CREATE` on `public`; no `auth` usage; effective privileges = `profiles` INSERT/SELECT/UPDATE only; RLS on; three policies).
  - Section 2: no-op before migrations; revokes `alembic_version` from anon/authenticated (was exposed under legacy defaults); restores the `profiles` grants on a simulated old-version database (permission denied before, works after); idempotent.
  - Section 4 with two student UUIDs: without the grant `SET ROLE` is denied; inside the test `current_user` is `nexora_app`, no identity sees 0 rows, each student sees only their own row; after `ROLLBACK` `postgres` has SET=false and USAGE=false, and only the automatic admin membership (grantor `supabase_admin`) remains.
  - Cross-student writes as `nexora_app`: updating another student's row changes nothing; inserting another student's id and re-keying one's own row are rejected by RLS; DELETE is denied (no privilege).
  - `alembic downgrade base` then `upgrade head` works on a real database.
  - Backend: `RUN_DB_TESTS=1` pytest against the container 25 passed (incl. restricted role, `/health/db`, `/profile/me` per user, RLS isolation). Default run 21 passed, 4 skipped. `ruff` clean.
- Fix found by testing: Section 1's error message contained the `<STRONG_PASSWORD>` token, so a find-and-replace-all would copy the real password into the error output. Message reworded; re-tested (password not echoed).
- Cleanup: container removed (`--rm` and `docker rm -f -v`), no volume created, temp folder deleted, nothing listening on 55432. The `postgres:17` image (646 MB) is still cached locally.

### 2026-11-10 Live pre-migration inspection (read-only; nothing changed)
- Method: read-only `SELECT`s on project `Nexora` (`mhqrdsftecafmvlaixup`, ap-south-1) through the Supabase MCP connection (as `postgres`), because the `.env` database URLs are empty. Public JWKS fetched over HTTPS. No migrations, no DDL, no writes.
- Postgres 17.11 (`170011`): use the Postgres 16+ grant line in `docs/db-role.sql` Section 4.
- `pg_net`: not installed (available), no `net` schema. Check 3c should show `public` only.
- Data API exposure: `postgres` default privileges in `public` grant ALL on new tables, sequences and functions to `anon`, `authenticated`, `service_role` ("Automatically expose new tables" behaviour is ON).
- Clean target: no tables in `public` (no `profiles`, no `alembic_version`); role `nexora_app` does not exist yet.
- `auth.users`: owned by `supabase_auth_admin`, `id uuid` primary key, RLS on, 0 users, no user triggers. `postgres` has USAGE on `auth` and REFERENCES (table and `id` column), SELECT, INSERT, DELETE on `auth.users`, so the `profiles` FK can be created.
- `postgres` attributes: not superuser; CREATEROLE, CREATEDB, BYPASSRLS, LOGIN.
- JWT: JWKS has one ES256 (P-256) key, so the project uses asymmetric signing. `SUPABASE_JWT_SECRET` is not needed.
- `.env`: `SUPABASE_URL` still holds the template placeholder (does not match the frontend project). `DATABASE_URL` and `MIGRATION_DATABASE_URL` are empty, so pooler host/port/role checks could not run.

### 2026-11-10 `alembic_version` protected at creation (local only; Supabase not touched)
- Lifecycle (Alembic 1.20.1, SQLAlchemy 2.1.8, verified in source): `alembic_version` is created by `MigrationContext._ensure_version_table()` via `Table.create(checkfirst=True)` before the first migration on `upgrade`/`downgrade` of an empty DB, and by `stamp` and `ensure_version` with no migration at all. `current` never creates it. In `--sql` mode it is created at the start of the first step.
- Implementation: `backend/app/db/version_table.py` registers two SQLAlchemy `after_create` listeners on `Table`, filtered to `alembic_version`: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and a guarded `REVOKE ALL ... FROM anon, authenticated`. `alembic/env.py` installs them before configuring Alembic. They run on the migration connection, inside the same transaction as `CREATE TABLE`. No migration changes; `nexora_app` gets nothing.
- `docs/db-role.sql`: Section 2 is now recovery-only and also enables RLS on a legacy `alembic_version`; checks 3h (all privileges for anon/authenticated/nexora_app) and 3i (RLS, owner) replace the old SELECT-only check.
- Tests added: `tests/test_version_table.py` (no DB: listener idempotence, filter, asyncpg rendering of `%s`/`%I`); `test_alembic_version_protected` in `tests/test_db_integration.py` (opt-in; also usable on live).
- Disposable Docker Postgres 17.11 (tmpfs, `127.0.0.1:55432`, same default privileges as the live project): **83 checks passed, 0 failed**. 22 earlier attempts were superseded after harness bugs (a PowerShell `$C` variable collision, a pytest transaction misuse in the new test, `-q -v` output, trailing blank lines); all re-ran and passed.
  - Fault injection (event triggers raising on `ALTER TABLE` or on `REVOKE`) for `upgrade`, `stamp`, `ensure_version`, `downgrade`: Alembic exits 1 and `alembic_version` does not exist afterwards in all 8 runs. Control run without fault creates the protected table.
  - Fresh DB per path (`upgrade head`, `stamp head`, `ensure_version`, `downgrade base`): RLS on (not forced), owner `postgres`; anon/authenticated/nexora_app hold none of the 7 table privileges; ACL has no anon/authenticated entry; anon and authenticated denied SELECT/INSERT/UPDATE/DELETE (8/8); owner inserts/updates/reads in a rolled-back transaction; `alembic current` works. Control table in the same DB is exposed to anon/authenticated, proving the hook (not the setup) removes the exposure.
  - asyncpg path: the Postgres server log shows `EXECUTE format('REVOKE ALL ON TABLE %s FROM %I', 'alembic_version', r)` (single `%`, no `%%`) and `ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY`; env.py's migration URL resolves to `postgresql+asyncpg`.
  - Existing table: on a protected DB and on a legacy unprotected DB, 7 Alembic operations (upgrade, current, ensure_version, stamp, downgrade, upgrade, stamp) leave the table's oid, RLS flag and ACL unchanged; no DDL touched `alembic_version` (event-trigger log); REVOKE count equals the migrations' own. The hook does not repair a legacy table; Section 2 does, and is idempotent.
  - `test_alembic_version_protected` fails on an exposed table and passes on a protected one. `RUN_DB_TESTS=1`: 30 passed on both the fresh and the repaired DB. `nexora_app` effective privileges remain `profiles` INSERT/SELECT/UPDATE only.
- Local without DB: 25 passed, 5 skipped; `ruff` clean; offline `upgrade head --sql` = BEGIN, CREATE alembic_version, ENABLE RLS, REVOKE, then 0001 ... COMMIT; offline downgrade renders.
- Cleanup: container removed, no volume, temp folder deleted, port free.

### 2026-11-10 `alembic_version` hook also revokes `service_role` (local only; Supabase not touched)
- Why: `service_role` has BYPASSRLS on Supabase, so RLS alone does not stop it, and the project's default privileges give it ALL on new `public` tables.
- `app/db/version_table.py`: the guarded revoke loop now covers `anon`, `authenticated`, `service_role`. `docs/db-role.sql`: Section 2 recovery revokes all three; check 3h checks `anon`, `authenticated`, `service_role`, `nexora_app`. Tests: `test_alembic_version_protected` now includes `service_role`; the asyncpg rendering test asserts the three-role array.
- Disposable Docker Postgres 17 (tmpfs, `127.0.0.1:55432`, same default privileges as the live project): **26 checks passed, 0 failed**.
  - `upgrade head`, `stamp head`, `ensure_version` on fresh DBs: all three roles hold 0 of 7 table privileges; ACL is owner-only (`{postgres=arwdDxtm/postgres}`); RLS on; `service_role` (BYPASSRLS) denied SELECT/INSERT/UPDATE/DELETE 4/4; owner can still insert/update/read. A plain new table in the same DB is granted to `service_role`, so the hook is what removes it.
  - Legacy unprotected table: the hook leaves it alone (all three roles still exposed after `upgrade head`); Section 2 removes every privilege from all three and enables RLS; second run is a no-op; check 3h returns no rows.
  - `RUN_DB_TESTS=1`: 30 passed on the fresh and on the repaired DB. `test_alembic_version_protected` passes on a protected table and fails when only `service_role` holds a privilege.
- Local without DB: 25 passed, 5 skipped; `ruff` clean; offline upgrade SQL renders the three-role revoke before 0001; offline downgrade renders.
- Fault-injection rollback and existing-table tests were not repeated: the change only extends the role array inside the same DO statement, so the transaction behaviour proven in the previous entry is unchanged.
- Cleanup: container removed, no volume, temp folder deleted, port free.

### 2026-11-10 Security hardening verification and API contract proposal (no Supabase, no commits)
- Hook and recovery SQL already covered `anon`, `authenticated`, `service_role` (previous entry); no code change needed this round.
- Re-verified: no-DB pytest 25 passed, 5 skipped; `ruff` clean; offline upgrade SQL = BEGIN, CREATE alembic_version, RLS, three-role REVOKE, 0001, 0002, COMMIT; offline downgrade renders.
- Disposable Docker Postgres 17 (tmpfs, `127.0.0.1:55432`, live-like default privileges): 9/9 checks passed. Fresh `upgrade head`: anon/authenticated/service_role/nexora_app hold 0 privileges on `alembic_version`, ACL owner-only, RLS on; `RUN_DB_TESTS=1` 30 passed; `downgrade base` keeps the (still protected) empty version table and drops `profiles`; `upgrade head` again; 30 passed again. One earlier attempt was invalid (container not running, harness cleanup ran late) and was re-run.
- Added `docs/api-contract-proposed.md` (draft for team review): conventions, error codes, and proposed endpoints for profile, resume, jobs/eligibility, fit, documents, Evidence Ledger, approval, applications, interviews, AI module interfaces, ownership, open questions.

### 2026-11-10 Contract v0.2 and team onboarding (documents only)
- `docs/api-contract-proposed.md` revised to v0.2. Separate document and application lifecycles; approvals reference exact version + validation; facts carry revisions; generic task resource with error codes; eligibility exclusion codes; AI interfaces as Python types; security tasks SEC-1 to SEC-10; ownership table; 16 open decisions (D-1 to D-16).
- Added `docs/TEAM_START_HERE.md`.
- Found: `pip install -e ".[dev]"` failed (setuptools flat-layout discovery: no `[build-system]`/package config in `backend/pyproject.toml`). Fixed in the next entry.

### 2026-11-10 Backend packaging fixed (no logic changes)
- `backend/pyproject.toml`: added `[build-system]` (`setuptools>=77`, `setuptools.build_meta`) and `[tool.setuptools.packages.find] include = ["app*"]`. Only `app` is packaged; `tests/` and the `alembic/` migrations folder are not, so the folder can't shadow the `alembic` library.
- Root `.gitignore`: added `*.egg-info/`, `build/`, `dist/` (the editable install writes `backend/nexora_backend.egg-info`; verified ignored).
- Verified in a brand-new venv (Python 3.14, only pip installed beforehand): `pip install -e ".[dev]"` succeeds as an editable install; `pip check` clean; from outside `backend/`, `import app` resolves to the source tree and `import alembic` to the library; `tests` is not installed; pytest 25 passed, 5 skipped; ruff clean; `alembic upgrade head --sql` and `downgrade 0002:base --sql` exit 0. Temporary venvs removed.
- `docs/TEAM_START_HERE.md`: setup now uses `pip install -e ".[dev]"`; first-day task M1-2 removed.

### 2026-11-10 Contract v0.3: decisions D-1 to D-16 applied (documents only)
- `docs/api-contract-proposed.md` rewritten as v0.3: lifecycle diagrams (Mermaid), `withdrawn` stage, manual applications, duplicate guard (409 `APPLICATION_EXISTS` + DB unique index), required/optional documents for approval, revocation, immutable submission snapshots, fact archive/revisions, strict eligibility with `location_restriction`, in-app reminders, configuration (section 16), tooling (section 15), database implications (section 17), decision log (section 20), open questions O-1 to O-9 and resolved implications I-1 to I-7 (section 21).
- `docs/TEAM_START_HERE.md` updated: dev database rules (D-16), tooling commands (D-15), deferred features, synthetic-data rule, section references, first-day deliverables.
- No code, migrations, `.env` or Supabase changes.

### 2026-11-10 Contract v0.4: O-1 to O-9 applied, security review (documents only)
- `docs/api-contract-proposed.md` v0.4:
  - Decisions: archive → stale; explicit two-event invalidation; re-save after withdraw (partial unique index excluding `withdrawn`); manual `job_description` with job/manual/generic contexts; `eligible_locations`; four hourly limits; 900 s token lifetime; no DB credentials for M2/M3; withdrawn locked but readable.
  - New sections: D-1 guarantee table (3.3), transaction rules (3.6), submitted-snapshot guarantees (11.1), immutable-record controls (17.2), active-uniqueness walkthrough (17.3), commit-time stage guard (17.4).
  - Deletion: `nexora_deleter` role plus a SECURITY DEFINER function replaces the settable-variable exception (section 18).
- Access-token lifetime: target 900 s. **Configured value: not verified** (no Supabase access in this round). Owner action is in contract SEC-9.
- `docs/TEAM_START_HERE.md`: credentials rules (O-8), backend URL, section references, first-day tasks.
- Nothing tested: these are design documents. The partial index and stage-guard behaviour are described, not run.

### 2026-11-10 Contract v0.5: targeted corrections (documents only)
- `docs/api-contract-proposed.md` v0.5. Sections changed: header, 1, 1.1, 2 (new 2.1 and 2.2), 3.1, 3.6, 4, 5 (rewritten), 9, 12, 13, 14, 16, 17.1, 17.2, 17.2.1 (new), 17.4 (rewritten), 18 (rewritten, 18.1 to 18.9), 19, 20, 21, 22.
- **Stage guard (17.4):** corrected the invalid statement-level constraint trigger. Constraint triggers are `AFTER ... FOR EACH ROW` only (checked against the PostgreSQL 17 `CREATE TRIGGER` page). New mechanism: row-level deferred triggers on `applications`, `application_events`, `documents`, `document_versions`, `evidence_validations`, `approval_revocations` and `profile_facts` (with a `WHEN` on revision/status), all calling one check function. The service cascades stage changes in the same transaction. Test matrix G1 to G17.
- **Deletion (18):** `deletion_requests` is no longer deleted by the function; it stays and cascades away with the Auth user. A separate `nexora_private.deletion_audit` survives, holding counts and timestamps. `student_id` is kept only until the login is removed (target 7 days), the rest for 12 months (**proposed, needs confirmation: R-5**), readable by the migration owner only. Single-transaction deletion, idempotent, residue-safe, with a failure matrix. Account is closed (403 `ACCOUNT_CLOSED`) from the request (**R-6**).
- **Immutability (17.2.1):** removed the claim that triggers stop privileged users. Trust boundaries now listed for the runtime role, definer roles, migration owner and platform administrators. New SEC-13 detects disabled triggers.
- **SECURITY DEFINER (18.3):** `SET search_path = pg_catalog, pg_temp`, qualified names, no dynamic SQL, per-function owner and `EXECUTE` grants, create/revoke/grant in one transaction. Tests D1 to D18 (cross-student, shadowing, partial failure, catalog checks).
- **Tasks (2.1, 2.2):** startup recovery fails `queued` and `running` tasks, watchdog every 60 s, compare-and-set transitions so a failed task can never commit, per-operation uniqueness so retries create no duplicate versions, validations or submissions. Tests T1 to T9. Single-instance shortcut documented.
- **R-3 applied:** resumes parsed in memory and never stored; `retain_resume_file` reserved (422); no service-role key in the MVP backend; manual Auth-user removal (18.6); Storage left possible later.
- **R-4 applied:** limits for explicit revalidation (30/h) and job refresh (30/h); automatic validation separate (`trigger` column).
- Whole-contract check: scripted cross-reference check found no dangling section, SEC, R, O, D or I references; table column counts consistent; code fences balanced. Search found and fixed stale uses of the removed `retain_file`, a statement-level trigger, and "no limit" text.
- `docs/TEAM_START_HERE.md`: v0.5 references, credentials wording, deferred list, new first-day task M1-6.
- **Nothing was run or tested.** The guard triggers, definer functions and recovery logic are designs; G1 to G17, D1 to D18 and T1 to T9 have never executed.

### 2026-11-11 `docs/TEAM_START_HERE.md` aligned with contract v0.5 (documents only)
- Found no remaining v0.4 text; the guide already said v0.5. A script confirmed every `D`, `O`, `R`, `SEC`, `G`, `T` ID and every contract section number it cites exists in the contract.
- Added a "Credentials at a glance" table (section 1): frontend uses Supabase Auth with the publishable key; FastAPI uses the restricted `nexora_app` role; only M1 holds database credentials; M2 and M3 hold none.
- Setup (section 3): `.env` step split by role so M2 and M3 are not asked for `DATABASE_URL` or `MIGRATION_DATABASE_URL`; added a resume-upload rule (in memory, no retention, Storage deferred, no service-role key in the MVP backend); `VITE_API_BASE_URL` falls back to mock mode until R-2 is settled.
- Section references now say "contract section N" where they mean the contract; ownership rows match contract section 20; first-day tasks M1-5 and M1-6 reordered (prove designs first, then the shared-project setup).

### 2026-11-11 Contract v0.6: targeted corrections (documents only; two throwaway SQL prototypes)
- `docs/api-contract-proposed.md` v0.6. Sections changed: header, 1, 1.1, 3.1, 3.6, 4, 8, 9, 13, 16 (new 16.1), 17.1, 17.2, 17.2.1, 17.2.2 (new), 17.4, 18 (rewritten), 19, 20, 21, 22. `docs/TEAM_START_HERE.md`: v0.6 references, remaining-question and test-range lists, credentials and ownership wording.
- **F-1 sealed child rows (17.2.2):** closes a gap where `nexora_app` could insert into `approval_items`, `evidence_validation_claims`, `evidence_claim_sources` (and `submission_items`) after the parent existed. Window: only the parent's own transaction (`created_txid = pg_current_xact_id()`, `BEFORE INSERT` triggers, `NX003`), plus declared child counts checked at commit (`NX004`).
- **F-2 / F-3 deletion (18):** with one shared role and an identity setting the runtime controls, per-student authorization cannot be guaranteed. Deletion is **operator-run**. `nexora_app` can no longer execute `execute_deletion`; the JWT-setting check is gone; `list_stalled_deletions`, `mark_deletion_failed` and the student retry endpoint are removed. Statuses are `requested`, `data_deleted`, `rejected`. Threat model, operator runbook and 19 tests added. RLS is no longer described as preventing impersonation by a compromised runtime.
- **F-4 stage guard (17.4):** fourth invariant (sealed contents), constraint triggers on the three child tables, regression tests G18 to G22.
- **F-5 / R-8 rate limits (16.1):** edit (60/h per application), claim-link (120/h per application) and per-student (300/h) limits. Claim linking needs its own limit because every call appends a full immutable validation. Tests RL1 to RL9. Defaults are proposals (R-9).
- **What actually ran:** on 2026-11-11, a throwaway PostgreSQL 17.11 container (tmpfs, `127.0.0.1` only, since removed) with simplified stand-in tables. Child-row window: W1 to W4, W6 to W16 passed as the contract describes (late inserts rejected with `NX003` while `nexora_app` had a student identity; count mismatches failed at commit with `NX004`; same-transaction and savepoint inserts committed; explicit `created_txid` and UPDATE/DELETE denied). Deletion: D1, D2 (first three roles), D4, D5 (unknown id, invalid method), D6, D7 (re-run deletes 0), D8 (`prosecdef`, owner, `search_path`), D9, D19 passed. The prototype SQL was not kept.
- **Not run:** everything else, including all of G1 to G22, T1 to T9, RL1 to RL9, W5 and W17 to W19, and the rest of D. Nothing ran against the real schema, real migrations or Supabase.

### 2026-11-11 `docs/TEAM_START_HERE.md` first-day tasks corrected (documents only)
- M1-1 now states the real git state, checked read-only: `108219b` holds hygiene files and the frontend scaffold, **no backend code**; `backend/`, `docs/`, frontend auth code and other changes are uncommitted. M1 reviews `git status`, commits the rest by file name, and pushes only when ready.
- M1-5 gets explicit acceptance criteria (late child inserts, forged-identity deletion attempts, maintenance-function exposure, plus the original matrices). Stand-in runs do not count.
- M1-6 (Supabase security setup, no migration) is split from a new M1-7 (first live migration), which stays blocked until the contract concerns are accepted, the M1-5 matrix passes on disposable PostgreSQL 17, and the Supabase ownership and exposure checks pass.
- M2-2 now says fixture mode does not exist until M2-2 builds it.

### Open issues
- Contract remaining questions R-1, R-2, R-5, R-6, R-7, R-9, R-10 (section 22) need team answers.
- Unverified before implementation (contract 22.3): ownership transfer of `SECURITY DEFINER` functions on Supabase, `nexora_private` not exposed through the Data API, statement-timeout behaviour through the pooler, the 900 s token lifetime.
- Owner action: turn off "Automatically expose new tables" in the Supabase Data API settings (not done by the agent).
- Every future migration must grant `nexora_app` explicitly; Supabase no longer auto-grants new tables (from 30 Oct 2026).
- Task 7 needs table/column names agreed with Members 2 and 3 first.
- `NEXORA_MVP_Scope.md` is empty.
- All work after `108219b` is uncommitted.
