"""Bias-check node -- audits the decision the scorer just made.

The substantive check is a counterfactual: re-score the resume with only the
candidate's name edited out, because `calculate_ats` is a pure function
of its inputs, an identical score is expected, and any difference is direct
evidence that name-derived signal moved the outcome. Names are the documented
proxy for gender and ethnicity in ATS discrimination cases, so this is the check
worth being able to fail.

It runs after the feedback node so it can also inspect the generated
explanation, which is the artefact a candidate would actually receive.
"""

from __future__ import annotations

import logging

from app.agents.state import ScreeningState
from app.services.ats_engine import calculate_ats
from app.services.bias_check import assess

logger = logging.getLogger(__name__)

NODE_NAME = "bias_check"


def run(state: ScreeningState) -> ScreeningState:
    """Populate `state.bias` and surface any flags as concerns."""

    def score_only(text: str) -> float:
        """Re-score 'text' holding every other input constant."""
        return calculate_ats(
            text,
            state.required_skills,
            state.preferred_skills,
            state.min_experience_years,
            state.section_count,
            semantic_score=state.semantic_score,
            sections=state.sections,
        ).overall_score

    state.bias = assess(
        scoring_text=state.scoring_text,
        name_redacted_text=state.name_redacted_text,
        score_fn=score_only,
        explanation=state.explanation,
    )

    # Fairness findings belong in the reviewer-visible narrative, not only in a
    # log line -- but only once, so a re-run cannot duplicate them.
    for flag in state.bias.flags:
        if flag not in state.concerns:
            state.concerns.append(flag)

    if state.bias.review_required:
        logger.warning(
            "Application %s needs fairness review (name delta %+.2f)",
            state.application_id,
            state.bias.name_sensitivity_delta,
        )

    return state