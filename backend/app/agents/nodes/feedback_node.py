"""Feedback node -- human-readable improvement notes.

The only node that talks to an external model, and the only place resume-derived
text crosses a network boundary. Two constraints are enforced structurally
rather than by convention:

1. It reads 'state.llm_text', never 'raw_resume_text' or 'scoring_text'. The
   redaction node has already removed names, contact details, addresses and URL
   paths from that view.
2. It cannot change a score. Every number is fixed by the scorer before this
   runs; the model contributes narrative only. If it returns nothing usable, the
   deterministic explanation stands and the result is still complete.

'provider' and 'model_name' are recorded so an explanation shown to a candidate
can be attributed to whatever actually generated it -- including
'deterministic'/'none' when the whole fallback chain was unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.llm_router import (
    DETERMINISTIC_PROVIDER,
    NO_MODEL,
    AllProvidersFailed,
    LLMResponse,
    router,
)
from app.agents.state import ScreeningState

logger = logging.getLogger(__name__)

NODE_NAME = "feedback"

MAX_ITEMS = 5
MAX_SUGGESTION_CHARS = 400
MAX_EXPLANATION_CHARS = 4_000
MAX_JOB_DESCRIPTION_CHARS = 12_000
MAX_RESUME_CHARS = 20_000

SYSTEM_PROMPT = """You are the explainability layer of a recruitment screening system.

Rules you must follow:
- Use only job-relevant evidence that appears in the provided text.
- Never infer, mention, or agree age, gender, race, religion, nationality,
  marital status, health, disability, appearance, or any other protected
  characteristics. Redacted placeholders such as [NAME_REDACTED] must be ignored,
  never guessed at.
- Never invent skills, employers, or experience that is not present.
- Do not restate or contradict the numeric scores you are given; they are final.
- Write for the recruiter and the candidate: specific, actionable, neutral.

Return a JSON object with exactly these keys:
- "strengths": array of short strings
- "concerns": array of short strings
- "improvement_suggestions": array of short, actionable strings
- "explanation": a string of two to four sentences justifying the score
"""

# Used when no provider is reachable. Generic by necessity, but still tied to
# the actual score rather than being a fixed string.
STATIC_SUGGESTIONS: tuple[str, ...] = (
    "Add concrete evidence for any missing required skills, ideally in a "
    "dedicated skills section.",
    "Quantify impact on experience and project descriptions (scale, latency, "
    "cost, revenue).",
    "Use standard section headings so automated parsers detect every section.",
)


def run(state: ScreeningState) -> ScreeningState:
    """Enrich the narrative via the LLM chain, or fall back deterministically."""
    if state.ats is None:
        # The scorer must have run first; without it there is nothing to explain.
        _apply_deterministic(state)
        return state

    if not router.any_available:
        logger.info("No LLM provider configured; using deterministic explanation")
        _apply_deterministic(state)
        return state

    try:
        response = router.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=_build_prompt(state),
        )
    except AllProvidersFailed as exc:
        logger.warning(
            "LLM chain exhausted (%s); using deterministic explanation",
            ", ".join(f"{a.provider} ({a.reason})" for a in exc.attempts),
        )
        _apply_deterministic(state)
        return state

    _apply_llm_response(state, response)
    return state


def _build_prompt(state: ScreeningState) -> str:
    """Assemble the user prompt from redacted text and the fixed scores."""
    assert state.ats is not None # guarded by the caller

    baseline = {
        "overall_score": state.ats.overall_score,
        "sub_scores": {
            "keyword": state.ats.keyword_score,
            "skills": state.ats.skill_score,
            "semantic": state.ats.semantic_score,
            "experience": state.ats.experience_score,
            "completeness": state.ats.completeness_score,
        },
        "recommendation": state.ats.recommendation,
        "matched_required_skills": state.ats.matched_required,
        "missing_required_skills": state.ats.missing_required,
        "matched_preferred_skills": state.ats.matched_preferred,
        "detected_experience_years": state.ats.detected_experience_years,
        "sections_detected": sorted(state.sections),
    }

    return (
        f"JOB TITLE:\n{state.job_title}\n\n"
        f"JOB DESCRIPTION:\n{state.job_description[:MAX_JOB_DESCRIPTION_CHARS]}\n\n"
        f"REDACTED RESUME:\n{state.llm_text[:MAX_RESUME_CHARS]}\n\n"
        f"FIXED SCORES (authoritative, do not recompute):\n"
        f"{json.dumps(baseline, indent=2)}\n"
    )


def _clean_items(value: Any, *, limit: int = MAX_ITEMS) -> list[str]:
    """Coerce a model-supplied field into a bounded list of clean strings."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []

    items: list[str] = []
    for entry in value:
        if not isinstance(entry, (str, int, float)):
            continue
        text = str(entry).strip()
        if text and text not in items:
            items.append(text[:MAX_SUGGESTION_CHARS])
            if len(items) >= limit:
                break
    return items


def _apply_llm_response(state: ScreeningState, response: LLMResponse) -> None:
    """Merge model output, bounding deterministic findings as the floor."""
    parsed = response.as_json()

    state.provider = response.provider
    state.model_name = response.model

    llm_strengths = _clean_items(parsed.get("strengths"))
    llm_concerns = _clean_items(parsed.get("concerns"))
    suggestions = _clean_items(parsed.get("improvement_suggestions"))

    # Deterministic findings are evidence-linked and must not be dropped just
    # because the model omitted them, so they are merged rather than replaced.
    state.strengths = _merge(state.strengths, llm_strengths)
    state.concerns = _merge(state.concerns, llm_concerns)
    state.improvement_suggestions = suggestions or list(STATIC_SUGGESTIONS)

    explanation = parsed.get("explanation")
    if (
        isinstance(explanation, (str, int, float))
        and (explanation := str(explanation).strip())
    ):
        state.explanation = explanation[:MAX_EXPLANATION_CHARS]
    else:
        state.explanation = _deterministic_explanation(state)


def _merge(primary: list[str], secondary: list[str]) -> list[str]:
    """Concatenate, de-duplicate case-insensitively, and bound the length."""
    merged: list[str] = []
    seen: set[str] = set()
    for item in (*primary, *secondary):
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            merged.append(item)
            if len(merged) >= MAX_ITEMS:
                break
    return merged


def _apply_deterministic(state: ScreeningState) -> None:
    """Produce a complete explanation with no model involvement."""
    state.provider = DETERMINISTIC_PROVIDER
    state.model_name = NO_MODEL
    state.improvement_suggestions = _build_deterministic_suggestions(state)
    state.explanation = _deterministic_explanation(state)


def _build_deterministic_suggestions(state: ScreeningState) -> list[str]:
    """Targeted suggestions derived from the actual gaps found."""
    suggestions: list[str] = []

    if state.ats is not None and state.ats.missing_required:
        missing = ", ".join(state.ats.missing_required[:3])
        suggestions.append(
            f"Add explicit evidence for the required skills not found: {missing}."
        )

    if state.section_count < 3:
        missing_sections = [
            name
            for name in ("summary", "experience", "education", "skills", "projects")
            if not state.sections.get(name)
        ]
        if missing_sections:
            suggestions.append(
                "Add clearly headed sections for: "
                f"{', '.join(missing_sections[:3])}."
            )

    if state.ats is not None and state.ats.experience_score < 100:
        suggestions.append(
            "State total years of relevant experience explicitly, for example "
            "'N years of professional experience'."
        )

    for fallback in STATIC_SUGGESTIONS:
        if len(suggestions) >= MAX_ITEMS:
            break
        if fallback not in suggestions:
            suggestions.append(fallback)

    return suggestions[:MAX_ITEMS]


def _deterministic_explanation(state: ScreeningState) -> str:
    """Score justification assembled from the sub-scores and the evidence."""
    if state.ats is None:
        return (
            "This resume could not be scored because no readable text was "
            "extracted. It is a screening aid, not a hiring decision."
        )

    ats = state.ats
    parts: list[str] = [
        f"The screening score is {ats.overall_score:.1f}/100 "
        f"({ats.recommendation.replace('_', ' ').lower()}). "
        f"It combines keyword match ({ats.keyword_score:.0f}), "
        f"semantic similarity ({ats.semantic_score:.0f}), "
        f"experience fit ({ats.experience_score:.0f}), and "
        f"section completeness ({ats.completeness_score:.0f}), "
        f"weighted 40/35/20/50."
    ]

    if ats.matched_required:
        parts.append(
            f"Required skills evidenced: {', '.join(ats.matched_required[:4])}."
        )

    if ats.missing_required:
        parts.append(
            f"No evidence found for: {', '.join(ats.missing_required[:4])}."
        )

    parts.append(
        "This score is a screening aid computed by deterministic rules, "
        "not a hiring decision."
    )

    return " ".join(parts)[:MAX_EXPLANATION_CHARS]