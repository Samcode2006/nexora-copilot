"""Safe, structured errors for AI orchestration workflows."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class WorkflowType(StrEnum):
    RESUME_PROCESSING = "resume_processing"
    JOB_MATCHING = "job_matching"
    RESUME_TAILORING = "resume_tailoring"
    INTERVIEW_PREPARATION = "interview_preparation"
    ANSWER_EVALUATION = "answer_evaluation"


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class WorkflowStage(StrEnum):
    INPUT_VALIDATION = "input_validation"
    RESUME_PARSING = "resume_parsing"
    PROFILE_EXTRACTION = "profile_extraction"
    RESULT_VALIDATION = "result_validation"
    JOB_DISCOVERY = "job_discovery"
    JOB_NORMALIZATION = "job_normalization"
    JOB_MATCHING = "job_matching"
    RESUME_TAILORING = "resume_tailoring"
    COVER_LETTER_GENERATION = "cover_letter_generation"
    INTERVIEW_QUESTION_GENERATION = "interview_question_generation"
    ANSWER_EVALUATION = "answer_evaluation"
    COMPLETE = "complete"


class WorkflowErrorCategory(StrEnum):
    VALIDATION = "validation"
    RESUME = "resume"
    PROFILE = "profile"
    JOB_DISCOVERY = "job_discovery"
    MATCHING = "matching"
    TAILORING = "tailoring"
    INTERVIEW = "interview"
    INTERNAL = "internal"


class WorkflowErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    RESUME_PARSE_FAILURE = "resume_parse_failure"
    PROFILE_EXTRACTION_FAILURE = "profile_extraction_failure"
    JOB_DISCOVERY_FAILURE = "job_discovery_failure"
    NO_JOBS_FOUND = "no_jobs_found"
    NO_MATCHES = "no_matches"
    MATCHING_FAILURE = "matching_failure"
    TAILORING_FAILURE = "tailoring_failure"
    COVER_LETTER_FAILURE = "cover_letter_failure"
    INTERVIEW_QUESTION_GENERATION_FAILURE = "interview_question_generation_failure"
    ANSWER_EVALUATION_FAILURE = "answer_evaluation_failure"
    UNEXPECTED_INTERNAL_ERROR = "unexpected_internal_error"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


_ERROR_DETAILS: dict[WorkflowErrorCode, tuple[WorkflowErrorCategory, str, IssueSeverity]] = {
    WorkflowErrorCode.INVALID_INPUT: (
        WorkflowErrorCategory.VALIDATION,
        "Workflow input was invalid.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.RESUME_PARSE_FAILURE: (
        WorkflowErrorCategory.RESUME,
        "The resume could not be parsed. Check the file type and size.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.PROFILE_EXTRACTION_FAILURE: (
        WorkflowErrorCategory.PROFILE,
        "Student profile extraction failed.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.JOB_DISCOVERY_FAILURE: (
        WorkflowErrorCategory.JOB_DISCOVERY,
        "Job discovery or normalization failed. No listings were fabricated.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.NO_JOBS_FOUND: (
        WorkflowErrorCategory.JOB_DISCOVERY,
        "No job listings matched the search criteria.",
        IssueSeverity.INFO,
    ),
    WorkflowErrorCode.MATCHING_FAILURE: (
        WorkflowErrorCategory.MATCHING,
        "Job matching failed.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.NO_MATCHES: (
        WorkflowErrorCategory.MATCHING,
        "No jobs matched the supplied profile.",
        IssueSeverity.INFO,
    ),
    WorkflowErrorCode.TAILORING_FAILURE: (
        WorkflowErrorCategory.TAILORING,
        "Resume tailoring failed for this job.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.COVER_LETTER_FAILURE: (
        WorkflowErrorCategory.TAILORING,
        "Cover letter generation failed for this job.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.INTERVIEW_QUESTION_GENERATION_FAILURE: (
        WorkflowErrorCategory.INTERVIEW,
        "Interview question generation failed.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.ANSWER_EVALUATION_FAILURE: (
        WorkflowErrorCategory.INTERVIEW,
        "Interview answer evaluation failed.",
        IssueSeverity.ERROR,
    ),
    WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR: (
        WorkflowErrorCategory.INTERNAL,
        "The workflow failed because of an unexpected internal error.",
        IssueSeverity.ERROR,
    ),
}


class WorkflowIssue(StrictModel):
    """User-safe issue; exception messages and provider payloads are never copied."""

    category: WorkflowErrorCategory
    code: WorkflowErrorCode
    message: str
    severity: IssueSeverity
    retryable: bool = False


def make_issue(
    code: WorkflowErrorCode,
    *,
    severity: IssueSeverity | None = None,
    retryable: bool = False,
) -> WorkflowIssue:
    category, message, default_severity = _ERROR_DETAILS[code]
    return WorkflowIssue(
        category=category,
        code=code,
        message=message,
        severity=severity or default_severity,
        retryable=retryable,
    )


def has_error(issues: list[WorkflowIssue]) -> bool:
    return any(issue.severity == IssueSeverity.ERROR for issue in issues)
