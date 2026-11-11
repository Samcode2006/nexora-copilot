import io
from importlib import import_module

import pytest

from app.ai.resume_intelligence import ResumeParseError, parse_resume
from app.ai.resume_intelligence import parser as resume_parser
from app.ai.resume_intelligence.parser import (
    DEFAULT_MAX_FILE_BYTES,
    _identify_sections,
)


def _load_pymupdf():
    try:
        return import_module("pymupdf")
    except ImportError:
        try:
            return import_module("fitz")
        except ImportError:
            pytest.skip("PyMuPDF is not installed")


def _pdf_content_of_size(size: int) -> bytes:
    pymupdf = _load_pymupdf()
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Nexora resume parser size fixture")
    content = document.tobytes()
    document.close()
    if len(content) > size:
        pytest.fail(f"Generated PDF fixture ({len(content)} bytes) exceeds target size {size}.")
    return content + b" " * (size - len(content))


def test_rejects_unsupported_file_type() -> None:
    with pytest.raises(ResumeParseError) as error:
        parse_resume(b"data", "resume.txt")
    assert error.value.code == "unsupported_type"


def test_rejects_malformed_pdf() -> None:
    with pytest.raises(ResumeParseError) as error:
        parse_resume(b"not a pdf", "resume.pdf")
    assert error.value.code == "malformed_document"


def test_extracts_pdf_text_and_sections() -> None:
    pymupdf = _load_pymupdf()
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Asha Rao\nEducation\nNexora University")
    content = document.tobytes()
    document.close()

    result = parse_resume(content, "resume.pdf")
    assert result.source_format == "pdf"
    assert "Asha Rao" in result.text
    assert result.sections["education"] == "Nexora University"
    assert result.normalized_text == "Asha Rao\nEducation\nNexora University"


def test_rejects_empty_and_oversized_files() -> None:
    with pytest.raises(ResumeParseError, match="empty"):
        parse_resume(b"", "resume.pdf")
    with pytest.raises(ResumeParseError) as error:
        parse_resume(b"%PDF-data", "resume.pdf", max_file_bytes=5)
    assert error.value.code == "file_too_large"


@pytest.mark.parametrize(
    "size",
    [DEFAULT_MAX_FILE_BYTES - 1, DEFAULT_MAX_FILE_BYTES],
    ids=["one-byte-below-limit", "exact-limit"],
)
def test_accepts_valid_pdf_at_or_below_default_size_limit(size: int) -> None:
    content = _pdf_content_of_size(size)
    assert len(content) == size

    result = parse_resume(content, "resume.pdf")

    assert result.source_format == "pdf"
    assert "Nexora resume parser size fixture" in result.text


def test_rejects_file_one_byte_above_default_limit_before_parsing(monkeypatch) -> None:
    def fail_if_pdf_parser_runs(_content: bytes) -> tuple[str, list[str]]:
        pytest.fail("PDF parsing must not run for an oversized file.")

    monkeypatch.setattr(resume_parser, "_extract_pdf", fail_if_pdf_parser_runs)
    content = b"%PDF-" + b"x" * (DEFAULT_MAX_FILE_BYTES + 1 - len(b"%PDF-"))

    with pytest.raises(ResumeParseError) as error:
        parse_resume(content, "resume.pdf")

    assert error.value.code == "file_too_large"
    assert str(error.value) == "The resume exceeds the 5,000,000-byte size limit."


def test_explicit_custom_size_limit_override_is_preserved() -> None:
    content = _pdf_content_of_size(DEFAULT_MAX_FILE_BYTES + 1)

    result = parse_resume(
        content,
        "resume.pdf",
        max_file_bytes=DEFAULT_MAX_FILE_BYTES + 1,
    )

    assert result.source_format == "pdf"
    assert "Nexora resume parser size fixture" in result.text


def test_blank_filename_retains_validation_error() -> None:
    with pytest.raises(ResumeParseError) as error:
        parse_resume(b"%PDF-data", "   ")
    assert error.value.code == "invalid_filename"


def test_extracts_docx_text_and_recognizes_sections() -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    for value in ["Asha Rao", "Education", "Nexora University", "Skills", "Python"]:
        document.add_paragraph(value)
    buffer = io.BytesIO()
    document.save(buffer)
    result = parse_resume(
        buffer.getvalue(),
        "resume.docx",
    )
    assert result.source_format == "docx"
    assert result.sections == {"header": "Asha Rao", "education": "Nexora University", "skills": "Python"}
    assert "Asha Rao" in result.text


def test_empty_docx_text_is_reported() -> None:
    docx = pytest.importorskip("docx")
    buffer = io.BytesIO()
    docx.Document().save(buffer)
    with pytest.raises(ResumeParseError) as error:
        parse_resume(buffer.getvalue(), "empty.docx")
    assert error.value.code == "no_extractable_text"


def test_heading_detection_ignores_case_and_spacing_variations() -> None:
    sections = _identify_sections("Candidate\n  eDuCaTiOn : \nNorth  Valley University")
    assert sections["education"] == "North Valley University"


def test_multiple_resume_sections_are_identified() -> None:
    sections = _identify_sections(
        "Candidate Name\nEDUCATION\nNorth Valley University\n"
        "technical skills\nPython, SQL\nWork Experience\nBackend Intern"
    )
    assert sections == {
        "header": "Candidate Name",
        "education": "North Valley University",
        "skills": "Python, SQL",
        "experience": "Backend Intern",
    }


def test_multiword_heading_split_across_lines_is_recognized() -> None:
    sections = _identify_sections("Candidate\nProfessional\nExperience\nBackend Intern")
    assert sections["experience"] == "Backend Intern"


def test_missing_section_headings_keep_content_in_header() -> None:
    text = "Built tools for education access and student mentoring."
    assert _identify_sections(text) == {"header": text}


def test_unrecognized_heading_is_preserved_as_content() -> None:
    sections = _identify_sections(
        "Candidate\nEducation\nNorth Valley University\nCommunity Work\nCampus mentor"
    )
    assert "community_work" not in sections
    assert sections["education"] == "North Valley University\nCommunity Work\nCampus mentor"


def test_empty_pdf_document_is_reported() -> None:
    pymupdf = _load_pymupdf()
    document = pymupdf.open()
    document.new_page()
    content = document.tobytes()
    document.close()

    with pytest.raises(ResumeParseError) as error:
        parse_resume(content, "empty.pdf")
    assert error.value.code == "no_extractable_text"
