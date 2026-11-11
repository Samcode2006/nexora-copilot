-- =============================================================================
-- NEXORA: restricted application role `nexora_app`
-- =============================================================================
-- Run as `postgres` in the Supabase SQL Editor (role selector: postgres).
--
-- ORDER (important):
--   1. Run SECTION 1 here.                 -> creates the role
--   2. Run `alembic upgrade head` locally  -> creates tables and grants them to nexora_app
--   3. Run SECTION 2 here.                 -> post-migration fixes (safe to repeat)
--   4. Run SECTION 3 and SECTION 4 here.   -> read-only checks and an RLS test
--
-- The role MUST exist before step 2. Migrations 0001 and 0002 stop with an error
-- ("Role nexora_app does not exist") if it is missing, and nothing is applied.
-- SECTION 2 is kept as a recovery step for databases migrated by an earlier
-- version of 0001/0002 that skipped the grants instead of failing.
--
-- SECRETS: this file must never contain a real password.
--   - Replace <STRONG_PASSWORD> only in the SQL Editor, never in this file.
--   - Do not save the query as a snippet; delete it from the editor history afterwards.
--   - Generate a password locally (64 hex chars, no URL escaping needed):
--       $b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Fill($b); [Convert]::ToHexString($b)
--   - Put it only in DATABASE_URL in your local .env.
--     Pooler username format: nexora_app.<project-ref>
--
-- Every section is safe to run more than once.
-- =============================================================================


-- =============================================================================
-- SECTION 1: create the role (before migrations)
-- =============================================================================
-- Creates nexora_app if it is missing. If it already exists, the password is
-- left unchanged and the script stops if the role is misconfigured: an elevated
-- attribute, NOLOGIN, or an expired VALID UNTIL. Problems are reported, not
-- silently changed.
DO $setup$
DECLARE
  pw constant text := '<STRONG_PASSWORD>';  -- replace in the SQL Editor only
  r  pg_roles%ROWTYPE;
  problems text[] := '{}';
BEGIN
  SELECT * INTO r FROM pg_roles WHERE rolname = 'nexora_app';

  IF NOT FOUND THEN
    IF pw LIKE '<%>' OR length(pw) < 32 THEN
      -- The message must not contain the placeholder token: a find-and-replace-all
      -- would otherwise copy the password into the error output.
      RAISE EXCEPTION 'pw is still the placeholder or shorter than 32 characters; set a generated password first.';
    END IF;
    EXECUTE format(
      'CREATE ROLE nexora_app LOGIN PASSWORD %L '
      || 'NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS '
      || 'CONNECTION LIMIT 20',
      pw
    );
    RAISE NOTICE 'Created role nexora_app.';
  ELSE
    IF r.rolsuper       THEN problems := problems || 'SUPERUSER'::text;   END IF;
    IF r.rolcreatedb    THEN problems := problems || 'CREATEDB'::text;    END IF;
    IF r.rolcreaterole  THEN problems := problems || 'CREATEROLE'::text;  END IF;
    IF r.rolreplication THEN problems := problems || 'REPLICATION'::text; END IF;
    IF r.rolbypassrls   THEN problems := problems || 'BYPASSRLS'::text;   END IF;
    IF NOT r.rolcanlogin THEN problems := problems || 'NOLOGIN'::text;    END IF;
    IF r.rolvaliduntil IS NOT NULL AND r.rolvaliduntil <= now() THEN
      problems := problems || 'password expired (VALID UNTIL)'::text;
    END IF;

    IF cardinality(problems) > 0 THEN
      RAISE EXCEPTION 'nexora_app exists but is misconfigured: %. Nothing was changed.',
        array_to_string(problems, ', ')
        USING HINT = 'Review the role manually. For NOLOGIN only: ALTER ROLE nexora_app LOGIN;';
    END IF;
    RAISE NOTICE 'nexora_app already exists, can log in and is restricted. Password unchanged.';
  END IF;
END
$setup$;

-- Limits: caps connections (backend pool uses up to 7 per process) and runaway queries.
ALTER ROLE nexora_app CONNECTION LIMIT 20;
ALTER ROLE nexora_app SET statement_timeout = '15s';

-- Use objects in `public`, never create them. PUBLIC already holds USAGE on
-- `public` on Supabase; the explicit grant keeps the app working if that changes.
GRANT USAGE ON SCHEMA public TO nexora_app;

-- Deliberately NOT included: GRANT nexora_app TO postgres.
-- The app does not need it. SECTION 4 grants it temporarily inside a
-- transaction that is rolled back.


-- =============================================================================
-- SECTION 2: after `alembic upgrade head` (safe to repeat)
-- =============================================================================
-- Recovery only. On databases set up with the current code everything below is
-- a no-op:
--   - migrations always grant nexora_app (they fail if the role is missing);
--   - alembic/env.py protects alembic_version in the same transaction that
--     creates it (RLS on, anon/authenticated/service_role revoked; see
--     app/db/version_table.py).
-- It repairs databases migrated by an earlier version, where grants were skipped
-- or alembic_version was created without protection. Alembic never re-creates an
-- existing version table, so the hook cannot fix those.
DO $post$
BEGIN
  -- Repairs the case where migrations ran before the role existed.
  IF to_regclass('public.profiles') IS NOT NULL THEN
    GRANT SELECT, INSERT, UPDATE ON public.profiles TO nexora_app;
  END IF;

  -- Alembic's bookkeeping table must not be reachable through the Data API.
  -- service_role has BYPASSRLS, so it needs the revoke too (RLS alone won't stop it).
  IF to_regclass('public.alembic_version') IS NOT NULL THEN
    REVOKE ALL ON public.alembic_version FROM anon, authenticated, service_role;
    ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;
  END IF;
END
$post$;


-- =============================================================================
-- SECTION 3: read-only verification
-- =============================================================================

-- 3a. Expect: rolcanlogin = true, every other flag false, rolconnlimit = 20,
--     rolvaliduntil NULL or in the future.
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole,
       rolreplication, rolbypassrls, rolconnlimit, rolvaliduntil, rolconfig
FROM pg_roles WHERE rolname = 'nexora_app';

-- 3b. Expect: no rows. nexora_app must not be a member of any role.
SELECT m.roleid::regrole AS member_of
FROM pg_auth_members m
WHERE m.member = 'nexora_app'::regrole;

-- 3c. Schemas nexora_app can use. Expect: public. `net` also appears if the
--     pg_net extension is enabled (granted to PUBLIC by Supabase, cannot be
--     revoked); NEXORA does not need pg_net, so keep it disabled.
SELECT nspname AS schema
FROM pg_namespace
WHERE has_schema_privilege('nexora_app', oid, 'USAGE')
  AND nspname NOT IN ('pg_catalog', 'information_schema')
  AND nspname NOT LIKE 'pg\_%'
ORDER BY 1;

-- 3d. Expect: public_create = false, auth_usage = false.
SELECT has_schema_privilege('nexora_app', 'public', 'CREATE') AS public_create,
       has_schema_privilege('nexora_app', 'auth',   'USAGE')  AS auth_usage;

-- 3e. Effective table privileges in usable schemas (includes PUBLIC grants).
--     Expect: public.profiles -> INSERT, SELECT, UPDATE, and nothing else in public.
--     net.* rows appear only if pg_net is enabled (see 3c).
SELECT n.nspname AS schema, c.relname AS object,
       string_agg(p.priv, ', ' ORDER BY p.priv) AS privileges
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE']) AS p(priv)
WHERE c.relkind IN ('r','p','v','m','f')
  AND n.nspname NOT IN ('pg_catalog','information_schema')
  AND has_schema_privilege('nexora_app', n.oid, 'USAGE')
  AND has_table_privilege('nexora_app', c.oid, p.priv)
GROUP BY 1, 2
ORDER BY 1, 2;

-- 3f. Expect: relrowsecurity = true, owner = postgres (not nexora_app).
SELECT relname, relrowsecurity, relforcerowsecurity, pg_get_userbyid(relowner) AS owner
FROM pg_class WHERE oid = 'public.profiles'::regclass;

-- 3g. Expect: three policies (SELECT, INSERT, UPDATE) using request.jwt.claim.sub.
SELECT policyname, cmd, qual, with_check
FROM pg_policies WHERE schemaname = 'public' AND tablename = 'profiles';

-- 3h. Expect: no rows (no privilege of any kind for the API roles or nexora_app).
SELECT r AS role, p AS privilege
FROM unnest(ARRAY['anon','authenticated','service_role','nexora_app']) AS r
CROSS JOIN unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) AS p
WHERE has_table_privilege(r, 'public.alembic_version', p);

-- 3i. Expect: relrowsecurity = true, owner = postgres.
SELECT relrowsecurity, relforcerowsecurity, pg_get_userbyid(relowner) AS owner
FROM pg_class WHERE oid = 'public.alembic_version'::regclass;


-- =============================================================================
-- SECTION 4: RLS test as nexora_app (changes nothing; everything is rolled back)
-- =============================================================================
-- `postgres` cannot SET ROLE to nexora_app by default (on Postgres 16+ it only
-- holds an admin membership with SET off). The GRANT below is temporary: the
-- ROLLBACK undoes it together with everything else.
-- Check your version first: SHOW server_version;

BEGIN;
GRANT nexora_app TO postgres WITH SET TRUE, INHERIT FALSE;  -- Postgres 16+
-- GRANT nexora_app TO postgres;                            -- Postgres 15: use this line instead
SET LOCAL ROLE nexora_app;

SELECT current_user;                                        -- expect nexora_app
SELECT count(*) AS rows_without_identity FROM public.profiles;   -- expect 0

SELECT set_config('request.jwt.claim.sub', '<SOME_USER_UUID>', true);
SELECT id FROM public.profiles;                             -- expect only that user's row (if it exists)
ROLLBACK;

-- Confirm nothing was left behind. Expect: false.
SELECT pg_has_role('postgres', 'nexora_app', 'USAGE') AS postgres_inherits_nexora_app;
-- Expect: no rows granted by postgres (Postgres 16+ shows one supabase_admin admin row; that is normal).
SELECT m.member::regrole AS member, m.grantor::regrole AS grantor, m.admin_option
FROM pg_auth_members m WHERE m.roleid = 'nexora_app'::regrole;
