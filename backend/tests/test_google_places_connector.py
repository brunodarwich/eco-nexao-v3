"""Contract tests for Places API (New) using HTTPX MockTransport only."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.connectors.google_places import (
    GooglePlacesBudgetExceeded,
    GooglePlacesClient,
    GooglePlacesError,
)


def async_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


@pytest.mark.asyncio
async def test_nearby_uses_new_post_endpoint_minimal_headers_and_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/places:searchNearby"
        assert request.headers["X-Goog-Api-Key"] == "test-secret"
        assert request.headers["X-Goog-FieldMask"] == (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.primaryType"
        )
        body = json.loads(request.content)
        assert body == {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": -2.45, "longitude": -54.7},
                    "radius": 1500,
                }
            },
            "maxResultCount": 5,
            "includedTypes": ["restaurant"],
        }
        return httpx.Response(200, json={"places": [{"id": "place-1"}]})

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("test-secret", client=client)
        result = await connector.nearby_search(
            latitude=-2.45,
            longitude=-54.7,
            radius_m=1500,
            included_types=["restaurant"],
            max_results=5,
        )

    assert result.places[0]["id"] == "place-1"
    assert connector.metrics.calls == 1
    assert connector.metrics.successes == 1


@pytest.mark.asyncio
async def test_text_search_paginates_with_matching_body_and_page_token() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        assert request.url.path == "/v1/places:searchText"
        if len(bodies) == 1:
            return httpx.Response(200, json={"places": [{"id": "one"}], "nextPageToken": "token-2"})
        return httpx.Response(200, json={"places": [{"id": "two"}]})

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("test-secret", client=client)
        result = await connector.text_search(
            "artesanato em Santarem",
            page_size=10,
            max_pages=3,
            location_bias={
                "circle": {
                    "center": {"latitude": -2.45, "longitude": -54.7},
                    "radius": 5000,
                }
            },
        )

    assert [place["id"] for place in result.places] == ["one", "two"]
    assert result.next_page_token is None
    assert bodies[1] == {**bodies[0], "pageToken": "token-2"}
    assert connector.metrics.calls == 2


@pytest.mark.asyncio
async def test_text_search_returns_unconsumed_token_at_page_limit() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"places": [{"id": "one"}], "nextPageToken": "more"}
        )
    )
    async with async_client(transport) as client:
        result = await GooglePlacesClient("key", client=client).text_search("pousada")
    assert result.next_page_token == "more"


@pytest.mark.asyncio
async def test_details_url_encodes_place_id_and_uses_detail_mask() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.raw_path == b"/v1/places/id%2Fwith%20space"
        assert request.headers["X-Goog-FieldMask"] == "id,displayName"
        return httpx.Response(200, json={"id": "id/with space"})

    async with async_client(httpx.MockTransport(handler)) as client:
        result = await GooglePlacesClient("key", client=client).place_details(
            "id/with space", fields=("id", "displayName")
        )
    assert result["id"] == "id/with space"


@pytest.mark.asyncio
async def test_retries_429_5xx_and_network_with_exponential_delays() -> None:
    attempts = 0
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectTimeout("sensitive network detail", request=request)
        if attempts == 2:
            return httpx.Response(429, json={"error": {"message": "sensitive payload"}})
        if attempts == 3:
            return httpx.Response(503, text="sensitive payload")
        return httpx.Response(200, json={"places": []})

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient(
            "key",
            client=client,
            max_retries=3,
            retry_base_delay_s=0.5,
            sleep=fake_sleep,
        )
        await connector.text_search("hotel")

    assert attempts == 4
    assert delays == [0.5, 1.0, 2.0]
    assert connector.metrics.retries == 3


@pytest.mark.asyncio
async def test_does_not_retry_non_retryable_4xx_and_error_is_safe() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, text="payload-secret-marker")

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("api-key-secret-marker", client=client, max_retries=3)
        with pytest.raises(GooglePlacesError) as captured:
            await connector.text_search("hotel")

    assert calls == 1
    assert "payload-secret-marker" not in str(captured.value)
    assert "api-key-secret-marker" not in str(captured.value)
    assert connector.metrics.failures == 1


@pytest.mark.asyncio
async def test_retry_exhaustion_does_not_leak_network_or_payload_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("network-secret-marker", request=request)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client, max_retries=1, sleep=no_sleep)
        with pytest.raises(GooglePlacesError) as captured:
            await connector.text_search("hotel")
    assert "network-secret-marker" not in str(captured.value)
    assert connector.metrics.calls == 2
    assert connector.metrics.failures == 1


async def no_sleep(delay: float) -> None:
    del delay


@pytest.mark.asyncio
async def test_budget_counts_every_http_attempt_and_stops_before_network() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient(
            "key", client=client, call_budget=2, max_retries=5, sleep=no_sleep
        )
        with pytest.raises(GooglePlacesBudgetExceeded):
            await connector.text_search("hotel")

    assert calls == 2
    assert connector.metrics.calls == 2
    assert connector.metrics.retries == 2
    assert connector.metrics.budget_exhaustions == 1


@pytest.mark.asyncio
async def test_field_masks_reject_wildcards_and_unknown_or_wrong_shape_fields() -> None:
    transport = httpx.MockTransport(lambda request: pytest.fail("network must not be called"))
    async with async_client(transport) as client:
        connector = GooglePlacesClient("key", client=client)
        with pytest.raises(ValueError, match="unsupported"):
            await connector.text_search("hotel", fields=("*",))
        with pytest.raises(ValueError, match="unsupported"):
            await connector.place_details("id", fields=("places.id",))
        with pytest.raises(ValueError, match="at least one"):
            await connector.text_search("hotel", fields=())


@pytest.mark.asyncio
async def test_invalid_response_is_safe_and_input_validation_precedes_network() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"places": "bad"}))
    async with async_client(transport) as client:
        connector = GooglePlacesClient("key", client=client)
        with pytest.raises(GooglePlacesError, match="invalid response"):
            await connector.text_search("hotel")
        with pytest.raises(ValueError):
            await connector.nearby_search(latitude=91, longitude=0, radius_m=10)


def test_configuration_validation() -> None:
    with pytest.raises(ValueError):
        GooglePlacesClient("")
    with pytest.raises(ValueError):
        GooglePlacesClient("key", call_budget=0)
    with pytest.raises(ValueError):
        GooglePlacesClient("key", max_retries=-1)
    with pytest.raises(ValueError):
        GooglePlacesClient("key", timeout_s=0)


def test_metrics_are_scalar_only_and_do_not_retain_key_or_payload() -> None:
    metrics = GooglePlacesClient("secret-key").metrics
    assert metrics.calls == 0
    assert not hasattr(metrics, "api_key")
    assert not hasattr(metrics, "payload")
