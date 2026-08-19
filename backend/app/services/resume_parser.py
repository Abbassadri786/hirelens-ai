"""Resume text extraction from PDF and DOCX files.

Raises 'ResumeParseError' (the previous bare 'ValueError'/uncaught exceptions,
so the API layer can distinguish "this document is unusable" from an internal
fault and return 422 rather than 500.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

# Beyond this a "resume" is something else -- a scanned book, or a crafted file
# designed to exhaust memory during extraction.
MAX_PDF_PAGES: Final = 50
MAX_DOCX_PARAGRAPHS: Final = 5_000
MAX_DOCX_TABLE_CELLS: Final = 5_000

# Matches the 'extracted_text' storage limit, so truncation happens once here
# rather than silently at the database boundary.
MAX_EXTRACTED_CHARS: Final = 100_000


class ResumeParseError(Exception):
    """The document could not be read as a resume."""


def extract_pdf(path: Path) -> str:
    """Extract text from a PDF, page-bounded."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc: # pragma: no cover - dependency guard
        raise ResumeParseError("PDF support is unavailable") from exc

    try:
        with fitz.open(path) as document:
            if document.is_encrypted and not document.authenticate(""):
                raise ResumeParseError("Password-protected PDFs are not supported")

            page_count = min(document.page_count, MAX_PDF_PAGES)
            if document.page_count > MAX_PDF_PAGES:
                logger.warning(
                    "Truncating PDF: %d pages exceeds the %d-page limit",
                    document.page_count,
                    MAX_PDF_PAGES,
                )

            parts = [
                document.load_page(index).get_text("text")
                for index in range(page_count)
            ]
    except ResumeParseError:
        raise
    except Exception as exc:
        # Malformed or malicious PDF. Deliberately not surfacing the parser's
        # message, which can echo little internal back to the caller.
        logger.warning("PDF extraction failed", exc_info=True)
        raise ResumeParseError("Could not read this PDF") from exc

    return "\n".join(parts).strip()


def extract_docx(path: Path) -> str:
    """Extract paragraph and table text from a DOCX, element-bounded."""
    try:
        from docx import Document
    except ImportError as exc: # pragma: no cover - dependency guard
        raise ResumeParseError("DOCX support is unavailable") from exc

    try:
        document = Document(str(path))

        parts: list[str] = []
        for index, paragraph in enumerate(document.paragraphs):
            if index >= MAX_DOCX_PARAGRAPHS:
                break
            text = paragraph.text.strip()
            if text:
                parts.append(text)

        # Skills are very often laid out in tables, so table text is included
        # rather than discarded -- dropping it would lose real skill signal.
        cells_seen = 0
        for table in document.tables:
            for row in table.rows:
                if cells_seen >= MAX_DOCX_TABLE_CELLS:
                    break
                values = [cell.text.strip() for cell in row.cells]
                cells_seen += len(values)
                joined = " | ".join(v for v in values if v)
                if joined:
                    parts.append(joined)
    except Exception as exc:
        logger.warning("DOCX extraction failed", exc_info=True)
        raise ResumeParseError("Could not read this DOCX document") from exc

    return "\n".join(parts).strip()


def extract_resume_text(path: Path, file_type: str) -> str:
    """Extract text for a stored resume of the given type.

    Raises 'ResumeParseError' for unsupported types, unreadable documents, and
    documents containing no extractable text -- the last of which usually means a
    scanned image, which needs OCR rather than a text parser.
    """
    normalized = str(file_type).upper()

    if normalized == "PDF":
        text = extract_pdf(path)
    elif normalized == "DOCX":
        text = extract_docx(path)
    else:
        raise ResumeParseError(f"Unsupported resume type: {file_type}")

    if not text.strip():
        raise ResumeParseError(
            "No readable text found. Scanned or image-only resumes are not "
            "supported."
        )

    return text[:MAX_EXTRACTED_CHARS]