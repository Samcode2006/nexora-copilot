"""Optional Gemini implementation of the provider interface."""

from __future__ import annotations

import os
import re
import socket
from typing import TypeVar
from urllib.error import URLError

from pydantic import BaseModel, ValidationError

from .base import (
    LLMProviderError,
    _provider_error,
    _unavailable_error,
)

T = TypeVar("T", bound=BaseModel)
DEFAULT_GEMINI_TIMEOUT_MS = 60_000


class GeminiProvider:
    """Gemini structured-output provider, loaded only when configured."""

    name = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        client: object | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise _unavailable_error("Gemini model configuration is invalid.")
        self.model = model.strip()
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        if client is None and (not isinstance(key, str) or not key.strip()):
            raise _unavailable_error("GEMINI_API_KEY is not configured.")

        if client is None:
            try:
                from google import genai
                from google.genai import types
            except ImportError:
                raise _unavailable_error(
                    "Gemini support is not installed. Install the 'gemini' extra."
                ) from None
            try:
                client = genai.Client(
                    api_key=key,
                    http_options=types.HttpOptions(timeout=DEFAULT_GEMINI_TIMEOUT_MS),
                )
            # SDK construction failures vary by installed google-genai version.
            # Keep their raw text out of public errors and result metadata.
            except Exception as exc:  # noqa: BLE001
                raise _unavailable_error(
                    "Gemini client initialization failed.",
                    category="initialization",
                    diagnostic_exception_type=type(exc).__name__,
                ) from None
        self._client = client

    def generate_structured(self, *, prompt: str, response_model: type[T]) -> T:
        """Call Gemini and validate its JSON output as the requested model."""
        try:
            response = self._client.models.generate_content(  # type: ignore[attr-defined]
                model=self.model,
                contents=prompt,
                # Keep injected clients independent of the optional Gemini SDK.
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_model,
                },
            )
            response_text = getattr(response, "text", None)
            if not isinstance(response_text, (str, bytes)) or not response_text.strip():
                raise _provider_error(
                    "Gemini returned an empty structured response.",
                    category="invalid_response",
                    retryable=True,
                )
            try:
                return response_model.model_validate_json(response_text)
            except (ValidationError, ValueError, TypeError):
                raise _provider_error(
                    "Gemini response did not match the requested structured schema.",
                    category="invalid_response",
                    retryable=True,
                ) from None
        except LLMProviderError:
            raise
        # SDK transport exception types vary by version; classify and sanitize
        # the failure at this provider boundary.
        except (TypeError, AttributeError, NameError, AssertionError):
            raise
        except Exception as exc:  # noqa: BLE001
            category, retryable, message = _classify_provider_exception(exc)
            raise _provider_error(
                message,
                category=category,
                retryable=retryable,
            ) from None


def _classify_provider_exception(exc: Exception) -> tuple[str, bool, str]:
    status_code = _status_code(exc)
    if status_code in {401, 403}:
        return "authentication", False, "Gemini authentication failed."
    if status_code == 429:
        return "rate_limit", True, "Gemini rate limit was reached."
    if status_code in {408, 504}:
        return "timeout", True, "Gemini request timed out."
    if status_code is not None and 500 <= status_code <= 599:
        return "server", True, "Gemini returned a server error."
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout", True, "Gemini request timed out."
    if isinstance(exc, (ConnectionError, OSError, URLError)):
        return "connection", True, "Gemini request failed: connection error."
    return "provider", False, "Gemini request failed: provider error."


def _status_code(exc: Exception) -> int | None:
    for attribute in ("status_code", "code", "status"):
        try:
            value = getattr(exc, attribute, None)
        # Some SDKs expose status through properties; a broken diagnostic
        # property should not replace the original, sanitized provider error.
        except Exception:  # noqa: BLE001, S112
            continue
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and re.fullmatch(r"\s*\d{3}\s*", value):
            return int(value.strip())
    return None
