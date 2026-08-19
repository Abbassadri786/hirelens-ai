# backend/app/agents/state.py

"""State object threaded through the screening pipeline.

The state also carries its own provenance -- per-node timings, recorded errors,
and which backend produced each component -- so a completed run can explain
itself without re-executing anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.services.ats_engine import ATSResult
from app.services.bias_check import BiasAssessment
from app.services.pii_redaction import RedactionReport

# Bumped when the scoring semantics change, so historical decisions remain
# interpretable against the logic that actually produced them.
PIPELINE_VERSION = "1"


@dataclass(slots=True)
class NodeOutcome:
    """Execution record for a single node."""

    name: str
    succeeded: bool
    duration_ms: int
    detail: str = ""


@dataclass(slots=True)
class ScreeningState:
    """Mutable state for one screening run."""

    # -- Identity --
    application_id: UUID
    organization_id: UUID
    job_id: UUID

    # -- Inputs --
    raw_resume_text: str = ""
    job_description: str = ""
    job_title: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_experience_years: int | None = None

    # Candidate names known from the database, used for exact-match redaction
    # rather than inferring names from the document.
    known_names: tuple[str, ...] = ()

    # -- parser_node --
    sections: dict[str, str] = field(default_factory=dict)
    section_count: int = 0

    # -- redaction_node --
    # Contact details removed, URLs intact. Safe for local scoring only.
    scoring_text: str = ""
    # Names, addresses and URL paths also removed. The only view that may be
    # transmitted to an external provider.
    llm_text: str = ""
    # Same as 'llm_text' but with names removed regardless of configuration,
    # used as the counterfactual input for the fairness check.
    name_redacted_text: str = ""
    redaction_report: RedactionReport | None = None

    # -- matcher_node --
    semantic_score: float = 0.0
    semantic_backend: str = "lexical"

    # -- scorer_node --
    ats: ATSResult | None = None

    # -- bias_check_node --
    bias: BiasAssessment | None = None

    # -- feedback_node --
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    explanation: str = ""
    provider: str = "deterministic"
    model_name: str = "none"

    # -- Execution record --
    outcomes: list[NodeOutcome] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    pipeline_version: str = PIPELINE_VERSION

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def record(self, outcome: NodeOutcome) -> None:
        self.outcomes.append(outcome)
        if not outcome.succeeded and outcome.detail:
            self.errors.append(f"{outcome.name}: {outcome.detail}")

    @property
    def total_duration_ms(self) -> int:
        return sum(outcome.duration_ms for outcome in self.outcomes)

    @property
    def has_resume_text(self) -> bool:
        return bool(self.raw_resume_text.strip())

    def audit_payload(self) -> dict[str, Any]:
        """Compact, PII-free summary for the audit trail.

        Deliberately excludes every text field. Only counts, scores and backend
        identifiers appear here, so writing an audit row can never itself become
        a disclosure.
        """
        payload: dict[str, Any] = {
            "pipeline_version": self.pipeline_version,
            "provider": self.provider,
            "model": self.model_name,
            "semantic_backend": self.semantic_backend,
            "section_count": self.section_count,
            "processing_ms": self.total_duration_ms,
            "nodes": [
                {
                    "name": outcome.name,
                    "ok": outcome.succeeded,
                    "ms": outcome.duration_ms,
                }
                for outcome in self.outcomes
            ],
        }

        if self.ats is not None:
            payload["scores"] = {
                "overall": self.ats.overall_score,
                "skills": self.ats.skill_score,
                "keyword": self.ats.keyword_score,
                "semantic": self.ats.semantic_score,
                "experience": self.ats.experience_score,
                "completeness": self.ats.completeness_score,
            }
            payload["weighted_contributions"] = self.ats.score_breakdown()
            payload["recommendation"] = self.ats.recommendation
            payload["matched_required_count"] = len(self.ats.matched_required)
            payload["missing_required_count"] = len(self.ats.missing_required)

        if self.redaction_report is not None:
            payload["redaction"] = self.redaction_report.as_dict()

        if self.bias is not None:
            payload["fairness"] = self.bias.as_dict()

        if self.errors:
            payload["errors"] = list(self.errors)

        return payload