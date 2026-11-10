"""Production middleware — security headers, request identity, rate limiting."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("lumina.middleware")

LLM_PATHS = {
    "/api/ask",
    "/api/scan",
    "/api/suggestions",
    "/api/breach-clock",
    "/api/access-request",
    "/api/baa-screen",
    "/api/upload",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if request.url.path.startswith(("/docs", "/redoc", "/openapi")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; img-src 'self' data:"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window limiter with stricter budgets for LLM routes.

    X-Forwarded-For is ignored unless trust_proxy=True (set only behind a
    known reverse proxy that overwrites the header).
    """

    def __init__(
        self,
        app,
        limit_per_minute: int = 120,
        llm_limit_per_minute: int = 20,
        trust_proxy: bool = False,
    ):
        super().__init__(app)
        self.limit = max(1, limit_per_minute)
        self.llm_limit = max(1, llm_limit_per_minute)
        self.trust_proxy = trust_proxy
        self.window = 60.0
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        if self.trust_proxy:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _limit_for(self, path: str) -> int:
        if path in LLM_PATHS:
            return self.llm_limit
        return self.limit

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/ready", "/"}:
            return await call_next(request)

        key = f"{self._client_key(request)}:{request.url.path if request.url.path in LLM_PATHS else 'general'}"
        limit = self._limit_for(request.url.path)
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= limit:
                logger.warning("Rate limit exceeded for %s on %s", key, request.url.path)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Slow down and retry."},
                    headers={"Retry-After": "60"},
                )
            bucket.append(now)

        return await call_next(request)
