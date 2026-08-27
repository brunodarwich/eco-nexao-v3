"""Unit tests for the staging smoke verification script (ECO-2002)."""

from typing import Any
from unittest.mock import patch

import pytest

from scripts.staging_smoke import (
    DEFAULT_REQUIRED_ORIGINS,
    DEFAULT_STAGING_HOST,
    FORBIDDEN_TEST_ORIGIN,
    check_cors_denied_origin,
    check_cors_preflight_and_get,
    run_smoke_test,
    validate_map_payload,
    validate_staging_target,
)


def _valid_map_payload(route_id: str, origin_id: str) -> dict[str, Any]:
    return {
        "data": {
            "route_id": route_id,
            "selected_origin_id": origin_id,
            "bounds": {
                "min_lat": -2.6,
                "max_lat": -2.4,
                "min_lng": -55.0,
                "max_lng": -54.8,
            },
            "pins": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "actor_id": "22222222-2222-2222-2222-222222222222",
                    "name": "Restaurante da Praia",
                    "category_slug": "alimentacao",
                    "category_label": "Alimentação",
                    "color": "#D97706",
                    "icon": "utensils",
                    "latitude": -2.51,
                    "longitude": -54.91,
                    "layer": "route_corridor",
                },
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "actor_id": "44444444-4444-4444-4444-444444444444",
                    "name": "Pousada do Sol",
                    "category_slug": "hospedagem",
                    "category_label": "Hospedagem",
                    "color": "#2563EB",
                    "icon": "bed",
                    "latitude": -2.52,
                    "longitude": -54.92,
                    "layer": "route_corridor",
                },
            ],
            "legend": [
                {
                    "category_slug": "alimentacao",
                    "label": "Alimentação",
                    "color": "#D97706",
                    "icon": "utensils",
                    "count": 1,
                    "sort_order": 1,
                },
                {
                    "category_slug": "hospedagem",
                    "label": "Hospedagem",
                    "color": "#2563EB",
                    "icon": "bed",
                    "count": 1,
                    "sort_order": 2,
                },
            ],
        }
    }


def test_validate_staging_target_accepts_valid_default_staging_host() -> None:
    url = f"https://{DEFAULT_STAGING_HOST}"
    assert validate_staging_target(url) == f"https://{DEFAULT_STAGING_HOST}"
    assert validate_staging_target(f"{url}/") == f"https://{DEFAULT_STAGING_HOST}"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://econexao-backend-staging.onrender.com",
        "https://eco-nexao-v3.onrender.com",
        "https://econexao.app",
        "https://api.econexao.app",
        "https://prod-backend.onrender.com",
    ],
)
def test_validate_staging_target_rejects_forbidden_and_insecure_targets(invalid_url: str) -> None:
    with pytest.raises(ValueError):
        validate_staging_target(invalid_url)


def test_validate_staging_target_requires_confirmation() -> None:
    with pytest.raises(ValueError, match="confirmation"):
        validate_staging_target(f"https://{DEFAULT_STAGING_HOST}", confirm_staging=False)


def test_validate_map_payload_passes_for_canonical_contract() -> None:
    route_id = "55555555-5555-5555-5555-555555555555"
    origin_id = "66666666-6666-6666-6666-666666666666"
    payload = _valid_map_payload(route_id, origin_id)
    errors = validate_map_payload(payload, route_id, origin_id)
    assert errors == []


def test_validate_map_payload_detects_route_and_origin_mismatches() -> None:
    payload = _valid_map_payload("id-1", "origin-1")
    errors = validate_map_payload(payload, "id-2", "origin-2")
    assert any("route_id mismatch" in e for e in errors)
    assert any("selected_origin_id mismatch" in e for e in errors)


def test_validate_map_payload_detects_invalid_hex_color_and_icon() -> None:
    route_id = "id-1"
    origin_id = "origin-1"
    payload = _valid_map_payload(route_id, origin_id)
    payload["data"]["pins"][0]["color"] = "invalid-color"
    payload["data"]["pins"][0]["icon"] = "invalid-icon"
    payload["data"]["pins"][0]["layer"] = "invalid-layer"

    errors = validate_map_payload(payload, route_id, origin_id)
    assert any("invalid hex color" in e for e in errors)
    assert any("not in allowed icons" in e for e in errors)
    assert any("not in allowed layers" in e for e in errors)


def test_validate_map_payload_detects_legend_reconciliation_mismatch() -> None:
    route_id = "id-1"
    origin_id = "origin-1"
    payload = _valid_map_payload(route_id, origin_id)
    payload["data"]["legend"][0]["count"] = 99  # Mismatch with pins count 1

    errors = validate_map_payload(payload, route_id, origin_id)
    assert any(
        "does not match pin count" in e or "does not match legend count" in e
        for e in errors
    )


def test_validate_map_payload_detects_missing_pins_or_bounds() -> None:
    route_id = "id-1"
    origin_id = "origin-1"
    payload = _valid_map_payload(route_id, origin_id)
    payload["data"]["pins"] = []

    errors = validate_map_payload(payload, route_id, origin_id)
    assert any("Pin count out of bounds" in e for e in errors)


def test_check_cors_preflight_and_get_success() -> None:
    origin = "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"

    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        return True, 200, {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }, {"status": "ok"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_preflight_and_get("https://test-host", origin)
        assert ok is True
        assert "passed" in msg


def test_check_cors_preflight_and_get_fails_on_missing_or_mismatched_origin() -> None:
    origin = "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"

    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        # Omit Access-Control-Allow-Origin
        return True, 200, {}, {"status": "ok"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_preflight_and_get("https://test-host", origin)
        assert ok is False
        assert "mismatch" in msg


def test_check_cors_denied_origin_success() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        if method == "OPTIONS":
            return False, 400, {}, {"error": "Disallowed CORS origin"}
        return True, 200, {}, {"status": "ok"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_denied_origin("https://test-host", FORBIDDEN_TEST_ORIGIN)
        assert ok is True
        assert "rejected" in msg


def test_check_cors_denied_origin_fails_when_header_erroneously_returned() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        return False, 400, {"Access-Control-Allow-Origin": "https://evil.com"}, {"status": "ok"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_denied_origin("https://test-host", "https://evil.com")
        assert ok is False
        assert "erroneously" in msg


def test_check_cors_denied_origin_fails_on_timeout_and_transport_error() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        return False, 0, {}, {"error": "timed out"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_denied_origin("https://test-host", FORBIDDEN_TEST_ORIGIN)
        assert ok is False
        assert "transport error/timeout" in msg


def test_check_cors_denied_origin_fails_on_5xx_server_error() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        return False, 502, {}, {"error": "bad gateway"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_denied_origin("https://test-host", FORBIDDEN_TEST_ORIGIN)
        assert ok is False
        assert "5xx error" in msg


def test_check_cors_denied_origin_fails_on_unexpected_status_code() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        # OPTIONS returns 200 without CORS header instead of 400/403
        if method == "OPTIONS":
            return True, 200, {}, {"status": "ok"}
        return True, 200, {}, {"status": "ok"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_denied_origin("https://test-host", FORBIDDEN_TEST_ORIGIN)
        assert ok is False
        assert "expected HTTP 400/403" in msg


def test_check_cors_error_responses_success() -> None:
    origin = "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"

    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        resp_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "X-Request-ID": "req_test",
        }
        if url.endswith("/api/v1/auth/session"):
            return False, 401, resp_headers, {"error": "unauthorized"}
        if url.endswith("/api/v1/smoke-probe-not-found-endpoint"):
            return False, 404, resp_headers, {"error": "not found"}
        if url.endswith("/api/v1/auth/verify"):
            return False, 422, resp_headers, {"error": "validation"}
        if url.endswith("/api/v1/health/error-probe"):
            return False, 500, resp_headers, {"error": "internal"}
        return False, 404, {}, {}

    from scripts.staging_smoke import check_cors_error_responses

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_error_responses("https://test-host", origin)
        assert ok is True
        assert "verified on 401, 404, 422, and 500" in msg


def test_check_cors_error_responses_fails_on_missing_cors_header() -> None:
    origin = "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"

    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        # 401 response without CORS header
        if url.endswith("/api/v1/auth/session"):
            return False, 401, {}, {"error": "unauthorized"}
        return False, 404, {}, {}

    from scripts.staging_smoke import check_cors_error_responses

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        ok, msg = check_cors_error_responses("https://test-host", origin)
        assert ok is False
        assert "missing or mismatched" in msg


def test_run_smoke_test_complete_success() -> None:
    route_id = "55555555-5555-5555-5555-555555555555"
    origin_id = "66666666-6666-6666-6666-666666666666"

    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        req_origin = (headers or {}).get("Origin", "")
        resp_headers: dict[str, str] = {}
        if req_origin in DEFAULT_REQUIRED_ORIGINS:
            resp_headers["Access-Control-Allow-Origin"] = req_origin
            resp_headers["Access-Control-Allow-Credentials"] = "true"

        if url.endswith("/api/v1/health") and method == "OPTIONS":
            if req_origin in DEFAULT_REQUIRED_ORIGINS:
                return True, 200, resp_headers, {}
            return False, 400, {}, {"error": "Disallowed CORS origin"}
        if url.endswith("/api/v1/health/live"):
            resp_headers["X-Commit-SHA"] = "abcdef12345"
            return (
                True,
                200,
                resp_headers,
                {"status": "ok", "version": "1.0.0", "commit_sha": "abcdef12345"},
            )
        if url.endswith("/api/v1/auth/session"):
            return False, 401, resp_headers, {"error": "unauthorized"}
        if url.endswith("/api/v1/smoke-probe-not-found-endpoint"):
            return False, 404, resp_headers, {"error": "not found"}
        if url.endswith("/api/v1/auth/verify"):
            return False, 422, resp_headers, {"error": "validation"}
        if url.endswith("/api/v1/health/error-probe"):
            return False, 500, resp_headers, {"error": "internal"}
        if url.endswith("/api/v1/health/ready"):
            return (
                True,
                200,
                {},
                {"status": "ok", "version": "1.0.0", "database": {"status": "ok", "postgis": True}},
            )
        if url.endswith("/api/v1/regions"):
            return (
                True,
                200,
                {},
                {"data": [{"id": "reg-1", "slug": "alter-do-chao", "name": "Alter do Chão"}]},
            )
        if url.endswith("/api/v1/routes"):
            return (
                True,
                200,
                {},
                {"data": [{"id": route_id, "slug": "rota-pindobal", "title": "Rota Pindobal"}]},
            )
        if url.endswith(f"/api/v1/routes/{route_id}/origins"):
            return (
                True,
                200,
                {},
                {"data": [{"id": origin_id, "title": "Orla de Alter do Chão"}]},
            )
        if f"/api/v1/routes/{route_id}/map" in url:
            return True, 200, {}, _valid_map_payload(route_id, origin_id)
        return False, 404, {}, {"error": "not found"}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        exit_code = run_smoke_test(
            base_url=f"https://{DEFAULT_STAGING_HOST}",
            expected_commit="abcdef12345",
            max_retries=2,
            delay_seconds=0.01,
        )
        assert exit_code == 0


def test_run_smoke_test_fails_closed_on_unready_database() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        if url.endswith("/api/v1/health/live"):
            return True, 200, {}, {"status": "ok", "version": "1.0.0"}
        if url.endswith("/api/v1/health/ready"):
            return (
                True,
                200,
                {},
                {"status": "ok", "database": {"status": "unknown", "postgis": False}},
            )
        return False, 404, {}, {}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        exit_code = run_smoke_test(
            base_url=f"https://{DEFAULT_STAGING_HOST}",
            max_retries=1,
            delay_seconds=0.01,
        )
        assert exit_code == 1


def test_run_smoke_test_fails_closed_on_cors_rejection() -> None:
    def mock_check_endpoint(
        url: str,
        timeout_seconds: float = 10.0,
        headers: dict[str, str] | None = None,
        method: str | None = None,
        body: bytes | None = None,
    ) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
        if url.endswith("/api/v1/health/live"):
            return True, 200, {}, {"status": "ok", "version": "1.0.0"}
        if url.endswith("/api/v1/health/ready"):
            return (
                True,
                200,
                {},
                {"status": "ok", "database": {"status": "ok", "postgis": True}},
            )
        # Missing CORS allow-origin on OPTIONS preflight
        if url.endswith("/api/v1/health") and method == "OPTIONS":
            return True, 200, {}, {}
        return False, 404, {}, {}

    with patch("scripts.staging_smoke.check_endpoint", side_effect=mock_check_endpoint):
        exit_code = run_smoke_test(
            base_url=f"https://{DEFAULT_STAGING_HOST}",
            max_retries=1,
            delay_seconds=0.01,
        )
        assert exit_code == 1

