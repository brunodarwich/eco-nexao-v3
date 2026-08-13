"""Tests for user profile, preferences, and idempotent favorites (ECO-0604, ECO-0605)."""

import uuid
from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.auth import AuthUser
from app.core.security import get_current_user
from app.main import app
from app.schemas.envelopes import (
    ActorListEnvelope,
    PaginationMeta,
    RouteListEnvelope,
    StandardSuccessResponse,
    UserPreferencesEnvelope,
    UserPreferencesSchema,
    UserProfileEnvelope,
    UserProfileSchema,
)
from app.services.dependencies import get_user_service


@pytest.fixture
def mock_user_service() -> SimpleNamespace:
    user_id = uuid.uuid4()
    profile_schema = UserProfileSchema(
        id=user_id,
        name="Usuário Teste",
        location="Alter do Chão",
        avatar_media_id=None,
        status="active",
    )
    pref_schema = UserPreferencesSchema(
        id=uuid.uuid4(),
        user_id=user_id,
        active_region_id=None,
        screen_reader_mode=False,
        high_contrast=False,
        text_scale=1.0,
        locale="pt-BR",
    )
    service = SimpleNamespace(
        get_profile=AsyncMock(return_value=UserProfileEnvelope(data=profile_schema)),
        update_profile=AsyncMock(return_value=UserProfileEnvelope(data=profile_schema)),
        get_preferences=AsyncMock(return_value=UserPreferencesEnvelope(data=pref_schema)),
        update_preferences=AsyncMock(return_value=UserPreferencesEnvelope(data=pref_schema)),
        get_favorite_routes=AsyncMock(
            return_value=RouteListEnvelope(
                data=[], meta=PaginationMeta(total=0, limit=20, next_cursor=None)
            )
        ),
        add_favorite_route=AsyncMock(return_value=StandardSuccessResponse(success=True)),
        remove_favorite_route=AsyncMock(return_value=StandardSuccessResponse(success=True)),
        get_favorite_actors=AsyncMock(
            return_value=ActorListEnvelope(
                data=[], meta=PaginationMeta(total=0, limit=20, next_cursor=None)
            )
        ),
        add_favorite_actor=AsyncMock(return_value=StandardSuccessResponse(success=True)),
        remove_favorite_actor=AsyncMock(return_value=StandardSuccessResponse(success=True)),
    )
    return service


@pytest.fixture
def api_client(
    mock_user_service: SimpleNamespace,
) -> Generator[tuple[TestClient, SimpleNamespace, AuthUser]]:
    user = AuthUser(

        id=uuid.uuid4(),
        email="test@econexao.org",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": "123"},
    )
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as client:
            yield client, mock_user_service, user
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 1. Unauthenticated Requests (401 Unauthorized)
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,endpoint,body",
    [
        ("GET", "/api/v1/me", None),
        ("PATCH", "/api/v1/me", {"name": "Test"}),
        ("GET", "/api/v1/me/preferences", None),
        ("PATCH", "/api/v1/me/preferences", {"high_contrast": True}),
        ("GET", "/api/v1/me/favorite-routes", None),
        ("PUT", f"/api/v1/me/favorite-routes/{uuid.uuid4()}", None),
        ("DELETE", f"/api/v1/me/favorite-routes/{uuid.uuid4()}", None),
        ("GET", "/api/v1/me/favorite-actors", None),
        ("PUT", f"/api/v1/me/favorite-actors/{uuid.uuid4()}", None),
        ("DELETE", f"/api/v1/me/favorite-actors/{uuid.uuid4()}", None),
    ],
)
def test_unauthenticated_requests_return_401(
    method: str, endpoint: str, body: dict[str, str | bool] | None
) -> None:
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "PATCH":
            response = client.patch(endpoint, json=body)
        elif method == "PUT":
            response = client.put(endpoint, json=body)
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


# -----------------------------------------------------------------------------
# 2. Invalid Input Validation (422 Unprocessable Entity)
# -----------------------------------------------------------------------------


def test_invalid_uuid_returns_422(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, _, _ = api_client
    res_put_route = client.put("/api/v1/me/favorite-routes/invalid-uuid")
    assert res_put_route.status_code == 422

    res_del_route = client.delete("/api/v1/me/favorite-routes/invalid-uuid")
    assert res_del_route.status_code == 422

    res_put_actor = client.put("/api/v1/me/favorite-actors/invalid-uuid")
    assert res_put_actor.status_code == 422

    res_del_actor = client.delete("/api/v1/me/favorite-actors/invalid-uuid")
    assert res_del_actor.status_code == 422


# -----------------------------------------------------------------------------
# 3. Profile Endpoints (200 OK)
# -----------------------------------------------------------------------------


def test_get_my_profile(api_client: tuple[TestClient, SimpleNamespace, AuthUser]) -> None:
    client, service, user = api_client
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Usuário Teste"
    service.get_profile.assert_awaited_once_with(user_id=user.id)


def test_update_my_profile(api_client: tuple[TestClient, SimpleNamespace, AuthUser]) -> None:
    client, service, _ = api_client
    payload = {"name": "Novo Nome", "location": "Santarém, PA"}
    response = client.patch("/api/v1/me", json=payload)
    assert response.status_code == 200
    service.update_profile.assert_awaited_once()


# -----------------------------------------------------------------------------
# 4. Preferences Endpoints (200 OK)
# -----------------------------------------------------------------------------


def test_get_my_preferences(api_client: tuple[TestClient, SimpleNamespace, AuthUser]) -> None:
    client, service, user = api_client
    response = client.get("/api/v1/me/preferences")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["locale"] == "pt-BR"
    service.get_preferences.assert_awaited_once_with(user_id=user.id)


def test_update_my_preferences(api_client: tuple[TestClient, SimpleNamespace, AuthUser]) -> None:
    client, service, _ = api_client
    payload = {"high_contrast": True, "screen_reader_mode": True}
    response = client.patch("/api/v1/me/preferences", json=payload)
    assert response.status_code == 200
    service.update_preferences.assert_awaited_once()


# -----------------------------------------------------------------------------
# 5. Favorite Routes Endpoints (200 OK & Idempotency)
# -----------------------------------------------------------------------------


def test_get_my_favorite_routes(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, user = api_client
    response = client.get("/api/v1/me/favorite-routes")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    service.get_favorite_routes.assert_awaited_once_with(user_id=user.id)


def test_add_favorite_route_idempotent(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    route_id = uuid.uuid4()

    # First PUT
    res1 = client.put(f"/api/v1/me/favorite-routes/{route_id}")
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Second PUT (Idempotent repeat)
    res2 = client.put(f"/api/v1/me/favorite-routes/{route_id}")
    assert res2.status_code == 200
    assert res2.json()["success"] is True

    assert service.add_favorite_route.await_count == 2


def test_remove_favorite_route_idempotent(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    route_id = uuid.uuid4()

    # First DELETE
    res1 = client.delete(f"/api/v1/me/favorite-routes/{route_id}")
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Second DELETE (Idempotent repeat)
    res2 = client.delete(f"/api/v1/me/favorite-routes/{route_id}")
    assert res2.status_code == 200
    assert res2.json()["success"] is True

    assert service.remove_favorite_route.await_count == 2


# -----------------------------------------------------------------------------
# 6. Favorite Actors Endpoints (200 OK & Idempotency)
# -----------------------------------------------------------------------------


def test_get_my_favorite_actors(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, user = api_client
    response = client.get("/api/v1/me/favorite-actors")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    service.get_favorite_actors.assert_awaited_once_with(user_id=user.id)


def test_add_favorite_actor_idempotent(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    actor_id = uuid.uuid4()

    # First PUT
    res1 = client.put(f"/api/v1/me/favorite-actors/{actor_id}")
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Second PUT (Idempotent repeat)
    res2 = client.put(f"/api/v1/me/favorite-actors/{actor_id}")
    assert res2.status_code == 200
    assert res2.json()["success"] is True

    assert service.add_favorite_actor.await_count == 2


def test_remove_favorite_actor_idempotent(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    actor_id = uuid.uuid4()

    # First DELETE
    res1 = client.delete(f"/api/v1/me/favorite-actors/{actor_id}")
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # Second DELETE (Idempotent repeat)
    res2 = client.delete(f"/api/v1/me/favorite-actors/{actor_id}")
    assert res2.status_code == 200
    assert res2.json()["success"] is True

    assert service.remove_favorite_actor.await_count == 2


# -----------------------------------------------------------------------------
# 7. Not Found Error (404 Not Found)
# -----------------------------------------------------------------------------


def test_add_non_existent_favorite_route_returns_404(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    service.add_favorite_route.side_effect = HTTPException(
        status_code=404, detail="A rota solicitada não foi encontrada."
    )

    route_id = uuid.uuid4()
    response = client.put(f"/api/v1/me/favorite-routes/{route_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_add_non_existent_favorite_actor_returns_404(
    api_client: tuple[TestClient, SimpleNamespace, AuthUser],
) -> None:
    client, service, _ = api_client
    service.add_favorite_actor.side_effect = HTTPException(
        status_code=404, detail="O ator solicitado não foi encontrado."
    )

    actor_id = uuid.uuid4()
    response = client.put(f"/api/v1/me/favorite-actors/{actor_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
