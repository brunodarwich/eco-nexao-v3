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
    routes, total, has_more = await repo.list_routes(
        region_id=region_id, q="Test", verified=True, limit=10
    )

    assert total == 2
    assert len(routes) == 2
    assert routes[0].title == "Route 1"
    assert has_more is False


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
    mock_exec.all.return_value = [(actor, "culinaria", "Culinária", -2.5, -48.0, 0)]
    mock_db.execute.return_value = mock_exec
    mock_db.scalar.return_value = 1

    repo = TerritorialRepository(mock_db)
    cats = await repo.list_actor_categories()
    actors, total, has_more = await repo.list_route_actors(
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
    assert has_more is False


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
    service.repo.get_route_by_id = AsyncMock(
        return_value=MagicMock(id=route_id, region_id=uuid.uuid4(), origins=[])
    )
    geojson = {"type": "LineString", "coordinates": [[-54.96, -2.58], [-54.95, -2.57]]}
    service.repo.get_route_geometry = AsyncMock(return_value=(None, geojson))
    service.repo.find_route_corridor_actors = AsyncMock(
        return_value=[(actor, "hospedagem", -2.58, -54.96, False, 0)]
    )
    service.repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.repo.get_region_bounds = AsyncMock(return_value=None)
    service.repo.get_buffered_route_bounds = AsyncMock(return_value=None)

    envelope = await service.get_route_map_payload(route_id, origin_id=origin_id)

    assert envelope is not None
    assert envelope.data.selected_origin_id == origin_id
    assert [pin.actor_id for pin in envelope.data.pins] == [actor.id]
    service.repo.find_route_corridor_actors.assert_awaited_once_with(
        geojson_geom=geojson,
        region_id=service.repo.get_route_by_id.return_value.region_id,
        route_id=route_id,
        origin_id=origin_id,
        category_slug=None,
        buffer_m=1000.0,
        limit=200,
    )


@pytest.mark.asyncio
async def test_get_route_geometry_sql_compiles_with_geometry_cast():
    """Verify that get_route_geometry uses cast(geometry, Geometry) with
    ST_SimplifyPreserveTopology.
    """
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
    route_mock = MagicMock(id=route_id, region_id=uuid.uuid4(), origins=[origin_mock])

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
    service.repo.list_route_actors = AsyncMock(return_value=([], 0, False))
    service.repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.repo.get_region_bounds = AsyncMock(return_value=None)

    envelope = await service.get_route_map_payload(route_id, origin_id=None)

    assert envelope is not None
    assert envelope.data.selected_origin_id == origin_1_id
    assert envelope.data.bounds is not None
    assert envelope.data.bounds.model_dump() == custom_bounds
    assert envelope.data.geometry is not None


@pytest.mark.asyncio
async def test_route_map_payload_pins_and_legend_visual_metadata_and_ordering():
    """Verify MapPinSchema visual metadata, legend counts/ordering and consistency with taxonomy."""
    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()

    actor_hosp1 = Actor(
        id=uuid.uuid4(), slug="pousada-sol", name="Pousada Sol", category_id=uuid.uuid4()
    )
    actor_hosp2 = Actor(
        id=uuid.uuid4(), slug="hotel-lua", name="Hotel Lua", category_id=uuid.uuid4()
    )
    actor_alim = Actor(
        id=uuid.uuid4(), slug="restaurante-mar", name="Restaurante Mar", category_id=uuid.uuid4()
    )
    actor_unknown = Actor(
        id=uuid.uuid4(), slug="outro-local", name="Outro Local", category_id=uuid.uuid4()
    )

    service = TerritorialService(AsyncMock())
    service.repo.get_route_by_id = AsyncMock(
        return_value=MagicMock(id=route_id, region_id=uuid.uuid4(), origins=[])
    )
    geojson = {"type": "LineString", "coordinates": [[-54.97, -2.59], [-54.90, -2.50]]}
    service.repo.get_route_geometry = AsyncMock(return_value=(None, geojson))
    service.repo.find_route_corridor_actors = AsyncMock(
        return_value=[
            (actor_hosp1, "hospedagem", -2.58, -54.96, False, 0),
            (actor_alim, "alimentacao", -2.55, -54.94, False, 0),
            (actor_hosp2, "hospedagem", -2.59, -54.97, False, 0),
            (actor_unknown, "categoria-desconhecida", -2.50, -54.90, False, 0),
        ]
    )
    service.repo.list_region_essential_actors = AsyncMock(return_value=[])
    service.repo.get_region_bounds = AsyncMock(return_value=None)
    service.repo.get_buffered_route_bounds = AsyncMock(return_value=None)

    envelope = await service.get_route_map_payload(route_id, origin_id=origin_id)

    assert envelope is not None
    payload = envelope.data
    assert len(payload.pins) == 4

    # a) MapPinSchema com category_label, color, icon preenchidos
    pin_alim = next(p for p in payload.pins if p.actor_id == actor_alim.id)
    assert pin_alim.category_slug == "alimentacao"
    assert pin_alim.category_label == "Alimentação"
    assert pin_alim.color == "#D97706"
    assert pin_alim.icon == "utensils"

    pin_hosp = next(p for p in payload.pins if p.actor_id == actor_hosp1.id)
    assert pin_hosp.category_slug == "hospedagem"
    assert pin_hosp.category_label == "Hospedagem"
    assert pin_hosp.color == "#2563EB"
    assert pin_hosp.icon == "bed"

    # c) fallback determinístico para categoria desconhecida/não cadastrada (usando 'outros')
    pin_unk = next(p for p in payload.pins if p.actor_id == actor_unknown.id)
    assert pin_unk.category_slug == "outros"
    assert pin_unk.category_label == "Outros"
    assert pin_unk.color == "#6B7280"
    assert pin_unk.icon == "help-circle"

    # b) legend com metadados idênticos aos pins e contagens exatas (soma igual a len(pins))
    assert sum(item.count for item in payload.legend) == len(payload.pins)
    assert len(payload.legend) == 3

    # d) ordenação da legenda por sort_order ascendente e depois label
    # alimentacao (sort_order=1), hospedagem (sort_order=3), outros (sort_order=99)
    assert [item.category_slug for item in payload.legend] == [
        "alimentacao",
        "hospedagem",
        "outros",
    ]
    assert payload.legend[0].category_slug == "alimentacao"
    assert payload.legend[0].count == 1
    assert payload.legend[0].sort_order == 1
    assert payload.legend[0].label == "Alimentação"

    assert payload.legend[1].category_slug == "hospedagem"
    assert payload.legend[1].count == 2
    assert payload.legend[1].sort_order == 3
    assert payload.legend[1].label == "Hospedagem"

    assert payload.legend[2].category_slug == "outros"
    assert payload.legend[2].count == 1
    assert payload.legend[2].sort_order == 99
    assert payload.legend[2].label == "Outros"


@pytest.mark.asyncio
async def test_route_map_payload_dual_layers_and_city_bounds():
    """Verify canonical ADR 0011 layers and independent route/city bounds."""
    route_id = uuid.uuid4()
    region_id = uuid.uuid4()
    origin_id = uuid.uuid4()

    # Actor in corridor only
    actor_corridor = Actor(
        id=uuid.uuid4(),
        slug="restaurante-praia",
        name="Restaurante da Praia",
        category_id=uuid.uuid4(),
        region_id=region_id,
        green_badge_status="none",
    )
    # Actor essential in region AND on route -> layer: both
    actor_both = Actor(
        id=uuid.uuid4(),
        slug="posto-saude-central",
        name="Posto de Saúde Central",
        category_id=uuid.uuid4(),
        region_id=region_id,
        green_badge_status="verified",
    )
    # Actor essential in region ONLY -> layer: city
    actor_city = Actor(
        id=uuid.uuid4(),
        slug="delegacia-policia",
        name="Delegacia de Polícia",
        category_id=uuid.uuid4(),
        region_id=region_id,
        green_badge_status="none",
    )

    route_mock = MagicMock(id=route_id, region_id=region_id, origins=[])
    region_bounds = {
        "min_lat": -2.60,
        "max_lat": -2.40,
        "min_lng": -55.00,
        "max_lng": -54.70,
    }

    service = TerritorialService(AsyncMock())
    service.repo.get_route_by_id = AsyncMock(return_value=route_mock)
    geojson = {"type": "LineString", "coordinates": [[-54.95, -2.55], [-54.90, -2.50]]}
    service.repo.get_route_geometry = AsyncMock(return_value=(None, geojson))
    service.repo.find_route_corridor_actors = AsyncMock(
        return_value=[
            (actor_corridor, "alimentacao", -2.55, -54.95, False, 10),
            (actor_both, "transporte", -2.50, -54.90, True, 20),
        ]
    )
    service.repo.list_region_essential_actors = AsyncMock(
        return_value=[
            (actor_both, "transporte", -2.50, -54.90),
            (actor_city, "seguranca", -2.45, -54.75),
        ]
    )
    service.repo.get_region_bounds = AsyncMock(return_value=region_bounds)
    service.repo.get_buffered_route_bounds = AsyncMock(
        return_value={
            "min_lat": -2.55,
            "max_lat": -2.50,
            "min_lng": -54.95,
            "max_lng": -54.90,
        }
    )

    envelope = await service.get_route_map_payload(route_id, origin_id=origin_id)

    assert envelope is not None
    payload = envelope.data
    assert len(payload.pins) == 3

    pin_corridor = next(p for p in payload.pins if p.actor_id == actor_corridor.id)
    assert pin_corridor.layer == "route_corridor"

    pin_both = next(p for p in payload.pins if p.actor_id == actor_both.id)
    assert pin_both.layer == "both"

    pin_city = next(p for p in payload.pins if p.actor_id == actor_city.id)
    assert pin_city.layer == "citywide_essential"

    # Route bounds isolate corridor/both pins only (exclude city-only pin at -2.45, -54.75)
    assert payload.bounds is not None
    assert payload.bounds.min_lat == -2.55
    assert payload.bounds.max_lat == -2.50
    assert payload.bounds.min_lng == -54.95
    assert payload.bounds.max_lng == -54.90

    # City bounds encompasses the whole region
    assert payload.city_bounds is not None
    assert payload.city_bounds.model_dump() == region_bounds

    # Check prioritization: actor_both has verified green badge (comes before corridor/city)
    assert payload.pins[0].actor_id == actor_both.id
