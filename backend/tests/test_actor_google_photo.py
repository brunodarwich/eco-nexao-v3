from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.actors import get_actor_google_photo_service
from app.connectors.google_places import GooglePlacesClient, GooglePlacesError
from app.main import app
from app.repositories.territorial import TerritorialRepository
from app.services.actor_google_photo import (
    ActorGooglePhotoService,
    ActorGooglePhotoUnavailable,
    ActorGooglePhotoUpstreamUnavailable,
)
from app.services.google_photo_proxy import GooglePhotoProxyService


class _Repository:
    def __init__(self, place_id: str | None = "place-1") -> None:
        self.place_id = place_id

    async def get_active_google_place_id(self, _: uuid.UUID) -> str | None:
        return self.place_id


async def _fetcher(_: str, __: int, ___: int) -> tuple[bytes, str]:
    return b"photo", "image/jpeg"


@pytest.mark.asyncio
async def test_issues_opaque_grant_from_fresh_details_mock_transport() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "photos": [
                    {
                        "name": "places/place-1/photos/fresh-resource",
                        "widthPx": 1200,
                        "heightPx": 900,
                        "authorAttributions": [
                            {"displayName": "Ana", "uri": "//maps.google.com/maps/contrib/1"}
                        ],
                    }
                ],
                "googleMapsUri": "https://www.google.com/maps/place/example",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        places = GooglePlacesClient("test-key", client=http_client)
        service = ActorGooglePhotoService(_Repository(), places, GooglePhotoProxyService(_fetcher))
        grant = await service.issue(uuid.uuid4())

    assert "places/" not in grant.token
    assert grant.attributions == (
        {"display_name": "Ana", "uri": "https://maps.google.com/maps/contrib/1"},
    )
    assert seen[0].headers["X-Goog-FieldMask"] == "photos,googleMapsUri"
    assert "test-key" not in str(seen[0].url)


@pytest.mark.asyncio
async def test_canonical_google_places_reference_is_selected_and_can_issue_grant() -> None:
    db = MagicMock()
    db.scalar = AsyncMock(return_value="place-1")
    repository = TerritorialRepository(db)
    assert await repository.get_active_google_place_id(uuid.uuid4()) == "place-1"
    statement = db.scalar.await_args.args[0]
    compiled = statement.compile()
    assert "google_places" in compiled.params.values()

    class Places:
        async def place_details(self, *_: object, **__: object) -> object:
            return {
                "photos": [
                    {"name": "places/place-1/photos/current", "widthPx": 10, "heightPx": 10}
                ],
                "googleMapsUri": "https://www.google.com/maps/place/example",
            }

    grant = await ActorGooglePhotoService(
        repository,
        Places(),
        GooglePhotoProxyService(_fetcher),  # type: ignore[arg-type]
    ).issue(uuid.uuid4())
    assert grant.token and "places/" not in grant.token


def test_actor_endpoint_is_safe_for_success_no_photo_and_upstream_failure() -> None:
    actor_id = uuid.uuid4()

    class SuccessfulService:
        async def issue(self, _: uuid.UUID):  # type: ignore[no-untyped-def]
            return GooglePhotoProxyService(_fetcher).grant(
                resource_name="places/place-1/photos/fresh-resource",
                attributions=[{"display_name": "Ana"}],
                google_maps_uri="https://www.google.com/maps/place/example",
                width_px=1200,
                height_px=900,
            )

    app.dependency_overrides[get_actor_google_photo_service] = SuccessfulService
    try:
        response = TestClient(app).get(f"/api/v1/actors/{actor_id}/google-photo")
        assert response.status_code == 200
        assert "places/place-1" not in response.text
        assert "googleusercontent" not in response.text
        assert response.json()["data"]["author_attributions"] == [
            {"display_name": "Ana", "uri": None}
        ]
    finally:
        app.dependency_overrides.clear()

    class NoPhotoService:
        async def issue(self, _: uuid.UUID) -> object:
            raise ActorGooglePhotoUnavailable("photo unavailable")

    app.dependency_overrides[get_actor_google_photo_service] = NoPhotoService
    try:
        assert TestClient(app).get(f"/api/v1/actors/{actor_id}/google-photo").status_code == 404
    finally:
        app.dependency_overrides.clear()

    class UnavailableService:
        async def issue(self, _: uuid.UUID) -> object:
            raise ActorGooglePhotoUpstreamUnavailable("https://upstream.example/private")

    app.dependency_overrides[get_actor_google_photo_service] = UnavailableService
    try:
        response = TestClient(app).get(f"/api/v1/actors/{actor_id}/google-photo")
        assert response.status_code == 503
        assert "upstream.example" not in response.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_missing_reconciled_reference_and_upstream_error_fail_closed() -> None:
    service = ActorGooglePhotoService(
        _Repository(None),
        GooglePlacesClient("test-key", enabled=False),
        GooglePhotoProxyService(_fetcher),
    )
    with pytest.raises(Exception) as missing:
        await service.issue(uuid.uuid4())
    assert "place" not in str(missing.value).lower()

    class BrokenPlaces:
        async def place_details(self, *_: object, **__: object) -> object:
            raise GooglePlacesError("https://upstream.example/private")

    broken = ActorGooglePhotoService(
        _Repository(), BrokenPlaces(), GooglePhotoProxyService(_fetcher)
    )  # type: ignore[arg-type]
    with pytest.raises(Exception) as upstream:
        await broken.issue(uuid.uuid4())
    assert "upstream.example" not in str(upstream.value)
