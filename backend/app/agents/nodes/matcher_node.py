"""Matcher node -- semantic similarity between resume and job description.

This is what the old ATS engine's fabricated 'semantic_score' was standing in
for: it was 'keyword_score * 0.8 + length_bonus', which carries no semantic
information, while the real MiniLM implementation sat in unreachable code.

Similarity is computed from 'scoring_text' rather than 'llm_text'. That is safe
and deliberate: the embedding model runs locally and in-process, so no text
leaves the host for this step, and the richer view produces a better match. The
backend actually used is recorded, so a score is never silently attributed to a
model that did not run.
"""

from __future__ import annotations

import logging

from app.agents.state import ScreeningState
from app.services.embeddings import semantic_similarity

logger = logging.getLogger(__name__)

NODE_NAME = "matcher"


def run(state: ScreeningState) -> ScreeningState:
    """Populate 'semantic_score' and 'semantic_backend'."""
    if not state.scoring_text.strip() or not state.job_description.strip():
        state.semantic_score = 0.0
        state.semantic_backend = "lexical"
        return state

    result = semantic_similarity(state.scoring_text, state.job_description)
    state.semantic_score = result.score
    state.semantic_backend = result.backend

    if not result.available:
        # The scorer substitutes the keyword score for a missing semantic
        # component, so this reduces precision rather than the score's scale.
        logger.info(
            "Semantic matching unavailable (%s; falling back to lexical signal)",
            result.backend,
        )

    return state