"""Reuse the shared LLM service and provide safe feature-owned fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers import LLMService, create_llm_service

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class DraftGeneration:
    value: BaseModel
    provider: str
    is_fallback: bool
    warnings: tuple[str, ...] = ()


def generate_draft(
    *,
    prompt: str,
    response_model: type[T],
    fallback: T,
    llm_service: LLMService | None,
) -> DraftGeneration:
    service = llm_service if llm_service is not None else create_llm_service()
    try:
        result = service.generate_structured(
            prompt=prompt,
            response_model=response_model,
            fallback=lambda: fallback,
            max_attempts=2,
        )
    # A custom provider adapter may raise SDK-specific exceptions. Keep the
    # fallback boundary broad, but return only sanitized exception metadata.
    except Exception as exc:  # noqa: BLE001
        # An unexpected adapter exception must not leak generated output or be
        # mislabeled as an LLM result. Re-run the feature-owned empty plan.
        result = LLMService().generate_structured(
            prompt="",
            response_model=response_model,
            fallback=lambda: fallback,
        )
        return DraftGeneration(
            value=result.value,
            provider="deterministic_fallback",
            is_fallback=True,
            warnings=(
                f"The configured LLM service failed ({type(exc).__name__}); deterministic tailoring was used.",
            ),
        )

    warnings: list[str] = []
    if result.is_fallback:
        reason = result.fallback_reason or "No LLM provider is configured."
        warnings.append(f"The LLM was unavailable or invalid; deterministic tailoring was used. {reason}")
    return DraftGeneration(
        value=result.value,
        provider=result.provider,
        is_fallback=result.is_fallback,
        warnings=tuple(warnings),
    )
