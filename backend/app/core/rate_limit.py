import ipaddress
import re
import threading
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import request_id_ctx_var
from app.core.security import verify_supabase_jwt


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter in memory."""

    def __init__(self, default_limit: int = 120, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_pruned = time.time()
        self._lock = threading.Lock()

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
        with self._lock:
            return self._check_locked(key, limit, window_seconds)

    def _check_locked(
        self, key: str, limit: int | None, window_seconds: int | None
    ) -> tuple[bool, int, int, int]:
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
        with self._lock:
            self._history.clear()
            self._last_pruned = time.time()


limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract validated client IP, trusting X-Forwarded-For only from configured proxies."""
    client_host = request.client.host if request.client else "unknown"
    trusted_proxies = getattr(settings, "TRUSTED_PROXIES", ["127.0.0.1", "::1", "testclient"])

    is_trusted = client_host in trusted_proxies
    if not is_trusted:
        try:
            client_addr = ipaddress.ip_address(client_host)
            for proxy in trusted_proxies:
                try:
                    if "/" in proxy and client_addr in ipaddress.ip_network(proxy, strict=False):
                        is_trusted = True
                        break
                except ValueError:
                    continue
        except ValueError:
            pass

    if is_trusted:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Parse reverse-proxy chain from left to right; take first valid IP
            ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
            for candidate in ips:
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    continue

    return client_host


def get_client_identifier(request: Request) -> str:
    """Extract validated user identity from JWT or fallback safely to verified client IP."""
    client_ip = get_client_ip(request)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()
        if raw_token:
            try:
                user = verify_supabase_jwt(raw_token)
                if not user.is_anonymous:
                    return f"user:{user.id}"
                # Anonymous authenticated user tied to client IP to prevent token-rotation bypass
                return f"ip:{client_ip}"
            except Exception:
                # Invalid, expired, tampered or random Bearer tokens must not create new buckets
                return f"ip:{client_ip}"

    return f"ip:{client_ip}"


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
    is_routing_preview = request.method == "POST" and re.fullmatch(
        r"/api/v1/routes/[^/]+/preview", path
    )
    limit = (
        settings.DYNAMIC_ROUTING_RATE_LIMIT_PER_MINUTE
        if is_routing_preview
        else settings.RATE_LIMIT_REQUESTS_PER_MINUTE
    )
    bucket = "routing-preview" if is_routing_preview else "general"
    is_limited, limit_val, remaining, reset_sec = limiter.check(
        f"{bucket}:{client_id}", limit=limit, window_seconds=60
    )

    if is_limited:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx_var.get() or "unknown"
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
