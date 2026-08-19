"""Analytics schemas.

Previously the analytics roots returned bare dicts, so the response shape existed
only in the frontend's hand-written TypeScript type and drifted freely from the
backend. These models put the contract in OpenAPI where the client can be
generated from it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationCounts(BaseModel):
    strong_match: int = 0
    review: int = 0
    low_match: int = 0


class AnalyticsOverview(BaseModel):
    total_jobs: int
    total_applications: int
    screened_applications: int
    average_score: float
    # Applications with no screening result yet.
    pending_screening: int
    percentage_screened: float
    # Decisions the fairness check escalated for review.
    bias_review_required: int
    recommendations: RecommendationCounts


class ScoreBucket(BaseModel):
    """One ten-point band of the score histogram. 'upper' is exclusive."""

    lower: int
    upper: int
    count: int


class ScoreDistribution(BaseModel):
    buckets: list[ScoreBucket] = Field(default_factory=list)
    total: int


class BiasDecisionItem(BaseModel):
    """A single escalated decision.

    Carries the application id rather than the candidate's name: a compliance
    view does not need to restate identity to be actionable.
    """

    application_id: UUID
    overall_score: float
    recommendation: str
    flags: list[str] = Field(default_factory=list)
    created_at: datetime


class FairnessSummary(BaseModel):
    total_screened: int
    total_flagged: int
    items: list[BiasDecisionItem] = Field(default_factory=list)