"""Tests for rate limiting, client identification, and trusted proxy boundary (ECO-2314)."""

import time
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import (
    SlidingWindowRateLimiter,
    get_client_identifier,
    get_client_ip,
    limiter,
)
from app.core.security import AuthenticatedUser
from app.main import app
from app.schemas.envelopes import (
    RouteBoundsSchema,
    RoutePreviewDataSchema,
    RoutePreviewEnvelope,
)
from app.services.dependencies import get_routing_service
from app.services.routing_service import RoutingService


def _build_request(
    client_host: str = "192.168.1.50",
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode("latin-1"), v.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/routes",
        "headers": raw_headers,
        "client": (client_host, 12345),
    }
    return Request(scope)


def test_sliding_window_rate_limiter_basic_and_reset() -> None:
    limiter_inst = SlidingWindowRateLimiter(default_limit=2, window_seconds=60)
    is_lim, limit_val, remaining, reset_sec = limiter_inst.check("k1")
    assert not is_lim
    assert remaining == 1

    is_lim, limit_val, remaining, reset_sec = limiter_inst.check("k1")
    assert not is_lim
    assert remaining == 0

    is_lim, limit_val, remaining, reset_sec = limiter_inst.check("k1")
    assert is_lim
    assert remaining == 0
    assert reset_sec > 0

    limiter_inst.reset()
    is_lim, limit_val, remaining, reset_sec = limiter_inst.check("k1")
    assert not is_lim
    assert remaining == 1


def test_sliding_window_rate_limiter_pruning() -> None:
    limiter_inst = SlidingWindowRateLimiter(default_limit=5, window_seconds=1)
    limiter_inst.check("k1")
    limiter_inst._last_pruned = time.time() - 35
    time.sleep(1.05)
    limiter_inst.check("k2")
    assert "k1" not in limiter_inst._history


def test_get_client_ip_untrusted_client_ignores_x_forwarded_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["127.0.0.1", "::1"])
    # Client host is untrusted direct IP: 203.0.113.195
    req = _build_request(
        client_host="203.0.113.195",
        headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"},
    )
    ip = get_client_ip(req)
    assert ip == "203.0.113.195"


def test_get_client_ip_trusted_proxy_extracts_client_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["127.0.0.1", "::1"])
    req = _build_request(
        client_host="127.0.0.1",
        headers={"X-Forwarded-For": "203.0.113.50, 10.0.0.1"},
    )
    ip = get_client_ip(req)
    assert ip == "203.0.113.50"


def test_get_client_ip_cidr_trusted_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["10.0.0.0/8"])
    req = _build_request(
        client_host="10.1.2.3",
        headers={"X-Forwarded-For": "198.51.100.22"},
    )
    ip = get_client_ip(req)
    assert ip == "198.51.100.22"


def test_get_client_identifier_permanent_user_uses_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email="test@example.com",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr("app.core.rate_limit.verify_supabase_jwt", lambda tok: mock_user)

    req = _build_request(
        client_host="203.0.113.10",
        headers={"Authorization": "Bearer valid_permanent_jwt"},
    )
    ident = get_client_identifier(req)
    assert ident == f"user:{user_id}"


def test_get_client_identifier_anonymous_user_is_tied_to_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email=None,
        is_anonymous=True,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr("app.core.rate_limit.verify_supabase_jwt", lambda tok: mock_user)

    req = _build_request(
        client_host="203.0.113.10",
        headers={"Authorization": "Bearer anonymous_jwt"},
    )
    ident = get_client_identifier(req)
    assert ident == "ip:203.0.113.10"


def test_get_client_identifier_invalid_bearer_falls_back_to_ip() -> None:
    req = _build_request(
        client_host="203.0.113.10",
        headers={"Authorization": "Bearer forged_random_token_123"},
    )
    ident = get_client_identifier(req)
    assert ident == "ip:203.0.113.10"


def test_get_client_identifier_no_auth_header() -> None:
    req = _build_request(client_host="203.0.113.10")
    ident = get_client_identifier(req)
    assert ident == "ip:203.0.113.10"


def test_preview_endpoint_rejects_rate_limit_bypass_via_random_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies that rotating arbitrary Bearer strings does NOT bypass the 10 req/min limit."""
    monkeypatch.setattr(settings, "ENABLE_DYNAMIC_ROUTING", True)
    monkeypatch.setattr(settings, "APP_ENV", "test")
    limiter.reset()

    route_id = uuid.uuid4()
    mock_service = MagicMock(spec=RoutingService)
    mock_envelope = RoutePreviewEnvelope(
        data=RoutePreviewDataSchema(
            route_id=route_id,
            provider="fake_deterministic",
            distance_m=1000,
            duration_s=100,
            geojson={"type": "LineString", "coordinates": [[-54.7, -2.4], [-54.8, -2.5]]},
            bounds=RouteBoundsSchema(min_lat=-2.5, max_lat=-2.4, min_lng=-54.8, max_lng=-54.7),
        )
    )

    async def fake_preview(*args, **kwargs):
        return mock_envelope

    mock_service.preview_route.side_effect = fake_preview
    app.dependency_overrides[get_routing_service] = lambda: mock_service

    try:
        with TestClient(app) as client:
            responses = []
            for i in range(12):
                # Send a different random bearer token on every request
                token = f"random_token_attempt_{i}_{uuid.uuid4()}"
                res = client.post(
                    f"/api/v1/routes/{route_id}/preview",
                    json={"latitude": -2.44, "longitude": -54.70, "travel_mode": "DRIVE"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                responses.append(res)

            # First 10 succeed
            assert [r.status_code for r in responses[:10]] == [200] * 10
            # 11th and 12th fail with 429
            assert responses[10].status_code == 429
            assert responses[11].status_code == 429
            assert responses[10].json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert "X-RateLimit-Limit" in responses[10].headers
            assert "Retry-After" in responses[10].headers
    finally:
        app.dependency_overrides.clear()
        limiter.reset()
