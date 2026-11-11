"""Evidence-backed semantic and deterministic job matching."""

from .embeddings import (
    EmbeddingProvider,
    EmbeddingProviderError,
    SentenceTransformerEmbeddingProvider,
    create_embedding_provider_from_env,
)
from .schemas import (
    EligibilityAssessment,
    JobMatch,
    MatchConfig,
    MatchDimension,
    MatchWeights,
)
from .scoring import match_jobs

__all__ = [
    "EligibilityAssessment",
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "JobMatch",
    "MatchConfig",
    "MatchDimension",
    "MatchWeights",
    "SentenceTransformerEmbeddingProvider",
    "create_embedding_provider_from_env",
    "match_jobs",
]
