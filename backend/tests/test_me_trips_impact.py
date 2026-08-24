"""Tests for user trips and support content (ECO-0606, ECO-0607)."""

import uuid
from collections.abc import Generator
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.auth import AuthUser
from app.core.security import get_current_user
from app.main import app
from app.schemas.envelopes import (
    SupportContentEnvelope,
    TripEnvelope,
    TripListEnvelope,
)
from app.services.dependencies import get_content_service, get_user_service


@pytest.fixture
def mock_user_service() -> SimpleNamespace:
    user_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    route_id = uuid.uuid4()

    trip_data = {
        "id": str(trip_id),
        "user_id": str(user_id),
        "route_id": str(route_id),
        "started_at": "2026-08-12T10:00:00Z",
        "completed_at": None,
        "status": "in_progress",
        "created_at": "2026-08-12T10:00:00Z",
        "updated_at": "2026-08-12T10:00:00Z",
        "route_title": "Rota Pindobal",
    }

    async def mock_create_trip(user_id: uuid.UUID, route_id: uuid.UUID) -> TripEnvelope:
        nonexistent_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        if route_id == nonexistent_id:
            raise HTTPException(status_code=404, detail="A rota solicitada não foi encontrada.")
        return TripEnvelope(
            data={
                "id": str(uuid.uuid4()),
                "user_id": str(user_id),
                "route_id": str(route_id),
                "started_at": "2026-08-12T10:00:00Z",
                "completed_at": None,
                "status": "in_progress",
                "created_at": "2026-08-12T10:00:00Z",
                "updated_at": "2026-08-12T10:00:00Z",
                "route_title": "Rota Pindobal",
            }
        )

    service = SimpleNamespace(
        get_trips=AsyncMock(return_value=TripListEnvelope(data=[trip_data])),
        create_trip=AsyncMock(side_effect=mock_create_trip),
    )
    return service


@pytest.fixture
def mock_content_service() -> SimpleNamespace:
    content_data = {
        "faq": [{"id": "faq-1", "question": "Dúvida?", "answer": "Resposta.", "category": "Geral"}],
        "contacts": {
            "email": "suporte@econexao.org",
            "phone": "+55 93 99999-0000",
            "whatsapp": "https://wa.me/5593999990000",
            "operating_hours": "08:00 - 18:00",
        },
        "help_links": [{"title": "Ajuda", "url": "https://econexao.org"}],
        "editorial_info": {
            "version": "1.0.0",
            "last_updated": "2026-08-12",
            "publisher": "SEMTUR Team",
        },
    }
    service = SimpleNamespace(
        get_support_content=AsyncMock(return_value=SupportContentEnvelope(data=content_data))
    )
    return service


@pytest.fixture
def api_client(
    mock_user_service: SimpleNamespace,
    mock_content_service: SimpleNamespace,
) -> Generator[tuple[TestClient, SimpleNamespace, SimpleNamespace, AuthUser]]:
    user = AuthUser(
        id=uuid.uuid4(),
        email="test@econexao.org",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": "123"},
    )
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_content_service] = lambda: mock_content_service
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as client:
            yield client, mock_user_service, mock_content_service, user
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 1. Unauthenticated Requests (401 Unauthorized)
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,endpoint,body",
    [
        ("GET", "/api/v1/me/trips", None),
        ("POST", "/api/v1/me/trips", {"route_id": str(uuid.uuid4())}),
    ],
)
def test_unauthenticated_endpoints_return_401(
    method: str, endpoint: str, body: dict[str, Any] | None
) -> None:
    app.dependency_overrides.clear()
    with TestClient(app) as unauth_client:
        if method == "GET":
            response = unauth_client.get(endpoint)
        elif method == "POST":
            response = unauth_client.post(endpoint, json=body)
        assert response.status_code == 401
        res_json = response.json()
        assert res_json["error"]["code"] == "UNAUTHORIZED"


# -----------------------------------------------------------------------------
# 2. Authenticated Trips Tests (200/201, 404)
# -----------------------------------------------------------------------------


def test_get_my_trips_success(
    api_client: tuple[TestClient, SimpleNamespace, SimpleNamespace, AuthUser],
) -> None:
    client, mock_user, _, _ = api_client
    response = client.get("/api/v1/me/trips")
    assert response.status_code == 200
    res_json = response.json()
    assert "data" in res_json
    assert isinstance(res_json["data"], list)
    assert len(res_json["data"]) == 1
    assert res_json["data"][0]["route_title"] == "Rota Pindobal"


def test_create_trip_success(
    api_client: tuple[TestClient, SimpleNamespace, SimpleNamespace, AuthUser],
) -> None:
    client, _, _, _ = api_client
    route_id = str(uuid.uuid4())
    response = client.post("/api/v1/me/trips", json={"route_id": route_id})
    assert response.status_code == 201
    res_json = response.json()
    assert "data" in res_json
    assert res_json["data"]["route_id"] == route_id
    assert res_json["data"]["status"] == "in_progress"


def test_create_trip_nonexistent_route_404(
    api_client: tuple[TestClient, SimpleNamespace, SimpleNamespace, AuthUser],
) -> None:
    client, _, _, _ = api_client
    nonexistent_id = "00000000-0000-0000-0000-000000000000"
    response = client.post("/api/v1/me/trips", json={"route_id": nonexistent_id})
    assert response.status_code == 404
    res_json = response.json()
    assert res_json["error"]["code"] == "NOT_FOUND"


# -----------------------------------------------------------------------------
# 3. Support Content Test (200 Public Endpoint)
# -----------------------------------------------------------------------------


def test_get_support_content_success(
    api_client: tuple[TestClient, SimpleNamespace, SimpleNamespace, AuthUser],
) -> None:
    client, _, _, _ = api_client
    response = client.get("/api/v1/content/support")
    assert response.status_code == 200
    res_json = response.json()
    assert "data" in res_json
    assert "faq" in res_json["data"]
    assert "contacts" in res_json["data"]
