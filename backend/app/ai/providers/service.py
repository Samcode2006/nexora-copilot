"""Provider selection and explicit, task-supplied deterministic fallbacks."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .base import LLMProvider, LLMProviderError, LLMResult
from .gemini import GeminiProvider

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Routes structured generation and labels fallback outputs explicitly.

    Each AI feature supplies its own deterministic fallback function. This keeps
    fallback behavior grounded in that feature's inputs instead of returning
    generic or fabricated model data.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    def generate_structured(
        self,
        *,
        prompt: str,
        response_model: type[T],
        fallback: Callable[[], T],
        max_attempts: int = 1,
    ) -> LLMResult[T]:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.provider is None:
            return LLMResult(
                value=response_model.model_validate(fallback()),
                provider="deterministic_fallback",
                is_fallback=True,
                fallback_reason="No LLM provider is configured.",
            )

        last_error: LLMProviderError | None = None
        for attempt in range(max_attempts):
            attempt_prompt = prompt
            if attempt:
                attempt_prompt += (
                    "\nYour previous response failed validation. Return a fresh response "
                    "that strictly matches the requested schema and contains valid JSON."
                )
            try:
                raw_value = self.provider.generate_structured(
                    prompt=attempt_prompt,
                    response_model=response_model,
                )
                value = response_model.model_validate(raw_value)
            except LLMProviderError as exc:
                last_error = exc
            except ValidationError as exc:
                last_error = LLMProviderError(
                    f"Provider response did not match {response_model.__name__}."
                )
                last_error.__cause__ = exc
            else:
                return LLMResult(
                    value=value,
                    provider=self.provider.name,
                    is_fallback=False,
                    model=getattr(self.provider, "model", None),
                )

        return LLMResult(
            value=response_model.model_validate(fallback()),
            provider="deterministic_fallback",
            is_fallback=True,
            fallback_reason=str(last_error or "Provider response validation failed."),
        )


def create_llm_service() -> LLMService:
    """Use Gemini when credentials exist; otherwise use feature fallbacks."""
    if not os.getenv("GEMINI_API_KEY"):
        return LLMService()
    try:
        return LLMService(provider=GeminiProvider())
    except LLMProviderError:
        return LLMService()
