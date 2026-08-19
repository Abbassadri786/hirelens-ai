"""FastAPI application entrypoint.

One middleware, doing one thing: security headers. Rate limiting is a dependency
on the two endpoints that need it rather than a global middleware, and request
correlation IDs were removed - useful in a distributed system, noise in a
single-service app.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.llm_router import router as llm_router
from app.api.v1 import (
    analytics,
    applications,
    audit,
    auth,
    health,
    jobs,
    organizations,
    screening,
)
from app.core.config import settings
from app.services.embeddings import is_available as embeddings_available

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Set up logging and report which optional capabilities resolved.

    Logging the resolved providers turns a silent degradation into a visible
    one: a missing API key otherwise behaves identically to a working one, just
    with worse output.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # SQLAlchemy echoes bound parameters at INFO, which can include resume text.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.info(
        "Starting %s (env=%s) | LLM providers: %s | embeddings: %s",
        settings.APP_NAME,
        settings.ENVIRONMENT,
        llm_router.configured_providers or "none (deterministic explanations)",
        embeddings_available(),
    )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Multi-agent resume screening API. Scores come from a deterministic "
        "pipeline; language models contribute narrative only."
    ),
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Attach hardening headers to every response."""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Screening results are candidate data; intermediaries must not cache them.
    if request.url.path.startswith(API_PREFIX):
        response.headers["Cache-Control"] = "no-store"

    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"

    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors without echoing the submitted value.

    FastAPI's default handler includes the offending input, which here could mean
    reflecting a password or resume content back to the caller.
    """
    return JSONResponse(
        {
            "detail": [
                {
                    "field": ".".join(str(part) for part in error.get("loc", ())),
                    "message": error.get("msg", "Invalid value"),
                }
                for error in exc.errors()
            ]
        },
        status_code=422,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the failure in full; tell the client nothing about internals."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "An internal error occurred."}, status_code=500)


for router in (
    health.router,
    auth.router,
    organizations.router,
    jobs.router,
    applications.router,
    screening.router,
    analytics.router,
    audit.router,
):
    app.include_router(router, prefix=API_PREFIX)