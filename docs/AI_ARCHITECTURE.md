# NEXORA AI architecture (Phases 1–6)

The repository was empty when this module was started, so Phase 1 establishes a
backend package under `backend/app/ai` without assuming ownership of API routes,
authentication, database tables, or approval logic.

## Current flow

```text
PDF/DOCX bytes -> format and size validation -> text extraction -> normalized
source text + recognized section boundaries
```

Resume parsing is deterministic and preserves extracted text. It does not infer
facts. Phase 2 converts the parsed text into a typed student profile. Each
profile fact carries an excerpt checked against the supplied text, a derived
section, a confidence indicator, and an unverified or needs-review status.
Claims without matching evidence are omitted. Scanned PDFs are reported as
lacking a text layer; OCR is outside these phases.

Structured LLM calls use the `LLMProvider` interface. `GeminiProvider` is an
optional implementation. A feature supplies its own deterministic fallback to
`LLMService`, and each result identifies its provider and `is_fallback` status.
This prevents a development fallback from being presented as model output.

Profile extraction uses the same provider boundary with a Pydantic response
schema and one retry for provider or schema failures. If the provider remains
unavailable, a deterministic fallback extracts only labelled or recognized
source facts. Its limited output is marked in the profile provenance metadata.
The main backend remains responsible for authentication, storage, persistence,
and student confirmation.

Phase 3 adds a separate job discovery path:

```text
JOBS_PROVIDER -> mock or Remotive provider -> provider-neutral normalization
-> duplicate removal -> query/location filters -> limited JobListing results
```

`JobProvider` is injectable. The mock provider marks its records as demo-only.
The Remotive adapter reads the public remote-jobs endpoint, caches a bounded
feed snapshot for six hours by default, filters locally, preserves the listing
URL/source attribution, and retries one transient request failure. Provider
and response errors are surfaced instead of silently switching to demo
listings. This phase adds no routes, database models, persistence, or application
workflow.

Phase 4 adds an isolated evidence-backed matching path:

```text
StudentProfile + JobListing[] -> exact/synonym skill checks
-> education/experience/project relevance -> hard eligibility assessment
-> weighted score + evidence references -> ranked JobMatch[]
```

`job_matching` does not write to profiles, listings, applications, or databases.
Unknown dimensions are excluded from the weighted mean and reported in
`score_coverage`; no score is returned if nothing is assessable. A confirmed
hard eligibility mismatch caps the score at 39; unknown eligibility caps it at
69. The explanation makes both caps visible.

The optional Sentence Transformers provider generates normalized embeddings
and cosine similarity for contextual education, experience, and project
relevance. Required/preferred skill equivalence uses explicit synonyms so
related concepts are not automatically treated as the same qualification. If
the embedding dependency or model is unavailable, every job is rescored with a
deterministic keyword baseline and marked `keyword_fallback`.

The default dimension weights are required skills 0.30, preferred skills 0.10,
education 0.15, experience 0.15, projects 0.15, and eligibility 0.15. They are
validated through `MatchWeights`; assessed weights are renormalized when other
dimensions are unknown or not applicable. Scores are evidence-match summaries,
not hiring probabilities.

Phase 5 adds `resume_tailoring`, which consumes existing profile, job, and
optional match models without changing them:

```text
StudentProfile + JobListing [+ JobMatch] + preferences
-> evidence-path prompt -> shared LLMService / deterministic fallback
-> claim and number validation -> separate TailoredResume / CoverLetter drafts
-> evidence report + student-review metadata
```

The package has Pydantic schemas, focused resume/cover-letter services, prompt
builders, a shared generation adapter, and deterministic evidence validation.
Provider text must cite profile paths; unsupported references, content terms,
and numerical claims are omitted from document content and kept in the audit
report. The deterministic path reorders source facts and uses source text rather
than inventing achievements. Skills are distinguished as listed or appearing
in project/experience context.

Tailoring uses the Phase 1 `LLMService`/`GeminiProvider` abstraction. It does
not create a separate LLM provider interface. Structured responses are retried
once by the shared service. Missing credentials, provider errors, and invalid
output produce explicit deterministic-fallback metadata. Offline tests use
mock providers; they do not verify a live Gemini call.

All outputs are validated drafts, not student-reviewed or approved documents.
The lifecycle fields preserve that distinction; no approval controller,
application submission, or external communication is added. The service does
not write to the profile or uploaded resume. DOCX/PDF export is deferred so a
document renderer can be added separately from AI generation.

The lexical validator is a deterministic guard, not a semantic entailment
system. Students must review every draft and confirmation-required fact before
using it. Resume length preferences cap the displayed skill and project/role
lists, but do not guarantee a rendered page count because no document layout
engine exists yet.

The Remotive feed is remote-only, may be delayed by 24 hours, and requires a
backlink plus source attribution. The adapter uses it only as a discovery source.
See the [official Remotive API documentation](https://github.com/remotive-com/remote-jobs-api#documentation).

## Dependencies

Core parsing requires Pydantic 2, PyMuPDF, and python-docx. Gemini is optional;
install the `gemini` extra and set `GEMINI_API_KEY` to enable it. If the key is
absent, `create_llm_service()` returns a service that uses the feature-provided
fallbacks.
Job discovery uses Python's standard HTTP and JSON libraries. Set
`JOBS_PROVIDER=remotive` to use the public API or leave it unset for explicitly
labelled demo listings.

Sentence Transformers is optional because its PyTorch/model dependencies are
larger than the core services. Install `.[matching]` and set
`JOB_MATCH_EMBEDDINGS=sentence-transformers` to request that provider
explicitly; `auto` attempts it and falls back if unavailable. A model may need
to be downloaded on first use. This environment did not run a real model;
automated tests use controlled embedding providers and verify fallback behavior.

Phase 6 adds an isolated, in-memory interview intelligence service:

```text
StudentProfile + JobListing [+ JobMatch]
  -> evidence-grounded question generation
  -> student answer
  -> independently scored rubric dimensions
  -> competency/session update
  -> deterministic adaptive next-question selection
  -> session report
```

`interview_intelligence` is divided into Pydantic contracts, prompt builders,
rubrics, role-aware question generation, answer evaluation, adaptive selection,
and interview lifecycle services. It consumes the Phase 2–4 models and shared
`LLMService`; it introduces no new provider abstraction, routes, data tables, or
long-term state. A session contains snapshots and its turn history so a caller
can serialize it for backend-owned storage later.

Question templates cover technical, project-based, HR/behavioral, and
role-specific interviews. Structured Gemini output is validated against a
Pydantic draft and grounded to job requirements and evidence paths. Project
questions require supported project facts; without them, a profile-neutral
question asks whether the student has an example. Expected answer points and
rubric material are hidden from normal question serialization. Relevant
source-backed education, skill, project, and experience facts may be included
as context; personal contact fields are excluded from generation and evaluation
prompts. Provider
failures, schema failures, or no credentials use deterministic templates with
`generation_method="deterministic_templates"` and
`generation_provider="deterministic_fallback"`.

Evaluations use seven configurable dimensions: technical correctness,
conceptual understanding, depth, relevance, problem solving, communication,
and practical application. Their default weights are documented in
`AI_SERVICE_CONTRACTS.md`; `RubricWeights` checks that active weights total 1.
The total is the weighted mean over assessed dimensions only, with
`score_coverage` identifying how much of the rubric could be assessed.
Technical correctness is separately weighted from communication. The LLM's
overall score is never accepted directly; the service calculates it from
validated dimension scores. Exact answer excerpts are required for feedback
evidence. No confidence above medium is assigned because the provider's
evaluation is not independently calibrated.

The no-provider evaluator is intentionally limited: it uses guide-word overlap,
answer length, punctuation-based sentence count, and simple example/sequence
markers. It labels itself `deterministic_heuristic`, gives low confidence, and
leaves technical correctness unassessed. It must not be represented as an LLM
evaluation or fact checker. Live Gemini operation is not established by offline
tests; tests use mock providers or no provider.

The adaptive engine makes a single focused reinforcement available after a
low-scoring answer, then moves to another unasked job competency or unresolved
weakness. It prioritizes required skills and match-missing requirements before
preferred skills. A score below 45 reduces difficulty by one level; a score of
80 or higher increases it by one; the middle band keeps it steady. Selection
records a human-readable reason and excludes prior question wording.
Competency averages, trends, repeated weak scores, and confidence are limited
to the current session; they are not career memory and do not imply progress
across interviews.

The interview report summarizes completed answers, strength/weakness areas,
practice topics, and limitations. An incomplete or early-terminated session is
reported as such. A report is not a hiring decision or readiness certification.
Its overall score is the mean of assessable answer scores; communication and
technical performance are separately averaged from their assessed dimensions.
Session persistence, audio/transcription, speech delivery assessment,
cross-session career memory, and live-provider monitoring remain future work.
