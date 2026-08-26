import logging
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.connectors.fake_routing_connector import FakeRoutingConnector
from app.connectors.routing_connector import (
    Coordinate,
    RouteCalculationResult,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
    RoutingTimeoutError,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.main import app
from app.schemas.envelopes import (
    RouteBoundsSchema,
    RoutePreviewDataSchema,
    RoutePreviewEnvelope,
    RoutePreviewRequest,
)
from app.services import dependencies
from app.services.dependencies import get_routing_service
from app.services.routing_service import (
    DynamicRoutingDisabledError,
    RouteDestinationMissingError,
    RouteNotFoundError,
    RoutingService,
)


@pytest.fixture(autouse=True)
def enable_dynamic_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENABLE_DYNAMIC_ROUTING", True)
    monkeypatch.setattr(settings, "APP_ENV", "test")
    limiter.reset()


@pytest.mark.asyncio
async def test_fake_routing_connector_deterministic_calculation() -> None:
    """FakeRoutingConnector computes distance and geojson deterministically."""
    connector = FakeRoutingConnector(steps=5, average_speed_kmh=40.0)
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    result = await connector.calculate_route(origin, destination, travel_mode="DRIVE")

    assert isinstance(result, RouteCalculationResult)
    assert result.provider == "fake_deterministic"
    assert result.distance_m > 0
    assert result.duration_s > 0
    assert result.geojson["type"] == "LineString"
    assert len(result.geojson["coordinates"]) == 5
    assert result.geojson["coordinates"][0] == [
        round(origin.longitude, 6),
        round(origin.latitude, 6),
    ]
    assert result.geojson["coordinates"][-1] == [
        round(destination.longitude, 6),
        round(destination.latitude, 6),
    ]
    assert result.bounds is not None
    assert result.bounds["min_lat"] == min(origin.latitude, destination.latitude)
    assert result.bounds["max_lat"] == max(origin.latitude, destination.latitude)
    assert result.bounds["min_lng"] == min(origin.longitude, destination.longitude)
    assert result.bounds["max_lng"] == max(origin.longitude, destination.longitude)


@pytest.mark.asyncio
async def test_fake_routing_connector_rejects_non_drive() -> None:
    """The development fake enforces the ADR's DRIVE-only contract too."""
    connector = FakeRoutingConnector(steps=3)
    origin = Coordinate(latitude=-2.44, longitude=-54.72)
    destination = Coordinate(latitude=-2.63, longitude=-54.94)

    with pytest.raises(RoutingNoRouteFoundError):
        await connector.calculate_route(origin, destination, travel_mode="WALKING")


@pytest.mark.asyncio
async def test_routing_service_preview_route_success() -> None:
    """RoutingService returns ephemeral RoutePreviewEnvelope with pins, legend, and bounds
    without writing to database.
    """
    region_id = uuid.uuid4()
    route_id = uuid.uuid4()

    mock_route = MagicMock()
    mock_route.id = route_id
    mock_route.region_id = region_id

    corridor_actor_id = uuid.uuid4()
    corridor_actor = MagicMock()
    corridor_actor.id = corridor_actor_id
    corridor_actor.name = "Restaurante Beira Rio"
    corridor_actor.is_featured = True
    corridor_actor.green_badge_status = "verified"
    corridor_actor.sort_order = 1

    essential_actor_id = uuid.uuid4()
    essential_actor = MagicMock()
    essential_actor.id = essential_actor_id
    essential_actor.name = "Hospital Municipal"
    essential_actor.is_featured = False
    essential_actor.green_badge_status = "none"
    essential_actor.sort_order = 1

    both_actor_id = uuid.uuid4()
    both_actor = MagicMock()
    both_actor.id = both_actor_id
    both_actor.name = "Posto Policial"
    both_actor.is_featured = False
    both_actor.green_badge_status = "verified"
    both_actor.sort_order = 2

    db_mock = AsyncMock()

    connector = FakeRoutingConnector(steps=4)
    service = RoutingService(db=db_mock, connector=connector)

    # Mock _get_route_anchor_coordinate
    service._get_route_anchor_coordinate = AsyncMock(
        return_value=Coordinate(latitude=-2.63, longitude=-54.94)
    )
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=region_id)

    # Mock territorial_repo methods
    service.territorial_repo.find_corridor_actors_by_geometry = AsyncMock(
        return_value=[
            (corridor_actor, "alimentacao", -2.50, -54.78),
            (both_actor, "transporte", -2.55, -54.85),
        ]
    )
    service.territorial_repo.list_region_essential_actors = AsyncMock(
        return_value=[
            (both_actor, "transporte", -2.55, -54.85),
            (essential_actor, "saude", -2.44, -54.71),
        ]
    )
    service.territorial_repo.get_region_bounds = AsyncMock(
        return_value={
            "min_lat": -2.70,
            "max_lat": -2.40,
            "min_lng": -55.00,
            "max_lng": -54.60,
        }
    )

    request_payload = RoutePreviewRequest(
        latitude=-2.4431,
        longitude=-54.7082,
        travel_mode="DRIVE",
    )

    envelope = await service.preview_route(route_id, request_payload)

    assert envelope is not None
    assert isinstance(envelope, RoutePreviewEnvelope)
    assert envelope.data.route_id == route_id
    assert envelope.data.route_kind == "dynamic_preview"
    assert envelope.data.is_verified is False
    assert envelope.data.provider == "fake_deterministic"
    assert envelope.data.distance_m > 0
    assert envelope.data.duration_s > 0
    assert envelope.data.geojson["type"] == "LineString"
    assert len(envelope.data.geojson["coordinates"]) == 4

    # Bounds strictly dynamic from route geometry, not expanded to city bounds
    assert envelope.data.bounds.min_lat <= envelope.data.bounds.max_lat
    assert envelope.data.bounds.min_lng <= envelope.data.bounds.max_lng
    assert envelope.data.bounds.min_lat >= -2.64
    assert envelope.data.bounds.max_lat <= -2.44

    # City bounds present separately
    assert envelope.data.city_bounds is not None
    assert envelope.data.city_bounds.min_lat == -2.70

    # Pins verification and layer classification
    assert len(envelope.data.pins) == 3
    pins_by_id = {pin.actor_id: pin for pin in envelope.data.pins}
    assert pins_by_id[corridor_actor_id].layer == "route_corridor"
    assert pins_by_id[both_actor_id].layer == "both"
    assert pins_by_id[essential_actor_id].layer == "citywide_essential"

    # Legend verification
    assert len(envelope.data.legend) == 3
    legend_slugs = [item.category_slug for item in envelope.data.legend]
    # Sorted by sort_order: alimentacao (1), transporte (5), saude (6)
    assert legend_slugs == ["alimentacao", "transporte", "saude"]

    # Verify find_corridor_actors_by_geometry received region_id
    service.territorial_repo.find_corridor_actors_by_geometry.assert_awaited_once_with(
        envelope.data.geojson,
        region_id=region_id,
        buffer_m=settings.ROUTE_CORRIDOR_BUFFER_METERS,
        limit=settings.STATIC_MAP_MAX_PINS,
    )

    # Zero database writes / persistence
    assert not db_mock.add.called
    assert not db_mock.delete.called
    assert not db_mock.commit.called
    assert not db_mock.flush.called


@pytest.mark.asyncio
async def test_routing_service_multi_region_isolation() -> None:
    """RoutingService filters corridor actors strictly by the route region."""
    region_a_id = uuid.uuid4()
    route_id = uuid.uuid4()

    actor_region_a = MagicMock()
    actor_region_a.id = uuid.uuid4()
    actor_region_a.name = "Restaurante Regiao A"
    actor_region_a.region_id = region_a_id
    actor_region_a.is_featured = False
    actor_region_a.green_badge_status = "verified"
    actor_region_a.sort_order = 1

    db_mock = AsyncMock()
    connector = FakeRoutingConnector(steps=4)
    service = RoutingService(db=db_mock, connector=connector)

    service._get_route_anchor_coordinate = AsyncMock(
        return_value=Coordinate(latitude=-2.63, longitude=-54.94)
    )
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=region_a_id)

    # find_corridor_actors_by_geometry mock checks region_id passed
    async def mock_find_corridor(geojson_geom, region_id, buffer_m, limit=200):
        if region_id == region_a_id:
            return [(actor_region_a, "alimentacao", -2.50, -54.78)]
        return []

    service.territorial_repo.find_corridor_actors_by_geometry = AsyncMock(
        side_effect=mock_find_corridor
    )
    service.territorial_repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.territorial_repo.get_region_bounds = AsyncMock(return_value=None)

    envelope = await service.preview_route(
        route_id,
        RoutePreviewRequest(latitude=-2.4431, longitude=-54.7082, travel_mode="DRIVE"),
    )

    assert len(envelope.data.pins) == 1
    assert envelope.data.pins[0].actor_id == actor_region_a.id
    service.territorial_repo.find_corridor_actors_by_geometry.assert_awaited_once_with(
        envelope.data.geojson,
        region_id=region_a_id,
        buffer_m=settings.ROUTE_CORRIDOR_BUFFER_METERS,
        limit=settings.STATIC_MAP_MAX_PINS,
    )


@pytest.mark.asyncio
async def test_routing_service_feature_flag_off_never_calls_connector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENABLE_DYNAMIC_ROUTING", False)
    connector = AsyncMock()
    service = RoutingService(db=AsyncMock(), connector=connector)

    with pytest.raises(DynamicRoutingDisabledError):
        await service.preview_route(
            uuid.uuid4(), RoutePreviewRequest(latitude=-2.44, longitude=-54.70)
        )

    connector.calculate_route.assert_not_awaited()


@pytest.mark.asyncio
async def test_routing_service_uses_common_official_geometry_endpoint_as_destination() -> None:
    route_id = uuid.uuid4()
    region_id = uuid.uuid4()
    connector = AsyncMock()
    connector.calculate_route.return_value = RouteCalculationResult(
        provider="fake_deterministic",
        distance_m=1,
        duration_s=1,
        geojson={"type": "LineString", "coordinates": [[-54.70, -2.44], [-54.978506, -2.558521]]},
        bounds={"min_lat": -2.558521, "max_lat": -2.44, "min_lng": -54.978506, "max_lng": -54.70},
    )
    service = RoutingService(db=AsyncMock(), connector=connector)
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=region_id)
    service.routing_repo.list_official_destination_endpoints = AsyncMock(
        return_value=[
            (-2.558521, -54.978506),
            (-2.558521, -54.978506),
            (-2.558521, -54.978506),
        ]
    )
    service.territorial_repo.find_corridor_actors_by_geometry = AsyncMock(return_value=[])
    service.territorial_repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.territorial_repo.get_region_bounds = AsyncMock(return_value=None)

    await service.preview_route(
        route_id, RoutePreviewRequest(latitude=-2.44, longitude=-54.70)
    )

    assert connector.calculate_route.await_args.kwargs["destination"] == Coordinate(
        latitude=-2.558521, longitude=-54.978506
    )


@pytest.mark.asyncio
async def test_routing_service_rejects_missing_or_divergent_official_destination() -> None:
    service = RoutingService(db=AsyncMock(), connector=AsyncMock())
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=uuid.uuid4())
    for endpoints in ([], [(-2.558521, -54.978506), (-2.50, -54.90)]):
        service.routing_repo.list_official_destination_endpoints = AsyncMock(
            return_value=endpoints
        )
        with pytest.raises(RouteDestinationMissingError):
            await service.preview_route(
                uuid.uuid4(), RoutePreviewRequest(latitude=-2.44, longitude=-54.70)
            )


@pytest.mark.asyncio
async def test_routing_service_preview_route_not_found() -> None:
    """RoutingService distinguishes a missing route from a missing destination."""
    db_mock = AsyncMock()
    service = RoutingService(db=db_mock, connector=FakeRoutingConnector())
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=None)
    route_id = uuid.uuid4()
    with pytest.raises(RouteNotFoundError):
        await service.preview_route(
            route_id, RoutePreviewRequest(latitude=-2.44, longitude=-54.70)
        )


@pytest.mark.asyncio
async def test_routing_service_sanitized_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Logs MUST NOT leak user coordinates."""
    mock_route = MagicMock()
    mock_route.id = uuid.uuid4()
    mock_route.region_id = uuid.uuid4()

    db_mock = AsyncMock()
    service = RoutingService(db=db_mock, connector=FakeRoutingConnector())
    service.routing_repo.get_active_route_region_id = AsyncMock(return_value=mock_route.region_id)
    service._get_route_anchor_coordinate = AsyncMock(
        return_value=Coordinate(latitude=-2.63, longitude=-54.94)
    )
    service.territorial_repo.find_corridor_actors_by_geometry = AsyncMock(return_value=[])
    service.territorial_repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.territorial_repo.get_region_bounds = AsyncMock(return_value=None)

    route_id = mock_route.id
    secret_lat = -2.4412345
    secret_lng = -54.7098765

    with caplog.at_level(logging.INFO):
        await service.preview_route(
            route_id,
            RoutePreviewRequest(latitude=secret_lat, longitude=secret_lng, travel_mode="DRIVE"),
        )

    log_text = caplog.text
    assert str(route_id) in log_text
    assert "DRIVE" in log_text
    assert str(secret_lat) not in log_text
    assert str(secret_lng) not in log_text
    assert "-2.4412345" not in log_text
    assert "-54.7098765" not in log_text


def test_api_route_preview_200_success() -> None:
    """HTTP POST /api/v1/routes/{route_id}/preview returns 200 with dynamic preview payload."""
    route_id = uuid.uuid4()
    preview_envelope = RoutePreviewEnvelope(
        data=RoutePreviewDataSchema(
            route_id=route_id,
            route_kind="dynamic_preview",
            is_verified=False,
            provider="fake_deterministic",
            distance_m=35000,
            duration_s=3150,
            geojson={
                "type": "LineString",
                "coordinates": [[-54.70, -2.44], [-54.94, -2.63]],
            },
            bounds=RouteBoundsSchema(
                min_lat=-2.63,
                max_lat=-2.44,
                min_lng=-54.94,
                max_lng=-54.70,
            ),
        )
    )

    mock_service = AsyncMock(spec=RoutingService)
    mock_service.preview_route.return_value = preview_envelope

    app.dependency_overrides[get_routing_service] = lambda: mock_service
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routes/{route_id}/preview",
                json={
                    "latitude": -2.44,
                    "longitude": -54.70,
                    "travel_mode": "DRIVE",
                },
            )
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["route_id"] == str(route_id)
            assert data["route_kind"] == "dynamic_preview"
            assert data["is_verified"] is False
            assert data["provider"] == "fake_deterministic"
            assert data["distance_m"] == 35000
            assert data["duration_s"] == 3150
            assert data["geojson"]["type"] == "LineString"
            assert data["bounds"]["min_lat"] == -2.63
    finally:
        app.dependency_overrides.clear()


def test_api_route_preview_404_not_found() -> None:
    """HTTP POST /api/v1/routes/{route_id}/preview returns 404 when route does not exist."""
    mock_service = AsyncMock(spec=RoutingService)
    mock_service.preview_route.side_effect = RouteNotFoundError

    app.dependency_overrides[get_routing_service] = lambda: mock_service
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routes/{uuid.uuid4()}/preview",
                json={
                    "latitude": -2.44,
                    "longitude": -54.70,
                    "travel_mode": "DRIVE",
                },
            )
            assert response.status_code == 404
            json_resp = response.json()
            assert json_resp.get("error", {}).get(
                "code"
            ) == "NOT_FOUND" or "não foi encontrada" in str(json_resp)
    finally:
        app.dependency_overrides.clear()


def test_api_route_preview_422_invalid_coordinates() -> None:
    """HTTP POST /api/v1/routes/{route_id}/preview returns 422 for invalid coordinate ranges."""
    with TestClient(app) as client:
        # Latitude > 90
        response = client.post(
            f"/api/v1/routes/{uuid.uuid4()}/preview",
            json={
                "latitude": 195.0,
                "longitude": -54.70,
                "travel_mode": "DRIVE",
            },
        )
        assert response.status_code == 422

        # Longitude < -180
        response2 = client.post(
            f"/api/v1/routes/{uuid.uuid4()}/preview",
            json={
                "latitude": -2.44,
                "longitude": -200.0,
                "travel_mode": "DRIVE",
            },
        )
        assert response2.status_code == 422

        # Invalid travel mode
        response3 = client.post(
            f"/api/v1/routes/{uuid.uuid4()}/preview",
            json={
                "latitude": -2.44,
                "longitude": -54.70,
                "travel_mode": "HELICOPTER",
            },
        )
        assert response3.status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (RouteDestinationMissingError(), 422, "ROUTE_DESTINATION_MISSING"),
        (RoutingNoRouteFoundError(), 422, "ROUTING_NO_ROUTE"),
        (RoutingProviderUnavailableError(), 503, "ROUTING_PROVIDER_UNAVAILABLE"),
        (RoutingTimeoutError(), 504, "ROUTING_TIMEOUT"),
    ],
)
def test_api_route_preview_typed_safe_errors(
    error: Exception, status_code: int, code: str
) -> None:
    secret_lat = -2.4412345
    secret_lng = -54.7098765
    mock_service = AsyncMock(spec=RoutingService)
    mock_service.preview_route.side_effect = error
    app.dependency_overrides[get_routing_service] = lambda: mock_service
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routes/{uuid.uuid4()}/preview",
                json={"latitude": secret_lat, "longitude": secret_lng, "travel_mode": "DRIVE"},
            )
        assert response.status_code == status_code
        body = response.json()
        assert body["error"]["code"] == code
        assert body["request_id"]
        assert str(secret_lat) not in response.text
        assert str(secret_lng) not in response.text
    finally:
        app.dependency_overrides.clear()


def test_api_route_preview_feature_flag_off() -> None:
    mock_service = AsyncMock(spec=RoutingService)
    mock_service.preview_route.side_effect = DynamicRoutingDisabledError
    app.dependency_overrides[get_routing_service] = lambda: mock_service
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/routes/{uuid.uuid4()}/preview",
                json={"latitude": -2.44, "longitude": -54.70, "travel_mode": "DRIVE"},
            )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DYNAMIC_ROUTING_DISABLED"
    finally:
        app.dependency_overrides.clear()


def test_fake_connector_selection_is_explicit_and_closed_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ROUTING_PROVIDER", "fake_deterministic")
    monkeypatch.setattr(settings, "APP_ENV", "test")
    assert isinstance(dependencies.get_routing_connector(), FakeRoutingConnector)

    monkeypatch.setattr(settings, "APP_ENV", "production")
    with pytest.raises(RuntimeError, match="não é permitido"):
        dependencies.get_routing_connector()


def test_google_connector_is_shared_between_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ROUTING_PROVIDER", "google_routes")
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "GOOGLE_ROUTES_API_KEY", SecretStr("test-only"))
    dependencies._build_routing_connector.cache_clear()
    first = dependencies.get_routing_connector()
    second = dependencies.get_routing_connector()
    assert first is second


def test_unknown_provider_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ROUTING_PROVIDER", "unknown")
    with pytest.raises(RuntimeError, match="não está implementado"):
        dependencies.get_routing_connector()


def test_api_route_preview_rate_limit_is_ten_per_minute() -> None:
    route_id = uuid.uuid4()
    mock_service = AsyncMock(spec=RoutingService)
    mock_service.preview_route.return_value = RoutePreviewEnvelope(
            data=RoutePreviewDataSchema(
                route_id=route_id,
                provider="fake_deterministic",
            distance_m=1,
            duration_s=1,
            geojson={"type": "LineString", "coordinates": [[-54.70, -2.44], [-54.71, -2.45]]},
            bounds=RouteBoundsSchema(
                min_lat=-2.45, max_lat=-2.44, min_lng=-54.71, max_lng=-54.70
            ),
        )
    )
    app.dependency_overrides[get_routing_service] = lambda: mock_service
    try:
        with TestClient(app) as client:
            responses = [
                client.post(
                    f"/api/v1/routes/{route_id}/preview",
                    json={"latitude": -2.44, "longitude": -54.70, "travel_mode": "DRIVE"},
                )
                for _ in range(11)
            ]
        assert [response.status_code for response in responses[:10]] == [200] * 10
        assert responses[10].status_code == 429
        assert responses[10].json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        app.dependency_overrides.clear()
