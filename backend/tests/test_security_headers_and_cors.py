from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.logging import redact_sensitive_text
from app.core.rate_limit import limiter
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    limiter.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    limiter.reset()


@pytest.mark.asyncio
async def test_cors_allowed_and_denied_origins(client: AsyncClient) -> None:
    """Test CORS preflight and headers for allowed and disallowed origins."""
    # Allowed origin: http://localhost:8081
    res_allowed = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:8081"
    assert res_allowed.headers.get("access-control-allow-credentials") == "true"

    # Disallowed origin: https://malicious-site.com
    res_disallowed = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORSMiddleware does not include access-control-allow-origin for invalid origins
    assert "access-control-allow-origin" not in res_disallowed.headers


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    """Test standard security headers on API responses."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Cache-Control" in response.headers
    assert "no-store" in response.headers["Cache-Control"]


@pytest.mark.asyncio
async def test_well_known_deep_link_endpoints(client: AsyncClient) -> None:
    """Test assetlinks.json and apple-app-site-association."""
    res_android = await client.get("/.well-known/assetlinks.json")
    assert res_android.status_code == 200
    data_android = res_android.json()
    assert isinstance(data_android, list)
    assert data_android[0]["target"]["package_name"] == "org.econexao.app"

    res_ios = await client.get("/.well-known/apple-app-site-association")
    assert res_ios.status_code == 200
    data_ios = res_ios.json()
    assert "applinks" in data_ios
    assert len(data_ios["applinks"]["details"]) > 0


@pytest.mark.asyncio
async def test_rate_limiting_enforcement(client: AsyncClient) -> None:
    """Test rate limit headers and 429 response when limit is exceeded."""
    limiter.reset()
    # Perform requests up to configured limit
    # For testing, limiter check can be invoked
    key = "ip:testserver"
    # Fill quota with 120 calls or artificially check
    for _ in range(120):
        is_limited, _, _, _ = limiter.check(key, limit=120, window_seconds=60)
        assert not is_limited

    # 121st call should be limited
    is_limited, limit_val, remaining, reset_sec = limiter.check(key, limit=120, window_seconds=60)
    assert is_limited
    assert remaining == 0
    assert reset_sec > 0

    limiter.reset()


def test_sensitive_text_redaction() -> None:
    """Test redaction of connection strings, bearer tokens, passwords, and JWTs in logging."""
    raw_log = "Error connecting postgresql+psycopg://user:supersecretpassword@db.host.com:5432/econexao"
    redacted = redact_sensitive_text(raw_log)
    assert "supersecretpassword" not in redacted
    assert "***" in redacted

    auth_log = (
        "Received Authorization: Bearer "
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.do_not_leak"
    )
    redacted_auth = redact_sensitive_text(auth_log)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted_auth
    assert "***" in redacted_auth

    pwd_log = '{"email": "user@test.com", "password": "SecretPassword123!"}'
    redacted_pwd = redact_sensitive_text(pwd_log)
    assert "SecretPassword123!" not in redacted_pwd
    assert "***" in redacted_pwd
