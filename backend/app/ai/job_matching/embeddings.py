"""Replaceable semantic similarity providers for job matching."""

from __future__ import annotations

import math
import os
import threading
from collections.abc import Sequence
from typing import Protocol

DEFAULT_SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingProviderError(RuntimeError):
    """Raised when semantic embeddings cannot be generated or validated."""

    diagnostic_exception_type: str | None = None


def _embedding_error(
    message: str,
    *,
    diagnostic_exception_type: str | None = None,
) -> EmbeddingProviderError:
    error = EmbeddingProviderError(message)
    error.diagnostic_exception_type = diagnostic_exception_type
    return error


class EmbeddingProvider(Protocol):
    name: str

    def similarities(self, pairs: Sequence[tuple[str, str]]) -> Sequence[float]:
        """Return cosine similarities, one per input pair, in the range [-1, 1]."""


class SentenceTransformerEmbeddingProvider:
    """Lazy Sentence Transformers cosine-similarity implementation."""

    name = "sentence_transformers"

    def __init__(self, model_name: str = DEFAULT_SENTENCE_TRANSFORMER_MODEL) -> None:
        if not model_name.strip():
            raise ValueError("model_name must be non-empty")
        self.model_name = model_name.strip()
        self._model = None
        self._model_lock = threading.Lock()

    def similarities(self, pairs: Sequence[tuple[str, str]]) -> Sequence[float]:
        if not pairs:
            return []
        try:
            model = self._get_model()
            texts = [text for pair in pairs for text in pair]
            embeddings = model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            scores: list[float] = []
            for index in range(len(pairs)):
                left = embeddings[index * 2]
                right = embeddings[index * 2 + 1]
                score = sum(float(a) * float(b) for a, b in zip(left, right, strict=True))
                if not math.isfinite(score) or not -1.00001 <= score <= 1.00001:
                    raise EmbeddingProviderError("Embedding model returned an invalid cosine score.")
                scores.append(max(-1.0, min(1.0, score)))
            return scores
        except EmbeddingProviderError:
            raise
        # Sentence Transformers can surface version-specific backend errors;
        # convert those to a safe provider error for keyword fallback.
        except Exception as exc:  # noqa: BLE001
            raise _embedding_error(
                "Sentence Transformers could not produce embeddings.",
                diagnostic_exception_type=type(exc).__name__,
        ) from None

    def _get_model(self):
        with self._model_lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError:
                    raise _embedding_error(
                        "sentence-transformers is not installed. Install the matching extra.",
                        diagnostic_exception_type="ImportError",
                    ) from None
                try:
                    self._model = SentenceTransformer(self.model_name)
                # Model initialization errors vary across Torch/Transformers
                # versions and must be sanitized at this optional boundary.
                except Exception as exc:  # noqa: BLE001
                    raise _embedding_error(
                        "Sentence Transformers could not load the configured model.",
                        diagnostic_exception_type=type(exc).__name__,
        ) from None
            return self._model


_PROVIDER_CACHE: dict[str, SentenceTransformerEmbeddingProvider] = {}
_PROVIDER_LOCK = threading.Lock()


def create_embedding_provider_from_env() -> EmbeddingProvider | None:
    """Select embeddings from environment; auto mode falls back if unavailable."""
    mode = os.getenv("JOB_MATCH_EMBEDDINGS", "auto").strip().casefold()
    if mode in {"keyword", "off", "disabled"}:
        return None
    if mode not in {"auto", "sentence-transformers", "sentence_transformers"}:
        raise EmbeddingProviderError(
            "Unsupported JOB_MATCH_EMBEDDINGS; choose 'auto', 'sentence-transformers', or 'keyword'."
        )

    model_name = os.getenv("JOB_MATCH_MODEL", DEFAULT_SENTENCE_TRANSFORMER_MODEL).strip()
    if not model_name:
        raise EmbeddingProviderError("JOB_MATCH_MODEL must be non-empty.")
    with _PROVIDER_LOCK:
        provider = _PROVIDER_CACHE.get(model_name)
        if provider is None:
            provider = SentenceTransformerEmbeddingProvider(model_name)
            _PROVIDER_CACHE[model_name] = provider
        return provider
