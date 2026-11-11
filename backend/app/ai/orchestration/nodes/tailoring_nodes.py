"""Independent multi-job resume and cover-letter generation nodes."""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStage,
    WorkflowStatus,
    make_issue,
)
from app.ai.orchestration.nodes._shared import begin_stage, complete_stage, terminal_stage
from app.ai.orchestration.schemas import (
    PartialSuccessSummary,
    ResumeTailoringInput,
    TailoredJobOutcome,
)
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState
from app.ai.resume_tailoring.schemas import CoverLetter, TailoredResume


def validate_tailoring_input_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.INPUT_VALIDATION
    begin_stage(state, services, stage)
    try:
        request = ResumeTailoringInput.model_validate(state["runtime_input"])
    except (ValidationError, TypeError, ValueError) as exc:
        from app.ai.orchestration.nodes._shared import failed_stage

        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.INVALID_INPUT,
            expected_exceptions=(ValidationError, TypeError, ValueError),
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={
            "student_profile": request.student_profile,
            "selected_jobs": request.selected_jobs,
            "job_matches": request.job_matches,
            "tailoring_preferences": request.preferences,
        },
        input_item_count=len(request.selected_jobs),
    )


def tailor_selected_jobs_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.RESUME_TAILORING
    jobs = state["selected_jobs"]
    begin_stage(state, services, stage, input_item_count=len(jobs))
    outcomes: list[TailoredJobOutcome] = []
    issues = list(state["errors"])
    for job in jobs:
        try:
            tailored = services.tailor_resume_fn(
                state["student_profile"],
                job,
                state["job_matches"].get(job.job_id),
                state["tailoring_preferences"],
                llm_service=services.llm_service,
            )
            tailored = TailoredResume.model_validate(tailored)
            if tailored.job_id != job.job_id:
                raise ValueError("Tailoring result refers to another job.")
            outcomes.append(
                TailoredJobOutcome(
                    job_id=job.job_id,
                    job_title=job.title,
                    status=WorkflowStatus.PARTIAL,
                    tailored_resume=tailored,
                )
            )
        except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
            issue = make_issue(
                WorkflowErrorCode.TAILORING_FAILURE
                if isinstance(exc, (ValueError, TypeError, ValidationError))
                else WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR
            )
            issues.append(issue)
            outcomes.append(
                TailoredJobOutcome(
                    job_id=job.job_id,
                    job_title=job.title,
                    status=WorkflowStatus.FAILED,
                    errors=[issue],
                )
            )
    return complete_stage(
        state,
        services,
        stage,
        updates={"tailoring_outcomes": outcomes, "errors": issues},
        input_item_count=len(jobs),
        output_item_count=len(outcomes),
    )


def generate_cover_letters_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.COVER_LETTER_GENERATION
    jobs_by_id = {job.job_id: job for job in state["selected_jobs"]}
    outcomes: list[TailoredJobOutcome] = []
    issues = list(state["errors"])
    attempted = 0
    begin_stage(state, services, stage, input_item_count=len(state["tailoring_outcomes"]))
    for outcome in state["tailoring_outcomes"]:
        if outcome.tailored_resume is None:
            outcomes.append(outcome)
            continue
        attempted += 1
        try:
            job = jobs_by_id[outcome.job_id]
            letter = services.generate_cover_letter_fn(
                state["student_profile"],
                job,
                outcome.tailored_resume,
                state["tailoring_preferences"],
                llm_service=services.llm_service,
            )
            letter = CoverLetter.model_validate(letter)
            if letter.job_id != outcome.job_id:
                raise ValueError("Cover letter result refers to another job.")
            outcomes.append(
                outcome.model_copy(
                    update={"cover_letter": letter, "status": WorkflowStatus.SUCCEEDED}
                )
            )
        except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
            issue = make_issue(
                WorkflowErrorCode.COVER_LETTER_FAILURE
                if isinstance(exc, (ValueError, TypeError, ValidationError))
                else WorkflowErrorCode.UNEXPECTED_INTERNAL_ERROR
            )
            issues.append(issue)
            outcomes.append(
                outcome.model_copy(
                    update={
                        "status": WorkflowStatus.PARTIAL,
                        "errors": [*outcome.errors, issue],
                    }
                )
            )
    return complete_stage(
        state,
        services,
        stage,
        updates={"tailoring_outcomes": outcomes, "errors": issues},
        input_item_count=attempted,
        output_item_count=sum(outcome.cover_letter is not None for outcome in outcomes),
    )


def finish_tailoring_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    outcomes = state["tailoring_outcomes"]
    succeeded = sum(
        outcome.tailored_resume is not None and outcome.cover_letter is not None
        for outcome in outcomes
    )
    partial = sum(
        (outcome.tailored_resume is not None or outcome.cover_letter is not None)
        and outcome.status != WorkflowStatus.SUCCEEDED
        for outcome in outcomes
    )
    failed = len(outcomes) - succeeded - partial
    summary = PartialSuccessSummary(
        total_items=len(outcomes),
        succeeded_items=succeeded,
        partial_items=partial,
        failed_items=failed,
    )
    if succeeded == len(outcomes):
        status = WorkflowStatus.SUCCEEDED
    elif succeeded + partial > 0:
        status = WorkflowStatus.PARTIAL
    else:
        status = WorkflowStatus.FAILED
    changes = terminal_stage(
        state,
        services,
        status=status,
        output_item_count=succeeded + partial,
    )
    changes["partial_success"] = summary
    return changes
