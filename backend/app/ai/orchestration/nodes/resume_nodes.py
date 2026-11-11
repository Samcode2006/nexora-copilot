"""Resume-processing nodes."""

from __future__ import annotations

from pydantic import ValidationError

from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStage,
)
from app.ai.orchestration.nodes._shared import (
    begin_stage,
    complete_stage,
    failed_stage,
    terminal_stage,
)
from app.ai.orchestration.schemas import ResumeProcessingInput
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState
from app.ai.resume_intelligence.parser import ResumeParseError
from app.ai.resume_intelligence.profile_schemas import StudentProfile
from app.ai.resume_intelligence.schemas import ParsedResume


def validate_resume_input_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.INPUT_VALIDATION
    begin_stage(state, services, stage)
    try:
        request = ResumeProcessingInput.model_validate(state["runtime_input"])
    except (ValidationError, TypeError, ValueError) as exc:
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
            "runtime_input": {"filename": request.filename},
            "raw_resume_bytes": request.content,
        },
        input_item_count=1,
    )


def parse_resume_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.RESUME_PARSING
    begin_stage(state, services, stage, input_item_count=1)
    try:
        runtime_input = state["runtime_input"]
        content = state["raw_resume_bytes"]
        if not isinstance(runtime_input, dict) or not content:
            raise ValueError("Resume input is unavailable.")
        parsed = services.parse_resume_fn(content, runtime_input["filename"])
        parsed = ParsedResume.model_validate(parsed)
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.RESUME_PARSE_FAILURE,
            expected_exceptions=(ResumeParseError, ValueError, TypeError, ValidationError),
            input_item_count=1,
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"parsed_resume": parsed, "raw_resume_bytes": None},
        input_item_count=1,
        output_item_count=1,
    )


def extract_profile_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.PROFILE_EXTRACTION
    begin_stage(state, services, stage, input_item_count=1)
    try:
        parsed = state["parsed_resume"]
        if parsed is None:
            raise ValueError("Parsed resume is unavailable.")
        profile = services.extract_student_profile_fn(
            parsed.text,
            llm_service=services.llm_service,
        )
        profile = StudentProfile.model_validate(profile)
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.PROFILE_EXTRACTION_FAILURE,
            expected_exceptions=(ValidationError, TypeError, ValueError),
            input_item_count=1,
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"student_profile": profile},
        input_item_count=1,
        output_item_count=1,
    )


def validate_resume_result_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.RESULT_VALIDATION
    begin_stage(state, services, stage, input_item_count=1)
    try:
        parsed = ParsedResume.model_validate(state["parsed_resume"])
        profile = StudentProfile.model_validate(state["student_profile"])
    except (ValidationError, TypeError, ValueError) as exc:
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.PROFILE_EXTRACTION_FAILURE,
            expected_exceptions=(ValidationError, TypeError, ValueError),
            input_item_count=1,
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"parsed_resume": parsed, "student_profile": profile},
        input_item_count=1,
        output_item_count=1,
    )


def finish_resume_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    return terminal_stage(
        state,
        services,
        output_item_count=1 if state["student_profile"] is not None else 0,
    )
