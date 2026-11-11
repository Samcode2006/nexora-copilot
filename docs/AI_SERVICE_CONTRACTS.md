# AI service contracts (Phases 1–6)

These functions are backend-library contracts. No HTTP routes, database models,
authentication flow, or approval endpoint existed in the repository at the
start of this phase, so those remain owned by the main backend member.

## Resume parsing

```python
parse_resume(
    content: bytes,
    filename: str,
    *,
    max_file_bytes: int = 5_000_000,
) -> ParsedResume
```

`ParsedResume` contains the original filename, detected supported format,
extracted text, normalized text, recognized section text, and warnings. It does
not infer student facts. Errors are `ResumeParseError`, a `ValueError` with a
stable `code` attribute (`invalid_filename`, `empty_file`, `file_too_large`,
`unsupported_type`, `malformed_document`, `dependency_missing`, or
`no_extractable_text`). Scanned PDFs currently need an OCR stage, which is not
part of Phase 1. The default upload cap is exactly 5,000,000 bytes; a file at
that size is accepted and a file one byte larger is rejected before document
parsing. Callers can supply an explicit `max_file_bytes` override.

## Structured LLM calls

`LLMProvider.generate_structured(prompt=..., response_model=...)` is the provider
interface. `GeminiProvider` implements it when the optional Gemini dependency
and `GEMINI_API_KEY` are configured. `LLMService.generate_structured(...)`
accepts a feature-owned deterministic `fallback` callable and returns an
`LLMResult` with `provider`, `is_fallback`, and (when applicable) `model` and
`fallback_reason`. Consumers should surface `is_fallback` when presenting
generated content. Retry counts are bounded to at most three attempts, and
non-retryable configuration/authentication failures stop immediately. Public
fallback reasons use safe failure categories rather than raw provider messages.
A native Gemini client uses a 60-second request timeout. An injected client uses
the provider-neutral dict configuration and does not require importing the
optional Gemini SDK on the request path.

## Structured student profile extraction

```python
extract_student_profile(
    resume_text: str,
    *,
    llm_service: LLMService | None = None,
) -> StudentProfile
```

`resume_text` is text extracted by the Phase 1 parser (or equivalent plain
resume text). The optional service parameter supports dependency injection and
tests; normal application code can call `extract_student_profile(resume_text)`.
A non-string input raises `TypeError`. Empty text returns an empty profile with
a fallback warning.

`StudentProfile` contains:

- `personal_information`: name, email, phone, and location.
- `education`: institution, degree, branch, graduation year, CGPA, and percentage.
- `skills`: programming languages, frameworks, databases, cloud technologies,
  tools, and technical domains.
- `projects`: name, description, technologies, responsibilities, and achievements.
- `experience` and `internships`: company, position, duration, responsibilities,
  and achievements.
- `certifications`, `awards`, and `achievements`.
- `extraction_provider`, `is_fallback`, and `warnings` provenance metadata.

Every non-null factual field and list item is an `EvidenceValue` with `value`,
`source_text`, `source_section`, `confidence`, `evidence_status`, and
`verification_status`. The service checks that the quote occurs in the input
and that the value occurs in the quote; unsupported claims are omitted. The
section is derived from the matching excerpt, not accepted from the model.
Whitespace is normalized for matching, and the returned excerpt preserves the
original text, whitespace, and capitalization. Explicit, directly matched
facts may be marked high confidence, but remain `unverified` until the student
confirms them. Inferred or uncertain values are low confidence and marked
`needs_review`.

When Gemini is configured, the provider is called through `LLMService` and
schema/provider failures are retried once. If no credentials exist or both
attempts fail, deterministic extraction handles high-precision labelled
contact and education fields, recognized skills, and lines in certifications
or achievements sections, and labelled experience/internship fields. It
deliberately leaves other fields empty rather than guessing. The output identifies this as
`extraction_provider="deterministic_fallback"` and `is_fallback=True`.

## Job discovery and normalization

```python
search_jobs(
    query: str,
    location: str | None = None,
    limit: int = 20,
    *,
    provider: JobProvider | None = None,
) -> list[JobListing]
```

`query` must contain 1–200 characters, `location` is optional and limited to
100 characters, and `limit` must be an integer from 1 through 100. The optional
provider supports dependency injection in tests and demos. If omitted, the
service reads `JOBS_PROVIDER` (`mock` by default or `remotive`). Search and
location filtering are applied after normalization. Worldwide remote jobs
match a specific requested location.

`JobListing` normalizes identity, title, company, description, required and
preferred skills, eligibility, experience bounds, location, work mode,
employment type, salary, application/source URLs, deadline, publication/update
timestamps, source provider, and original source ID. Unavailable facts remain
null or empty. Invalid URLs are omitted with a warning. Duplicate source IDs
and duplicate record fingerprints are removed. `source_provider`, `source_url`,
and `is_mock` identify provenance; mock records also carry an explicit
not-live warning.

Provider errors are raised as `JobProviderError` or its configuration/response
subclasses. A failed live request never returns mock listings. Remotive retries
one transient timeout/network/429/5xx failure and then fails clearly. Other
response-shape or non-transient HTTP errors are not retried.

### Provider configuration

```powershell
$env:JOBS_PROVIDER = "remotive" # or "mock"
$env:JOB_PROVIDER_TIMEOUT_SECONDS = "8"
$env:REMOTIVE_CACHE_TTL_SECONDS = "21600"
# Optional endpoint override; HTTPS is required.
$env:REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
```

The mock provider needs no credentials and its listings are demos only. The
Remotive public API needs no API key. Its feed is remote-only, may be delayed
by 24 hours, and requires attribution plus a link back to Remotive. Remotive
advises fetching at most four times per day; the default six-hour cache follows
that guidance. See the [official Remotive API documentation](https://github.com/remotive-com/remote-jobs-api#documentation).

The adapter fetches a bounded 1,000-listing snapshot and filters it locally.
The cache is in process memory, so it is not shared across workers or process
restarts. Required/preferred skills are populated from structured provider
fields or tags; this phase does not use an LLM to infer skills from job
descriptions. Salary text is preserved when a numeric range cannot be parsed.

## Semantic job matching

```python
match_jobs(
    student_profile: StudentProfile,
    job_listings: list[JobListing] | tuple[JobListing, ...],
    *,
    config: MatchConfig | dict | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[JobMatch]
```

The function validates the supplied profile/listings, matches every job,
returns `JobMatch` objects sorted by relevance, and assigns a 1-based rank.
An empty listing list returns an empty list. If no profile evidence can be
scored, `overall_score` is `null`; it is not reported as a zero or a failed
candidate.

### Dimensions and score formula

Default weights are:

| Dimension | Weight |
| --- | ---: |
| Required skills | 0.30 |
| Preferred skills | 0.10 |
| Education relevance | 0.15 |
| Experience relevance | 0.15 |
| Project relevance | 0.15 |
| Eligibility | 0.15 |

`MatchWeights` validates that weights are each between 0 and 1 and sum to 1.
Pass a `MatchConfig(weights=MatchWeights(...))` to customize them. The raw
overall score is the weighted mean of assessed dimensions. Unknown and
not-applicable dimensions are excluded, and the remaining weights are
renormalized. `score_coverage` reports what fraction of the original weight
was assessed. If no dimension is assessed, no overall score is produced.

An explicitly verified hard eligibility mismatch caps the overall score at
39. Unknown eligibility caps it at 69 and carries an uncertainty warning.
These caps prevent other strong dimensions from hiding eligibility risk;
neither score estimates the probability of getting hired. A missing required
skill is labelled `not_evidenced`, not proof the student lacks that skill.

### Embedding and fallback behavior

`EmbeddingProvider.similarities(pairs)` is replaceable and returns cosine
similarities in `[-1, 1]`. The optional
`SentenceTransformerEmbeddingProvider` uses the
`sentence-transformers/all-MiniLM-L6-v2` model and cosine similarity for
education, experience, and project text relevance. Skill synonyms use a
small, explicit alias map instead of treating any semantically related term
as an equivalent qualification. See the [Sentence Transformers semantic similarity guide](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html).

`matching_method` identifies the provider actually used. If embeddings are
disabled, missing, malformed, or fail, all jobs are rescored with the
deterministic keyword baseline and the result says `keyword_fallback`. The
baseline uses token overlap and exact configured skill synonyms; it does not
claim semantic matching.

Configuration:

```powershell
$env:JOB_MATCH_EMBEDDINGS = "auto" # default; try Sentence Transformers
$env:JOB_MATCH_EMBEDDINGS = "keyword" # disable embeddings
$env:JOB_MATCH_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
python -m pip install -e ".[matching]"
```

Every matched skill, relevance dimension, and evaluated eligibility criterion
includes `EvidenceReference` entries pointing to a `StudentProfile` path and
its source excerpt. Values without explicit traceable evidence are excluded.
Eligibility is only marked met or mismatched when the relevant facts are
student-verified; missing, unverified, and unsupported criteria remain unknown.
Current deterministic eligibility checks cover explicit CGPA/graduation-year
criteria and explicitly stated total experience. Other criteria remain unknown
for student review.

## Job-specific resume and cover-letter tailoring

```python
tailor_resume(
    student_profile: StudentProfile,
    job_listing: JobListing,
    job_match: JobMatch | None = None,
    preferences: TailoringPreferences | dict | None = None,
    *,
    llm_service: LLMService | None = None,
) -> TailoredResume

generate_cover_letter(
    student_profile: StudentProfile,
    job_listing: JobListing,
    tailored_resume: TailoredResume | None = None,
    preferences: TailoringPreferences | dict | None = None,
    *,
    llm_service: LLMService | None = None,
) -> CoverLetter
```

Both functions accept the existing `StudentProfile` and `JobListing` models.
`TailoringRequest` validates the inputs and rejects a `JobMatch` or tailored
resume that refers to a different job. Preferences include target resume
length, tone (`concise`, `professional`, `technical`, or `ats_friendly`),
student instructions, cover-letter length, contact display, section ordering,
and bullet style. Student instructions affect style and ordering only; they do
not authorize new facts.

`TailoredResume` is a separate structured representation containing contact
details, professional summary, ordered skills, education, projects, experience,
internships, certifications, awards, achievements, change explanations, and a
validation report. A skill is labeled `demonstrated_in_context` only when it
also occurs in source-backed project or experience prose; otherwise it remains
`listed_skill`. Project and experience facts preserve their original meaning
and numbers. Source details are used verbatim when a proposed rewrite fails
validation.

`CoverLetter` contains a greeting, opening, relevant experience, role relevance,
closing, sign-off, evidence, validation report, and generation metadata. Missing
company or student information is omitted or handled with a generic greeting;
the service does not create recruiter names or company research. The closing is
fixed to the canonical neutral boilerplate and `CoverLetter` validation rejects
other closing text, including text supplied during direct construction or
JSON reconstruction.

### Claim validation and student review

Each included fact-bearing string is a `ValidatedClaim` with profile or job
evidence references, source excerpts, source section, confidence, validation
status, and `student_confirmation_required`. Explicit facts that have not been
student-confirmed are marked `needs_review`; they are never presented as
verified. Generated claims must cite existing evidence paths. The deterministic
validator rejects unknown references, factual terms that do not occur in cited
fact values, and numbers or percentage units that are not explicitly present.
Rejected provider text is excluded from resume and letter content and retained
only in `validation_report.omitted_claims` for audit.

The deterministic check is conservative but is not a full semantic-entailment
model. Outputs remain drafts requiring student review; lexical validation alone
must not be treated as student approval or proof that every paraphrase preserves
meaning. Lifecycle metadata distinguishes `ai_generated_draft`,
`validated_draft`, `student_reviewed_draft`, and `student_approved_document`.
These services produce only a `validated_draft` with review and approval unset.
The backend-owned approval workflow remains outside this package.

### Provider and fallback behavior

Tailoring uses the existing `LLMService` and configured `GeminiProvider`; it
does not introduce a second provider framework. The LLM receives structured
Pydantic response schemas and must cite profile evidence paths. The shared
service retries retryable provider failures and invalid structured output
within the bounded attempt limit. Provider errors, invalid responses, or absent
credentials use deterministic source-based ordering and cover-letter text. `generation.provider`, `is_fallback`, `generation_method`,
warnings, and the validation report identify what was actually used. Live
Gemini generation has not been exercised by the offline tests; they inject
deterministic mock providers.

DOCX/PDF export is not implemented. This package returns validated structured
data only; a future document-rendering integration can consume it without
changing the source profile or uploaded resume.

## Adaptive mock interview intelligence

The `interview_intelligence` package reuses `StudentProfile`, `JobListing`,
`JobMatch`, and the existing `LLMService` provider boundary. It does not add
routes, persistence, application tracking, or cross-session memory.

```python
generate_interview_questions(
    student_profile,
    job_listing,
    interview_type,  # technical | project_based | hr_behavioral | role_specific
    difficulty,      # beginner | intermediate | advanced
    question_count=10,
    *, job_match=None, llm_service=None,
) -> list[InterviewQuestion]

evaluate_interview_answer(
    question, answer, student_profile, job_listing,
    *, llm_service=None, rubric_weights=None,
) -> AnswerEvaluation

start_interview(
    student_profile, job_listing, interview_type,
    difficulty="intermediate", question_count=10,
    *, job_match=None, llm_service=None,
) -> InterviewSession

submit_interview_answer(session, answer_text, *, llm_service=None) -> InterviewSession
select_next_question(session, *, llm_service=None) -> QuestionSelection | None
get_interview_report(session) -> InterviewReport
end_interview(session, reason="student_requested") -> InterviewSession
```

Question counts are validated from 1 through 30. The session stores validated
profile and job snapshots, the optional matching result, current and planned
difficulty, all question/answer/evaluation turns, competency measurements, and
status (`in_progress`, `completed`, or `terminated`). Validation requires every
turn's complete question, answer, and evaluation to match the corresponding
history entry. Session data is service-level only; persistence is the backend
integration layer's job. `serialize_interview_session` omits evaluator-only
answer guidance by default, but retains profile and answer snapshots. Its
trusted `include_evaluation_material=True` flag only controls serialization; it
does not authorize access. Project a privacy-appropriate response DTO before
exposing serialized data to a student. `get_question_evaluation_material` also requires an
explicit flag before it returns hidden guidance.

### Question generation and grounding

Questions are structured with an ID, category, difficulty, competency,
relevant job requirement, follow-up guidance, generation provenance, and
supported profile evidence references. Project questions use traceable project
facts; when there are no supported project details, a deterministic prompt
asks whether the student has an example and allows them to skip. HR questions
do not presume work, leadership, or conflict experience and provide STAR
guidance for past examples. Relevant education, skills, and experience can
inform technical or role-focused questions. Personal contact fields are not
included in question-generation or evaluation prompts. The engine filters
repeated question wording and provider claims that cannot be tied to the
selected job or referenced project facts. Expected answer points and the
rubric are excluded from ordinary question serialization until explicitly
requested by a trusted evaluation flow.

### Rubric and score calculation

All dimensions are rated on a 0–100 scale. `RubricWeights` validates that the
weights for the selected question total 1.0. Defaults are:

| Dimension | Technical | Project | HR/behavioral | Role-specific |
| --- | ---: | ---: | ---: | ---: |
| Technical correctness | 0.25 | 0.15 | 0.00 | 0.20 |
| Conceptual understanding | 0.18 | 0.15 | 0.10 | 0.16 |
| Depth of explanation | 0.12 | 0.15 | 0.15 | 0.12 |
| Relevance | 0.14 | 0.15 | 0.20 | 0.18 |
| Problem solving | 0.12 | 0.15 | 0.20 | 0.14 |
| Communication clarity | 0.09 | 0.10 | 0.25 | 0.10 |
| Practical application | 0.10 | 0.15 | 0.10 | 0.10 |

For assessable dimensions, `overall_score = sum(score × weight) / sum(assessed
weights)`. `score_coverage` is the sum of assessed weights from the original
rubric. Not-assessed dimensions are excluded and the remaining weights are
renormalized. An empty answer has no overall score. Technical correctness and
communication are separate dimensions; communication cannot compensate for a
low correctness score.

When an LLM provider is available, it returns a validated structured draft and
the service recomputes the weighted total rather than accepting an LLM total.
Feedback quotes are retained only if the exact excerpt occurs in the submitted
answer. Confidence is capped at `medium` because this assessment is not
externally calibrated. Reports include limitations and do not represent a
hiring decision.

Without a provider, or after provider/schema failures, a deterministic
heuristic considers guide-term overlap, response length, sentence count, and
simple sequencing/example markers. It explicitly leaves technical correctness
unassessed, uses `evaluation_method="deterministic_heuristic"`, marks
`is_fallback=True`, and has low confidence. This heuristic is not a semantic
correctness checker or readiness certification. `LLMService` retries structured
provider/schema failures once; no live Gemini request is made by offline tests.

### Adaptation and competency tracking

Selection is deterministic and explainable. A response below 55/100 can trigger
one same-competency reinforcement, and a subsequent weak answer moves on to an
unasked role competency or another unresolved weakness. The engine prioritizes
not-yet-asked required skills (including match-missing skills), then preferred
skills, before repeating an assessed area. It filters prior question text.
Scores below 45 lower the next difficulty one step; scores of at least 80 raise
it one step; other scores keep it steady. Difficulty is bounded by beginner
and advanced. Insufficiently assessable responses do not change difficulty.

Each competency records attempts, scored and unscored answers, average,
improving/declining/stable trend when enough scored samples exist, repeated low
scores, fallback count, and conservative confidence. These observations cover
only the current session. They do not imply durable learning progress.

The report's overall score is the simple average of non-null per-answer overall
scores; unanswered or unscored answers are excluded. Technical and
communication performance are the respective averages of assessed dimension
scores. Each figure remains qualified by score coverage, evaluation method,
and the report's limitations.

## Install and configure

```powershell
# Run from the backend/ directory (the backend owns this pyproject.toml).
python -m pip install -e ".[dev,gemini]"
$env:GEMINI_API_KEY = "..."
```

The Gemini extra is optional. For document parsing only, install the base
dependencies and leave `GEMINI_API_KEY` unset.
