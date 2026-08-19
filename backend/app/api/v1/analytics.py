from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import joinedload

from app.api.deps import AdminUser, DbSession, StaffUser, require_admin, require_staff
from app.models.application import Application
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.schemas.analytics import (
    AnalyticsOverview,
    BiasDecisionItem,
    FairnessSummary,
    RecommendationCounts,
    ScoreBucket,
    ScoreDistribution,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Ten-point buckets across the 0-100 score range.
BUCKET_SIZE = 10


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    dependencies=[Depends(require_staff)],
)
def overview(db: DbSession, user: StaffUser) -> AnalyticsOverview:
    """Headline counts and recommendation split for the active tenant."""
    org = user.organization_id

    total_jobs = (
        db.scalar(select(func.count(Job.id)).where(Job.organization_id == org)) or 0
    )
    total_applications = (
        db.scalar(
            select(func.count(Application.id)).where(
                Application.organization_id == org
            )
        )
        or 0
    )

    # One pass over screening_results instead of five separate counts.
    aggregate = db.execute(
        select(
            func.count(ScreeningResult.id),
            func.coalesce(func.avg(ScreeningResult.overall_score), 0.0),
            func.coalesce(
                func.sum(
                    case((ScreeningResult.recommendation == "STRONG_MATCH", 1), else_=0)
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case((ScreeningResult.recommendation == "REVIEW", 1), else_=0)
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case((ScreeningResult.recommendation == "LOW_MATCH", 1), else_=0)
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case((ScreeningResult.bias_review_required.is_(True), 1), else_=0)
                ),
                0,
            ),
        ).where(ScreeningResult.organization_id == org)
    ).one()

    screened, average, strong, review, low, flagged = aggregate

    return AnalyticsOverview(
        total_jobs=total_jobs,
        total_applications=total_applications,
        screened_applications=screened or 0,
        average_score=round(float(average), 2),
        percentage_screened=(
            round(screened / total_applications * 100, 2)
            if total_applications > 0
            else 0.0
        ),
        bias_review_required=flagged or 0,
        recommendation=RecommendationCounts(
            strong_match=strong or 0,
            review=review or 0,
            low_match=low or 0,
        ),
    )


@router.get(
    "/score-distribution",
    response_model=ScoreDistribution,
    dependencies=[Depends(require_staff)],
)
def score_distribution(db: DbSession, user: StaffUser) -> ScoreDistribution:
    """Score histogram in ten-point buckets."""
    org = user.organization_id

    # Bucket in SQL. Scores of exactly 100 would land in an eleventh bucket, so
    # they are folded back into the 90-100 band.
    bucket_expr = func.least(
        func.floor(ScreeningResult.overall_score / BUCKET_SIZE), 9
    )

    rows = db.execute(
        select(bucket_expr.label("bucket"), func.count(ScreeningResult.id))
        .where(ScreeningResult.organization_id == org)
        .group_by(bucket_expr)
        .order_by(bucket_expr)
    ).all()

    counts = {int(bucket): count for bucket, count in rows}

    return ScoreDistribution(
        buckets=[
            ScoreBucket(
                lower_index=index,
                lower=(index * BUCKET_SIZE),
                upper=((index + 1) * BUCKET_SIZE),
                count=counts.get(index, 0),
            )
            for index in range(10)
        ],
        total=sum(counts.values()),
    )


@router.get(
    "/fairness",
    response_model=FairnessSummary,
    dependencies=[Depends(require_admin)],
)
def fairness_summary(
    db: DbSession,
    user: AdminUser,
    limit: int = Query(default=50, ge=1, le=200),
) -> FairnessSummary:
    """Decisions the bias check escalated for human review.

    Admin-only. Each entry names the application and the specific flags raised,
    so a reviewer can act on it rather than only seeing that a count is non-zero.
    """
    org = user.organization_id

    total_screened = (
        db.scalar(
            select(func.count(ScreeningResult.id)).where(
                ScreeningResult.organization_id == org
            )
        )
        or 0
    )

    # Counted separately from the listing: len(items) would be capped by
    # 'limit' and would under-report the true number of escalations.
    total_flagged = (
        db.scalar(
            select(func.count(ScreeningResult.id)).where(
                ScreeningResult.organization_id == org,
                ScreeningResult.bias_review_required.is_(True),
            )
        )
        or 0
    )

    flagged_rows = (
        db.scalars(
            select(ScreeningResult)
            .options(
                joinedload(ScreeningResult.application).joinedload(
                    Application.candidate
                )
            )
            .where(
                ScreeningResult.organization_id == org,
                ScreeningResult.bias_review_required.is_(True),
            )
            .order_by(ScreeningResult.created_at.desc())
            .limit(limit)
        )
        .unique()
        .all()
    )

    return FairnessSummary(
        total_screened=total_screened,
        total_flagged=total_flagged,
        items=[
            BiasDecisionItem(
                application_id=row.application_id,
                overall_score=row.overall_score,
                recommendation=row.recommendation,
                flags=list(row.bias_flags or ()),
                created_at=row.created_at,
            )
            for row in flagged_rows
        ],
    )