"""Contract tests for the isolated OSRM connector using HTTPX MockTransport."""

import httpx
import pytest

from app.connectors.osrm import Coordinate, OsrmConnector, OsrmConnectorError


def client_for(handler: httpx.MockTransport) -> httpx.AsyncClient:
    """Create a client whose requests never leave the test process."""
    return httpx.AsyncClient(transport=handler)


@pytest.mark.asyncio
async def test_calculate_route_normalizes_success_and_wire_coordinate_order() -> None:
    """The connector sends lon,lat and returns a provider-independent result."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/route/v1/driving/-54.7000000,-2.4000000;-54.8000000,-2.5000000" in str(request.url)
        assert request.url.params["geometries"] == "geojson"
        assert request.url.params["overview"] == "full"
        return httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [
                    {
                        "distance": 45229.4,
                        "duration": 3600.2,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-54.7, -2.4], [-54.8, -2.5]],
                        },
                    }
                ],
            },
        )

    async with client_for(httpx.MockTransport(handler)) as client:
        result = await OsrmConnector("https://osrm.invalid", client=client).calculate_route(
            [Coordinate(-2.4, -54.7), Coordinate(-2.5, -54.8)]
        )

    assert result.distance_m == 45229
    assert result.duration_s == 3600
    assert result.provider == "osrm"
    assert result.geometry["type"] == "LineString"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"code": "NoRoute", "routes": []},
        {"code": "Ok", "routes": []},
        {"code": "Ok", "routes": [{"distance": 1, "duration": 1}]},
        {
            "code": "Ok",
            "routes": [
                {
                    "distance": -1,
                    "duration": 1,
                    "geometry": {"type": "LineString", "coordinates": []},
                }
            ],
        },
    ],
)
async def test_calculate_route_rejects_provider_failures(payload: dict[str, object]) -> None:
    """Provider errors and incomplete payloads become one safe domain exception."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    async with client_for(transport) as client:
        connector = OsrmConnector("https://osrm.invalid", client=client)
        with pytest.raises(OsrmConnectorError):
            await connector.calculate_route([Coordinate(-2.4, -54.7), Coordinate(-2.5, -54.8)])


@pytest.mark.asyncio
async def test_calculate_route_masks_network_error() -> None:
    """Network details do not escape through the public connector exception."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("secret upstream detail", request=request)

    async with client_for(httpx.MockTransport(handler)) as client:
        connector = OsrmConnector("https://osrm.invalid", client=client)
        with pytest.raises(OsrmConnectorError, match="OSRM request failed") as raised:
            await connector.calculate_route([Coordinate(-2.4, -54.7), Coordinate(-2.5, -54.8)])
    assert "secret upstream" not in str(raised.value)


def test_coordinate_and_request_validation() -> None:
    """Invalid domain input is rejected before any request is attempted."""
    with pytest.raises(ValueError):
        Coordinate(91, 0)
    connector = OsrmConnector("https://osrm.invalid")

    async def validate() -> None:
        with pytest.raises(ValueError):
            await connector.calculate_route([Coordinate(0, 0)])
        with pytest.raises(ValueError):
            await connector.calculate_route(
                [Coordinate(0, 0), Coordinate(1, 1)], profile="spaceship"
            )

    import asyncio

    asyncio.run(validate())
