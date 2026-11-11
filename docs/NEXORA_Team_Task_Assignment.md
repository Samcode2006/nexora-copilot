# NEXORA --- Team Task Assignment

**Repository:** `https://github.com/Samcode2006/nexora-copilot`\
**Base branch:** `main`\
**Project:** Evidence-grounded, human-in-the-loop AI placement co-pilot

This document defines the starting tasks and Git branches for the
frontend and AI/integrations workstreams. Follow the current API
contract and team guide in `docs/`; do not invent new API shapes or
silently change agreed product rules.

## 1. Git workflow --- mandatory

  ----------------------------------------------------------------------------
  Team member             Assigned branch              Ownership
  ----------------------- ---------------------------- -----------------------
  Member 2 --- Frontend   `feat/frontend-student-ui`   React student
                                                       experience and frontend
                                                       API integration

  Member 3 --- AI &       `feat/ai-integrations`       Resume parsing, job
  Integrations                                         processing, document
                                                       generation, interview
                                                       AI and provider
                                                       adapters
  ----------------------------------------------------------------------------

Both branches should be based on the latest `main`. Each person must
work only on their assigned branch.

### Initial setup

Clone the repository once:

``` bash
git clone https://github.com/Samcode2006/nexora-copilot.git
cd nexora-copilot
```

Member 2:

``` bash
git switch feat/frontend-student-ui
git pull origin feat/frontend-student-ui
```

Member 3:

``` bash
git switch feat/ai-integrations
git pull origin feat/ai-integrations
```

Before starting work each day:

``` bash
git status
git pull
```

Commit and push only to your assigned branch:

``` bash
git add <your-files>
git commit -m "feat: describe the change"
git push
```

Open a Pull Request from your assigned branch **into `main`**. Do not
push directly to `main`, force-push shared branches, or merge your own
PR without the agreed review.

If `main` changes and your branch needs updating, coordinate first. Do
not merge another member's feature branch into yours as a shortcut.

## 2. Shared project rules

1.  Read `docs/TEAM_START_HERE.md` and `docs/api-contract-proposed.md`
    before implementation.
2.  Treat the API contract as the source of truth for endpoint names,
    request/response shapes, status values, validation rules and error
    codes.
3.  Use synthetic test data only. Never use real student resumes or
    personal information in development fixtures.
4.  Never request, copy, commit or share the root `.env`, database
    passwords, migration credentials, Supabase service-role keys or
    other secrets.
5.  Member 2 must use the frontend mock/fixture mode until the shared
    FastAPI backend URL is provided by Member 1.
6.  Member 3 must develop AI components with deterministic mocks and
    fixtures. Do not connect directly to the database or persist
    application data from AI nodes.
7.  Keep business rules, authorization, persistence and approval
    decisions in the backend. An LLM must not approve applications,
    bypass validation or perform arbitrary database writes.
8.  Do not implement automatic job applications, employer-portal
    submission or outbound messages. The student remains in control.
9.  Do not add dependencies, change shared contracts, or modify another
    workstream's owned files without discussing it with the team.
10. Add or update tests for every meaningful feature. Keep lint,
    type-check and build commands passing.

## 3. Member 2 --- Frontend & Student Experience

**Branch:** `feat/frontend-student-ui`\
**Stack:** React, TypeScript, Vite; use the existing frontend
conventions and installed UI libraries.

### A. First tasks --- foundation

-   [ ] Inspect the existing `frontend/` structure before changing
    files.
-   [ ] Confirm the app starts, builds, type-checks and lints.
-   [ ] Establish the application shell, navigation, page layout and
    responsive behaviour.
-   [ ] Add routing for the agreed student-facing screens.
-   [ ] Keep authentication integration aligned with the existing
    Supabase Auth context.
-   [ ] Create or refine a typed API client. It must attach the current
    access token when calling the backend and handle the standard API
    error envelope.
-   [ ] Add a mock API/fixture mode so the UI can be developed without a
    live backend.
-   [ ] Keep mock data separate from production API code.

### B. Student experience screens

Implement in small, reviewable increments:

-   [ ] Sign up, sign in, sign out and session/loading/error states.
-   [ ] Onboarding and editable student profile.
-   [ ] Resume upload interaction and parsed-profile review. The MVP
    processes uploads in memory; do not build persistent resume storage.
-   [ ] Profile facts/evidence review, including source and verification
    status where returned by the API.
-   [ ] Job discovery list and job details.
-   [ ] Eligibility result with clear hard-filter outcomes and exclusion
    reasons.
-   [ ] Explainable fit score, including matched and missing
    requirements. Do not imply that a score guarantees selection.
-   [ ] Document editor for generated resume/cover-note versions.
-   [ ] Evidence Ledger view showing which verified facts support
    generated claims.
-   [ ] Validation results, unsupported-claim warnings and
    stale-validation states.
-   [ ] Approval screen. Disable approval when required validation is
    missing, failed or stale. Show the exact document version being
    approved.
-   [ ] Application tracker with the contract's application stages and
    history.
-   [ ] Mock interview screens and feedback display.
-   [ ] In-app reminders, where supported by the API.
-   [ ] Account/data-deletion request and account-closed states,
    following the contract.

### C. Frontend behaviour and acceptance criteria

-   [ ] Use API contract types; do not create competing status enums or
    endpoint shapes.
-   [ ] Show loading, empty, success and recoverable error states.
-   [ ] Do not treat unknown eligibility data as eligible.
-   [ ] Clearly distinguish a document's lifecycle from an application's
    lifecycle.
-   [ ] Display approval as an explicit student action. Never
    auto-approve.
-   [ ] If a document changes after approval, show that the new version
    requires revalidation/reapproval.
-   [ ] Once an application is submitted, respect the contract's
    submitted-version immutability rules.
-   [ ] Make forms keyboard accessible and provide labels and useful
    validation messages.
-   [ ] Test the UI with deterministic fixtures, including failed,
    stale, missing-evidence and empty states.

### D. Frontend deliverables

-   [ ] Working responsive student-facing shell and routes.
-   [ ] Typed API client and mock/fixture mode.
-   [ ] Screens implemented against the API contract.
-   [ ] Component/page tests for important flows and edge cases.
-   [ ] Updated frontend setup instructions if required.
-   [ ] Pull Request with screenshots or a short recording, test
    commands and known gaps.

### E. Frontend boundaries

Member 2 owns `frontend/` and frontend-specific documentation/tests.
Coordinate before changing shared API contract files, backend code,
database migrations, shared fixtures or root configuration. Do not add
database credentials to frontend environment files. The frontend may use
only the Supabase publishable key and project URL where required for
Supabase Auth.

## 4. Member 3 --- AI, Integrations & Background Workflows

**Branch:** `feat/ai-integrations`\
**Stack:** Python, existing FastAPI backend conventions, provider
adapter pattern; LangGraph only after individual workflow nodes work.

### A. First tasks --- AI foundation

-   [ ] Inspect the existing backend structure and current AI interfaces
    before implementation.
-   [ ] Read the AI/tooling sections of `docs/api-contract-proposed.md`.
-   [ ] Define provider interfaces behind a small adapter layer; avoid
    coupling business logic to one LLM vendor.
-   [ ] Implement deterministic mock providers and fixtures first. The
    default development configuration must work without paid API keys.
-   [ ] Keep prompts, schemas and provider-specific code separate from
    backend authorization and persistence.
-   [ ] Return structured, schema-validated outputs. Handle malformed,
    incomplete, timed-out and unavailable provider responses.

### B. Resume parsing and student facts

-   [ ] Implement resume text extraction for the formats explicitly
    supported by the contract.
-   [ ] Validate file type, size and parsing errors according to the
    contract.
-   [ ] Process uploaded files in memory for the MVP. Do not persist raw
    resumes or create a Storage bucket.
-   [ ] Extract candidate facts into a structured response with source
    references and confidence/uncertainty where the contract supports
    them.
-   [ ] Do not invent missing dates, skills, qualifications, scores or
    experience.
-   [ ] Keep extracted facts reviewable; parsing does not itself make a
    fact verified.
-   [ ] Add synthetic fixtures for clean, malformed, sparse and
    ambiguous resumes.

### C. Job normalization, eligibility and fit

-   [ ] Build a mock job source first, using synthetic job records.
-   [ ] Normalize job descriptions and requirements into the agreed
    schema.
-   [ ] Implement hard eligibility checks before fit scoring.
-   [ ] Treat missing profile information as unknown, not as a pass.
-   [ ] Apply explicit employer location restrictions as hard filters;
    ordinary student location preferences remain soft preferences as
    defined in the contract.
-   [ ] Return exclusion reason codes and the
    criteria/required/actual/message details required by the contract.
-   [ ] Produce explainable fit components, matched requirements and
    missing requirements.
-   [ ] Do not use name, gender, photograph or college tier as scoring
    inputs.
-   [ ] Add tests for eligible, ineligible, unknown and boundary cases.

### D. Evidence-grounded document generation

-   [ ] Generate resume content and optional cover notes only from
    verified student facts.
-   [ ] Preserve source fact references for every generated
    claim/sentence as required by the contract.
-   [ ] Do not create unsupported achievements, metrics, skills,
    employment or project claims.
-   [ ] Return structured document content and claim-to-fact mappings
    for backend validation.
-   [ ] Respect the contract's cover-note length and document-version
    rules.
-   [ ] If a manual application has no job description, keep
    job-specific document generation blocked as specified by the current
    contract.
-   [ ] Do not implement approval logic in the AI layer. The backend
    validates and persists; the student explicitly approves.
-   [ ] Add tests for unsupported claims, missing evidence, stale fact
    revisions and valid evidence mappings.

### E. Mock interviews and feedback

-   [ ] Generate role/job-relevant interview questions from available
    job context.
-   [ ] If job description/context is unavailable, avoid pretending the
    questions are job-specific.
-   [ ] Evaluate answers against explicit criteria and return structured
    feedback.
-   [ ] Persist weak-area or progress data only through backend-owned
    interfaces, not direct database access.
-   [ ] Use deterministic mock evaluation for local development and
    tests.
-   [ ] Add tests for empty answers, malformed model output and provider
    failure.

### F. Background workflows and orchestration

-   [ ] Implement AI workflow steps as independently testable
    functions/nodes first.
-   [ ] Use the agreed task request/result/status contract and
    idempotency behaviour.
-   [ ] Make retryability and failure information explicit.
-   [ ] Ensure retries do not create duplicate document versions or
    duplicate side effects.
-   [ ] Coordinate task startup recovery/watchdog behaviour with Member
    1, who owns backend task persistence and recovery.
-   [ ] Introduce LangGraph only when the individual nodes and contracts
    are stable.
-   [ ] Use selective RAG only for sourced job/company knowledge or
    interview preparation where it adds value. Student facts must come
    from structured, verified profile data, not vector retrieval.
-   [ ] Do not add Redis, Celery, Kubernetes or a separate vector
    database for the MVP without team approval.

### G. AI deliverables

-   [ ] Provider adapter and deterministic mock provider.
-   [ ] Resume parsing module with synthetic fixtures.
-   [ ] Job normalization, eligibility and explainable fit components.
-   [ ] Evidence-grounded document-generation component.
-   [ ] Interview question generation and answer evaluation components.
-   [ ] Unit/contract tests and example fixture outputs.
-   [ ] Documentation of required environment variable names and safe
    mock-mode setup (never include secret values).
-   [ ] Pull Request with test commands, sample synthetic outputs and
    known limitations.

### H. AI boundaries

Member 3 owns AI modules, provider adapters, AI-specific fixtures and
tests. Coordinate before changing shared backend interfaces, API
contract files, database schema/migrations or task persistence. AI code
must not connect directly to Supabase, write to the database, alter
application stages, create approvals, or submit applications. Backend
services validate AI outputs and own persistence and authorization.

## 5. Definition of done for every Pull Request

A PR is ready for review only when:

-   [ ] It targets `main` from the correct assigned branch.
-   [ ] Scope is limited and the PR description explains the change.
-   [ ] No secrets, `.env` files, real student data or credentials are
    included.
-   [ ] API contract compatibility has been checked.
-   [ ] Relevant tests pass; lint/type-check/build pass for the affected
    workstream.
-   [ ] Fixtures are synthetic and deterministic.
-   [ ] Loading/error/edge cases are handled where applicable.
-   [ ] Known limitations and deferred work are stated.
-   [ ] No unrelated formatting, generated files or another member's
    unfinished work are included.

## 6. Coordination and escalation

-   Member 1 (Backend Lead) owns backend APIs, database
    schema/migrations, authorization, RLS, approval rules, application
    state transitions and shared backend integration.
-   Member 2 owns the student-facing frontend and consumes the agreed
    API contract.
-   Member 3 owns AI capabilities and returns validated structured
    outputs through backend-owned interfaces.
-   If implementation requires a contract change, raise it in the team
    discussion and update the contract deliberately before coding
    against a different shape.
-   If a task is blocked by an unavailable backend endpoint, use a
    fixture/mock and record the dependency. Do not invent a temporary
    production API.

**Primary references:** `docs/TEAM_START_HERE.md` and
`docs/api-contract-proposed.md` in the repository. If this task sheet
conflicts with the latest approved API contract or a later team
decision, stop and clarify before implementing.
