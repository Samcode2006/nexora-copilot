"""Typed results for deterministic resume document parsing."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParsedResume(BaseModel):
    """Extracted source text and section boundaries, without inferred facts."""

    model_config = ConfigDict(extra="forbid")

    filename: str
    source_format: Literal["pdf", "docx"]
    text: str = Field(description="Extracted text in document order where available.")
    normalized_text: str = Field(description="Whitespace-normalized extracted text.")
    sections: dict[str, str] = Field(
        description="Recognized section headings mapped to their original text."
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Parsing limitations that a caller should surface or review.",
    )
