import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.events = defaultdict(deque)

    def check(self, key: str):
        now = time.monotonic()
        q = self.events[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        q.append(now)

api_limiter = InMemoryRateLimiter(limit=120, window_seconds=60)

async def rate_limit_dependency(request: Request):
    key = request.client.host if request.client else "unknown"
    api_limiter.check(key)
