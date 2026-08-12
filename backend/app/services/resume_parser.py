from pathlib import Path

import fitz
from docx import Document


def extract_pdf(path: Path) -> str:
    with fitz.open(path) as doc:
        return '\n'.join(p.get_text('text') for p in doc).strip()


def extract_docx(path: Path) -> str:
    doc = Document(path)
    parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(' | '.join(c.text.strip() for c in row.cells))
    return '\n'.join(parts).strip()


def extract_resume_text(path: Path, file_type: str) -> str:
    if file_type == 'PDF':
        return extract_pdf(path)
    if file_type == 'DOCX':
        return extract_docx(path)
    raise ValueError('Unsupported resume type')