from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.place_photos import get_google_photo_proxy
from app.connectors.google_places import GooglePlacesClient
from app.main import app
from app.services.google_photo_proxy import (
    GooglePhotoProxyService,
    PhotoProxyExpired,
    PhotoProxyNotFound,
)


async def _fixture_fetcher(name: str, height: int, width: int) -> tuple[bytes, str]:
    assert name == "places/place-1/photos/photo-1"
    assert (height, width) == (600, 800)
    return b"fixture-photo", "image/jpeg"


@pytest.mark.asyncio
async def test_grant_is_opaque_one_time_and_keeps_attribution_out_of_storage() -> None:
    proxy = GooglePhotoProxyService(_fixture_fetcher, ttl_seconds=60)
    grant = proxy.grant(
        resource_name="places/place-1/photos/photo-1",
        attributions=[{"displayName": "Photographer", "uri": "https://maps.google.com/user"}],
        google_maps_uri="https://www.google.com/maps/place/example",
        width_px=1200,
        height_px=900,
        now=100,
    )
    assert "places/" not in grant.token
    assert grant.attributions[0]["displayName"] == "Photographer"
    assert grant.google_maps_uri.endswith("/example")
    assert await proxy.consume(grant.token, max_height_px=600, max_width_px=800, now=101) == (
        b"fixture-photo",
        "image/jpeg",
    )
    with pytest.raises(PhotoProxyNotFound):
        await proxy.consume(grant.token, max_height_px=600, max_width_px=800, now=101)


@pytest.mark.asyncio
async def test_expired_grant_is_removed_without_upstream_call() -> None:
    proxy = GooglePhotoProxyService(_fixture_fetcher, ttl_seconds=1)
    grant = proxy.grant(
        resource_name="places/place-1/photos/photo-1",
        attributions=[],
        google_maps_uri="https://www.google.com/maps/place/example",
        width_px=1200,
        height_px=900,
        now=100,
    )
    with pytest.raises(PhotoProxyExpired):
        await proxy.consume(grant.token, max_height_px=600, max_width_px=800, now=101)


@pytest.mark.asyncio
async def test_connector_proxies_fixture_binary_without_exposing_redirect_url() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "places.googleapis.com":
            assert request.headers["X-Goog-Api-Key"] == "test-key"
            return httpx.Response(
                302,
                headers={"location": "https://lh3.googleusercontent.com/photo/opaque"},
            )
        assert request.url.host == "lh3.googleusercontent.com"
        assert "X-Goog-Api-Key" not in request.headers
        return httpx.Response(200, content=b"jpeg", headers={"content-type": "image/jpeg"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = GooglePlacesClient("test-key", client=http_client)
        assert await client.fetch_photo(
            "places/place-1/photos/photo-1", max_height_px=600, max_width_px=800
        ) == (b"jpeg", "image/jpeg")
    assert seen[0].url.params["maxHeightPx"] == "600"
    assert "skipHttpRedirect" not in str(seen[0].url)
    assert len(seen) == 2


@pytest.mark.asyncio
async def test_connector_rejects_non_google_photo_redirect_without_requesting_it() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(302, headers={"location": "https://attacker.invalid/photo"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GooglePlacesClient("test-key", client=http_client)
        with pytest.raises(Exception, match="photo request failed"):
            await client.fetch_photo(
                "places/place-1/photos/photo-1", max_height_px=600, max_width_px=800
            )
    assert len(seen) == 1


def test_metadata_and_binary_endpoints_are_safe_and_no_store() -> None:
    proxy = GooglePhotoProxyService(_fixture_fetcher, ttl_seconds=60)
    grant = proxy.grant(
        resource_name="places/place-1/photos/photo-1",
        attributions=[{"display_name": "Photographer", "uri": "https://maps.google.com/user"}],
        google_maps_uri="https://www.google.com/maps/place/example",
        width_px=1200,
        height_px=900,
    )
    app.dependency_overrides[get_google_photo_proxy] = lambda: proxy
    try:
        client = TestClient(app)
        metadata = client.get(f"/api/v1/places/photos/{grant.token}/metadata")
        assert metadata.status_code == 200
        assert metadata.headers["cache-control"] == "no-store, max-age=0"
        assert metadata.json()["data"] == {
            "proxy_url": f"/api/v1/places/photos/{grant.token}",
            "expires_at": grant.expires_at,
            "width_px": 1200,
            "height_px": 900,
            "author_attributions": [
                {"display_name": "Photographer", "uri": "https://maps.google.com/user"}
            ],
            "google_maps_uri": "https://www.google.com/maps/place/example",
        }
        assert "places/place-1" not in metadata.text and "photoUri" not in metadata.text
        binary = client.get(f"/api/v1/places/photos/{grant.token}")
        assert binary.status_code == 200 and binary.headers["cache-control"] == "no-store"
        assert client.get(f"/api/v1/places/photos/{grant.token}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_endpoint_returns_410_for_expired_and_503_without_leaking_resource() -> None:
    async def failing_fetcher(_: str, __: int, ___: int) -> tuple[bytes, str]:
        raise RuntimeError("https://lh3.googleusercontent.com/private")

    proxy = GooglePhotoProxyService(failing_fetcher, ttl_seconds=1)
    expired = proxy.grant(
        resource_name="places/place-1/photos/photo-1",
        attributions=[],
        google_maps_uri="https://www.google.com/maps/place/example",
        width_px=1,
        height_px=1,
        now=0,
    )
    live = proxy.grant(
        resource_name="places/place-1/photos/photo-1",
        attributions=[],
        google_maps_uri="https://www.google.com/maps/place/example",
        width_px=1,
        height_px=1,
    )
    app.dependency_overrides[get_google_photo_proxy] = lambda: proxy
    try:
        client = TestClient(app)
        assert client.get(f"/api/v1/places/photos/{expired.token}/metadata").status_code == 410
        response = client.get(f"/api/v1/places/photos/{live.token}")
        assert response.status_code == 503
        assert "lh3.googleusercontent" not in response.text
    finally:
        app.dependency_overrides.clear()
