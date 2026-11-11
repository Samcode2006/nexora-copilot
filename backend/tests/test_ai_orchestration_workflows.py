from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.ai.interview_intelligence.question_generator import generate_interview_questions
from app.ai.job_intelligence.providers import JobProviderError
from app.ai.orchestration import (
    AnswerEvaluationInput,
    InterviewPreparationInput,
    JobMatchingInput,
    ResumeTailoringInput,
    evaluate_answer,
    match_jobs_workflow,
    prepare_interview,
    process_resume,
    tailor_resume_workflow,
)
from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStatus,
)
from app.ai.orchestration.schemas import ResumeProcessingInput
from app.ai.providers import LLMService
from app.ai.resume_intelligence.parser import ResumeParseError
from app.ai.resume_intelligence.schemas import ParsedResume
from app.ai.resume_tailoring.tailoring import tailor_resume
from tests.ai_orchestration_helpers import (
    docx_bytes,
    fresh_store,
    mock_provider,
    offline_services,
    raw_job,
    sample_job,
    sample_profile,
)


def test_resume_processing_workflow_succeeds_offline() -> None:
    store = fresh_store()
    result = process_resume(
        ResumeProcessingInput(
            filename="resume.docx",
            content=docx_bytes("Name: Asha Rao\nEmail: asha@example.test\nSkills\nPython"),
        ),
        services=offline_services(store=store),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.parsed_resume is not None
    assert result.student_profile is not None
    assert WorkflowErrorCode.INVALID_INPUT not in {error.code for error in result.errors}
    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert metadata.status == WorkflowStatus.SUCCEEDED


def test_resume_processing_routes_parse_failure_without_leaking_exception() -> None:
    def fail_parse(_content: bytes, _filename: str):
        raise ResumeParseError("private provider text", code="malformed_document")

    store = fresh_store()
    result = process_resume(
        {"filename": "resume.docx", "content": docx_bytes()},
        services=offline_services(store=store, parse_resume_fn=fail_parse),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.errors[-1].code == WorkflowErrorCode.RESUME_PARSE_FAILURE
    assert "private provider text" not in result.errors[-1].message
    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert metadata.error_codes == (WorkflowErrorCode.RESUME_PARSE_FAILURE,)


def test_profile_extraction_failure_is_reported_safely() -> None:
    def fail_extraction(*_args, **_kwargs):
        raise ValueError("profile secret must not escape")

    result = process_resume(
        {"filename": "resume.docx", "content": docx_bytes()},
        services=offline_services(extract_student_profile_fn=fail_extraction),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.errors[-1].code == WorkflowErrorCode.PROFILE_EXTRACTION_FAILURE
    assert "profile secret" not in result.errors[-1].message


def test_job_workflow_discovers_normalizes_and_ranks_jobs() -> None:
    provider = mock_provider(
        raw_job("job-1", "Python Backend Intern"),
        raw_job("job-2", "FastAPI Engineering Intern"),
        raw_job("job-1", "Python Backend Intern"),
    )
    result = match_jobs_workflow(
        JobMatchingInput(student_profile=sample_profile(), query="Python"),
        services=offline_services(job_provider=provider),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert len(result.jobs) == 2
    assert result.matches
    assert [match.rank for match in result.matches] == list(range(1, len(result.matches) + 1))
    assert all(job.is_mock for job in result.jobs)


def test_no_jobs_is_successful_and_skips_matching() -> None:
    def unexpected_match(*_args, **_kwargs):
        raise AssertionError("matching should not run when discovery returns no jobs")

    result = match_jobs_workflow(
        {"student_profile": sample_profile(), "query": "Python"},
        services=offline_services(
            job_provider=mock_provider(),
            match_jobs_fn=unexpected_match,
        ),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.jobs == []
    assert result.matches == []
    assert result.errors[-1].code == WorkflowErrorCode.NO_JOBS_FOUND
    assert result.errors[-1].severity.value == "info"


def test_no_matches_is_successful_empty_result() -> None:
    result = match_jobs_workflow(
        {"student_profile": sample_profile(), "query": "Python"},
        services=offline_services(
            job_provider=mock_provider(raw_job("job-1", "Python Backend Intern")),
            match_jobs_fn=lambda *_args, **_kwargs: [],
        ),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert len(result.jobs) == 1
    assert result.matches == []
    assert result.errors[-1].code == WorkflowErrorCode.NO_MATCHES


def test_provider_failure_is_not_replaced_with_fabricated_jobs() -> None:
    class FailingProvider:
        name = "offline-failure"
        is_mock = False

        def search(self, _query: str, *, limit: int):
            raise JobProviderError("provider private details")

    result = match_jobs_workflow(
        {"student_profile": sample_profile(), "query": "Python"},
        services=offline_services(job_provider=FailingProvider()),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.jobs == []
    assert result.errors[-1].code == WorkflowErrorCode.JOB_DISCOVERY_FAILURE
    assert "provider private details" not in result.errors[-1].message


def test_multi_job_tailoring_succeeds() -> None:
    result = tailor_resume_workflow(
        ResumeTailoringInput(
            student_profile=sample_profile(),
            selected_jobs=[
                sample_job("job-1"),
                sample_job("job-2", title="Python Platform Intern"),
            ],
        ),
        services=offline_services(),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert len(result.outcomes) == 2
    assert all(item.tailored_resume is not None for item in result.outcomes)
    assert all(item.cover_letter is not None for item in result.outcomes)
    assert result.partial_success is not None
    assert result.partial_success.succeeded_items == 2
    assert result.partial_success.failed_items == 0


def test_one_tailoring_failure_does_not_stop_other_jobs() -> None:
    def tailor_one(profile, job, job_match, preferences, *, llm_service):
        if job.job_id == "job-fail":
            raise ValueError("private tailoring exception")
        return tailor_resume(
            profile,
            job,
            job_match,
            preferences,
            llm_service=llm_service,
        )

    result = tailor_resume_workflow(
        {
            "student_profile": sample_profile(),
            "selected_jobs": [
                sample_job("job-fail"),
                sample_job("job-ok", title="Python Platform Intern"),
            ],
        },
        services=offline_services(tailor_resume_fn=tailor_one),
    )

    assert result.status == WorkflowStatus.PARTIAL
    by_id = {outcome.job_id: outcome for outcome in result.outcomes}
    assert by_id["job-fail"].tailored_resume is None
    assert by_id["job-fail"].errors[-1].code == WorkflowErrorCode.TAILORING_FAILURE
    assert by_id["job-ok"].tailored_resume is not None
    assert by_id["job-ok"].cover_letter is not None
    assert result.partial_success is not None
    assert result.partial_success.succeeded_items == 1
    assert result.partial_success.failed_items == 1


def test_cover_letter_failure_preserves_tailored_resume() -> None:
    def fail_letter(*_args, **_kwargs):
        raise ValueError("private letter details")

    result = tailor_resume_workflow(
        {
            "student_profile": sample_profile(),
            "selected_jobs": [sample_job("job-1")],
        },
        services=offline_services(generate_cover_letter_fn=fail_letter),
    )

    assert result.status == WorkflowStatus.PARTIAL
    outcome = result.outcomes[0]
    assert outcome.tailored_resume is not None
    assert outcome.cover_letter is None
    assert outcome.errors[-1].code == WorkflowErrorCode.COVER_LETTER_FAILURE
    assert "private letter details" not in outcome.errors[-1].message
    assert result.partial_success is not None
    assert result.partial_success.partial_items == 1


def test_interview_preparation_does_not_evaluate_answers() -> None:
    evaluated: list[str] = []

    def evaluator(question, answer, profile, job, **kwargs):
        evaluated.append(answer)
        raise AssertionError("answer evaluation must be a separate workflow")

    result = prepare_interview(
        InterviewPreparationInput(
            student_profile=sample_profile(),
            job_listing=sample_job(),
            question_count=3,
        ),
        services=offline_services(evaluate_interview_answer_fn=evaluator),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert len(result.questions) == 3
    assert evaluated == []


def test_answer_evaluation_is_a_separate_graph_invocation() -> None:
    profile = sample_profile()
    job = sample_job()
    question = generate_interview_questions(
        profile,
        job,
        "technical",
        "intermediate",
        1,
        llm_service=LLMService(),
    )[0]
    result = evaluate_answer(
        AnswerEvaluationInput(
            student_profile=profile,
            job_listing=job,
            question=question,
            answer="I would verify inputs, implement the API, and test its error cases.",
        ),
        services=offline_services(),
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.question_id == question.question_id
    assert result.evaluation is not None
    assert result.evaluation.question_id == question.question_id


def test_invalid_input_returns_structured_failure_without_payload() -> None:
    store = fresh_store()
    result = process_resume(
        {"filename": " ", "content": "RAW-INVALID-SECRET"},
        services=offline_services(store=store),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.errors[-1].code == WorkflowErrorCode.INVALID_INPUT
    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert "RAW-INVALID-SECRET" not in metadata.model_dump_json()


def test_unexpected_exception_uses_safe_internal_error() -> None:
    def explode(*_args, **_kwargs):
        raise RuntimeError("INTERNAL-SECRET")

    store = fresh_store()
    result = process_resume(
        {"filename": "resume.docx", "content": docx_bytes()},
        services=offline_services(store=store, parse_resume_fn=explode),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.errors[-1].code == WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR
    assert "INTERNAL-SECRET" not in result.errors[-1].message
    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert "INTERNAL-SECRET" not in metadata.model_dump_json()


def test_resume_bytes_and_profile_snapshots_never_enter_checkpoint() -> None:
    store = fresh_store()
    sensitive_profile = sample_profile("PROFILE-CHECKPOINT-CANARY@example.test")

    def parse_stub(content: bytes, filename: str) -> ParsedResume:
        assert content == b"RAW-RESUME-CHECKPOINT-CANARY"
        return ParsedResume(
            filename=filename,
            source_format="docx",
            text="Private resume text",
            normalized_text="Private resume text",
            sections={},
        )

    result = process_resume(
        {"filename": "resume.docx", "content": b"RAW-RESUME-CHECKPOINT-CANARY"},
        services=offline_services(
            store=store,
            parse_resume_fn=parse_stub,
            extract_student_profile_fn=lambda *_args, **_kwargs: sensitive_profile,
        ),
    )

    assert result.student_profile is sensitive_profile
    metadata = store.get(result.workflow_id)
    assert metadata is not None
    serialized = metadata.model_dump_json()
    assert "RAW-RESUME-CHECKPOINT-CANARY" not in serialized
    assert "PROFILE-CHECKPOINT-CANARY" not in serialized
    assert "Private resume text" not in serialized


def test_profile_snapshot_never_enters_job_checkpoint() -> None:
    store = fresh_store()
    profile = sample_profile("PROFILE-MATCH-CHECKPOINT-CANARY@example.test")
    result = match_jobs_workflow(
        {"student_profile": profile, "query": "Python"},
        services=offline_services(
            store=store,
            job_provider=mock_provider(raw_job("job-1", "Python Backend Intern")),
        ),
    )

    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert "PROFILE-MATCH-CHECKPOINT-CANARY" not in metadata.model_dump_json()


def test_interview_answer_never_enters_checkpoint() -> None:
    store = fresh_store()
    profile = sample_profile()
    job = sample_job()
    question = generate_interview_questions(
        profile, job, "technical", "intermediate", 1, llm_service=LLMService()
    )[0]
    result = evaluate_answer(
        {
            "student_profile": profile,
            "job_listing": job,
            "question": question,
            "answer": "ANSWER-CHECKPOINT-CANARY",
        },
        services=offline_services(store=store),
    )

    metadata = store.get(result.workflow_id)
    assert metadata is not None
    assert "ANSWER-CHECKPOINT-CANARY" not in metadata.model_dump_json()


def test_concurrent_workflows_do_not_share_runtime_state() -> None:
    profile = sample_profile()
    first = offline_services(job_provider=mock_provider(raw_job("job-a", "Python A")))
    second = offline_services(job_provider=mock_provider(raw_job("job-b", "Python B")))

    with ThreadPoolExecutor(max_workers=2) as executor:
        left = executor.submit(
            match_jobs_workflow,
            {"student_profile": profile, "query": "Python"},
            services=first,
        )
        right = executor.submit(
            match_jobs_workflow,
            {"student_profile": profile, "query": "Python"},
            services=second,
        )
        result_a = left.result()
        result_b = right.result()

    assert result_a.workflow_id != result_b.workflow_id
    assert [job.source_job_id for job in result_a.jobs] == ["job-a"]
    assert [job.source_job_id for job in result_b.jobs] == ["job-b"]


def test_matching_failure_uses_matching_error_code() -> None:
    result = match_jobs_workflow(
        {"student_profile": sample_profile(), "query": "Python"},
        services=offline_services(
            job_provider=mock_provider(raw_job("job-1", "Python Backend Intern")),
            match_jobs_fn=lambda *_args, **_kwargs: [None],
        ),
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.errors[-1].code == WorkflowErrorCode.MATCHING_FAILURE


def test_invalid_interview_and_answer_inputs_have_no_fabricated_ids() -> None:
    interview = prepare_interview({}, services=offline_services())
    evaluation = evaluate_answer({}, services=offline_services())

    assert interview.status == WorkflowStatus.FAILED
    assert interview.job_id is None
    assert evaluation.status == WorkflowStatus.FAILED
    assert evaluation.question_id is None
