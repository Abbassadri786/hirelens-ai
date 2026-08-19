"""Redaction node - the PII boundary of the pipeline.

Every node after this one works from a redacted view. Placing redaction before
matching, scoring and explanation is what makes "no candidate PII reaches a
third-party API" a structural property rather than a promise each call site has
to remember.
"""

from __future__ import annotations

import logging

from app.agents.state import ScreeningState
from app.services.pii_redaction import redact_resume

logger = logging.getLogger(__name__)

NODE_NAME = "redaction"


def run(state: ScreeningState) -> ScreeningState:
    """Populate the three text views and the redaction report."""
    redacted = redact_resume(state.raw_resume_text, known_names=state.known_names)

    state.scoring_text = redacted.scoring_text
    state.llm_text = redacted.llm_text
    state.redaction_report = redacted.report

    if redacted.sections:
        state.sections = redacted.sections
        state.section_count = redacted.scored_section_count

    # The counterfactual view always strips names, independent of the
    # PII_REDACT_NAMES setting - otherwise disabling redaction would silently
    # disable the fairness check along with it.
    state.name_redacted_text = redacted.name_redacted_text

    logger.info(
        "Redacted %d PII item(s) before any external call", redacted.report.total
    )
    return state