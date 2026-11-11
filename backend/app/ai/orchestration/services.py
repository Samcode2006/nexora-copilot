"""Injectable adapters to the existing AI service layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.ai.interview_intelligence.evaluation import evaluate_interview_answer
from app.ai.interview_intelligence.question_generator import generate_interview_questions
from app.ai.job_intelligence.discovery import search_jobs
from app.ai.job_intelligence.normalizer import normalize_job, normalize_jobs
from app.ai.job_intelligence.providers import JobProvider
from app.ai.job_matching.embeddings import EmbeddingProvider
from app.ai.job_matching.scoring import match_jobs
from app.ai.orchestration.checkpoint import (
    InMemoryMetadataCheckpointStore,
    default_checkpoint_store,
)
from app.ai.providers import LLMService
from app.ai.resume_intelligence.parser import parse_resume
from app.ai.resume_intelligence.profile_extractor import extract_student_profile
from app.ai.resume_tailoring.cover_letter import generate_cover_letter
from app.ai.resume_tailoring.tailoring import tailor_resume


@dataclass(frozen=True, slots=True)
class OrchestrationServices:
    """Service functions/providers used by nodes; easy to replace in offline tests."""

    parse_resume_fn: Callable[..., Any] = parse_resume
    extract_student_profile_fn: Callable[..., Any] = extract_student_profile
    search_jobs_fn: Callable[..., Any] = search_jobs
    normalize_job_fn: Callable[..., Any] = normalize_job
    normalize_jobs_fn: Callable[..., Any] = normalize_jobs
    match_jobs_fn: Callable[..., Any] = match_jobs
    tailor_resume_fn: Callable[..., Any] = tailor_resume
    generate_cover_letter_fn: Callable[..., Any] = generate_cover_letter
    generate_interview_questions_fn: Callable[..., Any] = generate_interview_questions
    evaluate_interview_answer_fn: Callable[..., Any] = evaluate_interview_answer
    llm_service: LLMService | None = None
    job_provider: JobProvider | None = None
    embedding_provider: EmbeddingProvider | None = None
    checkpoint_store: InMemoryMetadataCheckpointStore = field(
        default_factory=default_checkpoint_store
    )
