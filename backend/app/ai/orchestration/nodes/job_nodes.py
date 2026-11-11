"""Job discovery, normalization, and matching nodes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from pydantic import ValidationError

from app.ai.job_intelligence.normalizer import JobNormalizationError
from app.ai.job_intelligence.providers import JobProviderError
from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.schemas import JobMatch
from app.ai.orchestration.errors import (
    WorkflowErrorCode,
    WorkflowStage,
    make_issue,
)
from app.ai.orchestration.nodes._shared import (
    begin_stage,
    complete_stage,
    failed_stage,
    terminal_stage,
)
from app.ai.orchestration.schemas import JobMatchingInput
from app.ai.orchestration.services import OrchestrationServices
from app.ai.orchestration.state import WorkflowState


def validate_job_search_input_node(
    state: WorkflowState, *, services: OrchestrationServices
) -> dict:
    stage = WorkflowStage.INPUT_VALIDATION
    begin_stage(state, services, stage)
    try:
        request = JobMatchingInput.model_validate(state["runtime_input"])
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
        updates={"search_criteria": request, "student_profile": request.student_profile},
        input_item_count=1,
    )


def discover_jobs_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.JOB_DISCOVERY
    criteria = state["search_criteria"]
    begin_stage(state, services, stage)
    try:
        jobs = services.search_jobs_fn(
            criteria.query,
            criteria.location,
            criteria.limit,
            provider=services.job_provider,
        )
        if isinstance(jobs, (str, bytes)) or not isinstance(jobs, list):
            raise TypeError("Job service returned an invalid collection.")
        normalized = [JobListing.model_validate(job) for job in jobs]
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.JOB_DISCOVERY_FAILURE,
            expected_exceptions=(JobProviderError, ValidationError, TypeError, ValueError),
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"discovered_jobs": normalized},
        output_item_count=len(normalized),
    )


def normalize_discovered_jobs_node(
    state: WorkflowState, *, services: OrchestrationServices
) -> dict:
    stage = WorkflowStage.JOB_NORMALIZATION
    discovered = state["discovered_jobs"]
    begin_stage(state, services, stage, input_item_count=len(discovered))
    if not discovered:
        issue = make_issue(WorkflowErrorCode.NO_JOBS_FOUND)
        return complete_stage(
            state,
            services,
            stage,
            updates={
                "normalized_jobs": [],
                "errors": [*state["errors"], issue],
            },
            input_item_count=0,
            output_item_count=0,
        )

    try:
        verified = [
            services.normalize_job_fn(
                job.model_dump(mode="python"),
                job.source_provider,
                is_mock=job.is_mock,
            )
            for job in discovered
        ]
        grouped: dict[str, list[JobListing]] = defaultdict(list)
        for job in verified:
            candidate = JobListing.model_validate(job)
            grouped[candidate.source_provider].append(candidate)

        normalized: list[JobListing] = []
        for provider_name, provider_jobs in grouped.items():
            raw_records: list[Mapping] = [job.model_dump(mode="python") for job in provider_jobs]
            normalized.extend(
                JobListing.model_validate(job)
                for job in services.normalize_jobs_fn(
                    raw_records,
                    provider_name,
                    is_mock=any(job.is_mock for job in provider_jobs),
                )
            )

        unique: dict[str, JobListing] = {}
        for job in normalized:
            unique.setdefault(job.job_id, job)
        normalized = list(unique.values())
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.JOB_DISCOVERY_FAILURE,
            expected_exceptions=(
                JobNormalizationError,
                JobProviderError,
                ValidationError,
                TypeError,
                ValueError,
            ),
            input_item_count=len(discovered),
        )
    return complete_stage(
        state,
        services,
        stage,
        updates={"normalized_jobs": normalized},
        input_item_count=len(discovered),
        output_item_count=len(normalized),
    )


def match_discovered_jobs_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    stage = WorkflowStage.JOB_MATCHING
    jobs = state["normalized_jobs"]
    begin_stage(state, services, stage, input_item_count=len(jobs))
    try:
        criteria = state["search_criteria"]
        matches = services.match_jobs_fn(
            state["student_profile"],
            jobs,
            config=criteria.match_config,
            embedding_provider=services.embedding_provider,
        )
        if isinstance(matches, (str, bytes)) or not isinstance(matches, list):
            raise TypeError("Matching service returned an invalid collection.")
        ranked = [JobMatch.model_validate(match) for match in matches]
    except Exception as exc:  # noqa: BLE001 - convert unexpected service errors to safe workflow failures.
        return failed_stage(
            state,
            services,
            stage,
            exc,
            expected_code=WorkflowErrorCode.MATCHING_FAILURE,
            expected_exceptions=(ValidationError, TypeError, ValueError),
            input_item_count=len(jobs),
        )
    issues = list(state["errors"])
    if not ranked:
        issues.append(make_issue(WorkflowErrorCode.NO_MATCHES))
    return complete_stage(
        state,
        services,
        stage,
        updates={"ranked_matches": ranked, "errors": issues},
        input_item_count=len(jobs),
        output_item_count=len(ranked),
    )


def finish_job_matching_node(state: WorkflowState, *, services: OrchestrationServices) -> dict:
    return terminal_stage(
        state,
        services,
        output_item_count=len(state["ranked_matches"]),
    )
