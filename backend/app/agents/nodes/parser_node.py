"""Parser node -- normalise raw resume text and extract canonical sections.

PDF and docx parsers leave artefacts: this node works on the extracted text. Its job is to
make that text predictable for everything downstream: normalise the whitespace
and line breaks that PDF extraction mangles, then split the document into
canonical sections.

Section detection drives the completeness sub-score, so it is part of scoring
rather than a cosmetic step.
"""

from __future__ import annotations

import logging
import re

from app.agents.state import ScreeningState
from app.services.pii_redaction import SCORED_SECTIONS, extract_sections

logger = logging.getLogger(__name__)

NODE_NAME = "parser"

# PDF extraction commonly yields runs of non-breaking spaces and hyphenated line
# breaks. Left alone these break both heading detection and skill matching.
NBSP_RE = re.compile(r"[\u00a0\u200b\u200c\u200d]+")
HYPHEN_BREAK_RE = re.compile(r"(\w+)-\n(\w+)")
TRAILING_SPACE_RE = re.compile(r"[ \t]+$", re.MULTILINE)
EXCESS_BLANKS_RE = re.compile(r"\n{3,}")
BULLET_RE = re.compile(r"^[\s\u2022\u2023\u25e6\u2043\*\-]+", re.MULTILINE)


def normalise_text(text: str) -> str:
    """Make extracted resume text consistent enough to parse reliably."""
    if not text:
        return ""

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = NBSP_RE.sub(" ", cleaned)
    # Rejoin words split across a line break by PDF hyphenation.
    cleaned = HYPHEN_BREAK_RE.sub(r"\1\2", cleaned)
    cleaned = BULLET_RE.sub("- ", cleaned)
    cleaned = TRAILING_SPACE_RE.sub("", cleaned)
    cleaned = EXCESS_BLANKS_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def run(state: ScreeningState) -> ScreeningState:
    """Normalise the resume text and populate 'sections' / 'section_count'."""
    state.raw_resume_text = normalise_text(state.raw_resume_text)

    if not state.has_resume_text:
        # Not an exception: an unparseable resume should still produce a scored,
        # explainable result rather than a 500.
        logger.warning("Resume for %s has no extractable text", state.application_id)
        state.sections = {}
        state.section_count = 0
        return state

    state.sections = extract_sections(state.raw_resume_text)

    # Count only the canonical sections. Counting every alias group would let a
    # verbose resume pack completeness above 100%.
    state.section_count = sum(
        1 for name in SCORED_SECTIONS if state.sections.get(name)
    )
    return state