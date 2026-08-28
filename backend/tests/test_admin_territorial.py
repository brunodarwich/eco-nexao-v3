"""Test suite for administrative territorial CRUD operations (ECO-1602)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.models.domain import Region, Route, RouteGeometry, RouteOrigin
from app.repositories.territorial_admin import TerritorialAdminRepository
from app.schemas.admin_territorial import (
    AdminRegionCreateSchema,
    AdminRegionUpdateSchema,
    AdminRouteCreateSchema,
    AdminRouteGeometryCreateSchema,
    AdminRouteGeometryUpdateSchema,
    AdminRouteOriginCreateSchema,
    AdminRouteOriginUpdateSchema,
    AdminRouteUpdateSchema,
)
from app.services.dependencies import get_territorial_admin_service
from app.services.editorial_authorization import AuthorizationContext
from app.services.territorial_admin import TerritorialAdminService


def authenticated_user(*, anonymous: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid.uuid4(),
        email=None,
        is_anonymous=anonymous,
        role="authenticated",
        claims={},
    )


# -----------------------------------------------------------------------------
# Admin Regions API Tests
# -----------------------------------------------------------------------------


def test_admin_list_regions_requires_authorization() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    admin_service.list_regions.side_effect = HTTPException(
        status_code=403, detail="A identidade não possui a capability editorial necessária."
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).get(
            "/api/v1/admin/territory/regions",
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_region_header_reaches_service_context() -> None:
    user = authenticated_user()
    region_id = uuid.uuid4()
    admin_service = AsyncMock()
    admin_service.list_regions.return_value = {"data": []}

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).get(
            "/api/v1/admin/territory/regions",
            headers={
                "Authorization": "Bearer token",
                "X-Region-ID": str(region_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    context = admin_service.list_regions.await_args.args[0]
    assert context.scope_type == "region"
    assert context.scope_id == region_id


def test_admin_create_region_duplicate_slug_conflict() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    admin_service.create_region.side_effect = HTTPException(
        status_code=409, detail="Já existe uma região com o slug 'tapajos'."
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            "/api/v1/admin/territory/regions",
            json={
                "slug": "tapajos",
                "name": "Região do Tapajós",
                "state_code": "PA",
                "latitude": -2.44,
                "longitude": -54.7,
                "is_active": True,
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "slug" in response.json()["error"]["message"]


# -----------------------------------------------------------------------------
# Admin Routes API Tests
# -----------------------------------------------------------------------------


def test_admin_update_route_optimistic_concurrency_conflict() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    admin_service = AsyncMock()
    admin_service.update_route.side_effect = HTTPException(
        status_code=409,
        detail="A rota foi alterada por outro usuário. Por favor recarregue antes de salvar.",
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).put(
            f"/api/v1/admin/territory/routes/{route_id}",
            json={
                "title": "Rota Pindobal Alterada",
                "expected_version": "2026-08-12T00:00:00Z",
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    err_msg = response.json()["error"]["message"]
    assert "concorrência" in err_msg or "alterada" in err_msg


def test_admin_create_origin_duplicate_code_conflict() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    admin_service = AsyncMock()
    admin_service.create_origin.side_effect = HTTPException(
        status_code=409, detail="Já existe uma origem com o código 'porto' nesta rota."
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/territory/routes/{route_id}/origins",
            json={
                "code": "porto",
                "name": "Porto de Santarém",
                "latitude": -2.42,
                "longitude": -54.71,
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_admin_create_geometry_validation_failure() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    admin_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/territory/routes/{route_id}/origins/{origin_id}/geometries",
            json={
                "provider": "osrm",
                "coordinates": [[-2.42, -54.71]],  # Insufficient points (<2)
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


# -----------------------------------------------------------------------------
# TerritorialAdminService Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_list_regions_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)

    now = datetime.now(UTC)
    region = Region(
        id=uuid.uuid4(),
        slug="tapajos",
        name="Tapajós",
        state_code="PA",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    service.auth_service.require_capability = AsyncMock()
    service.repo.list_regions = AsyncMock(return_value=[region])
    service.repo.get_region_coordinates = AsyncMock(return_value=(-2.44, -54.7))

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    res = await service.list_regions(ctx)

    assert len(res.data) == 1
    assert res.data[0].slug == "tapajos"
    assert res.data[0].latitude == -2.44


@pytest.mark.asyncio
async def test_service_get_region_not_found() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()
    service.repo.get_region_by_id = AsyncMock(return_value=None)

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await service.get_region(ctx, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_service_create_region_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()
    service.repo.get_region_by_slug = AsyncMock(return_value=None)

    now = datetime.now(UTC)
    region = Region(
        id=uuid.uuid4(),
        slug="tapajos",
        name="Tapajós",
        state_code="PA",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    service.repo.create_region = AsyncMock(return_value=region)
    service.repo.get_region_coordinates = AsyncMock(return_value=(-2.44, -54.7))
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminRegionCreateSchema(
        slug="tapajos", name="Tapajós", state_code="PA", latitude=-2.44, longitude=-54.7
    )
    res = await service.create_region(ctx, body)

    assert res.data.slug == "tapajos"
    service.auth_repo.append_audit.assert_called_once()


@pytest.mark.asyncio
async def test_service_update_region_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    region = Region(
        id=uuid.uuid4(),
        slug="tapajos",
        name="Tapajós Atualizado",
        state_code="PA",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    service.repo.get_region_by_id = AsyncMock(return_value=region)
    service.repo.update_region = AsyncMock(return_value=region)
    service.repo.get_region_coordinates = AsyncMock(return_value=(-2.44, -54.7))
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminRegionUpdateSchema(name="Tapajós Atualizado")
    res = await service.update_region(ctx, region.id, body)

    assert res.data.name == "Tapajós Atualizado"


@pytest.mark.asyncio
async def test_service_list_routes_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    route = Route(
        id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        slug="rota-pindobal",
        title="Pindobal",
        summary="Resumo",
        city="Belterra",
        state_code="PA",
        status="published",
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    service.repo.list_routes = AsyncMock(return_value=([route], 1))

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    res = await service.list_routes(ctx)

    assert res.meta.total == 1
    assert res.data[0].title == "Pindobal"


@pytest.mark.asyncio
async def test_service_get_route_not_found() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()
    service.repo.get_route_by_id = AsyncMock(return_value=None)

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await service.get_route(ctx, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_service_create_route_publish_requires_capability() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    region = Region(id=uuid.uuid4(), slug="tapajos", name="Tapajós", state_code="PA")
    service.repo.get_region_by_id = AsyncMock(return_value=region)
    service.repo.get_route_by_slug = AsyncMock(return_value=None)

    # First call for territory.write passes, second call for content.publish fails
    async def cap_side_effect(ctx: AuthorizationContext, cap: str) -> None:
        if cap == "content.publish":
            raise HTTPException(status_code=403, detail="Sem permissão para publicar.")

    service.auth_service.require_capability = AsyncMock(side_effect=cap_side_effect)

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminRouteCreateSchema(
        region_id=region.id,
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="published",
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_route(ctx, body)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_service_create_route_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    region = Region(id=uuid.uuid4(), slug="tapajos", name="Tapajós", state_code="PA")
    route = Route(
        id=uuid.uuid4(),
        region_id=region.id,
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="draft",
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    service.repo.get_region_by_id = AsyncMock(return_value=region)
    service.repo.get_route_by_slug = AsyncMock(return_value=None)
    service.repo.create_route = AsyncMock(return_value=route)
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminRouteCreateSchema(
        region_id=region.id,
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="draft",
    )
    res = await service.create_route(ctx, body)

    assert res.data.title == "Pindobal"


@pytest.mark.asyncio
async def test_service_update_route_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    route = Route(
        id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        slug="rota-pindobal",
        title="Rota Pindobal Atualizada",
        city="Belterra",
        state_code="PA",
        status="draft",
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    service.repo.get_route_by_id = AsyncMock(return_value=route)
    service.repo.update_route = AsyncMock(return_value=route)
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminRouteUpdateSchema(title="Rota Pindobal Atualizada")
    res = await service.update_route(ctx, route.id, body)

    assert res.data.title == "Rota Pindobal Atualizada"


@pytest.mark.asyncio
async def test_service_archive_route_success() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    route = Route(
        id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="archived",
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    service.repo.get_route_by_id = AsyncMock(return_value=route)
    service.repo.archive_route = AsyncMock(return_value=route)
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    res = await service.archive_route(ctx, route.id)

    assert res.data.status == "archived"


@pytest.mark.asyncio
async def test_service_origin_operations() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    route_id = uuid.uuid4()
    route = Route(
        id=route_id,
        region_id=uuid.uuid4(),
        slug="rota",
        title="Rota",
        city="Santarém",
        state_code="PA",
    )
    origin = RouteOrigin(
        id=uuid.uuid4(),
        route_id=route_id,
        code="porto",
        name="Porto",
        description="Desc",
        distance_m=1000,
        duration_s=600,
        sort_order=1,
        created_at=now,
        updated_at=now,
    )

    service.repo.get_route_by_id = AsyncMock(return_value=route)
    service.repo.list_origins_by_route = AsyncMock(return_value=[origin])
    service.repo.get_origin_coordinates = AsyncMock(return_value=(-2.42, -54.71))
    service.repo.get_origin_by_code = AsyncMock(return_value=None)
    service.repo.create_origin = AsyncMock(return_value=origin)
    service.repo.get_origin_by_id = AsyncMock(return_value=origin)
    service.repo.update_origin = AsyncMock(return_value=origin)
    service.repo.delete_origin = AsyncMock(return_value=True)
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())

    # List
    origins_res = await service.list_origins(ctx, route_id)
    assert len(origins_res.data) == 1

    # Create
    create_body = AdminRouteOriginCreateSchema(
        code="porto", name="Porto", latitude=-2.42, longitude=-54.71
    )
    created_res = await service.create_origin(ctx, route_id, create_body)
    assert created_res.data.code == "porto"

    # Update
    update_body = AdminRouteOriginUpdateSchema(name="Porto Atualizado")
    updated_res = await service.update_origin(ctx, route_id, origin.id, update_body)
    assert updated_res.data.name == "Porto"

    # Delete
    await service.delete_origin(ctx, route_id, origin.id)
    service.repo.delete_origin.assert_awaited_with(origin.id)


@pytest.mark.asyncio
async def test_service_geometry_operations() -> None:
    db = AsyncMock()
    service = TerritorialAdminService(db)
    service.auth_service.require_capability = AsyncMock()

    now = datetime.now(UTC)
    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    origin = RouteOrigin(id=origin_id, route_id=route_id, code="porto", name="Porto")
    geom = RouteGeometry(
        id=uuid.uuid4(),
        route_origin_id=origin_id,
        provider="osrm",
        encoded_polyline="abc",
        distance_m=1200,
        duration_s=700,
        created_at=now,
        updated_at=now,
    )

    service.repo.get_origin_by_id = AsyncMock(return_value=origin)
    service.repo.get_route_by_id = AsyncMock(
        return_value=Route(
            id=route_id,
            region_id=uuid.uuid4(),
            slug="rota-geometria",
            title="Rota Geometria",
            city="Belterra",
            state_code="PA",
        )
    )
    service.repo.get_geometry_by_origin = AsyncMock(return_value=None)
    service.repo.create_geometry = AsyncMock(return_value=geom)
    service.repo.get_geometry_by_id = AsyncMock(return_value=geom)
    service.repo.update_geometry = AsyncMock(return_value=geom)
    service.repo.get_geometry_geojson = AsyncMock(
        return_value={"type": "LineString", "coordinates": [[-54.71, -2.42], [-54.7, -2.44]]}
    )
    service.auth_repo.append_audit = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())

    # Create geometry
    create_body = AdminRouteGeometryCreateSchema(
        provider="osrm",
        coordinates=[[-2.42, -54.71], [-2.44, -54.7]],
        distance_m=1200,
        duration_s=700,
    )
    geom_res = await service.create_geometry(ctx, route_id, origin_id, create_body)
    assert geom_res.data.provider == "osrm"

    # Update geometry
    update_body = AdminRouteGeometryUpdateSchema(distance_m=1300)
    updated_geom_res = await service.update_geometry(ctx, route_id, geom.id, update_body)
    assert updated_geom_res.data.distance_m == 1200


# -----------------------------------------------------------------------------
# TerritorialAdminRepository Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_repo_region_get_and_list() -> None:
    db = AsyncMock()
    repo = TerritorialAdminRepository(db)

    region_id = uuid.uuid4()
    now = datetime.now(UTC)
    region = Region(
        id=region_id,
        slug="tapajos",
        name="Tapajós",
        state_code="PA",
        center=MagicMock(),
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = region
    exec_mock.scalars.return_value.all.return_value = [region]
    exec_mock.first.return_value = MagicMock(lat=-2.44, lon=-54.7)
    db.execute = AsyncMock(return_value=exec_mock)

    r1 = await repo.get_region_by_id(region_id)
    assert r1 is not None and r1.slug == "tapajos"

    r2 = await repo.get_region_by_slug("tapajos")
    assert r2 is not None and r2.slug == "tapajos"

    regions = await repo.list_regions(include_inactive=True)
    assert len(regions) == 1

    lat, lon = await repo.get_region_coordinates(region)
    assert lat == -2.44 and lon == -54.7


@pytest.mark.asyncio
async def test_repo_region_create_and_update() -> None:
    db = AsyncMock()
    repo = TerritorialAdminRepository(db)
    region_id = uuid.uuid4()

    created = await repo.create_region(
        slug="novaregiao", name="Nova Região", state_code="PA", latitude=-2.5, longitude=-54.8
    )
    assert created.slug == "novaregiao"

    region = Region(id=region_id, slug="novaregiao", name="Nova Região", state_code="PA")
    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = region
    db.execute = AsyncMock(return_value=exec_mock)

    updated = await repo.update_region(region_id, name="Tapajós Editado", is_active=False)
    assert updated is not None and updated.name == "Tapajós Editado"


@pytest.mark.asyncio
async def test_repo_route_crud() -> None:
    db = AsyncMock()
    repo = TerritorialAdminRepository(db)

    route_id = uuid.uuid4()
    region_id = uuid.uuid4()
    now = datetime.now(UTC)
    route = Route(
        id=route_id,
        region_id=region_id,
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="draft",
        is_verified=False,
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = route
    exec_mock.scalar_one.return_value = 1
    exec_mock.scalars.return_value.all.return_value = [route]
    db.execute = AsyncMock(return_value=exec_mock)

    r1 = await repo.get_route_by_id(route_id)
    assert r1 is not None and r1.slug == "rota-pindobal"

    routes, total = await repo.list_routes(region_id=region_id)
    assert total == 1 and len(routes) == 1

    created = await repo.create_route(
        region_id=region_id, slug="nova-rota", title="Nova Rota", city="Belterra", state_code="PA"
    )
    assert created.slug == "nova-rota"

    updated = await repo.update_route(route_id, title="Rota Editada")
    assert updated is not None and updated.title == "Rota Editada"

    archived = await repo.archive_route(route_id)
    assert archived is not None and archived.status == "archived"


@pytest.mark.asyncio
async def test_repo_origin_crud() -> None:
    db = AsyncMock()
    repo = TerritorialAdminRepository(db)

    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    now = datetime.now(UTC)
    origin = RouteOrigin(
        id=origin_id,
        route_id=route_id,
        code="porto",
        name="Porto",
        sort_order=1,
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = origin
    exec_mock.scalars.return_value.all.return_value = [origin]
    exec_mock.first.return_value = MagicMock(lat=-2.42, lon=-54.71)
    db.execute = AsyncMock(return_value=exec_mock)

    o1 = await repo.get_origin_by_id(origin_id)
    assert o1 is not None and o1.code == "porto"

    origins = await repo.list_origins_by_route(route_id)
    assert len(origins) == 1

    lat, lon = await repo.get_origin_coordinates(origin)
    assert lat == -2.42 and lon == -54.71

    created = await repo.create_origin(
        route_id=route_id, code="praia", name="Praia", latitude=-2.5, longitude=-54.8
    )
    assert created.code == "praia"

    updated = await repo.update_origin(origin_id, name="Porto Principal")
    assert updated is not None and updated.name == "Porto Principal"

    deleted = await repo.delete_origin(origin_id)
    assert deleted is True


@pytest.mark.asyncio
async def test_repo_geometry_crud() -> None:
    db = AsyncMock()
    repo = TerritorialAdminRepository(db)

    geom_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    now = datetime.now(UTC)
    geom = RouteGeometry(
        id=geom_id,
        route_origin_id=origin_id,
        provider="osrm",
        distance_m=1000,
        duration_s=500,
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = geom
    exec_mock.scalar_one.return_value = "dummy-geometry-obj"
    db.execute = AsyncMock(return_value=exec_mock)

    g1 = await repo.get_geometry_by_id(geom_id)
    assert g1 is not None and g1.provider == "osrm"

    created = await repo.create_geometry(
        route_origin_id=origin_id,
        coordinates=[[-2.42, -54.71], [-2.44, -54.7]],
        provider="osrm",
    )
    assert created.provider == "osrm"

    updated = await repo.update_geometry(geom_id, distance_m=2000)
    assert updated is not None and updated.distance_m == 2000

    exec_mock.scalar_one_or_none.return_value = (
        '{"type":"LineString","coordinates":[[-54.71,-2.42]]}'
    )
    geojson = await repo.get_geometry_geojson(geom)
    assert geojson is not None and geojson["type"] == "LineString"


def test_admin_region_crud_endpoints() -> None:
    user = authenticated_user()
    region_id = uuid.uuid4()
    admin_service = AsyncMock()
    admin_service.get_region.return_value = {
        "data": {
            "id": region_id,
            "slug": "tapajos",
            "name": "Tapajós",
            "state_code": "PA",
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.update_region.return_value = {
        "data": {
            "id": region_id,
            "slug": "tapajos",
            "name": "Tapajós Atualizado",
            "state_code": "PA",
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_get = client.get(f"/api/v1/admin/territory/regions/{region_id}")
        assert res_get.status_code == 200
        assert res_get.json()["data"]["name"] == "Tapajós"

        res_put = client.put(
            f"/api/v1/admin/territory/regions/{region_id}",
            json={"name": "Tapajós Atualizado"},
        )
        assert res_put.status_code == 200
        assert res_put.json()["data"]["name"] == "Tapajós Atualizado"
    finally:
        app.dependency_overrides.clear()


def test_admin_route_crud_endpoints() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    region_id = uuid.uuid4()
    admin_service = AsyncMock()
    admin_service.get_route.return_value = {
        "data": {
            "id": route_id,
            "region_id": region_id,
            "slug": "rota-tapajos",
            "code": "RT01",
            "title": "Rota Tapajós",
            "city": "Santarém",
            "state_code": "PA",
            "version": 1,
            "status": "published",
            "is_verified": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.update_route.return_value = {
        "data": {
            "id": route_id,
            "region_id": region_id,
            "slug": "rota-tapajos",
            "code": "RT01",
            "title": "Rota Tapajós VIP",
            "city": "Santarém",
            "state_code": "PA",
            "version": 2,
            "status": "published",
            "is_verified": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.archive_route.return_value = {
        "data": {
            "id": route_id,
            "region_id": region_id,
            "slug": "rota-tapajos",
            "code": "RT01",
            "title": "Rota Tapajós",
            "city": "Santarém",
            "state_code": "PA",
            "version": 2,
            "status": "archived",
            "is_verified": False,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_get = client.get(f"/api/v1/admin/territory/routes/{route_id}")
        assert res_get.status_code == 200

        res_put = client.put(
            f"/api/v1/admin/territory/routes/{route_id}",
            json={"title": "Rota Tapajós VIP"},
        )
        assert res_put.status_code == 200
        assert res_put.json()["data"]["title"] == "Rota Tapajós VIP"

        res_del = client.delete(f"/api/v1/admin/territory/routes/{route_id}")
        assert res_del.status_code == 200
        assert res_del.json()["data"]["status"] == "archived"
    finally:
        app.dependency_overrides.clear()


def test_admin_origin_and_geometry_endpoints() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    geom_id = uuid.uuid4()
    admin_service = AsyncMock()

    admin_service.create_origin.return_value = {
        "data": {
            "id": origin_id,
            "route_id": route_id,
            "code": "orig-1",
            "name": "Origem 1",
            "latitude": -2.4,
            "longitude": -54.7,
            "sort_order": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.update_origin.return_value = {
        "data": {
            "id": origin_id,
            "route_id": route_id,
            "code": "orig-1",
            "name": "Origem 1 Atualizada",
            "latitude": -2.4,
            "longitude": -54.7,
            "sort_order": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.delete_origin.return_value = None

    admin_service.create_geometry.return_value = {
        "data": {
            "id": geom_id,
            "route_origin_id": origin_id,
            "provider": "osrm",
            "distance_m": 1500,
            "duration_s": 600,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }
    admin_service.update_geometry.return_value = {
        "data": {
            "id": geom_id,
            "route_origin_id": origin_id,
            "provider": "osrm",
            "distance_m": 2500,
            "duration_s": 800,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    }

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_territorial_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_orig = client.post(
            f"/api/v1/admin/territory/routes/{route_id}/origins",
            json={"code": "orig-1", "name": "Origem 1", "latitude": -2.4, "longitude": -54.7},
        )
        assert res_orig.status_code == 201

        res_put_orig = client.put(
            f"/api/v1/admin/territory/routes/{route_id}/origins/{origin_id}",
            json={"name": "Origem 1 Atualizada"},
        )
        assert res_put_orig.status_code == 200

        res_del_orig = client.delete(
            f"/api/v1/admin/territory/routes/{route_id}/origins/{origin_id}"
        )
        assert res_del_orig.status_code == 204

        res_geom = client.post(
            f"/api/v1/admin/territory/routes/{route_id}/origins/{origin_id}/geometries",
            json={"coordinates": [[-2.4, -54.7], [-2.5, -54.8]], "provider": "osrm"},
        )
        assert res_geom.status_code == 201

        res_put_geom = client.put(
            f"/api/v1/admin/territory/routes/{route_id}/geometries/{geom_id}",
            json={"distance_m": 2500},
        )
        assert res_put_geom.status_code == 200
    finally:
        app.dependency_overrides.clear()
