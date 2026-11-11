"""Provider-neutral types for structured LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(RuntimeError):
    """Base error for provider setup, transport, and response failures."""


class ProviderUnavailableError(LLMProviderError):
    """Raised when a provider cannot be used in the current environment."""


class LLMProvider(Protocol):
    """A provider that returns validated, structured Pydantic output."""

    name: str

    def generate_structured(self, *, prompt: str, response_model: type[T]) -> T:
        """Generate a response and validate it against ``response_model``."""


@dataclass(frozen=True)
class LLMResult(Generic[T]):
    """Output plus provenance so callers can disclose deterministic fallbacks."""

    value: T
    provider: str
    is_fallback: bool
    model: str | None = None
    fallback_reason: str | None = None
