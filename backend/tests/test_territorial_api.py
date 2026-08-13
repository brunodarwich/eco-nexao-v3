"""Offline HTTP contract tests for the territorial API."""

import uuid
from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.schemas.envelopes import (
    ActorCategoryListEnvelope,
    BootstrapDataSchema,
    BootstrapResponseEnvelope,
    PaginationMeta,
    RegionListEnvelope,
    RegionSchema,
    RouteListEnvelope,
)
from app.services.dependencies import get_territorial_service


@pytest.fixture
def api() -> Generator[tuple[TestClient, SimpleNamespace]]:
    region_id = uuid.uuid4()
    region = RegionSchema(
        id=region_id,
        slug="tapajos",
        name="Tapajós",
        state_code="PA",
        is_active=True,
    )
    service = SimpleNamespace(
        get_regions=AsyncMock(return_value=RegionListEnvelope(data=[region])),
        get_bootstrap=AsyncMock(
            return_value=BootstrapResponseEnvelope(
                data=BootstrapDataSchema(active_region=region, supported_regions=[region])
            )
        ),
        list_routes=AsyncMock(
            return_value=RouteListEnvelope(
                data=[], meta=PaginationMeta(total=0, limit=20, next_cursor=None)
            )
        ),
        get_route_detail=AsyncMock(return_value=None),
        get_route_origins=AsyncMock(return_value=None),
        get_route_geometry=AsyncMock(return_value=None),
        get_route_alerts=AsyncMock(return_value=None),
        list_route_actors=AsyncMock(return_value=None),
        get_route_map_payload=AsyncMock(return_value=None),
        list_actor_categories=AsyncMock(return_value=ActorCategoryListEnvelope(data=[])),
        get_actor_detail=AsyncMock(return_value=None),
    )
    user = AuthenticatedUser(
        id=uuid.uuid4(), email=None, is_anonymous=True, role="authenticated", claims={}
    )
    app.dependency_overrides[get_territorial_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()


def test_list_regions(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    assert response.json()["data"][0]["slug"] == "tapajos"
    service.get_regions.assert_awaited_once_with()


def test_bootstrap_requires_authentication() -> None:
    app.dependency_overrides[get_territorial_service] = lambda: SimpleNamespace()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/bootstrap")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_get_bootstrap(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    response = client.get("/api/v1/bootstrap")
    assert response.status_code == 200
    assert response.json()["data"]["feature_flags"]["anonymous_signin"] is True
    service.get_bootstrap.assert_awaited_once_with(preferred_region_id=None)


def test_get_bootstrap_passes_region(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    region_id = uuid.uuid4()
    assert client.get(f"/api/v1/bootstrap?region_id={region_id}").status_code == 200
    service.get_bootstrap.assert_awaited_once_with(preferred_region_id=region_id)


def test_list_routes_passes_filters(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    region_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/routes?region_id={region_id}&q=pindobal&verified=true&cursor=20&limit=10"
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 0
    service.list_routes.assert_awaited_once_with(
        region_id=region_id,
        q="pindobal",
        saved=None,
        user_id=None,
        verified=True,
        limit=10,
        offset=20,
    )


def test_saved_routes_require_authentication(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    response = client.get("/api/v1/routes?saved=true")
    assert response.status_code == 401
    service.list_routes.assert_not_awaited()


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/v1/routes/{id}", "get_route_detail"),
        ("/api/v1/routes/{id}/origins", "get_route_origins"),
        (f"/api/v1/routes/{{id}}/geometry?origin_id={uuid.uuid4()}", "get_route_geometry"),
        ("/api/v1/routes/{id}/alerts", "get_route_alerts"),
        ("/api/v1/routes/{id}/actors", "list_route_actors"),
        ("/api/v1/routes/{id}/map", "get_route_map_payload"),
        ("/api/v1/actors/{id}", "get_actor_detail"),
    ],
)
def test_resource_not_found(
    api: tuple[TestClient, SimpleNamespace], path: str, method: str
) -> None:
    client, service = api
    response = client.get(path.format(id=uuid.uuid4()))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    getattr(service, method).assert_awaited_once()


def test_list_actor_categories(api: tuple[TestClient, SimpleNamespace]) -> None:
    client, service = api
    response = client.get("/api/v1/actor-categories")
    assert response.status_code == 200
    assert response.json()["data"] == []
    service.list_actor_categories.assert_awaited_once_with()
