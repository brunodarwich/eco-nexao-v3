"""Unit tests for OSRMConnector (ECO-2314)."""

import logging
import time
from unittest.mock import AsyncMock

import httpx
import pytest

from app.connectors.osrm_connector import CircuitBreaker, OSRMConnector
from app.connectors.routing_connector import (
    Coordinate,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
    RoutingTimeoutError,
)


@pytest.mark.asyncio
async def test_osrm_connector_success_200() -> None:
    """OSRMConnector parses 200 OK response with valid route and GeoJSON LineString."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    mock_response_data = {
        "code": "Ok",
        "routes": [
            {
                "distance": 35420.5,
                "duration": 2100.2,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-54.72, -2.44],
                        [-54.80, -2.50],
                        [-54.94, -2.63],
                    ],
                },
            }
        ],
        "waypoints": [
            {"name": "Origin", "location": [-54.72, -2.44]},
            {"name": "Destination", "location": [-54.94, -2.63]},
        ],
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        200, json=mock_response_data, request=httpx.Request("GET", "http://test")
    )
    mock_client.get.return_value = mock_resp

    connector = OSRMConnector(
        base_url="http://osrm-backend:5000",
        http_client=mock_client,
    )

    result = await connector.calculate_route(origin, destination, travel_mode="DRIVE")

    assert result.provider == "osrm"
    assert result.distance_m == 35420
    assert result.duration_s == 2100
    assert result.geojson["type"] == "LineString"
    assert len(result.geojson["coordinates"]) == 3
    assert result.geojson["coordinates"][0] == [-54.72, -2.44]
    assert result.geojson["coordinates"][-1] == [-54.94, -2.63]
    assert result.bounds == {
        "min_lat": -2.63,
        "max_lat": -2.44,
        "min_lng": -54.94,
        "max_lng": -54.72,
    }


@pytest.mark.asyncio
async def test_osrm_connector_no_route_code() -> None:
    """OSRMConnector raises RoutingNoRouteFoundError when OSRM returns code: NoRoute."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    mock_response_data = {
        "code": "NoRoute",
        "message": "No route found between points",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        200, json=mock_response_data, request=httpx.Request("GET", "http://test")
    )
    mock_client.get.return_value = mock_resp

    connector = OSRMConnector(http_client=mock_client)

    with pytest.raises(RoutingNoRouteFoundError):
        await connector.calculate_route(origin, destination)


@pytest.mark.asyncio
async def test_osrm_connector_400_no_route() -> None:
    """OSRMConnector raises RoutingNoRouteFoundError when OSRM returns 400 with NoRoute."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    mock_response_data = {
        "code": "NoRoute",
        "message": "No route found",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        400, json=mock_response_data, request=httpx.Request("GET", "http://test")
    )
    mock_client.get.return_value = mock_resp

    connector = OSRMConnector(http_client=mock_client)

    with pytest.raises(RoutingNoRouteFoundError):
        await connector.calculate_route(origin, destination)


@pytest.mark.asyncio
async def test_osrm_connector_rate_limited_or_server_error() -> None:
    """OSRMConnector raises RoutingProviderUnavailableError on 429 / 500 / 503."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    for status_code in (429, 500, 503):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = httpx.Response(
            status_code,
            text="Service Unavailable",
            request=httpx.Request("GET", "http://test"),
        )
        mock_client.get.return_value = mock_resp

        connector = OSRMConnector(max_retries=1, http_client=mock_client)

        with pytest.raises(RoutingProviderUnavailableError):
            await connector.calculate_route(origin, destination)


@pytest.mark.asyncio
async def test_osrm_connector_timeout() -> None:
    """OSRMConnector exposes the typed timeout required by the HTTP contract."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.ReadTimeout("Read timed out")

    connector = OSRMConnector(timeout_seconds=3.5, max_retries=1, http_client=mock_client)

    with pytest.raises(RoutingTimeoutError):
        await connector.calculate_route(origin, destination)


@pytest.mark.asyncio
async def test_osrm_connector_grid_cache_avoids_duplicate_provider_calls() -> None:
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "code": "Ok",
            "routes": [
                {
                    "distance": 10,
                    "duration": 2,
                    "geometry": {"coordinates": [[-54.7, -2.4], [-54.9, -2.6]]},
                }
            ],
        },
        request=httpx.Request("GET", "http://test"),
    )
    connector = OSRMConnector(http_client=mock_client, cache_grid_decimals=3)
    destination = Coordinate(latitude=-2.6001, longitude=-54.9001)

    first = await connector.calculate_route(
        Coordinate(latitude=-2.4001, longitude=-54.7001), destination
    )
    second = await connector.calculate_route(
        Coordinate(latitude=-2.4002, longitude=-54.7002), destination
    )

    assert first == second
    assert mock_client.get.await_count == 1
    assert connector.metrics.cache_misses == 1
    assert connector.metrics.cache_hits == 1


@pytest.mark.asyncio
async def test_osrm_circuit_breaker_triggers_and_resets() -> None:
    """Circuit breaker opens after consecutive failures and prevents network calls until reset."""
    circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout_seconds=60.0)

    # 4 failures: still available
    for _ in range(4):
        circuit_breaker.record_failure()
        assert circuit_breaker.is_available() is True

    # 5th failure: circuit opens
    circuit_breaker.record_failure()
    assert circuit_breaker.is_available() is False
    assert circuit_breaker.state == "OPEN"

    # Connector with open circuit breaker must immediately raise without calling HTTP
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    connector = OSRMConnector(circuit_breaker=circuit_breaker, http_client=mock_client)

    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    with pytest.raises(RoutingProviderUnavailableError) as exc_info:
        await connector.calculate_route(origin, destination)

    assert "aberto" in str(exc_info.value).lower()
    assert not mock_client.get.called

    # Simulate elapsed time beyond reset_timeout_seconds
    circuit_breaker.last_failure_time = time.time() - 65.0
    assert circuit_breaker.is_available() is True
    assert circuit_breaker.state == "HALF_OPEN"

    # On successful request, state resets to CLOSED
    circuit_breaker.record_success()
    assert circuit_breaker.state == "CLOSED"
    assert circuit_breaker.consecutive_failures == 0


@pytest.mark.asyncio
async def test_osrm_connector_profile_mapping() -> None:
    """Connector maps DRIVE -> driving, WALKING -> foot, BICYCLE -> bike in request URL."""
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        200,
        json={
            "code": "Ok",
            "routes": [{"distance": 1000, "duration": 300, "geometry": {"coordinates": []}}],
        },
        request=httpx.Request("GET", "http://test"),
    )
    mock_client.get.return_value = mock_resp

    connector = OSRMConnector(base_url="http://osrm-backend:5000", http_client=mock_client)

    await connector.calculate_route(origin, destination, travel_mode="DRIVE")
    assert "/route/v1/driving/" in mock_client.get.call_args[0][0]

    await connector.calculate_route(origin, destination, travel_mode="WALKING")
    assert "/route/v1/foot/" in mock_client.get.call_args[0][0]

    await connector.calculate_route(origin, destination, travel_mode="BICYCLE")
    assert "/route/v1/bike/" in mock_client.get.call_args[0][0]


@pytest.mark.asyncio
async def test_osrm_connector_sanitized_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Logs must not leak coordinate values in INFO / WARNING / ERROR."""
    origin = Coordinate(latitude=-2.441234, longitude=-54.729876)
    destination = Coordinate(latitude=-2.631234, longitude=-54.949876)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        200,
        json={
            "code": "Ok",
            "routes": [
                {
                    "distance": 1500,
                    "duration": 200,
                    "geometry": {
                        "coordinates": [
                            [-54.729876, -2.441234],
                            [-54.949876, -2.631234],
                        ]
                    },
                }
            ],
        },
        request=httpx.Request("GET", "http://test"),
    )
    mock_client.get.return_value = mock_resp

    connector = OSRMConnector(http_client=mock_client)

    with caplog.at_level(logging.INFO):
        await connector.calculate_route(origin, destination, travel_mode="DRIVE")

    for record in caplog.records:
        message = record.getMessage()
        assert "-2.441234" not in message
        assert "-54.729876" not in message
        assert "-2.631234" not in message
        assert "-54.949876" not in message
