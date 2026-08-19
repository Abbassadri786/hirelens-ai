"""Health and readiness schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    #: LLM providers currently configured, in fallback order. Empty means
    #: screening still works but explanations will be deterministic only.
    llm_providers: list[str] = Field(default_factory=list)
    embeddings_available: bool = False