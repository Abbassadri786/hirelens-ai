"""Scorer node - deterministic, explainable ATS sub-scores.

Scoring stays fully deterministic on purpose. The LLM contributes narrative in
the feedback node but never moves a number, so a score is reproducible, testable
and defensible in a way an LLM-assigned score would not be. That is also what
makes the fairness counterfactual meaningful: re-running a pure function with the
name removed isolates exactly one variable.
"""

from __future__ import annotations

import logging

from app.agents.state import ScreeningState
from app.services.ats_engine import calculate_ats

logger = logging.getLogger(__name__)

NODE_NAME = "scorer"


def run(state: ScreeningState) -> ScreeningState:
    """Compute the ATS result and copy its narrative onto the state."""
    state.ats = calculate_ats(
        state.scoring_text,
        state.required_skills,
        state.preferred_skills,
        state.min_experience_years,
        state.section_count,
        semantic_score=state.semantic_score,
        sections=state.sections,
    )

    # Deterministic narrative is the baseline.
    state.strengths = list(state.ats.strengths)
    state.concerns = list(state.ats.concerns)

    logger.info(
        "Scored application %s: %.1f/100 (%s), %d/%d required skills matched",
        state.application_id,
        state.ats.overall_score,
        state.ats.recommendation,
        len(state.ats.matched_required),
        len(state.ats.matched_required) + len(state.ats.missing_required),
    )
    return state