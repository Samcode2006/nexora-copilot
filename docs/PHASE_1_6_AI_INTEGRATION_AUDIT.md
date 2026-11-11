# NEXORA Phase 1–6 AI Integration Interface Audit

**Purpose:** describe the implemented AI library contracts for Member 1's shared backend integration work. This report records the repository as inspected on 2026-11-11. It does not define a new API, database schema, or shared-interface signature.

## Audit scope and verification status

The inspected implementation lives under `backend/app/ai/`. Public functions are synchronous Python functions; there are no `async def` AI service entry points. The AI package exposes Pydantic models and library services. It does not contain `backend/app/ai/interfaces.py`, HTTP route modules, authentication or authorization integration, database models, migrations, or persistent interview storage.

The source files, service contracts, architecture document, `pyproject.toml`, and test files were inspected. Source code was not edited for this audit. The only intended repository change is this report.

The current audit shell did not provide a runnable `python`, `python3`, `py`, or `pytest` command, and the project has no `.venv`. Therefore, the full suite could not be rerun during this audit. The most recent recorded full run from the preceding project verification was **143 passed, 1 warning** (the Google GenAI SDK `_UnionGenericAlias` deprecation warning) on Python 3.14.6. Treat that as the last verified result, not as a fresh run in this audit environment.

## 1. Actual module structure

Source tree below omits generated `__pycache__` files.

```text
backend/app/ai/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py                 # LLMProvider protocol, errors, LLMResult
│   ├── gemini.py               # Optional Gemini implementation
│   └── service.py              # Shared LLMService and provider selection
├── resume_intelligence/
│   ├── __init__.py
│   ├── parser.py               # PDF/DOCX validation, extraction, headings
│   ├── schemas.py              # ParsedResume
│   ├── profile_schemas.py      # EvidenceValue and StudentProfile models
│   └── profile_extractor.py    # Evidence-checked structured profile extraction
├── job_intelligence/
│   ├── __init__.py
│   ├── schemas.py              # Normalized JobListing
│   ├── providers.py            # JobProvider, mock, Remotive, env selection
│   ├── normalizer.py           # Provider payload normalization and deduplication
│   └── discovery.py            # search_jobs and local query/location filters
├── job_matching/
│   ├── __init__.py
│   ├── schemas.py              # MatchConfig, evidence, JobMatch, score models
│   ├── evidence.py             # Profile evidence traceability helpers
│   ├── eligibility.py          # Conservative machine-checkable eligibility
│   ├── embeddings.py            # EmbeddingProvider and Sentence Transformers
│   └── scoring.py              # Weighted scoring, fallback, ranking
├── resume_tailoring/
│   ├── __init__.py
│   ├── schemas.py              # Preferences, claims, documents, drafts
│   ├── prompts.py              # Resume and cover-letter prompts
│   ├── generation.py           # Adapter around the shared LLMService
│   ├── validation.py           # Evidence collection and claim validation
│   ├── tailoring.py            # tailor_resume
│   └── cover_letter.py         # generate_cover_letter
└── interview_intelligence/
    ├── __init__.py
    ├── schemas.py              # Question, evaluation, session, report models
    ├── prompts.py              # Question and answer-evaluation prompts
    ├── rubrics.py              # Default weights and criteria
    ├── question_generator.py   # LLM-validated and deterministic questions
    ├── evaluation.py           # Rubric evaluation and heuristic fallback
    ├── adaptive_engine.py      # Deterministic next-question selection
    └── interview_service.py    # In-memory session lifecycle and serialization
```

Relevant shared utilities are `providers/`, `job_matching/evidence.py`,
`resume_tailoring/validation.py`, and the normalizer/provider adapters. There is
no separate orchestration package or single end-to-end production service.

Tests under `backend/tests/`:

```text
test_resume_parser.py
test_profile_extractor.py
test_llm_provider.py
test_job_discovery.py
test_job_matching.py
test_resume_tailoring.py
test_interview_intelligence.py
test_ai_pipeline_offline.py
```

## 2. Public service and provider function inventory

All functions below are synchronous. Signatures are copied from the source;
constant defaults are shown with their source identifiers and resolved values
where useful. Exceptions listed are the implemented validation/error paths,
not an exhaustive list of runtime failures from Python or third-party SDKs.

### Primary AI services

| Function and exact signature | Input/output schemas | Validation and errors | Dependencies / notes |
| --- | --- | --- | --- |
| `parse_resume(content: bytes, filename: str, *, max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> ParsedResume` (`DEFAULT_MAX_FILE_BYTES` is 10 MiB) | Input: file bytes and filename. Output: `ParsedResume`. | Raises `ResumeParseError(ValueError)` with stable codes: `invalid_filename`, `empty_file`, `file_too_large`, `unsupported_type`, `malformed_document`, `dependency_missing`, `no_extractable_text`. | PyMuPDF with `pymupdf` import and `fitz` compatibility fallback; `python-docx`; parser helpers. Extracts source text only, not facts. |
| `extract_student_profile(resume_text: str, *, llm_service: LLMService \| None = None) -> StudentProfile` | Input: extracted/plain resume text. Output: `StudentProfile`. | Non-string input raises `TypeError`. Empty input returns an empty fallback profile with warning. Profile/model/provider validation is handled by Pydantic and `LLMService`; unsupported facts are omitted. | `_normalize_text`, `_identify_sections`, `StudentProfileFields`, shared `LLMService`, deterministic labelled-text fallback. Calls structured generation with at most two attempts. |
| `search_jobs(query: str, location: str \| None = None, limit: int = DEFAULT_RESULT_LIMIT, *, provider: JobProvider \| None = None) -> list[JobListing]` (`DEFAULT_RESULT_LIMIT` is 20) | Input: query, optional location, limit, optional injected provider. Output: normalized `JobListing` objects. | Raises `ValueError` for invalid query/location/limit. Provider/config/shape failures use `JobProviderError`, `JobProviderConfigurationError`, or `JobProviderResponseError`. It does not turn a failed live request into mock results. | Provider selected through `JOBS_PROVIDER` if none injected; normalizer; query/location filters; provider-level result cap 1,000 and final result cap 100. |
| `normalize_job(raw_job: Mapping[str, Any], source_provider: str, *, is_mock: bool = False) -> JobListing` | Raw provider mapping to `JobListing`. | Raises `JobNormalizationError(ValueError)` for invalid record/provider identity; invalid URLs are omitted with a warning rather than raising. | Provider key aliases, date/number parsers, URL validator, stable generated ID when source ID is absent. |
| `normalize_jobs(raw_jobs: Sequence[Mapping[str, Any]], source_provider: str, *, is_mock: bool = False) -> list[JobListing]` | Sequence of raw mappings to normalized list. | Raises `JobNormalizationError` for invalid sequence/record. Removes duplicate source IDs or fingerprints. | Calls `normalize_job`. |
| `match_jobs(student_profile: StudentProfile, job_listings: list[JobListing] \| tuple[JobListing, ...], *, config: MatchConfig \| dict[str, Any] \| None = None, embedding_provider: EmbeddingProvider \| None = None) -> list[JobMatch]` | Input profile and job objects/mappings, optional scoring config and provider. Output ranked `JobMatch` list. | Invalid job-list container raises `TypeError`; Pydantic validation errors propagate for invalid input/config. Embedding errors cause whole-batch deterministic keyword rescoring and are reported in warnings/method metadata. Empty jobs returns `[]`. | `MatchConfig`, evidence helpers, eligibility assessor, optional `EmbeddingProvider`; order is stable for ties; ranks start at 1. |
| `tailor_resume(student_profile: StudentProfile, job_listing: JobListing, job_match: JobMatch \| None = None, preferences: TailoringPreferences \| dict[str, Any] \| None = None, *, llm_service: LLMService \| None = None) -> TailoredResume` | Profile, selected job, optional same-job match, optional preferences. Output: separate structured `TailoredResume` draft. | `TailoringRequest` Pydantic validation rejects a match for another job. Invalid fields/preferences raise Pydantic `ValidationError`. Provider/claim validation failures fall back to source-based content and are disclosed in metadata/warnings. | Shared `LLMService` via `generate_draft`; source fact validation; no mutation of input profile. |
| `generate_cover_letter(student_profile: StudentProfile, job_listing: JobListing, tailored_resume: TailoredResume \| None = None, preferences: TailoringPreferences \| dict[str, Any] \| None = None, *, llm_service: LLMService \| None = None) -> CoverLetter` | Profile, selected job, optional matching tailored draft and preferences. Output: structured `CoverLetter` draft. | Invalid preferences raise Pydantic `ValidationError`. A tailored resume for another `job_id` raises `ValueError`. Provider/claim failures use deterministic wording with explicit metadata. | Shared `LLMService`; source evidence and claim validator; no recruiter/company research. |
| `generate_interview_questions(student_profile: StudentProfile, job_listing: JobListing, interview_type: InterviewType, difficulty: Difficulty, question_count: int = 10, *, job_match: JobMatch \| None = None, llm_service: LLMService \| None = None, focus_competency: str \| None = None, exclude_question_texts: tuple[str, ...] \| list[str] = (), variant_offset: int = 0) -> list[InterviewQuestion]` | Profile/job, optional same-job match, one of four categories, difficulty, count and adaptive controls. Output: questions. | Non-integer/bool `question_count` raises `ValueError`; `InterviewStartRequest` validation constrains 1–30 and checks match/job identity. Provider output is schema-checked and unsupported/repeated questions are filtered; deterministic templates fill gaps. | Shared `LLMService`; profile evidence; rubric factory; deterministic templates. `focus_competency`, exclusions, and offset are lower-level controls in the module signature. |
| `evaluate_interview_answer(question: InterviewQuestion, answer: str, student_profile: StudentProfile, job_listing: JobListing, *, llm_service: LLMService \| None = None, rubric_weights: RubricWeights \| dict[str, float] \| None = None) -> AnswerEvaluation` | Question, submitted answer, profile/job context, optional shared LLM service and custom weights. Output: validated evaluation. | Non-string answer raises `TypeError`; >12,000 characters raises `ValueError`; invalid profile/job/weights can raise Pydantic `ValidationError`. Empty/invalid/provider-failed responses are handled without fabricating evaluation; empty answer has null overall score. | Shared `LLMService`; question rubric; supported evidence references; deterministic fallback marks correctness unassessed and confidence low. |
| `start_interview(student_profile: StudentProfile, job_listing: JobListing, interview_type: InterviewType, difficulty: Difficulty = "intermediate", question_count: int = 10, *, job_match: JobMatch \| None = None, llm_service: LLMService \| None = None) -> InterviewSession` | Validated profile/job, optional same-job match, category/difficulty/count. Output: initialized session with first pending question. | `InterviewStartRequest` Pydantic validation (including 1–30 count and job-match identity); `RuntimeError` if no initial question is returned. | Calls `generate_interview_questions`; stores in-memory snapshots and UTC timestamps. |
| `select_next_question(interview_session: InterviewSession, *, llm_service: LLMService \| None = None) -> QuestionSelection \| None` | Current session. Output: selected question and reason, or `None` when not in progress/planned count reached. | Uses validated `InterviewSession`; selection output is Pydantic validated. | Deterministic competency/difficulty decision followed by question generator for wording; one same-competency reinforcement after a score below 55, then prefers unasked role targets. |
| `submit_interview_answer(interview_session: InterviewSession, answer_text: str, *, llm_service: LLMService \| None = None) -> InterviewSession` | In-progress session and answer string. Output: copied/updated session with evaluation and next question, or completed session. | `ValueError` if session is not in progress or has no pending question. `InterviewSubmitRequest` validates string/max 12,000 characters (empty is accepted and recorded as unscored). Evaluation/provider fallback is reported in evaluation metadata. | Calls evaluator, updates aligned answer/evaluation/turn histories and competency tracking, adjusts difficulty, then calls `select_next_question`. |
| `get_interview_report(interview_session: InterviewSession) -> InterviewReport` | Session to derived report. Output: `InterviewReport`. | Pydantic output validation; null overall score if no answer has an assessable score. | Pure session summary; no cross-session memory or hiring decision. |
| `end_interview(interview_session: InterviewSession, reason: str = "student_requested") -> InterviewSession` | Session and optional end reason. Output: terminated copy when active; unchanged terminal session otherwise. | Reason is normalized to default when blank; >240 characters raises `ValueError`. | No persistence. Keeps completed turns and an unanswered pending question if one existed. |
| `get_question_evaluation_material(question: InterviewQuestion, *, explicitly_requested: bool = False) -> QuestionEvaluationMaterial` | Question plus explicit access flag. Output: expected points and rubric. | Raises `PermissionError` unless flag is true. | Intended for trusted evaluator/internal use, not client display. |
| `serialize_interview_session(interview_session: InterviewSession, *, include_evaluation_material: bool = False) -> str` | Session and optional internal-material flag. Output: compact JSON string. | Standard JSON serialization errors can propagate for unsupported data; the model is Pydantic serializable. | Default excludes expected answer points, rubric, and evaluator keywords because their question fields have `exclude=True`. Trusted internal mode adds those fields to question history and turn questions. |

### Other exported utilities and provider interfaces

| Function/method and signature | Output / errors / purpose |
| --- | --- |
| `create_llm_service() -> LLMService` | Reads whether `GEMINI_API_KEY` is configured; creates Gemini provider if possible, else empty `LLMService`. No secret value is logged or included in this report. |
| `LLMService.generate_structured(self, *, prompt: str, response_model: type[T], fallback: Callable[[], T], max_attempts: int = 1) -> LLMResult[T]` | Returns validated model plus provider/fallback metadata. `max_attempts < 1` raises `ValueError`. Retries `LLMProviderError` and Pydantic `ValidationError`; after attempts, invokes caller fallback. Unexpected exceptions are left to feature wrappers/provider boundary. |
| `GeminiProvider.__init__(self, *, api_key: str \| None = None, model: str = "gemini-2.5-flash", client: object \| None = None)` | Optional injected client for tests. Without client/key, raises `ProviderUnavailableError`; missing optional package also raises it. `generate_structured(self, *, prompt: str, response_model: type[T]) -> T` validates the SDK JSON against the requested Pydantic model and wraps SDK/provider errors as `LLMProviderError`. |
| `create_job_provider_from_env() -> JobProvider` | Selects `mock` (default) or `remotive`; unsupported names/invalid settings raise job-provider configuration errors. |
| `create_embedding_provider_from_env() -> EmbeddingProvider \| None` | `keyword`/disabled mode returns `None`; `auto` or Sentence Transformers modes return cached lazy provider; invalid config raises `EmbeddingProviderError`, which `match_jobs` degrades to keyword scoring. |
| `default_rubric(interview_type: InterviewType, *, weights: RubricWeights \| dict[str, float] \| None = None) -> EvaluationRubric` | Validates rubric weights and returns dimension criteria. `RubricWeights` requires each weight in `[0,1]` and total 1.0. |
| `default_rubric_weights(interview_type: InterviewType) -> RubricWeights` | Returns validated defaults for a supported category. |
| `available_competencies(student_profile, job_listing, interview_type, *, job_match=None) -> list[str]` | Public function in `question_generator.py` but not re-exported in package `__init__.py`; deterministic helper used by adaptive selection. Its concrete parameter annotations are `StudentProfile`, `JobListing`, `InterviewType`, and optional `JobMatch`. |

`LLMProvider` is a `Protocol` with `name: str` and `generate_structured(prompt, response_model)`. `JobProvider` is a `Protocol` with `name`, `is_mock`, and `search(query, *, limit)`. `EmbeddingProvider` is a `Protocol` with `name` and `similarities(pairs)` returning one cosine score per pair. The AI package uses these adapters; it does not expose an HTTP API.

## 3. Pydantic schemas and validation

The schema modules use Pydantic v2. Several models set `extra="forbid"`; nested resume-profile, job, matching, tailoring, and interview schemas are therefore intended as validated contracts rather than permissive dictionaries.

### Resume parsing and student profile

| Schema | Fields and types | Required/default and validation |
| --- | --- | --- |
| `ParsedResume` (`resume_intelligence/schemas.py`) | `filename: str`; `source_format: Literal["pdf","docx"]`; `text: str`; `normalized_text: str`; `sections: dict[str,str]`; `warnings: list[str]`. | First five fields required. Warnings default to empty. Extra fields forbidden. |
| `EvidenceValue[T]` | `value: T`; `source_text: str \| None`; `source_section: str \| None`; `confidence: Literal["high","medium","low"]`; `evidence_status: Literal["explicit","inferred","uncertain"]`; `verification_status: Literal["unverified","needs_review","verified"]`. | `value` required; remaining metadata defaults to `None`/low/uncertain/needs_review. String value cannot be blank. Extractor verifies excerpt/value against supplied source and recomputes evidence metadata; profile facts remain unverified until student confirmation. |
| `PersonalInformation` | `name`, `email`, `phone`, `location`: each `EvidenceValue[str] \| None`. | Each defaults `None`; email format checked; phone must contain 7–15 digits. |
| `EducationProfile` | `institution`, `degree`, `branch`: `EvidenceValue[str] \| None`; `graduation_year: EvidenceValue[int] \| None`; `cgpa`, `percentage: EvidenceValue[float] \| None`. | All optional/default `None`; year 1900–2200; both score fields 0–100. |
| `SkillProfile` | Lists of `EvidenceValue[str]`: `programming_languages`, `frameworks`, `databases`, `cloud_technologies`, `tools`, `technical_domains`. | All default to empty lists. |
| `ProjectProfile` | `name`, `description: EvidenceValue[str] \| None`; `technologies`, `responsibilities`, `achievements: list[EvidenceValue[str]]`. | Scalars default `None`; lists empty. |
| `ExperienceProfile` | `company`, `position`, `duration: EvidenceValue[str] \| None`; `responsibilities`, `achievements: list[EvidenceValue[str]]`. | Scalars default `None`; lists empty. Used for both `experience` and `internships`. |
| `StudentProfileFields` | `personal_information: PersonalInformation`; `education: list[EducationProfile]`; `skills: SkillProfile`; `projects: list[ProjectProfile]`; `experience`, `internships: list[ExperienceProfile]`; `certifications`, `awards`, `achievements: list[EvidenceValue[str]]`. | Nested singleton/default models and lists default empty. |
| `StudentProfile` | Inherits all `StudentProfileFields` plus `extraction_provider: str`; `is_fallback: bool`; `warnings: list[str]`. | Provenance defaults to deterministic fallback, `True`, and empty warnings. |

### Jobs and job matching

| Schema | Fields and types | Required/default and validation |
| --- | --- | --- |
| `JobListing` (`job_intelligence/schemas.py`) | Required `job_id: str`, `source_provider: str`. Optional/defaulted: `title`, `company`, `description`, `location`, `source_job_id`, `salary_text: str \| None`; `required_skills`, `preferred_skills`, `eligibility_criteria`, `warnings: list[str]`; `min_experience_years`, `max_experience_years`, `salary_min`, `salary_max: float \| None`; `salary_currency: str \| None`; `salary_period: Literal["hour","day","week","month","year"] \| None`; `work_mode: Literal["remote","hybrid","on_site"] \| None`; `employment_type: Literal["full_time","part_time","contract","internship","freelance","temporary","other"] \| None`; `application_url`, `source_url: HttpUrl \| None`; `application_deadline: date \| None`; `published_at`, `last_updated: datetime \| None`; `is_mock: bool`. | Text fields cleaned, source provider casefolded, salary currency uppercase, list items trimmed, numeric values nonnegative; minimum experience cannot exceed maximum; salary minimum cannot exceed maximum. IDs, title/company, salary, dates, and URLs are not fabricated by normalization. |
| `MatchWeights` (`job_matching/schemas.py`) | Six floats in `[0,1]`: `required_skills`, `preferred_skills`, `education_relevance`, `experience_relevance`, `project_relevance`, `eligibility`. | Defaults `0.30, 0.10, 0.15, 0.15, 0.15, 0.15`; sum must be 1. |
| `MatchConfig` | `weights: MatchWeights`; `ineligible_score_cap: float`; `unknown_eligibility_score_cap: float`. | Defaults weights above, caps 39 and 69; caps 0–100. |
| `EvidenceReference` | `profile_path`, `value`, `source_text: str`; `source_section: str \| None`; confidence/evidence/verification literals as in profile evidence. | Required path/value/source and statuses. |
| `SkillMatch` / `SkillAssessment` | Match: `job_skill`, `student_skill`, category required/preferred, match type exact/synonym, evidence list. Assessment: `job_skill`, category, status matched/not_evidenced, explanation. | Evidence defaults empty on match. “Not evidenced” is not a claim of inability. |
| Matching `DimensionScore` | `score: float \| None`, `weight: float`, `status: assessed \| unknown \| not_applicable`, `explanation`, evidence references. | Score 0–100 when present; weight 0–1. |
| `EligibilityCriterionAssessment` / `EligibilityAssessment` | Criterion assessment: criterion, status met/mismatch/unknown, explanation, references. Aggregate: status eligible/not_eligible/unknown/not_applicable, criteria and warnings. | Criteria/warnings default empty. Only directly comparable, verified facts can establish met/mismatch for implemented checks; unsupported criteria remain unknown. |
| `JobMatch` | `job_id`, optional `job_title`; `rank >= 1`; `overall_score: float \| None`; `score_coverage`; `dimension_scores: dict[MatchDimension, DimensionScore]`; matched skills; missing required/preferred skills; skill assessments; eligibility assessment; explanation; evidence refs; `matching_method`; confidence high/medium/low; uncertainty/warnings. | Job ID, rank, coverage, dimensions, eligibility, explanation, method, confidence required; score 0–100; coverage 0–1; most lists default empty. |

Default matching score is the weighted mean of assessed dimensions, with remaining weights renormalized. If no dimension can be assessed, score is null. Hard verified eligibility mismatch and unknown eligibility apply score caps; the result is an evidence summary, not a hiring probability.

### Resume tailoring and cover letters

| Schema | Fields and types | Required/default and validation |
| --- | --- | --- |
| `ResumeFormatPreferences` | `section_order: list[Literal[summary,skills,projects,experience,internships,education,certifications,awards,achievements]]`; `include_contact_details: bool`; `bullet_style: Literal[bullets,numbered]`. | Defaults to listed order, `True`, `bullets`; duplicate sections rejected. |
| `TailoringPreferences` | `target_resume_length: Literal[one_page,two_pages,concise,standard,detailed]`; `tone: Literal[concise,professional,technical,ats_friendly]`; `student_instructions: str \| None`; `cover_letter_length: Literal[short,standard,long]`; `format_preferences: ResumeFormatPreferences`. | Defaults standard/professional/None/standard/default format; instructions max 2,000 chars and blank strings normalized to `None`. Instructions affect style/order only. |
| `TailoringRequest` | `student_profile`, `job_listing`, optional `job_match`, `preferences`. | Profile and listing required; preferences default; match must have same `job_id`. |
| `TailoringEvidenceReference` | `source_type: student_profile \| job_listing`; `source_path`; `value`; `source_text`; optional `source_section`; confidence/evidence status; verification status includes `not_applicable`. | All except section required. |
| `ValidatedClaim` | `text`; `evidence_references: list[TailoringEvidenceReference]`; `validation_status: supported \| needs_review`; confidence; `student_confirmation_required`. | Text nonempty and at least one reference. |
| `OmittedClaim` / `ValidationReport` | Omission: proposed text, unsupported/omitted status, reason, evidence paths. Report: supported/review counts, omitted claims, warnings. | Counts nonnegative; lists default empty. |
| `GenerationMetadata` / `DocumentReviewMetadata` | Provider, fallback flag, generation method (`llm_validated`, `mixed_llm_and_fallback`, `deterministic_fallback`, `deterministic_fallback_after_validation`), warnings. Review states include generated draft, validated draft, not reviewed/student reviewed, not approved/student approved. | Review/approval defaults to not reviewed/not approved; validator disallows approval without review. Services currently produce validated, unreviewed, unapproved drafts. |
| `TailoredSkill` / `TailoredEntry` | Skill claim, category, evidence class `demonstrated_in_context \| listed_skill`; entry optional heading and claims list. | Required skill/category/class; entry lists default empty. |
| `TailoredResume` | `job_id`; optional `job_title`; target length/tone/bullet style; personal-information claims; optional professional summary; skills; education/projects/experience/internships entries; certifications/awards/achievements claims; section order/change explanations; required validation report and generation metadata; review metadata. | Job ID, report and generation required; display collections default empty; review defaults to draft state. Separate output object; source profile is not mutated. |
| `CoverLetter` | `job_id`; target length/tone; required greeting; opening `ValidatedClaim`; optional relevant-experience and role-relevance claims; plain `closing_paragraph: str`; sign-off default; optional sign-off name claim; required validation/generation; review metadata. | Job ID, greeting, opening, closing, report and generation required; optional sections default `None`; validation prevents cross-job tailored resume input. |

`GeneratedClaimDraft`, `ClaimRewriteDraft`, `ResumeGenerationDraft`, and
`CoverLetterGenerationDraft` are provider-internal draft schemas. Generated
claim text must cite known evidence paths and pass lexical/numeric source
validation before inclusion. Rejected text is preserved only in the audit
report. PDF/DOCX output rendering is not implemented.

### Interview intelligence

| Schema | Fields and types | Required/default and validation |
| --- | --- | --- |
| `InterviewType` / `Difficulty` | Literal types: `technical`, `project_based`, `hr_behavioral`, `role_specific`; and `beginner`, `intermediate`, `advanced`. | Required where used. |
| `QuestionEvidenceReference` | Profile path/value/source text, optional section, confidence, evidence status, verification status. | Required except section; only supported relevant profile evidence is attached. |
| `RubricWeights` / `EvaluationRubric` | Seven scores in `[0,1]` (`technical_correctness`, `conceptual_understanding`, `depth_of_explanation`, `relevance`, `problem_solving`, `communication_clarity`, `practical_application`); rubric contains weights and `criteria: dict[DimensionName,str]`. | Every weight required and must sum to 1.0; criteria/weights required. |
| `InterviewQuestion` | `question_id`, `question_text`, type, difficulty, competency, optional job requirement, profile references, follow-up guidance, `selection_reason`, provider/method/warning; internal expected points, rubric, evaluation keywords. | ID/text/category/difficulty/competency/follow-up/provider/method required; text max 1,200, competency max 120, follow-up max 1,000; references and hidden answer fields default empty (rubric required). `expected_answer_points`, `evaluation_rubric`, and `evaluation_keywords` use `Field(exclude=True)` in normal Pydantic serialization. |
| `InterviewAnswer` | `question_id`, `answer_text`, `submitted_at: datetime`. | Required; text max 12,000; empty is permitted. |
| `AnswerEvidence` / `DimensionScore` | Evidence has dimension, exact answer excerpt (1–500), note (1–500). Score has optional 0–100 score, weight 0–1, assessed/not_assessed status, explanation, evidence. | A dimension score must be `None` exactly when not_assessed. |
| `AnswerEvaluation` | Question ID; optional overall 0–100; coverage 0–1; all seven dimension scores; strengths, weaknesses, missing concepts, suggestions, example-improvement areas; confidence low/medium/high; method `llm_rubric \| deterministic_heuristic`; provider; fallback flag; limitations. | Dimensions required and exactly all seven; dimension weights total 1; coverage and overall score must match assessed weighted dimensions. Empty answer has null overall. |
| `InterviewTurn` | Embedded question, answer, evaluation, selection reason and creation timestamp. | All required; one answered turn. |
| `CompetencyPerformance` | Competency; attempted count; scored values; unscored and fallback attempt counts; optional average; trend insufficient/improving/declining/stable; repeated weaknesses count; confidence. | Counts must align; fallback attempts cannot exceed attempts; average must equal recorded scores. |
| `InterviewSession` | ID; full `StudentProfile` and `JobListing` snapshots; optional `JobMatch`; type; original/current difficulty; planned question count; current index; question/answer/evaluation/turn histories; competency map; strengths/weaknesses/repeated weaknesses; status; optional termination reason/last focus; reinforcement-used flag; created/updated timestamps. | Profile/job/type/difficulty/count/index/timestamps required; count 1–30; lists/maps default empty. Match job ID must equal listing; answer/evaluation/turn lists align; current index equals completed turn count; question history contains completed turns and at most one pending question; in-progress requires a pending question and completed cannot have one. |
| `QuestionSelection` | Question, selection reason, target competency, reinforcement flag. | Target competency must equal question competency. |
| `InterviewReport` | Session ID/status; completed/planned counts; optional overall/technical/communication scores; competency breakdown; strong/weak/repeated areas; recommendations/practice topics/readiness observations/limitations; confidence; generated timestamp. | Counts and scores bounded; completed cannot exceed planned; lists/maps default empty. Derived from current session only. |
| `InterviewStartRequest` / `InterviewSubmitRequest` | Start embeds profile/job/optional match/type/difficulty/count; submit has answer text. | Start validates match job ID and count 1–30; difficulty defaults intermediate and count 10. Submit text max 12,000, no minimum. |

Interview rubric defaults are defined in `rubrics.py`. Technical correctness is
scored separately from communication. The service recomputes the weighted total
from dimension scores; it does not accept a provider's overall score. The
deterministic evaluator uses lexical/length/structure heuristics, leaves
technical correctness unassessed, and labels its result as a low-confidence
fallback.

## 4. Data flow and handoff points

```text
PDF/DOCX upload bytes + filename
    -> parse_resume
    -> ParsedResume.text / normalized_text / sections
    -> extract_student_profile(text)
    -> StudentProfile with claim-level evidence

query + optional location
    -> search_jobs
    -> list[JobListing] with source attribution and mock/live indicator

StudentProfile + list[JobListing]
    -> match_jobs
    -> ranked list[JobMatch]

StudentProfile + one selected JobListing + optional same-job JobMatch
    -> tailor_resume -> TailoredResume draft
    -> generate_cover_letter [optional TailoredResume] -> CoverLetter draft
    -> start_interview -> InterviewSession with pending question
    -> submit_interview_answer (repeat) -> updated InterviewSession
    -> get_interview_report -> InterviewReport
```

Verified direct handoffs:

1. The backend passes uploaded bytes and original filename to `parse_resume`.
2. Pass `ParsedResume.text` (not the `ParsedResume` object) to
   `extract_student_profile`. That extractor normalizes text/sections itself.
3. `search_jobs` is independent of the resume. Its returned `JobListing`
   objects can be passed directly to `match_jobs`.
4. The backend selects a listing from the search/match result and passes the
   exact `JobListing` plus `StudentProfile` to tailoring and interview services.
   Optional `JobMatch` must refer to the same `job_id`.
5. `generate_cover_letter` can receive the `TailoredResume` for the same job;
   it does not require it.
6. The services return Pydantic models suitable for `model_dump(mode="json")`
   after the backend decides what fields are safe for the requesting user.

There is no built-in orchestration object joining these services. The offline
end-to-end test covers extraction → mock job search → keyword job ranking, but
does not run the full tailoring and interview branches. There is no automatic
dependency from a job search to resume parsing or from a match result to
document/interview generation.

Potential transformations/adapters are the shared backend's responsibility:

- Convert upload/route data to `bytes` and `filename`.
- Select the desired `JobListing` from search/ranking results.
- Map shared user/profile/job identifiers to these Pydantic objects or provide
  snapshots; these schemas do not contain authenticated user IDs.
- Translate Pydantic and provider errors into the backend's HTTP/error format.
- For async routes, dispatch blocking synchronous work appropriately. Remotive
  uses synchronous `urllib`; Gemini and Sentence Transformers calls are also
  synchronous from these service contracts.
- Filter internal interview answer keys before returning question/session data.

## 5. Providers, configuration, and external dependencies

### LLM boundary

- `LLMProvider` is the replaceable structured-output protocol.
- `LLMService` accepts a Pydantic `response_model`, a feature-owned fallback
  factory, and retry count. `LLMResult` carries `value`, `provider`,
  `is_fallback`, optional `model`, and optional `fallback_reason`.
- `GeminiProvider` is the optional implementation. It requests JSON structured
  output and validates that JSON with Pydantic. It defaults to the source model
  name `gemini-2.5-flash`; tests can inject a client.
- `create_llm_service` checks whether `GEMINI_API_KEY` is configured and
  initializes Gemini only when available. **This report contains no key or
  environment value.** The Gemini extra is optional.
- Feature modules own deterministic fallbacks and label their provider/method.
  Profile extraction, tailoring, and interview question/evaluation paths use
  the shared abstraction. Live Gemini behavior is not proven by the offline
  test suite.

### Job discovery providers

- `MockJobProvider` supplies hardcoded demo records, sets `is_mock=True`, and
  results are clearly labeled as not live.
- `RemotiveJobProvider` reads the public Remotive feed; it does not require an
  API key. It uses HTTPS, an 8-second default timeout, six-hour in-process
  cache, bounded 1,000-record fetch, and one retry for transient network/timeout
  or selected HTTP 429/5xx errors. Response-shape failures are explicit.
- Configuration names (not values): `JOBS_PROVIDER`,
  `JOB_PROVIDER_TIMEOUT_SECONDS`, `REMOTIVE_CACHE_TTL_SECONDS`, and
  `REMOTIVE_API_URL`. Provider errors do not silently switch to mock jobs.
- The normalized `JobListing` records `source_provider`, `source_job_id`,
  `source_url`, `is_mock`, and warnings. Remotive results are remote-only,
  may be delayed, and require source attribution/backlink.

### Semantic matching

- `EmbeddingProvider` returns one cosine similarity per pair in `[-1,1]`.
- `SentenceTransformerEmbeddingProvider` lazily loads
  `sentence-transformers/all-MiniLM-L6-v2` by default. Matching mode/model
  configuration names are `JOB_MATCH_EMBEDDINGS` and `JOB_MATCH_MODEL`.
- Keyword fallback uses an explicit skill synonym map and deterministic text
  overlap. If any embedding call fails or scores are malformed, all jobs are
  rescored using keyword fallback and `matching_method` reports that mode.
- No Sentence Transformers model is required for the base dependency set.

### Declared packages (`pyproject.toml`)

- Runtime: `pydantic>=2.7,<3`, `PyMuPDF>=1.24,<2`,
  `python-docx>=1.1,<2`; Python requirement `>=3.11`.
- Optional Gemini: `google-genai>=1.0,<2`.
- Optional matching: `sentence-transformers>=3,<6`.
- Development: `pytest>=8,<10`.
- HTTP/JSON/cache/regex/date handling in provider modules otherwise uses the
  Python standard library. This AI project does not declare an ORM or web
  framework dependency.

## 6. Backend integration recommendations

### Reuse directly; do not duplicate

The shared backend can import and call existing public functions and reuse
existing Pydantic schemas for: parsed resumes, evidence-backed student profiles,
normalized listings, match results/configuration, tailored resume/cover-letter
drafts, and interview question/session/evaluation/report data. Preserve their
provenance and validation fields; do not replace evidence-bearing values with
untyped strings.

### Required shared backend interface capabilities

The following are recommended responsibilities for Member 1's shared
`backend/app/ai/interfaces.py`; these names describe capabilities, not existing
classes or invented function signatures.

| Shared interface capability | Existing implementation to wrap/reuse | Backend responsibility |
| --- | --- | --- |
| Resume parse and extraction boundary | `parse_resume`, `ParsedResume`, `extract_student_profile`, `StudentProfile` | Upload validation/error translation; bind output to authenticated user/profile; decide which source text is retained. |
| Job discovery/normalization boundary | `search_jobs`, `JobProvider`, `JobListing` | Query inputs, attribution policy, cache/refresh policy and mapping provider exceptions. |
| Match boundary | `match_jobs`, `MatchConfig`, `JobMatch` | Supply selected profile/listings, persist or cache rankings, interpret null scores and eligibility warnings correctly. |
| Tailoring boundary | `tailor_resume`, `generate_cover_letter`, their preferences/results | Persist draft plus validation/evidence metadata; keep student review/approval actions outside the generator. |
| Interview lifecycle boundary | `start_interview`, `submit_interview_answer`, `select_next_question`, `get_interview_report`, `end_interview`, `InterviewSession` | Load/save state atomically; authorize session ownership; protect evaluator material; route/report lifecycle. |
| Provider provenance/error boundary | `LLMService`, `LLMResult`, `JobProviderError`, `EmbeddingProviderError`, output provenance fields | Centralize configuration without exposing secrets; return accurate fallback/live labels; translate errors to backend contracts. |

Potential mappings should alias or wrap these Pydantic models rather than
redeclaring their fields in a second AI schema. Where a backend-owned API model
must differ, build explicit adapters and preserve values, evidence references,
null/unknown states, source attribution, and provider/fallback metadata.

### Backend-owned concerns and data to provide

Authentication, authorization, student consent, user/session ownership,
database access, transactions, retention/deletion policies, API routes, upload
storage, application tracking, and student approval are absent from the AI
package and must remain in backend-owned layers. The backend must provide valid
resume bytes/filename or resume text, selected `StudentProfile`, selected
normalized `JobListing`, optional matching configuration/result, user
preferences, and a trusted persisted `InterviewSession` snapshot when resuming.

Structured outputs worth persisting, subject to product retention/consent
policy, include:

- `ParsedResume` text/section output only if the product needs it; it can contain
  sensitive resume content.
- `StudentProfile` plus evidence excerpts and extraction provider/fallback
  warnings.
- Job source identity/attribution and normalized listing snapshot if a result
  must remain reproducible after an upstream listing changes.
- `JobMatch` score coverage, dimensions, eligibility, warnings, and evidence.
- `TailoredResume`/`CoverLetter` with `ValidationReport`, generation metadata,
  and review state. Services return draft state, not student approval.
- Interview session metadata, questions, answers, evaluations, competency
  state, and optionally a point-in-time report; see persistence checklist below.

## 7. Interview persistence and resume requirements

`InterviewSession` is a serializable Pydantic model, but its service currently
keeps it in memory and returns a new model snapshot after submission. No
repository, database model, cache keyed by session ID, or API route persists it.

### Required to resume the current interview faithfully

Persist these fields (or sufficient normalized equivalents):

1. **Session identity/state:** `session_id`, `status`, `termination_reason`,
   `created_at`, `updated_at`, `total_planned_questions`,
   `current_question_index`, `difficulty`, `current_difficulty`,
   `last_focus_competency`, `focus_reinforcement_used`.
2. **Context snapshot:** `student_profile`, `job_listing`, optional `job_match`,
   and `interview_type`. The service stores object snapshots, not profile/job
   database IDs. If backend stores references instead, it must define how
   changed profile/listing data is versioned so a session doesn't silently
   change context.
3. **Question history:** each question's visible fields and selection reason;
   generation provider/method/warning; relevant profile evidence references;
   internal `expected_answer_points`, `evaluation_rubric`, and
   `evaluation_keywords`. Hidden evaluation material is needed to evaluate a
   pending question deterministically and maintain the exact session contract.
4. **Completed turns:** `InterviewAnswer` including answer text and timestamp;
   full `AnswerEvaluation` for each completed question; and corresponding
   `InterviewTurn` selection reason/time. The session model also stores aligned
   `answer_history` and `evaluation_history` lists in addition to
   `turn_history`. A backend may normalize these instead of duplicating the
   same payload, but it must reconstruct all three lists with aligned question
   IDs when loading `InterviewSession`.
5. **Adaptive/report counters:** `competency_performance` including each
   competency's scores, unscored/fallback counts, average, trend, repeated
   weakness count, and confidence; `identified_strengths`,
   `identified_weaknesses`, and `repeated_weaknesses`.

The session validator requires all completed answer/evaluation/turn lists to
align, question history to contain completed turns plus at most one pending
question, in-progress sessions to have one pending question, completed sessions
to have none, current index to equal completed-turn count, unique question IDs,
and matching IDs across each turn's question/answer/evaluation.

`serialize_interview_session(session)` intentionally omits hidden rubric/key
fields and is student-visible-safe, but the source docstring states it cannot
reconstruct those hidden fields. Trusted persistence must use
`serialize_interview_session(session, include_evaluation_material=True)` and
strictly prevent that representation from being returned to a student before
answer submission. `get_question_evaluation_material` likewise requires an
explicit flag; authorization is not implemented by that flag and must be
enforced by the backend.

### Reporting-only / derivable data

`InterviewReport` is produced by `get_interview_report(session)` and is not a
field in `InterviewSession`. It can be recomputed from session histories and
competency state. Persist a report snapshot only if the product needs stable
historical report timestamps/content; its `generated_at` changes on each call.
Report fields are `overall_score`, technical and communication averages,
competency breakdown, strong/weak/repeated areas, recommendations, practice
topics, readiness observations, limitations, confidence, counts, status, and
generation time. It is not a hiring decision or durable readiness record.

Selection reason, generation provider/method, answer evidence excerpts, and
limitations may not be strictly required to choose the next question, but are
required to reproduce the same audit/report/provenance output and should be
retained if historical explanation is a product requirement.

## 8. Test coverage and status

| Test file | Verified coverage areas |
| --- | --- |
| `backend/tests/test_resume_parser.py` | PDF/DOCX validation, text extraction, section headings/case/line breaks, malformed/empty/oversized/unsupported files. |
| `backend/tests/test_profile_extractor.py` | Complete/missing/ambiguous profile facts, evidence, project lists, duplicate skills, invalid/provider response retries, fallback, schema validation. |
| `backend/tests/test_llm_provider.py` | Explicit fallback labels, Gemini structured response validation with injected mock client (no live request), provider failure. |
| `backend/tests/test_job_discovery.py` | Mock/Remotive normalization, fields/URLs/dates/deduplication, filtering/limits, response/provider errors, retry and environment selection. |
| `backend/tests/test_job_matching.py` | Exact/synonym and missing skills, education/experience/project dimensions, eligibility/unknowns, ranking, weights, evidence, embedding/fallback behavior. |
| `backend/tests/test_resume_tailoring.py` | Tailored resume and cover-letter generation, evidence checks, unsupported claims/numbers, provider retry/fallback, preferences, review state and input immutability. |
| `backend/tests/test_interview_intelligence.py` | Categories/difficulties, profile grounding, count/duplicate rules, PII prompt exclusion, evaluation scoring/quotes, provider failure/invalid output/fallback, adaptation, session lifecycle, serialization, report and early termination. |
| `backend/tests/test_ai_pipeline_offline.py` | Offline extraction → deterministic job search fixture → job-match ranking; asserts stage labels, result count/order and evidence. It does not execute tailoring/interview. |

Last recorded complete suite: **143 passed, 1 warning**. The warning was the
third-party `google.genai` deprecation warning in the injected-client provider
test. This audit could not rerun pytest because the current shell could not
resolve Python/pytest and no project virtual environment was present. No test
was changed or weakened.

## 9. Summary for Member 1

### Current capabilities

Phases 1–6 provide deterministic PDF/DOCX resume parsing; evidence-backed
profile extraction; mock and Remotive job discovery/normalization; explainable
weighted matching with optional semantic embeddings; evidence-validated resume
and cover-letter drafts; and adaptive mock interview sessions, answer
evaluations, competency tracking, and reports. Shared LLM calls use one
replaceable provider boundary with deterministic feature fallbacks. No live
Gemini integration was verified by tests.

### Public service interface table

| Capability | Existing function(s) | Primary output |
| --- | --- | --- |
| Resume parse | `parse_resume` | `ParsedResume` |
| Student profile | `extract_student_profile` | `StudentProfile` |
| Job search/normalization | `search_jobs`, `normalize_job`, `normalize_jobs` | `list[JobListing]` / `JobListing` |
| Job matching | `match_jobs` | ranked `list[JobMatch]` |
| Resume tailoring | `tailor_resume` | `TailoredResume` draft |
| Cover letter | `generate_cover_letter` | `CoverLetter` draft |
| Question generation | `generate_interview_questions` | `list[InterviewQuestion]` |
| Interview lifecycle | `start_interview`, `submit_interview_answer`, `select_next_question`, `end_interview` | `InterviewSession` / `QuestionSelection` |
| Evaluation/report | `evaluate_interview_answer`, `get_interview_report` | `AnswerEvaluation` / `InterviewReport` |

### Required shared backend interface capabilities

1. Reuse/adapt the existing schemas without duplicating factual fields or
   dropping evidence/provenance.
2. Provide upload, profile/job resolution, and normalized service inputs.
3. Translate AI/Pydantic/provider exceptions to backend/API error contracts.
4. Persist and authorize user-owned sessions/documents outside `app/ai`.
5. Keep hidden interview evaluation material server-side until allowed.
6. Preserve provider/fallback labels, source attribution, score coverage,
   unknown states, and document review/approval metadata.
7. Schedule synchronous network/model calls appropriately if invoked from async
   backend handlers.

### Unresolved integration decisions

- Will stored sessions use full profile/job snapshots or versioned IDs?
- Which retention, deletion, and consent policy applies to original resume text,
  evidence excerpts, interview answers, and hidden evaluation guidance?
- Will interview persistence normalize questions/answers/evaluations into
  separate records or store a session JSON snapshot? Either design must restore
  the model's alignment invariants.
- What API serialization view separates student-visible question fields from
  server-only answer points, rubric, and evaluator keywords?
- Should reports be recomputed or saved as point-in-time snapshots?
- How will provider and Pydantic errors map to shared HTTP status/error bodies?
- Which async execution/thread-pool policy will wrap blocking provider calls?
- Who owns Gemini, Remotive, and embedding configuration/secrets and controls
  provider enablement by environment?
- What interface maps the backend's profile/job IDs and authorization context to
  the AI package's ID-free `StudentProfile`/`JobListing` snapshots?

**Source-change confirmation:** no Python source, tests, database models,
migrations, routes, or shared interfaces were modified during this audit. The
only requested artifact created is `docs/PHASE_1_6_AI_INTEGRATION_AUDIT.md`.
