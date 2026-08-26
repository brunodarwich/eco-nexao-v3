"""Offline contract and guard tests for Google Routes API v2 (ECO-2314)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.connectors.google_routes_connector import (
    GOOGLE_ROUTES_FIELD_MASK,
    CircuitBreaker,
    DatabaseMonthlyUsageGuard,
    GoogleRoutesConnector,
    InMemoryMonthlyUsageGuard,
    MonthlyUsageGuard,
    _decode_polyline,
    _duration_seconds,
)
from app.connectors.routing_connector import (
    Coordinate,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
    RoutingQuotaExceededError,
    RoutingTimeoutError,
)


def _response(status: int = 200, polyline: str = "_p~iF~ps|U_ulLnnqC_mqNvxq`@") -> httpx.Response:
    request = httpx.Request("POST", "https://routes.googleapis.com/directions/v2:computeRoutes")
    if status == 200:
        return httpx.Response(
            200,
            request=request,
            json={
                "routes": [
                    {
                        "distanceMeters": 1234,
                        "duration": "321s",
                        "polyline": {"encodedPolyline": polyline},
                    }
                ]
            },
        )
    return httpx.Response(status, request=request, json={"error": {"message": "redacted"}})


@pytest.mark.asyncio
async def test_google_routes_uses_post_minimal_mask_and_no_coordinate_url() -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.return_value = _response()
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=0,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )

    result = await connector.calculate_route(
        Coordinate(-2.44, -54.72), Coordinate(-2.63, -54.94)
    )

    assert result.provider == "google_routes"
    assert result.distance_m == 1234
    assert result.duration_s == 321
    assert result.geojson["type"] == "LineString"
    url = client.post.await_args.args[0]
    kwargs = client.post.await_args.kwargs
    assert "-2.44" not in url and "-54.72" not in url
    assert kwargs["headers"]["X-Goog-FieldMask"] == GOOGLE_ROUTES_FIELD_MASK
    assert kwargs["json"]["routingPreference"] == "TRAFFIC_UNAWARE"
    assert kwargs["json"]["computeAlternativeRoutes"] is False


@pytest.mark.asyncio
async def test_google_routes_rejects_missing_key_or_invalid_mode() -> None:
    connector = GoogleRoutesConnector(
        "", monthly_guard=InMemoryMonthlyUsageGuard(limit=10)
    )
    with pytest.raises(RoutingProviderUnavailableError, match="Credencial"):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))

    connector_valid = GoogleRoutesConnector(
        "test-key", monthly_guard=InMemoryMonthlyUsageGuard(limit=10)
    )
    with pytest.raises(RoutingNoRouteFoundError, match="Modo de viagem"):
        await connector_valid.calculate_route(
            Coordinate(0, 0), Coordinate(1, 1), travel_mode="WALK"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404, 422])
async def test_google_routes_does_not_retry_client_errors(status: int) -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.return_value = _response(status)
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=2,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )
    with pytest.raises(RoutingNoRouteFoundError):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))
    assert client.post.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 500, 503])
async def test_google_routes_retries_transient_errors_only_with_bound(status: int) -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.return_value = _response(status)
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=1,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )
    with pytest.raises(RoutingProviderUnavailableError):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))
    assert client.post.await_count == 2
    assert connector.metrics.retries == 1


@pytest.mark.asyncio
async def test_google_routes_timeout_is_typed_and_bounded() -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.side_effect = httpx.ReadTimeout("timeout")
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=1,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )
    with pytest.raises(RoutingTimeoutError):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))
    assert client.post.await_count == 2


@pytest.mark.asyncio
async def test_google_routes_request_error_retries_and_fails_typed() -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.side_effect = httpx.ConnectError("connection refused")
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=1,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )
    with pytest.raises(RoutingProviderUnavailableError):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))
    assert client.post.await_count == 2
    assert connector.metrics.failures == 1


@pytest.mark.asyncio
async def test_google_routes_malformed_response_handling() -> None:
    client = AsyncMock(spec=httpx.AsyncClient)
    # Response with missing routes
    req = httpx.Request("POST", "https://routes.googleapis.com/directions/v2:computeRoutes")
    client.post.return_value = httpx.Response(200, request=req, json={"routes": []})
    connector = GoogleRoutesConnector(
        "test-key",
        http_client=client,
        max_retries=0,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=100),
    )
    with pytest.raises(RoutingProviderUnavailableError, match="Resposta inválida"):
        await connector.calculate_route(Coordinate(0, 0), Coordinate(1, 1))


@pytest.mark.asyncio
async def test_monthly_guard_blocks_before_paid_usage_and_emits_one_alert(
    caplog: pytest.LogCaptureFixture,
) -> None:
    guard = MonthlyUsageGuard(limit=3, alert_at=2)
    await guard.reserve()
    await guard.reserve()
    await guard.reserve()
    with pytest.raises(RoutingQuotaExceededError):
        await guard.reserve()
    assert guard.calls == 3
    assert caplog.text.count("monthly usage alert") == 1


@pytest.mark.asyncio
async def test_in_memory_monthly_guard_month_rollover() -> None:
    guard = InMemoryMonthlyUsageGuard(limit=2, alert_at=1)
    guard._month = "2026-01"
    await guard.reserve()
    assert guard.calls == 1
    # Rollover to another month
    guard._month = "2026-02"
    # When reserve is called with current month, it resets
    count = await guard.reserve()
    assert count == 1


@pytest.mark.asyncio
async def test_database_monthly_usage_guard_concurrency_and_atomicity(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Simulate concurrent workers reserving slots against DatabaseMonthlyUsageGuard."""
    # Build an atomic in-memory mock session factory simulating Postgres row locking
    stored_count = 0
    lock = asyncio.Lock()

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def begin(self):
            return self

        async def execute(self, statement, params):
            nonlocal stored_count
            async with lock:
                stored_count += 1
                result_mock = MagicMock()
                result_mock.scalar_one.return_value = stored_count
                return result_mock

    def fake_session_factory():
        return FakeSession()

    guard = DatabaseMonthlyUsageGuard(
        session_factory=fake_session_factory,
        limit=15,
        alert_at=10,
    )

    # 15 concurrent reservations
    results = await asyncio.gather(*[guard.reserve() for _ in range(15)])
    assert sorted(results) == list(range(1, 16))
    assert guard.calls == 15
    assert caplog.text.count("monthly usage alert") == 1

    # 16th reservation exceeds quota limit
    with pytest.raises(RoutingQuotaExceededError):
        await guard.reserve()


def test_circuit_breaker_state_is_shared_by_connector_instance() -> None:
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=0.05)
    connector = GoogleRoutesConnector(
        "test-key",
        circuit_breaker=breaker,
        monthly_guard=InMemoryMonthlyUsageGuard(limit=10),
    )
    assert breaker.is_available() is True
    breaker.record_failure()
    assert breaker.is_available() is True
    breaker.record_failure()
    assert breaker.is_available() is False
    assert connector.circuit_breaker.is_available() is False

    # After reset timeout, transitions to HALF_OPEN
    import time
    time.sleep(0.06)
    assert breaker.is_available() is True
    assert breaker.state == "HALF_OPEN"
    breaker.record_success()
    assert breaker.state == "CLOSED"
    assert breaker.consecutive_failures == 0


def test_decode_polyline_and_duration_helpers() -> None:
    # Valid polyline
    coords = _decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    assert len(coords) >= 2
    assert isinstance(coords[0][0], float)
    assert isinstance(coords[0][1], float)

    # Truncated / malformed polyline
    with pytest.raises(ValueError, match="invalid encoded polyline"):
        _decode_polyline("~")

    # Duration parsing
    assert _duration_seconds("120s") == 120
    assert _duration_seconds("0s") == 0
    assert _duration_seconds("45.4s") == 45
    with pytest.raises(ValueError, match="invalid duration"):
        _duration_seconds("120min")
