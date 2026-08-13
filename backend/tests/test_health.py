"""Unit and integration tests for health endpoints, CORS, request IDs, and errors."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.db.session import check_database_readiness
from app.main import app

client = TestClient(app)


probe_router = APIRouter(prefix="/__test__", include_in_schema=False)


@probe_router.get("/validation")
async def validation_probe(required_value: int) -> dict[str, int]:
    """Expose a typed parameter solely to exercise the validation handler."""
    return {"required_value": required_value}


@probe_router.get("/failure")
async def failure_probe() -> None:
    """Raise an internal error solely to exercise the safe 500 handler."""
    raise RuntimeError("database-password-must-not-leak")


app.include_router(probe_router)


def test_health_live_success() -> None:
    """Test /api/v1/health/live returns 200 and HealthStatus schema."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


def test_health_ready_success() -> None:
    """Test /api/v1/health/ready returns 200 and HealthStatus schema."""
    app.dependency_overrides[check_database_readiness] = lambda: True
    try:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "X-Request-ID" in response.headers
    finally:
        app.dependency_overrides.pop(check_database_readiness, None)


def test_health_ready_returns_safe_503_when_database_is_unavailable() -> None:
    """Test readiness fails closed without exposing connection details."""
    app.dependency_overrides[check_database_readiness] = lambda: False
    try:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "postgresql" not in response.text.lower()
        assert response.headers["X-Request-ID"] == body["request_id"]
    finally:
        app.dependency_overrides.pop(check_database_readiness, None)


def test_request_id_custom_header_propagation() -> None:
    """Test custom X-Request-ID header is preserved and echoed in response."""
    custom_id = "req_custom_12345"
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_404_error_envelope_format() -> None:
    """Test non-existent endpoint returns standardized error envelope."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "request_id" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert response.headers.get("X-Request-ID") == data["request_id"]


def test_cors_headers() -> None:
    """Test CORS headers are present for configured origins."""
    response = client.get(
        "/api/v1/health/live",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_validation_error_uses_safe_envelope_and_request_id() -> None:
    """Test 422 responses use the public envelope and propagate request IDs."""
    response = client.get("/__test__/validation", headers={"X-Request-ID": "req_validation"})

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "req_validation"
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["request_id"] == "req_validation"


def test_internal_error_does_not_leak_exception_details() -> None:
    """Test 500 responses do not reveal exception text or internal details."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    response = safe_client.get("/__test__/failure")
    body = response.json()

    assert response.status_code == 500
    assert body["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "Ocorreu um erro interno no servidor.",
        "details": None,
    }
    assert "database-password" not in response.text
    assert response.headers["X-Request-ID"] == body["request_id"]
