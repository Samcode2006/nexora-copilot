"""Ephemeral, orchestration-only LangGraph state."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from app.ai.interview_intelligence.schemas import AnswerEvaluation, InterviewQuestion
from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.orchestration.errors import (
    WorkflowIssue,
    WorkflowStage,
    WorkflowStatus,
    WorkflowType,
)
from app.ai.orchestration.schemas import (
    PartialSuccessSummary,
    TailoredJobOutcome,
)
from app.ai.resume_intelligence.profile_schemas import StudentProfile
from app.ai.resume_intelligence.schemas import ParsedResume
from app.ai.resume_tailoring.schemas import TailoringPreferences


class WorkflowState(TypedDict):
    """Runtime-only data. Never pass this state to a LangGraph checkpointer."""

    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    current_stage: WorkflowStage
    started_at: datetime
    completed_at: datetime | None
    runtime_input: Any
    raw_resume_bytes: bytes | None
    parsed_resume: ParsedResume | None
    student_profile: StudentProfile | None
    search_criteria: Any
    discovered_jobs: list[JobListing]
    normalized_jobs: list[JobListing]
    ranked_matches: list[JobMatch]
    selected_job: JobListing | None
    selected_jobs: list[JobListing]
    job_matches: dict[str, JobMatch]
    tailoring_preferences: TailoringPreferences | None
    tailoring_outcomes: list[TailoredJobOutcome]
    interview_questions: list[InterviewQuestion]
    answer_evaluation: AnswerEvaluation | None
    errors: list[WorkflowIssue]
    completed_stages: list[WorkflowStage]
    partial_success: PartialSuccessSummary | None
