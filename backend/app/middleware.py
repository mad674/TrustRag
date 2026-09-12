from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import settings

try:
    import redis
except ImportError:
    redis = None


class RequestProtectionMiddleware(BaseHTTPMiddleware):
    """Adds request correlation and a bounded per-client sliding-window limiter."""

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._redis = None
        if settings.REDIS_URL and redis is not None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _client_key(self, request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def _allowed(self, key: str) -> bool:
        if self._redis is not None:
            bucket_key = f"trustrag:rate:{key}"
            try:
                count = self._redis.incr(bucket_key)
                if count == 1:
                    self._redis.expire(bucket_key, settings.RATE_LIMIT_WINDOW_SECONDS)
                return count <= settings.RATE_LIMIT_REQUESTS
            except redis.RedisError:
                # A cache outage must not take the API down; use the local limiter.
                self._redis = None
        now = time.monotonic()
        cutoff = now - settings.RATE_LIMIT_WINDOW_SECONDS
        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
                return False
            bucket.append(now)
            if len(self._requests) > 5000:
                self._requests = defaultdict(deque, {key: bucket})
            return True

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        if not self._allowed(self._client_key(request)):
            response = JSONResponse(
                {"detail": "Rate limit exceeded. Please retry later.", "request_id": request_id},
                status_code=429,
                headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW_SECONDS)},
            )
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        return response
