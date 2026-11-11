"""Optional Gemini implementation of the provider interface."""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .base import LLMProviderError, ProviderUnavailableError

T = TypeVar("T", bound=BaseModel)


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
        self.model = model
        key = api_key or os.getenv("GEMINI_API_KEY")
        if client is None and not key:
            raise ProviderUnavailableError("GEMINI_API_KEY is not configured.")

        if client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise ProviderUnavailableError(
                    "Gemini support is not installed. Install the 'gemini' extra."
                ) from exc
            client = genai.Client(api_key=key)
        self._client = client

    def generate_structured(self, *, prompt: str, response_model: type[T]) -> T:
        """Call Gemini and validate its JSON output as the requested model."""
        try:
            from google.genai import types

            response = self._client.models.generate_content(  # type: ignore[attr-defined]
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
            response_text = getattr(response, "text", None)
            if not response_text:
                raise LLMProviderError("Gemini returned an empty structured response.")
            return response_model.model_validate_json(response_text)
        except ValidationError as exc:
            raise LLMProviderError(
                f"Gemini response did not match {response_model.__name__}."
            ) from exc
        except LLMProviderError:
            raise
        except Exception as exc:  # SDK transport errors vary by SDK version.
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc
