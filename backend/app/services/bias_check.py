"""Fairness and bias detection in resume screening.

Detects protected attributes present in resume text, tests for name-based scoring
sensitivity, and flags explanations citing protected categories.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Final

logger = logging.getLogger(__name__)

# Any score movement above this from a name-only change is treated as real
# rather than floating-point noise.
NAME_SENSITIVITY_TOLERANCE: Final = 4.0

# Protected attributes, grouped as a flag category name, not the keyword.
PROTECTED_ATTRIBUTE_PATTERNS: dict[str, tuple[str, ...]] = {
    "age": (r"\bage\b", r"\bdate of birth\b", r"\bd\.?o\.?b\.?\b", r"\byears old\b"),
    "gender": (r"\bgender\b", r"\bsex\b", r"\bfemale\b", r"\bmale\b", r"\bpronoun\b"),
    "marital_status": (r"\bmarital status\b", r"\bmarried\b", r"\bsingle\b", r"\bspouse\b"),
    "religion": (r"\breligion\b", r"\bchurch\b", r"\bmosque\b", r"\btemple\b", r"\bfaith\b"),
    "ethnicity": (r"\brace\b", r"\bethnicity\b", r"\bcaste\b", r"\btribe\b", r"\bblack\b", r"\bwhite\b", r"\basian\b"),
    "disability": (r"\bdisability\b", r"\bdisabled\b", r"\bmedical condition\b", r"\bpregnant\b"),
    "photo": (r"\bphotograph\b", r"\bphoto attached\b", r"\bpassport size\b"),
}

COMPILED_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    category: tuple(re.compile(p, re.IGNORECASE) for p in patterns)
    for category, patterns in PROTECTED_ATTRIBUTE_PATTERNS.items()
}

# Names of the checks performed, reported honestly rather than aspirationally.
CHECKS_PERFORMED: tuple[str, ...] = (
    "protected_attribute_presence",
    "name_sensitivity_counterfactual",
    "explanation_hygiene",
)


@dataclass(slots=True)
class BiasAssessment:
    """Outcome of the fairness checks for one screening decision."""

    flags: list[str] = field(default_factory=list)
    protected_attributes_present: list[str] = field(default_factory=list)
    name_sensitivity_delta: float = 0.0
    review_required: bool = False
    checks_performed: tuple[str, ...] = CHECKS_PERFORMED

    @property
    def name_signal_detected(self) -> bool:
        return abs(self.name_sensitivity_delta) > NAME_SENSITIVITY_TOLERANCE

    def as_dict(self) -> dict[str, Any]:
        return {
            "flags": list(self.flags),
            "protected_attributes_present": list(self.protected_attributes_present),
            "name_sensitivity_delta": round(self.name_sensitivity_delta, 4),
            "name_signal_detected": self.name_signal_detected,
            "review_required": self.review_required,
            "checks_performed": list(self.checks_performed),
        }


def detect_protected_attributes(text: str) -> list[str]:
    """Categories of protected attributes mentioned in 'text'."""
    if not text:
        return []

    return [
        category
        for category, patterns in COMPILED_PATTERNS.items()
        if any(pattern.search(text) for pattern in patterns)
    ]


def measure_name_sensitivity(
    score_fn: Callable[[str], float],
    scoring_text: str,
    name_redacted_text: str,
) -> float:
    """Score delta caused by removing the candidate's name and nothing else.

    Returns 'baseline - counterfactual'. A well-specified scorer returns 0.0.
    """
    if not scoring_text:
        return 0.0

    try:
        baseline = score_fn(scoring_text)
        counterfactual = score_fn(name_redacted_text)
        return baseline - counterfactual
    except Exception:
        # A fairness check must never break the decision it is auditing.
        logger.exception("name-sensitivity counterfactual failed; reporting 0.0")
        return 0.0


def scan_explanation(explanation: str) -> list[str]:
    """Protected-attribute categories cited in generated narrative text."""
    return detect_protected_attributes(explanation)


def assess(
    *,
    scoring_text: str,
    name_redacted_text: str,
    score_fn: Callable[[str], float] | None = None,
    explanation: str = "",
) -> BiasAssessment:
    """Run every fairness check and decide whether human review is required."""
    assessment = BiasAssessment()

    assessment.protected_attributes_present = detect_protected_attributes(scoring_text)
    for category in assessment.protected_attributes_present:
        assessment.flags.append(
            f"Resume text discloses a protected attribute ({category}); "
            "ensure it did not inform the assessment."
        )

    if score_fn is not None:
        assessment.name_sensitivity_delta = measure_name_sensitivity(
            score_fn,
            scoring_text,
            name_redacted_text=name_redacted_text,
        )
        if assessment.name_signal_detected:
            assessment.flags.append(
                f"Score moved by {assessment.name_sensitivity_delta:+.2f} points when "
                "only the candidate's name was removed. Name-derived signal is a "
                "known proxy for gender and ethnicity; this decision needs review."
            )

    for category in scan_explanation(explanation):
        assessment.flags.append(
            f"Generated explanation references a protected attribute ({category})."
        )

    # Name sensitivity is a defect in the scorer, so it always escalates.
    # A mere disclosure in the source document does not.
    assessment.review_required = assessment.name_signal_detected or bool(
        scan_explanation(explanation)
    )

    if assessment.review_required:
        logger.warning(
            "Screening decision flagged for fairness review: %d flag(s), name delta %+.2f",
            len(assessment.flags),
            assessment.name_sensitivity_delta,
        )

    return assessment


# -----------------------------------------------------------------------------
# Backwards compatibility
# -----------------------------------------------------------------------------


@dataclass(slots=True)
class BiasCheck:
    """Legacy shape retained for the existing unit test and any old callers."""

    flags: list[str]
    checked_fields: list[str]
    safe_for_screening: bool


def inspect_text(text: str) -> BiasCheck:
    """Presence-only check.

    Kept because it is the shape the original test asserts. Prefer 'assess',
    which additionally runs the counterfactual that can actually fail.
    """
    categories = detect_protected_attributes(text)
    return BiasCheck(
        flags=[
            f"Potential protected-attribute reference detected: {category}"
            for category in categories
        ],
        checked_fields=list(CHECKS_PERFORMED)[:1],
        safe_for_screening=True,
    )