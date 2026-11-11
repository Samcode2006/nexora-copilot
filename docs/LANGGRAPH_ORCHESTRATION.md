# NEXORA LangGraph Orchestration

## Scope

This package composes the existing AI services into four independent workflows. It is an AI-side orchestration layer only. It does not add FastAPI routes, authentication, persistence, repositories, approval enforcement, evidence records, or long-term career memory.

The public entry points are:

- process_resume(input_data, *, services=None, checkpoint_store=None)
- match_jobs_workflow(input_data, *, services=None, checkpoint_store=None)
- tailor_resume_workflow(input_data, *, services=None, checkpoint_store=None)
- prepare_interview(input_data, *, services=None, checkpoint_store=None)
- evaluate_answer(input_data, *, services=None, checkpoint_store=None)

Inputs and outputs are validated with orchestration-owned Pydantic models in app.ai.orchestration.schemas. The existing AI service signatures and shared service schemas remain unchanged.

## Package structure

- state.py defines the private TypedDict carried by each graph invocation.
- schemas.py defines workflow input and output models plus per-job partial results.
- errors.py defines safe error codes, categories, statuses, and user-facing messages.
- checkpoint.py provides an allowlisted, bounded in-memory metadata store.
- services.py injects existing AI functions and provider instances for deterministic tests.
- nodes/ contains independently testable input, resume, job, tailoring, and interview nodes.
- workflows/ composes each independent StateGraph and exposes the entry points.

The nodes call parse_resume, extract_student_profile, search_jobs, normalize_job, normalize_jobs, match_jobs, tailor_resume, generate_cover_letter, generate_interview_questions, and evaluate_interview_answer. They do not call HTTP routes or access a database/repository.

## Runtime state and privacy

Each entry point validates its input, creates a new workflow ID, compiles/invokes a graph, and returns a typed result. Runtime graph state is local to that invocation. It can briefly carry resume bytes, extracted text, student profiles, provider results, interview questions, or an explicitly supplied answer. Resume bytes are cleared after parsing. The graph is compiled without a LangGraph checkpointer, and no runtime state is saved to disk or a database.

InMemoryMetadataCheckpointStore stores only MetadataCheckpointRecord fields: workflow ID/type, current stage, status, completed stage IDs, error categories/codes, timestamps, and optional item counts. Its model rejects additional fields. It never receives a graph-state dictionary, prompt, resume, profile, answer, exception message, provider response, or credential.

This metadata record is operational progress only. It is not a resumable graph checkpoint and cannot restore a workflow. The default store is process-local and bounded to 1,000 records; older records are evicted as new ones arrive. Call store.cleanup(workflow_id) to remove one record or store.clear() to clear the store. Supplying a store is optional and useful for tests and lifecycle control.

No runtime state is logged. Exceptions are mapped to fixed safe messages; raw exception messages and provider payloads do not enter workflow errors or checkpoint metadata.

## State fields

The private TypedDict supports workflow ID/type, stage/status, runtime input, parsed resume, extracted profile, job search criteria, discovered and normalized jobs, ranked matches, selected job(s), tailored resumes and cover letters, interview questions, an explicitly requested answer evaluation, completed stages, structured issues, and partial-success counts.

Large values are held only where the active workflow needs them. The resume parser input bytes are released from graph state immediately after parsing. Other workflows reference validated input models rather than serializing copies into checkpoint storage.

## Nodes and workflows

### Resume processing

validate_resume_input → parse_resume → extract_profile → validate_result → finish

A parse or extraction failure terminates with a structured, safe error. The result can contain parsed text and an extracted profile for the caller, but neither is placed in checkpoint metadata.

### Job matching

validate_input → discover_jobs → normalize_jobs → [match_jobs] → finish

The discovery node calls search_jobs with an injectable JobProvider. The normalization stage validates and deduplicates through the existing normalize_job/normalize_jobs functions. An empty listing or match set is a successful empty result with an informational issue. Provider failure is an explicit failure and is never replaced by fabricated listings.

### Resume tailoring

validate_input → tailor_resumes → generate_cover_letters → finish

The workflow processes up to 20 selected jobs independently. A failed job does not stop other jobs. A cover-letter failure retains its successful tailored resume. Each job outcome is marked succeeded, partial, or failed, and the aggregate result reports counts.

### Interview preparation

validate_input → generate_questions → finish

Question generation reuses the existing interview question service. It does not evaluate answers or create a multi-turn session.

### Answer evaluation

validate_input → evaluate_answer → finish

This is a separate graph invocation and runs only when a caller explicitly supplies an answer, question, profile, and job.

## Error routing

Expected input, parse, extraction, discovery, normalization, matching, tailoring, cover-letter, question-generation, and answer-evaluation failures are mapped to orchestration error codes. Unexpected exceptions become unexpected_internal_error. The output contains fixed safe text and does not include the exception string.

The job-matching graph routes provider/normalization failures to completion, routes empty job results around the matching node, and only invokes matching when normalized jobs exist. Resume and interview graphs route failed stages to their finish node. Multi-job tailoring records per-job outcomes and continues through the remaining jobs.

No provider outage is turned into success. Existing deterministic fallbacks remain owned by their underlying AI services.

## Example invocations

~~~python
from app.ai.orchestration import process_resume

result = process_resume(
    {"filename": "resume.docx", "content": uploaded_bytes}
)
if result.status == "succeeded":
    profile = result.student_profile
~~~

~~~python
from app.ai.job_intelligence import MockJobProvider
from app.ai.orchestration import (
    JobMatchingInput,
    OrchestrationServices,
    match_jobs_workflow,
)
from app.ai.providers import LLMService

services = OrchestrationServices(
    job_provider=MockJobProvider(jobs=fixture_jobs),
    llm_service=LLMService(),
)
result = match_jobs_workflow(
    JobMatchingInput(student_profile=profile, query="Python internship"),
    services=services,
)
~~~

~~~python
from app.ai.orchestration import prepare_interview, evaluate_answer

questions = prepare_interview(
    {
        "student_profile": profile,
        "job_listing": selected_job,
        "interview_type": "technical",
        "difficulty": "intermediate",
        "question_count": 5,
    }
)
evaluation = evaluate_answer(
    {
        "student_profile": profile,
        "job_listing": selected_job,
        "question": questions.questions[0],
        "answer": "I would first verify the request inputs and write a regression test.",
    }
)
~~~

Callers may instead pass dictionaries; boundary models reject unknown fields and invalid values. Example data must be synthetic. Do not pass credentials, database handles, or repositories to AI services.

## Offline tests

Run from backend/:

~~~powershell
python -m pytest -p no:cacheprovider -q tests/test_ai_orchestration_nodes.py tests/test_ai_orchestration_workflows.py tests/test_ai_orchestration_checkpoint.py tests/test_ai_orchestration_regressions.py
python -m pytest -p no:cacheprovider -q
python -m ruff check app/ai/orchestration tests/test_ai_orchestration_*.py
~~~

These tests use deterministic services/providers and in-memory files. They do not call Gemini, Remotive, the internet, database connections, or model downloads.

## Future backend integration

Member 1 owns FastAPI request validation, authentication/authorization, task lifecycle and timeouts, routes, persistence, evidence records, approvals, and database transactions. Member 3's AI package supplies in-process functions and typed results. A backend adapter may call these entry points and map orchestration errors/results to the approved API contract, but that adapter is not implemented here. The metadata checkpoint store must not be used as backend persistence or as resumable workflow storage.
