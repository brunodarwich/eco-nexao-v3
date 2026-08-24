"""Behavioral unit tests for territorial domain repository and services (ECO-1301).

Focuses on domain business rules:
- Region filtering and slug lookup.
- Route listing with search, verification flag, region filters, and pagination.
- Route details, origins, geometry parsing.
- Route alerts within active time windows.
- Actor categories and actor filtering by category, origin, and search terms.
- Propagation of non-existent entity lookups.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.domain import (
    Actor,
    ActorCategory,
    Region,
    Route,
    RouteAlert,
    RouteGeometry,
    RouteOrigin,
)
from app.repositories.territorial import TerritorialRepository
from app.services.territorial import TerritorialService


@pytest.mark.asyncio
async def test_get_active_regions_behavior():
    """Verify get_active_regions returns active regions from DB scalar call."""
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    reg1 = Region(id=uuid.uuid4(), name="Region A", slug="region-a", is_active=True)
    reg2 = Region(id=uuid.uuid4(), name="Region B", slug="region-b", is_active=True)
    mock_scalars.all.return_value = [reg1, reg2]
    mock_db.scalars.return_value = mock_scalars

    repo = TerritorialRepository(mock_db)
    result = await repo.get_active_regions()

    assert len(result) == 2
    assert result[0].name == "Region A"
    assert result[1].name == "Region B"
    mock_db.scalars.assert_called_once()


@pytest.mark.asyncio
async def test_get_region_by_id_and_slug():
    """Verify region lookup by ID and slug."""
    mock_db = AsyncMock()
    reg_id = uuid.uuid4()
    reg = Region(id=reg_id, name="Test Region", slug="test-region", is_active=True)
    mock_db.scalar.return_value = reg

    repo = TerritorialRepository(mock_db)
    res_id = await repo.get_region_by_id(reg_id)
    res_slug = await repo.get_region_by_slug("test-region")

    assert res_id == reg
    assert res_slug == reg
    assert mock_db.scalar.call_count == 2


@pytest.mark.asyncio
async def test_list_routes_filtered_and_paginated():
    """Verify list_routes executes filtered query and returns tuple of (routes, total)."""
    mock_db = AsyncMock()
    route1 = Route(id=uuid.uuid4(), title="Route 1", status="active")
    route2 = Route(id=uuid.uuid4(), title="Route 2", status="active")

    # Mock count query and route query
    mock_db.scalar.return_value = 2
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [route1, route2]
    mock_db.scalars.return_value = mock_scalars

    repo = TerritorialRepository(mock_db)
    region_id = uuid.uuid4()
    routes, total = await repo.list_routes(
        region_id=region_id, q="Test", verified=True, limit=10, offset=0
    )

    assert total == 2
    assert len(routes) == 2
    assert routes[0].title == "Route 1"


@pytest.mark.asyncio
async def test_get_route_by_id_found_and_not_found():
    """Verify route detail retrieval including non-existent handling."""
    mock_db = AsyncMock()
    route_id = uuid.uuid4()
    route = Route(id=route_id, title="Sample Route", status="active")

    mock_db.scalar.side_effect = [route, None]
    repo = TerritorialRepository(mock_db)

    found = await repo.get_route_by_id(route_id)
    not_found = await repo.get_route_by_id(uuid.uuid4())

    assert found == route
    assert not_found is None


@pytest.mark.asyncio
async def test_get_route_origins_and_geometry():
    """Verify route origins listing and geometry GeoJSON parsing."""
    mock_db = AsyncMock()
    route_id = uuid.uuid4()
    origin = RouteOrigin(id=uuid.uuid4(), route_id=route_id, name="Origin A", code="ORIG_A")

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [origin]
    mock_db.scalars.return_value = mock_scalars

    # Mock geometry query
    geom = RouteGeometry(id=uuid.uuid4(), route_origin_id=origin.id)
    geojson_str = '{"type": "LineString", "coordinates": [[-48.0, -2.5], [-48.1, -2.6]]}'
    mock_exec = MagicMock()
    mock_exec.first.return_value = (geom, geojson_str)
    mock_db.execute.return_value = mock_exec

    repo = TerritorialRepository(mock_db)
    origins = await repo.get_route_origins(route_id)
    geom_res, geojson_obj = await repo.get_route_geometry(route_id, origin_id=origin.id)

    assert len(origins) == 1
    assert origins[0].name == "Origin A"
    assert geom_res == geom
    assert geojson_obj["type"] == "LineString"
    assert len(geojson_obj["coordinates"]) == 2


@pytest.mark.asyncio
async def test_get_route_geometry_not_found():
    """Verify geometry returns (None, None) when not found."""
    mock_db = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_db.execute.return_value = mock_exec

    repo = TerritorialRepository(mock_db)
    geom, geojson = await repo.get_route_geometry(uuid.uuid4())
    assert geom is None
    assert geojson is None


@pytest.mark.asyncio
async def test_get_active_route_alerts():
    """Verify get_active_route_alerts returns active alerts."""
    mock_db = AsyncMock()
    alert = RouteAlert(id=uuid.uuid4(), title="Caution", is_active=True)
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [alert]
    mock_db.scalars.return_value = mock_scalars

    repo = TerritorialRepository(mock_db)
    alerts = await repo.get_active_route_alerts(uuid.uuid4())
    assert len(alerts) == 1
    assert alerts[0].title == "Caution"


@pytest.mark.asyncio
async def test_list_actor_categories_and_actors():
    """Verify actor categories and actor listing with transient properties."""
    mock_db = AsyncMock()
    cat = ActorCategory(id=uuid.uuid4(), label="Culinária", slug="culinaria")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [cat]
    mock_db.scalars.return_value = mock_scalars

    # Mock list_route_actors execute
    actor = Actor(id=uuid.uuid4(), name="Restaurante Pindobal", category_id=cat.id)
    mock_exec = MagicMock()
    mock_exec.all.return_value = [(actor, "culinaria", "Culinária", -2.5, -48.0)]
    mock_db.execute.return_value = mock_exec
    mock_db.scalar.return_value = 1

    repo = TerritorialRepository(mock_db)
    cats = await repo.list_actor_categories()
    actors, total = await repo.list_route_actors(
        uuid.uuid4(), q="Pindobal", category_slug="culinaria"
    )

    assert len(cats) == 1
    assert total == 1
    assert len(actors) == 1
    act, slug, lat, lon = actors[0]
    assert act.name == "Restaurante Pindobal"
    assert slug == "culinaria"
    assert lat == -2.5
    assert lon == -48.0


@pytest.mark.asyncio
async def test_get_actor_by_id_with_features_and_google_ref():
    """Verify get_actor_by_id detailed extraction."""
    mock_db = AsyncMock()
    actor = Actor(id=uuid.uuid4(), name="Pousada Sol", city="Belterra")

    # 1st execute for actor, lat, lon
    mock_exec_actor = MagicMock()
    mock_exec_actor.first.return_value = (actor, -2.54, -48.12)

    # 2nd execute for features
    mock_exec_feats = MagicMock()
    mock_exec_feats.all.return_value = [("rampa-acesso", "Rampa de Acesso", "verified")]

    mock_db.execute.side_effect = [mock_exec_actor, mock_exec_feats]
    mock_db.scalar.return_value = "ChIJN1t_tDeuEmsRUsoyG83frY4"  # google_place_id

    repo = TerritorialRepository(mock_db)
    act, lat, lon, feats, place_id = await repo.get_actor_by_id(actor.id)

    assert act == actor
    assert lat == -2.54
    assert lon == -48.12
    assert len(feats) == 1
    assert feats[0]["slug"] == "rampa-acesso"
    assert place_id == "ChIJN1t_tDeuEmsRUsoyG83frY4"


@pytest.mark.asyncio
async def test_territorial_service_delegation():
    """Verify TerritorialService delegates correctly to repository methods."""
    mock_db = AsyncMock()
    reg = Region(id=uuid.uuid4(), name="Santarém", slug="santarem", state_code="PA", is_active=True)

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [reg]
    mock_db.scalars.return_value = mock_scalars

    service = TerritorialService(mock_db)
    envelope = await service.get_regions()

    assert len(envelope.data) == 1
    assert envelope.data[0].slug == "santarem"
    assert envelope.data[0].name == "Santarém"


@pytest.mark.asyncio
async def test_route_map_payload_filters_pins_by_selected_origin():
    """The reusable map payload must keep pins aligned with the selected journey."""
    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    actor = Actor(
        id=uuid.uuid4(),
        slug="pousada-pindobal",
        name="Pousada Pindobal",
        category_id=uuid.uuid4(),
    )

    service = TerritorialService(AsyncMock())
    service.repo.get_route_by_id = AsyncMock(return_value=MagicMock(id=route_id, origins=[]))
    service.repo.get_route_geometry = AsyncMock(return_value=(None, None))
    service.repo.list_route_actors = AsyncMock(
        return_value=([(actor, "hospedagem", -2.58, -54.96)], 1)
    )

    envelope = await service.get_route_map_payload(route_id, origin_id=origin_id)

    assert envelope is not None
    assert envelope.data.selected_origin_id == origin_id
    assert [pin.actor_id for pin in envelope.data.pins] == [actor.id]
    service.repo.list_route_actors.assert_awaited_once_with(
        route_id=route_id,
        origin_id=origin_id,
        limit=200,
        offset=0,
    )


@pytest.mark.asyncio
async def test_get_route_geometry_sql_compiles_with_geometry_cast():
    """Verify that get_route_geometry uses cast(geometry, Geometry) with ST_SimplifyPreserveTopology."""
    mock_db = AsyncMock()
    route_id = uuid.uuid4()
    geom = RouteGeometry(id=uuid.uuid4(), route_origin_id=uuid.uuid4())
    geojson_str = '{"type": "LineString", "coordinates": [[-54.9, -2.5], [-54.8, -2.4]]}'
    mock_exec = MagicMock()
    mock_exec.first.return_value = (geom, geojson_str)
    mock_db.execute.return_value = mock_exec

    repo = TerritorialRepository(mock_db)
    geom_res, geojson_res = await repo.get_route_geometry(
        route_id=route_id, simplify_tolerance=0.0001
    )

    assert geom_res == geom
    assert geojson_res == {"type": "LineString", "coordinates": [[-54.9, -2.5], [-54.8, -2.4]]}

    # Verify executed SQL statement has ST_SimplifyPreserveTopology and Geometry cast
    mock_db.execute.assert_called_once()
    stmt = mock_db.execute.call_args[0][0]
    stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "ST_SimplifyPreserveTopology" in stmt_str
    assert "geometry" in stmt_str.lower()
    assert "cast(" in stmt_str.lower() or "::geometry" in stmt_str.lower()


@pytest.mark.asyncio
async def test_route_map_payload_fallback_origin_and_bounds():
    """Verify fallback to route.origins and geom.bounds when pins have no coordinates."""
    route_id = uuid.uuid4()
    origin_1_id = uuid.uuid4()
    origin_mock = MagicMock(id=origin_1_id)
    route_mock = MagicMock(id=route_id, origins=[origin_mock])

    custom_bounds = {"min_lat": -2.6, "max_lat": -2.4, "min_lng": -55.0, "max_lng": -54.8}
    geom_mock = MagicMock(
        id=uuid.uuid4(),
        route_origin_id=origin_1_id,
        provider="osrm",
        encoded_polyline="abcd",
        distance_m=1000,
        duration_s=200,
        bounds=custom_bounds,
    )

    service = TerritorialService(AsyncMock())
    service.repo.get_route_by_id = AsyncMock(return_value=route_mock)
    service.repo.get_route_geometry = AsyncMock(return_value=(geom_mock, None))
    # No actors with coords
    service.repo.list_route_actors = AsyncMock(return_value=([], 0))

    envelope = await service.get_route_map_payload(route_id, origin_id=None)

    assert envelope is not None
    assert envelope.data.selected_origin_id == origin_1_id
    assert envelope.data.bounds == custom_bounds
    assert envelope.data.geometry is not None

