"""Workflow boundary inputs and typed orchestration outputs."""

from __future__ import annotations

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBytes,
    field_validator,
    model_validator,
)

from app.ai.interview_intelligence.schemas import (
    AnswerEvaluation,
    Difficulty,
    InterviewQuestion,
    InterviewType,
)
from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch, MatchConfig
from app.ai.orchestration.errors import (
    WorkflowIssue,
    WorkflowStage,
    WorkflowStatus,
)
from app.ai.resume_intelligence.profile_schemas import StudentProfile
from app.ai.resume_intelligence.schemas import ParsedResume
from app.ai.resume_tailoring.schemas import (
    CoverLetter,
    TailoredResume,
    TailoringPreferences,
)


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResumeProcessingInput(StrictSchema):
    filename: str = Field(min_length=1, max_length=255)
    content: Annotated[bytes, StrictBytes, Field(min_length=1)]

    @field_validator("filename")
    @classmethod
    def filename_is_not_blank(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("filename must not be blank")
        return clean


class JobMatchingInput(StrictSchema):
    student_profile: StudentProfile
    query: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)
    match_config: MatchConfig = Field(default_factory=MatchConfig)

    @field_validator("query")
    @classmethod
    def query_is_not_blank(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("query must not be blank")
        return clean

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None


class ResumeTailoringInput(StrictSchema):
    student_profile: StudentProfile
    selected_jobs: list[JobListing] = Field(min_length=1, max_length=20)
    job_matches: dict[str, JobMatch] = Field(default_factory=dict)
    preferences: TailoringPreferences = Field(default_factory=TailoringPreferences)

    @model_validator(mode="after")
    def selected_jobs_and_matches_are_consistent(self) -> ResumeTailoringInput:
        job_ids = [job.job_id for job in self.selected_jobs]
        if len(set(job_ids)) != len(job_ids):
            raise ValueError("selected_jobs must not contain duplicate job ids")
        selected_ids = set(job_ids)
        for key, match in self.job_matches.items():
            if key not in selected_ids or match.job_id != key:
                raise ValueError("job_matches must refer to selected jobs")
        return self


class InterviewPreparationInput(StrictSchema):
    student_profile: StudentProfile
    job_listing: JobListing
    interview_type: InterviewType = "technical"
    difficulty: Difficulty = "intermediate"
    question_count: int = Field(default=5, ge=1, le=30)
    job_match: JobMatch | None = None

    @model_validator(mode="after")
    def match_refers_to_selected_job(self) -> InterviewPreparationInput:
        if self.job_match is not None and self.job_match.job_id != self.job_listing.job_id:
            raise ValueError("job_match must refer to job_listing")
        return self


class AnswerEvaluationInput(StrictSchema):
    student_profile: StudentProfile
    job_listing: JobListing
    question: InterviewQuestion
    answer: str = Field(max_length=12_000)


class PartialSuccessSummary(StrictSchema):
    total_items: int = Field(ge=0)
    succeeded_items: int = Field(ge=0)
    partial_items: int = Field(ge=0)
    failed_items: int = Field(ge=0)

    @model_validator(mode="after")
    def counts_add_up(self) -> PartialSuccessSummary:
        if self.succeeded_items + self.partial_items + self.failed_items != self.total_items:
            raise ValueError("partial-success counts must sum to total_items")
        return self


class WorkflowOutput(StrictSchema):
    workflow_id: str = Field(min_length=1)
    status: WorkflowStatus
    completed_stages: list[WorkflowStage] = Field(default_factory=list)
    errors: list[WorkflowIssue] = Field(default_factory=list)
    partial_success: PartialSuccessSummary | None = None


class ResumeProcessingResult(WorkflowOutput):
    parsed_resume: ParsedResume | None = None
    student_profile: StudentProfile | None = None


class JobMatchingResult(WorkflowOutput):
    jobs: list[JobListing] = Field(default_factory=list)
    matches: list[JobMatch] = Field(default_factory=list)


class TailoredJobOutcome(StrictSchema):
    job_id: str = Field(min_length=1)
    job_title: str | None = None
    status: WorkflowStatus
    tailored_resume: TailoredResume | None = None
    cover_letter: CoverLetter | None = None
    errors: list[WorkflowIssue] = Field(default_factory=list)


class ResumeTailoringResult(WorkflowOutput):
    outcomes: list[TailoredJobOutcome] = Field(default_factory=list)


class InterviewPreparationResult(WorkflowOutput):
    job_id: str | None = None
    questions: list[InterviewQuestion] = Field(default_factory=list)


class AnswerEvaluationResult(WorkflowOutput):
    question_id: str | None = None
    evaluation: AnswerEvaluation | None = None


__all__ = [
    "AnswerEvaluationInput",
    "AnswerEvaluationResult",
    "InterviewPreparationInput",
    "InterviewPreparationResult",
    "JobMatchingInput",
    "JobMatchingResult",
    "PartialSuccessSummary",
    "ResumeProcessingInput",
    "ResumeProcessingResult",
    "ResumeTailoringInput",
    "ResumeTailoringResult",
    "TailoredJobOutcome",
    "WorkflowOutput",
]
