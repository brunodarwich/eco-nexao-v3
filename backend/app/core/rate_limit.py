"""In-memory rate limiter middleware and utilities with sliding-window accounting."""

import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import request_id_ctx_var


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter in memory."""

    def __init__(self, default_limit: int = 120, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_pruned = time.time()

    def _prune_expired(self, now: float) -> None:
        """Prune entries older than the window to prevent unbounded memory growth."""
        if now - self._last_pruned < 30:
            return
        cutoff = now - self.window_seconds
        expired_keys = [
            k
            for k, timestamps in self._history.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for k in expired_keys:
            self._history.pop(k, None)
        self._last_pruned = now

    def check(
        self, key: str, limit: int | None = None, window_seconds: int | None = None
    ) -> tuple[bool, int, int, int]:
        """Check if request is allowed.

        Returns (is_limited, limit, remaining, reset_seconds).
        """
        now = time.time()
        self._prune_expired(now)

        active_limit = limit if limit is not None else self.default_limit
        active_window = window_seconds if window_seconds is not None else self.window_seconds
        cutoff = now - active_window

        timestamps = [ts for ts in self._history[key] if ts > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= active_limit:
            oldest = timestamps[0]
            reset_seconds = max(1, int(oldest + active_window - now))
            return True, active_limit, 0, reset_seconds

        timestamps.append(now)
        remaining = max(0, active_limit - len(timestamps))
        reset_seconds = active_window
        return False, active_limit, remaining, reset_seconds

    def reset(self) -> None:
        """Clear all stored rate limit history."""
        self._history.clear()
        self._last_pruned = time.time()


limiter = SlidingWindowRateLimiter()


def get_client_identifier(request: Request) -> str:
    """Extract client identity from Authorization header sub/token or fallback to client IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return f"auth:{auth_header[7:32]}"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


async def rate_limit_middleware(request: Request, call_next: Any) -> Response:
    """Middleware enforcing sliding window rate limits with standard headers."""
    if not getattr(settings, "RATE_LIMIT_ENABLED", True):
        res: Response = await call_next(request)
        return res

    # Skip health and well-known checks from rate limiting
    path = request.url.path
    if (
        path.startswith("/api/v1/health")
        or path.startswith("/.well-known")
        or path in ("/docs", "/redoc", "/openapi.json")
    ):
        res_skipped: Response = await call_next(request)
        return res_skipped

    client_id = get_client_identifier(request)
    limit = getattr(settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 120)
    is_limited, limit_val, remaining, reset_sec = limiter.check(
        client_id, limit=limit, window_seconds=60
    )

    if is_limited:
        req_id = (
            getattr(request.state, "request_id", None)
            or request_id_ctx_var.get()
            or "unknown"
        )
        headers = {
            "X-RateLimit-Limit": str(limit_val),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_sec),
            "Retry-After": str(reset_sec),
            "X-Request-ID": req_id,
        }
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Limite de requisições excedido. Tente novamente mais tarde.",
                    "details": {"retry_after_seconds": reset_sec},
                },
                "request_id": req_id,
            },
            headers=headers,
        )

    response: Response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit_val)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_sec)
    return response
