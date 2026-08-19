"""Health and readiness checks.

/health is a liveness probe: zero checks. /readiness checks the database so the
service cannot serve traffic if it is pulled from rotation rather than restarted.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.agents.llm_router import router as llm_router
from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.embeddings import is_available as embeddings_available

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness. Deliberately dependency-free."""
    return HealthResponse(
        status="ok",
        service="hirelens-api",
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness(db: DbSession, response: Response) -> ReadinessResponse:
    """Readiness, including the capabilities actually available right now.

    Reporting LLM and embedding availability here means a degraded deployment -
    running, but with no provider configured - is visible from outside the
    process instead of only in the startup log.
    """
    database_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False
        logger.exception("Readiness check failed: database unreachable")

    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if database_ok else "not_ready",
        database="ok" if database_ok else "unreachable",
        llm_providers=llm_router.configured_providers,
        embeddings_available=embeddings_available(),
    )