NEXORA --- AI-Powered Placement Co-Pilot
NEXORA is an AI-powered career and placement assistant designed to help
students move from resume preparation to job discovery, application
tracking, and interview readiness.

Instead of sending the same generic resume to every opening and
preparing without direction, students can use NEXORA to understand their
profile, discover relevant opportunities, tailor application documents,
track progress, and practice interviews with structured feedback.
Project status: Active development. This README describes the
product scope and intended architecture. Individual features and
integrations may vary by branch; check the implementation and
PROGRESS.md before treating a capability as production-ready.

Table of Contents
- Problem
- Solution
- Core Capabilities
- Typical User Journey
- Architecture
- Technology Stack
- Repository Structure
- Getting Started
- Configuration
- Development and Testing
- Security and Responsible AI
- Roadmap
- Contributing
- Disclaimer
Problem
Students often face a fragmented placement-preparation process:
- Resumes are generic and are not adapted to individual job
  descriptions.
- Relevant openings and eligibility requirements are difficult to
  track.
- Application deadlines can be missed.
- Interview preparation is often disconnected from a student's actual
  skills and target role.
- Students have limited visibility into their strengths, skill gaps,
  and preparation progress.
Solution
NEXORA brings these activities into one workflow. It combines structured
student data, job-fit analysis, evidence-aware AI assistance,
application tracking, and adaptive interview practice.

The system is designed as an agentic application, not merely a
question-and-answer chatbot: workflows coordinate services and produce
structured outputs that can be reviewed and acted on by the student.
Core Capabilities
1. Resume intelligence
- Accept and parse a student's resume.
- Extract structured profile information and skills.
- Keep extracted facts reviewable so students can confirm or correct
  them.
- Retain source context for facts used in generated content.
2. Job discovery and matching
- Normalize job listings from supported providers or configured mock
  data.
- Compare opportunities with a student's profile.
- Explain match results using relevant skills, eligibility
  information, and identified gaps.
3. Resume tailoring and cover letters
- Generate role-specific resume content and cover-letter drafts.
- Ground generated claims in available student information.
- Flag content that requires student confirmation.
- Keep the student in control of reviewing and approving documents.
4. Application tracking
- Organize saved opportunities and application records.
- Track application stages, important dates, and deadlines.
- Provide a consolidated view of application progress.
5. Adaptive interview preparation
- Generate questions based on the target role and student profile.
- Evaluate submitted answers and provide structured feedback.
- Identify weak areas and support focused practice.
- Build a longer-term view of interview preparation progress as
  persistence capabilities are completed.
6. Career insights
- Bring together confirmed profile information, job-match results,
  applications, and interview feedback.
- Highlight strengths, skill gaps, and practical next steps.
- Keep persistent career history in the backend rather than relying on
  temporary workflow memory.
Typical User Journey
1. Create an account and access a personal workspace.
2. Upload a resume and review the extracted profile.
3. Confirm profile facts and correct any inaccurate information.
4. Discover opportunities and inspect job-fit explanations.
5. Tailor application documents for a selected role.
6. Review and approve documents before using them.
7. Track applications and upcoming deadlines.
8. Practice interviews with role-relevant questions and feedback.
9. Review progress and work on recommended skill gaps.
Architecture
NEXORA separates the user interface, backend responsibilities, and AI
intelligence into distinct layers.
                     ┌──────────────────────────┐
                     │       Student UI         │
                     │  Profile • Jobs • Docs   │
                     │ Applications • Interviews│
                     └────────────┬─────────────┘
                                  │ HTTPS / REST
                     ┌────────────▼─────────────┐
                     │       FastAPI Backend    │
                     │ Auth • API • Validation  │
                     │ Ownership • Approval     │
                     │ Persistence • Tasks      │
                     └───────┬─────────┬────────┘
                             │         │
                    ┌────────▼───┐ ┌───▼────────────┐
                    │ PostgreSQL │ │   AI Services  │
                    │ Student &  │ │ Resume • Jobs  │
                    │ Career Data│ │ Documents      │
                    └────────────┘ │ Interviews     │
                                   └──────┬─────────┘
                                          │
                                  ┌───────▼────────┐
                                  │ LangGraph      │
                                  │ Workflows      │
                                  └───────┬────────┘
                                          │
                                  ┌───────▼────────┐
                                  │ LLM Provider   │
                                  │ Gemini adapter │
                                  └────────────────┘
Architectural responsibilities
  Layer                               Responsibility
  Frontend                            User experience, forms, dashboards,
and API consumption

  Backend                             Authentication, authorization,
ownership checks, validation,
persistence, task lifecycle, and
approval enforcement

  AI services                         Resume parsing, profile extraction,
job matching, document generation,
and interview intelligence

  LangGraph workflows                 Orchestrating multi-step AI
operations with typed inputs and
outputs
Database                            Durable storage for student and
career records
Important design boundaries
- AI modules should not directly access the database or depend on
  FastAPI routes.
- The backend is the source of truth for ownership, persistence, and
  approval.
- Workflow state held in memory is temporary; it is not a replacement
  for durable career history.
- Generated claims should be traceable to source information and
  reviewed by the student.
- NEXORA assists with applications; it should not submit external
  applications without the student's explicit action.
Technology Stack
The project uses the following technologies across its application
layers. Exact dependencies and versions are defined in the relevant
package files.

  Area                 Technologies
  Backend API          Python, FastAPI
AI / orchestration   Python AI services, LangGraph
LLM integration      Gemini provider adapter
Database             PostgreSQL, SQLAlchemy, Alembic
Authentication       Supabase Auth / JWT-based authentication
Frontend             React, TypeScript, Vite
Styling              Tailwind CSS
Testing              Pytest, frontend test tooling, Ruff
Version control      Git and GitHub
Repository Structure
The exact tree may evolve during development. The main application areas
are organized approximately as follows:
nexora/
├── backend/
│   ├── app/
│   │   ├── ai/                 # AI services and orchestration
│   │   ├── api/                # Versioned API routes
│   │   ├── core/               # Configuration, auth, errors
│   │   ├── db/                 # Models and repositories
│   │   ├── schemas/            # Request and response schemas
│   │   └── services/           # Backend application services
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend and integration tests
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/                # API client and shared utilities
│   └── package.json
├── docs/                       # Architecture and technical docs
├── PROGRESS.md                 # Development progress and milestones
└── README.md
Getting Started
Prerequisites
- Git
- Python version supported by backend/pyproject.toml
- Node.js and npm
- PostgreSQL
- Supabase project credentials, if using Supabase authentication
- Gemini API credentials, if using live LLM features
1. Clone the repository
git clone https://github.com/Samcode2006/nexora-copilot.git
cd nexora-copilot
2. Set up the backend
cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

# Install project dependencies
pip install -e ".[dev]"
If the checked-out branch does not define a dev extra, install
dependencies using the instructions in pyproject.toml.

Configure the backend environment variables (see
Configuration), then run migrations:
alembic upgrade head
Start the API:
uvicorn app.main:app --reload
API documentation is typically available at
http://127.0.0.1:8000/docs.
3. Set up the frontend
Open a second terminal:
cd frontend
npm install
npm run dev
Use the local URL printed by Vite.
These are standard development commands. Available scripts, migration
requirements, and environment variable names can differ between
branches. Check the relevant pyproject.toml, package.json, Alembic
configuration, and example environment files in your checkout.

Configuration
Do not commit secrets or real credentials. Use local environment files
and keep them out of version control.

Depending on the active implementation, the backend may require:

  Variable / setting           Purpose
  Database URL                 PostgreSQL connection
Supabase URL                 Supabase project endpoint
Supabase JWT/JWKS settings   Authentication token verification
Gemini API key               LLM provider access
CORS origins                 Allowed frontend origins
Upload size limits           Resume upload validation
Environment mode             Local development or deployment configuration

Use the exact variable names documented in the backend configuration
module or supplied example environment file. Never paste production
secrets into source code, commits, logs, or issue reports.
Development and Testing
Run commands from the relevant project directory.
Backend
cd backend
pytest
ruff check .
For database integration tests, configure a disposable test
database. Never point test or migration-reset commands at production
data.
Frontend
cd frontend
npm test
npm run lint
npm run build
Run only scripts defined in the checked-out package.json.
Before opening a pull request
- Run relevant unit and integration tests.
- Run linting and formatting checks.
- Verify database migrations on a disposable database.
- Confirm that authorization and cross-user data isolation are tested.
- Update PROGRESS.md and relevant documentation.
- Report skipped tests and environment-dependent failures clearly.
Security and Responsible AI
NEXORA handles personal student information. Security and user control
are core requirements.
- Enforce authentication and per-student authorization on protected
  resources.
- Apply database-level access controls where configured.
- Validate file type and size before processing uploads.
- Avoid logging resume contents, tokens, API keys, or other sensitive
  data.
- Treat AI output as a draft, not as verified truth.
- Preserve evidence for generated resume and cover-letter claims.
- Require student review and approval before a generated document is
  treated as final.
- Respect consent, retention, and deletion requirements.
- Use bounded retries and safe error handling for external AI
  providers.
- Do not automatically apply to jobs or send documents to employers
  without explicit student authorization.
Roadmap
The following areas describe the intended development sequence. Check
PROGRESS.md and the active branch for actual implementation status.
- [ ] Stabilize repository, environment configuration, and API
  contracts.
- [ ] Complete authentication, authorization, database, and migration
  verification.
- [ ] Complete resume upload, parsing, profile review, and fact
  confirmation.
- [ ] Implement a persistent evidence ledger and claim provenance.
- [ ] Integrate job discovery, normalization, matching, and
  explainable results.
- [ ] Complete document versioning, review, approval, and audit
  history.
- [ ] Complete application tracking and deadline management.
- [ ] Persist interview sessions, answers, evaluations, and career
  progress.
- [ ] Add reliable background task execution, retries, and recovery.
- [ ] Connect all frontend workflows to backend APIs.
- [ ] Complete end-to-end, security, deployment, and demo validation.
Contributing
Contributions should preserve the separation between frontend, backend,
and AI responsibilities.
1. Check PROGRESS.md and existing issues before starting work.
2. Coordinate API and schema changes with the team.
3. Work on a feature branch rather than committing directly to main.
4. Add or update tests for changed behavior.
5. Update documentation when contracts or setup steps change.
6. Open a pull request with a concise summary, test results, and known
   limitations.
Do not overwrite uncommitted work or perform destructive Git operations
without confirming that the work is backed up.
Disclaimer
NEXORA is a student-focused placement assistance project under active
development. Job information, match scores, generated documents, and AI
feedback may be incomplete or inaccurate. Students should verify job
requirements and review all generated content before using it. NEXORA
does not guarantee interviews, placements, or employment.
