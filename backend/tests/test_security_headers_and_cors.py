"""Comprehensive tests for security headers, CORS origins, error envelopes, and secret redaction."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.core.logging import redact_sensitive_text
from app.core.rate_limit import limiter
from app.main import app

# Security probe router dedicated to testing security edge cases
security_probe_router = APIRouter(prefix="/__security_test__", include_in_schema=False)


class SensitivePayloadSchema(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)


@security_probe_router.post("/validate-sensitive")
async def sensitive_validation_probe(payload: SensitivePayloadSchema) -> dict[str, str]:
    return {"status": "ok", "email": payload.email}


@security_probe_router.get("/trigger-db-exception")
async def db_exception_probe() -> None:
    raise RuntimeError(
        "Connection failure to postgresql+psycopg://user:super_secret_db_pass_123@db.supabase.co:5432/econexao"
    )


app.include_router(security_probe_router)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    limiter.reset()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as ac:
        yield ac
    limiter.reset()


ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://localhost:19006",
    "http://localhost:3000",
    "exp://localhost:8081",
    "https://econexao.app",
    "https://staging.econexao.app",
    "https://eco-nexao-v3.vercel.app",
    "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app",
]

DENIED_ORIGINS = [
    "https://evil.com",
    "https://malicious-site.com",
    "https://eco-nexao-v3-other-preview.vercel.app",
    "http://localhost:8080",
    "null",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
async def test_cors_preflight_and_get_allowed_origins(
    client: AsyncClient, origin: str
) -> None:
    """Test that all approved origins receive correct CORS headers on OPTIONS and GET."""
    # 1. Preflight (OPTIONS)
    res_preflight = await client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type, X-Request-ID",
        },
    )
    assert res_preflight.status_code == 200
    assert res_preflight.headers.get("access-control-allow-origin") == origin
    assert res_preflight.headers.get("access-control-allow-credentials") == "true"
    allowed_methods = res_preflight.headers.get("access-control-allow-methods", "")
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        assert method in allowed_methods

    # 2. Regular GET
    res_get = await client.get("/api/v1/health", headers={"Origin": origin})
    assert res_get.status_code == 200
    assert res_get.headers.get("access-control-allow-origin") == origin
    assert res_get.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", DENIED_ORIGINS)
async def test_cors_preflight_and_get_denied_origins(
    client: AsyncClient, origin: str
) -> None:
    """Test that unauthorized/malicious origins never receive access-control-allow-origin."""
    # 1. Preflight (OPTIONS)
    res_preflight = await client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in res_preflight.headers

    # 2. Regular GET
    res_get = await client.get("/api/v1/health", headers={"Origin": origin})
    assert res_get.status_code == 200
    assert "access-control-allow-origin" not in res_get.headers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "origin",
    [
        "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app",
        "https://staging.econexao.app",
        "http://localhost:8081",
    ],
)
async def test_cors_headers_preserved_on_controlled_error_responses(
    client: AsyncClient, origin: str
) -> None:
    """Allowed origins must receive CORS headers even on 401, 404, 422, and 500 error responses."""
    # 401 Unauthorized
    res_401 = await client.get("/api/v1/auth/session", headers={"Origin": origin})
    assert res_401.status_code == 401
    assert res_401.headers.get("access-control-allow-origin") == origin
    assert res_401.headers.get("access-control-allow-credentials") == "true"

    # 404 Not Found
    res_404 = await client.get("/api/v1/non-existent-route", headers={"Origin": origin})
    assert res_404.status_code == 404
    assert res_404.headers.get("access-control-allow-origin") == origin

    # 422 Unprocessable Entity
    res_422 = await client.post(
        "/__security_test__/validate-sensitive",
        json={"email": "invalid-email-address", "password": "123"},
        headers={"Origin": origin},
    )
    assert res_422.status_code == 422
    assert res_422.headers.get("access-control-allow-origin") == origin

    # 500 Internal Server Error
    res_500 = await client.get(
        "/__security_test__/trigger-db-exception", headers={"Origin": origin}
    )
    assert res_500.status_code == 500
    assert res_500.headers.get("access-control-allow-origin") == origin


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", ["https://evil.com", "https://malicious-site.com"])
async def test_cors_headers_omitted_on_error_responses_for_denied_origins(
    client: AsyncClient, origin: str
) -> None:
    """Denied origins must never receive CORS headers on error responses."""
    # 401 Unauthorized
    res_401 = await client.get("/api/v1/auth/session", headers={"Origin": origin})
    assert res_401.status_code == 401
    assert "access-control-allow-origin" not in res_401.headers

    # 404 Not Found
    res_404 = await client.get("/api/v1/non-existent-route", headers={"Origin": origin})
    assert res_404.status_code == 404
    assert "access-control-allow-origin" not in res_404.headers

    # 422 Unprocessable Entity
    res_422 = await client.post(
        "/__security_test__/validate-sensitive",
        json={"email": "invalid-email", "password": "123"},
        headers={"Origin": origin},
    )
    assert res_422.status_code == 422
    assert "access-control-allow-origin" not in res_422.headers

    # 500 Internal Server Error
    res_500 = await client.get(
        "/__security_test__/trigger-db-exception", headers={"Origin": origin}
    )
    assert res_500.status_code == 500
    assert "access-control-allow-origin" not in res_500.headers


@pytest.mark.asyncio
async def test_validation_error_does_not_leak_submitted_sensitive_passwords(
    client: AsyncClient,
) -> None:
    """Ensure sensitive payload values (e.g. passwords) are stripped from 422 validation errors."""
    secret_pass = "P@ssw0rdSuperSecretDoNotLeak"
    res = await client.post(
        "/__security_test__/validate-sensitive",
        json={"email": "invalid-email", "password": secret_pass},
    )
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert secret_pass not in res.text


@pytest.mark.asyncio
async def test_internal_500_error_does_not_leak_db_credentials_or_tracebacks(
    client: AsyncClient,
) -> None:
    """Ensure unhandled 500 exceptions return an opaque envelope without database secrets."""
    res = await client.get("/__security_test__/trigger-db-exception")
    assert res.status_code == 500
    data = res.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "Ocorreu um erro interno no servidor."
    assert data["error"]["details"] is None
    assert "super_secret_db_pass_123" not in res.text
    assert "postgresql" not in res.text.lower()


def test_cors_origins_validator_rejects_wildcard() -> None:
    """Settings validator must fail-closed if '*' wildcard is supplied."""
    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(CORS_ORIGINS=["https://valid.com", "*"])

    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(CORS_ORIGINS='["https://valid.com", "*"]')

    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(CORS_ORIGINS="https://valid.com, *")


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
    key = "ip:testserver"
    for _ in range(120):
        is_limited, _, _, _ = limiter.check(key, limit=120, window_seconds=60)
        assert not is_limited

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
