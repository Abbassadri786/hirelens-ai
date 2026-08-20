"""Multi-process deployment would need Redis for the limit to be global.
A local in-memory token bucket.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window keyed by user id, falling back to client address."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        # FastAPI runs sync endpoints in a thread pool, so the buckets are
        # touched concurrently.
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            cutoff = now - self.window
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.limit:
                return False

            bucket.append(now)
            return True

    def reset(self) -> None:
        """Clear all buckets. Used by tests."""
        with self._lock:
            self._hits.clear()


def _identity(request: Request, user_id: str | None = None) -> str:
    if user_id:
        return f"user:{user_id}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def rate_limit(limiter: RateLimiter):
    """Build a FastAPI dependency enforcing `limiter`."""

    def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        key = _identity(request)
        if not limiter.allow(key):
            logger.warning("Rate limit exceeded on %s", request.url.path)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry shortly.",
                headers={"Retry-After": str(limiter.window)},
            )

    return dependency


auth_limiter = RateLimiter(settings.RATE_LIMIT_AUTH_PER_MINUTE)
screening_limiter = RateLimiter(settings.RATE_LIMIT_SCREENING_PER_MINUTE)
upload_limiter = RateLimiter(settings.RATE_LIMIT_UPLOAD_PER_MINUTE)

# The public apply endpoint is unauthenticated and takes attacker-supplied files
# to malice-PDF parsers, so the surface most worth bounding.
upload_limiter = RateLimiter(settings.RATE_LIMIT_UPLOAD_PER_MINUTE)

ALL_LIMITERS: tuple[RateLimiter, ...] = (
    auth_limiter,
    screening_limiter,
    upload_limiter,
)

auth_rate_limit = rate_limit(auth_limiter)
screening_rate_limit = rate_limit(screening_limiter)
upload_rate_limit = rate_limit(upload_limiter)