"""Provider selection and explicit, task-supplied deterministic fallbacks."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .base import LLMProvider, LLMProviderError, LLMResult, _provider_error
from .gemini import GeminiProvider

T = TypeVar("T", bound=BaseModel)
_LOGGER = logging.getLogger(__name__)
_SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_FAILURE_DESCRIPTIONS = {
    "authentication": "authentication failed",
    "configuration": "is unavailable due to configuration",
    "connection": "connection failed",
    "initialization": "initialization failed",
    "invalid_response": "returned invalid structured output",
    "provider": "request failed",
    "rate_limit": "rate limit was reached",
    "server": "returned a server error",
    "timeout": "request timed out",
}


class LLMService:
    """Routes structured generation and labels fallback outputs explicitly.

    Each AI feature supplies its own deterministic fallback function. This keeps
    fallback behavior grounded in that feature's inputs instead of returning
    generic or fabricated model data.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider
        self._initialization_failure_reason: str | None = None

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
                fallback_reason=(
                    self._initialization_failure_reason
                    or "No LLM provider is configured."
                ),
            )

        last_error: LLMProviderError | None = None
        provider_name = _provider_name(self.provider)
        attempt_limit = min(max(1, max_attempts), 3)
        for attempt in range(attempt_limit):
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
                diagnostic_type = getattr(exc, "diagnostic_exception_type", None)
                _log_provider_failure(
                    provider_name,
                    exc.category,
                    attempt + 1,
                    attempt_limit,
                    diagnostic_type if isinstance(diagnostic_type, str) else type(exc).__name__,
                )
                if not exc.retryable:
                    break
            except ValidationError as exc:
                last_error = _provider_error(
                    "Provider response did not match the requested schema.",
                    category="invalid_response",
                    retryable=True,
                )
                _log_provider_failure(
                    provider_name,
                    last_error.category,
                    attempt + 1,
                    attempt_limit,
                    type(exc).__name__,
                )
            # Provider implementations may leak SDK-specific exceptions. Do
            # not expose their raw details; return the feature fallback.
            except (TypeError, AttributeError, NameError, AssertionError):
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = _provider_error(
                    "Provider request failed.",
                    category="provider",
                    retryable=False,
                )
                _log_provider_failure(
                    provider_name,
                    last_error.category,
                    attempt + 1,
                    attempt_limit,
                    type(exc).__name__,
                )
                break
            else:
                return LLMResult(
                    value=value,
                    provider=provider_name,
                    is_fallback=False,
                    model=getattr(self.provider, "model", None),
                )

        return LLMResult(
            value=response_model.model_validate(fallback()),
            provider="deterministic_fallback",
            is_fallback=True,
            fallback_reason=(
                _safe_failure_reason(provider_name, last_error)
                if last_error is not None
                else "Provider response validation failed."
            ),
        )


def create_llm_service() -> LLMService:
    """Use Gemini when credentials exist; otherwise use feature fallbacks."""
    if not os.getenv("GEMINI_API_KEY"):
        return LLMService()
    try:
        return LLMService(provider=GeminiProvider())
    except LLMProviderError as exc:
        return _initialization_fallback(
            exception_type=(
                exc.diagnostic_exception_type or type(exc).__name__
            ),
            category=exc.category,
        )
    # Keep unexpected SDK/client initialization errors within the provider
    # setup boundary and retain only a safe exception-type diagnostic.
    except Exception as exc:  # noqa: BLE001
        return _initialization_fallback(
            exception_type=type(exc).__name__,
            category="initialization",
        )


def _initialization_fallback(*, exception_type: str, category: str) -> LLMService:
    safe_type = exception_type if _SAFE_LABEL_RE.fullmatch(exception_type) else "ProviderError"
    _LOGGER.warning(
        "Gemini provider initialization failed category=%s exception_type=%s; deterministic fallback selected.",
        category,
        safe_type,
    )
    service = LLMService()
    if category == "configuration":
        service._initialization_failure_reason = (
            "Gemini is unavailable because its configuration or optional SDK is missing; "
            "deterministic fallback is active."
        )
    else:
        service._initialization_failure_reason = (
            f"Gemini initialization failed ({safe_type}); deterministic fallback is active."
        )
    return service


def _provider_name(provider: LLMProvider) -> str:
    candidate = getattr(provider, "name", None)
    if isinstance(candidate, str) and _SAFE_LABEL_RE.fullmatch(candidate):
        return candidate
    return type(provider).__name__


def _log_provider_failure(
    provider_name: str,
    category: str,
    attempt: int,
    max_attempts: int,
    exception_type: str,
) -> None:
    safe_category = category if category in _FAILURE_DESCRIPTIONS else "provider"
    safe_exception_type = (
        exception_type
        if isinstance(exception_type, str) and _SAFE_LABEL_RE.fullmatch(exception_type)
        else "ProviderError"
    )
    safe_provider_name = "Gemini" if provider_name.casefold() == "gemini" else provider_name
    _LOGGER.warning(
        "LLM provider attempt failed provider=%s category=%s attempt=%s/%s exception_type=%s",
        safe_provider_name,
        safe_category,
        attempt,
        max_attempts,
        safe_exception_type,
    )


def _safe_failure_reason(
    provider_name: str,
    error: LLMProviderError,
) -> str:
    category = error.category if error.category in _FAILURE_DESCRIPTIONS else "provider"
    description = _FAILURE_DESCRIPTIONS[category]
    if provider_name.casefold() == "gemini":
        if category == "timeout":
            return "Gemini request timed out."
        if category == "connection":
            return "Gemini request failed: connection error."
        if category == "rate_limit":
            return "Gemini rate limit was reached."
        if category == "server":
            return "Gemini returned a server error."
        if category == "authentication":
            return "Gemini authentication failed."
        if category == "invalid_response":
            return "Gemini returned invalid structured output."
        if category == "initialization":
            return "Gemini provider initialization failed."
        if category == "configuration":
            return "Gemini is unavailable due to configuration."
        return "Gemini request failed: provider error."
    return f"The {provider_name} provider {description}."
