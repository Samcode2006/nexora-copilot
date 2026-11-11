"""PDF and DOCX text extraction with conservative section identification."""

from __future__ import annotations

import io
import re
import unicodedata
from collections import OrderedDict

from .schemas import ParsedResume

# The shared upload contract's 5 MB limit is decimal: 5,000,000 bytes.
DEFAULT_MAX_FILE_BYTES = 5_000_000

_HEADING_ALIASES = {
    "summary": ("summary", "professional summary", "profile", "objective", "career objective"),
    "education": ("education", "academic background", "academic qualifications"),
    "skills": ("skills", "technical skills", "core skills", "technical proficiencies"),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
    ),
    "projects": ("projects", "academic projects", "personal projects"),
    "internships": ("internships", "internship experience"),
    "certifications": ("certifications", "certificates", "licenses and certifications"),
    "achievements": ("achievements", "awards", "honors", "accomplishments"),
    "publications": ("publications", "research", "papers"),
    "volunteering": ("volunteering", "volunteer experience", "community involvement"),
    "additional_information": ("additional information", "interests", "languages"),
}
_ALIAS_TO_SECTION = {
    re.sub(r"\s+", " ", alias.casefold()): section
    for section, aliases in _HEADING_ALIASES.items()
    for alias in aliases
}


class ResumeParseError(ValueError):
    """A safe, user-displayable error raised for invalid resume input."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def parse_resume(
    content: bytes,
    filename: str,
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> ParsedResume:
    """Validate a PDF/DOCX upload, extract text, and identify common sections.

    This phase deliberately extracts source text only; it does not infer student
    facts. Profile extraction and field-level evidence are a separate next phase.
    """
    if not filename or not filename.strip():
        raise ResumeParseError("A filename is required.", code="invalid_filename")
    if not content:
        raise ResumeParseError("The uploaded resume is empty.", code="empty_file")
    if len(content) > max_file_bytes:
        raise ResumeParseError(
            f"The resume exceeds the {max_file_bytes:,}-byte size limit.",
            code="file_too_large",
        )

    extension = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
    if extension not in {"pdf", "docx"}:
        raise ResumeParseError(
            "Unsupported file type. Upload a PDF or DOCX resume.", code="unsupported_type"
        )

    if extension == "pdf":
        if not content.startswith(b"%PDF-"):
            raise ResumeParseError("The PDF file is malformed.", code="malformed_document")
        extracted_text, warnings = _extract_pdf(content)
    else:
        if not content.startswith(b"PK"):
            raise ResumeParseError("The DOCX file is malformed.", code="malformed_document")
        extracted_text, warnings = _extract_docx(content)

    text = _clean_text(extracted_text)
    normalized = _normalize_text(text)
    if not normalized:
        raise ResumeParseError(
            "No readable text was found. The file may be scanned and require OCR.",
            code="no_extractable_text",
        )

    return ParsedResume(
        filename=filename,
        source_format=extension,  # type: ignore[arg-type]
        text=text,
        normalized_text=normalized,
        sections=_identify_sections(normalized),
        warnings=warnings,
    )


def _extract_pdf(content: bytes) -> tuple[str, list[str]]:
    try:
        try:
            import pymupdf
        except ImportError:
            # Compatibility with older PyMuPDF releases that exposed only fitz.
            import fitz as pymupdf
    except ImportError as exc:
        raise ResumeParseError(
            "PDF parsing dependency is missing. Install the project dependencies.",
            code="dependency_missing",
        ) from exc

    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            text = "\n\n".join(page.get_text("text") for page in document)
    except Exception as exc:
        raise ResumeParseError("The PDF file could not be read.", code="malformed_document") from exc

    return text, []


def _extract_docx(content: bytes) -> tuple[str, list[str]]:
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as exc:
        raise ResumeParseError(
            "DOCX parsing dependency is missing. Install the project dependencies.",
            code="dependency_missing",
        ) from exc

    try:
        document = Document(io.BytesIO(content))
        body = document.element.body
        chunks: list[str] = []
        for child in body.iterchildren():
            if child.tag == qn("w:p"):
                value = Paragraph(child, document).text
                if value.strip():
                    chunks.append(value)
            elif child.tag == qn("w:tbl"):
                table = Table(child, document)
                for row in table.rows:
                    values = [cell.text.strip() for cell in row.cells]
                    if any(values):
                        chunks.append(" | ".join(values))
        text = "\n\n".join(chunks)
    except Exception as exc:
        raise ResumeParseError("The DOCX file could not be read.", code="malformed_document") from exc
    return text, []


def _clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[\t\u00a0 ]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line
        if blank and previous_blank:
            continue
        cleaned.append(line)
        previous_blank = blank
    return "\n".join(cleaned).strip()


def _normalize_text(text: str) -> str:
    """Normalize spacing while retaining line breaks used to mark headings."""
    lines = [re.sub(r"[\t\u00a0 ]+", " ", line).strip() for line in text.splitlines()]
    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line
        if blank and previous_blank:
            continue
        normalized.append(line)
        previous_blank = blank
    return "\n".join(normalized).strip()


def _canonical_heading(line: str) -> str | None:
    candidate = re.sub(r"^[\s•*#\-]+|[\s:]+$", "", line).casefold()
    candidate = re.sub(r"\s+", " ", candidate)
    if len(candidate) > 55 or len(candidate.split()) > 6:
        return None
    return _ALIAS_TO_SECTION.get(candidate)


def _identify_sections(text: str) -> dict[str, str]:
    sections: OrderedDict[str, list[str]] = OrderedDict()
    active_section = "header"
    sections[active_section] = []
    lines = _normalize_text(text).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        heading = _canonical_heading(line)
        consumed_lines = 1

        # PDF extraction can wrap a multiword heading across adjacent lines.
        # Join only short, adjacent lines and only when the result exactly
        # matches a known alias, so prose is not promoted to a section heading.
        if heading is None and line.strip():
            for end in range(index + 2, min(index + 4, len(lines) + 1)):
                candidate_lines = lines[index:end]
                if any(not part.strip() or len(part.strip()) > 55 for part in candidate_lines):
                    break
                combined_heading = _canonical_heading(" ".join(candidate_lines))
                if combined_heading:
                    heading = combined_heading
                    consumed_lines = len(candidate_lines)
                    break

        if heading:
            active_section = heading
            sections.setdefault(active_section, [])
        else:
            sections[active_section].append(line)
        index += consumed_lines

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }
