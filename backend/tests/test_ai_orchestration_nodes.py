from __future__ import annotations

from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStatus,
    WorkflowType,
)
from app.ai.orchestration.nodes.resume_nodes import (
    extract_profile_node,
    parse_resume_node,
    validate_resume_input_node,
)
from app.ai.orchestration.schemas import ResumeProcessingInput
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.workflows._runtime import initial_state
from app.ai.resume_intelligence.parser import ResumeParseError
from app.ai.resume_intelligence.schemas import ParsedResume
from tests.ai_orchestration_helpers import fresh_store, offline_services


def _resume_state(services: OrchestrationServices):
    request = ResumeProcessingInput(filename="resume.docx", content=b"ephemeral-resume-bytes")
    state = initial_state(WorkflowType.RESUME_PROCESSING, request, services)
    state.update(validate_resume_input_node(state, services=services))
    return state


def test_resume_parse_node_success_clears_raw_bytes() -> None:
    services = offline_services(
        parse_resume_fn=lambda content, filename: ParsedResume(
            filename=filename,
            source_format="docx",
            text="Name: Asha Rao",
            normalized_text="Name: Asha Rao",
            sections={},
        )
    )
    state = _resume_state(services)

    changes = parse_resume_node(state, services=services)
    state.update(changes)

    assert state["parsed_resume"].text == "Name: Asha Rao"
    assert state["raw_resume_bytes"] is None
    record = services.checkpoint_store.get(state["workflow_id"])
    assert record is not None
    assert "ephemeral-resume-bytes" not in record.model_dump_json()


def test_resume_parse_node_routes_parse_failure_safely() -> None:
    def reject_resume(_content: bytes, _filename: str):
        raise ResumeParseError("private details must not leak", code="malformed_document")

    services = offline_services(parse_resume_fn=reject_resume)
    state = _resume_state(services)

    changes = parse_resume_node(state, services=services)

    assert changes["status"] == WorkflowStatus.FAILED
    assert changes["errors"][-1].code == WorkflowErrorCode.RESUME_PARSE_FAILURE
    assert "private details" not in changes["errors"][-1].message


def test_profile_extraction_node_returns_validated_profile() -> None:
    services = offline_services(
        parse_resume_fn=lambda _content, filename: ParsedResume(
            filename=filename,
            source_format="docx",
            text="Name: Asha Rao\nSkills: Python",
            normalized_text="Name: Asha Rao Skills: Python",
            sections={},
        )
    )
    state = _resume_state(services)
    state.update(parse_resume_node(state, services=services))

    changes = extract_profile_node(state, services=services)

    assert changes["student_profile"].personal_information.name.value == "Asha Rao"


def test_profile_extraction_node_returns_structured_failure() -> None:
    def fail_extraction(*_args, **_kwargs):
        raise ValueError("sensitive provider response")

    services = offline_services(extract_student_profile_fn=fail_extraction)
    state = _resume_state(services)
    state["parsed_resume"] = ParsedResume(
        filename="resume.docx",
        source_format="docx",
        text="Name: Asha Rao",
        normalized_text="Name: Asha Rao",
        sections={},
    )

    changes = extract_profile_node(state, services=services)

    assert changes["status"] == WorkflowStatus.FAILED
    assert changes["errors"][-1].code == WorkflowErrorCode.PROFILE_EXTRACTION_FAILURE
    assert "sensitive provider response" not in changes["errors"][-1].message


def test_node_checkpoints_contain_metadata_only() -> None:
    store = fresh_store()
    services = offline_services(store=store)
    state = _resume_state(services)
    parse_resume_node(state, services=services)
    record = store.get(state["workflow_id"])

    assert record is not None
    assert record.workflow_type == WorkflowType.RESUME_PROCESSING
    assert record.current_stage.value == "resume_parsing"
    assert record.input_item_count == 1
    assert record.output_item_count is None
    assert "ephemeral-resume-bytes" not in record.model_dump_json()
