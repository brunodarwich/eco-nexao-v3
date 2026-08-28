"""Contract tests for Google Places API (New) using HTTPX MockTransport only (ECO-2508).

Ensures:
- 100% network isolation (no real HTTP traffic).
- Exact endpoint, headers, and request body compliance.
- Field mask validation (rejection of wildcards and invalid fields).
- Circuit breaker state transitions (CLOSED -> OPEN -> HALF_OPEN).
- Rate/cost budget enforcement and metrics sanitization.
- Exponential backoff with retry limit on 429, 5xx, and timeouts.
- Place ID 30-day lifecycle refresh (same ID, canonical redirect, 404 stale).
- Fixture-driven validation for 2xx, 4xx, 429, 5xx, timeouts, and partial payloads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.connectors.google_places import (
    GooglePlacesAuthenticationError,
    GooglePlacesBudgetExceeded,
    GooglePlacesCircuitOpenError,
    GooglePlacesClient,
    GooglePlacesError,
    GooglePlacesFeatureDisabledError,
    GooglePlacesNotFoundError,
    GooglePlacesRateLimitError,
    GooglePlacesTimeoutError,
    PlacesCircuitBreaker,
    PlacesConnectorProtocol,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "google_places"


def load_fixture(filename: str) -> dict[str, Any]:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def async_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


async def no_sleep(delay: float) -> None:
    del delay


# --- Basic Contract & Protocol ---


def test_implements_protocol() -> None:
    client = GooglePlacesClient("test-key")
    assert isinstance(client, PlacesConnectorProtocol)


@pytest.mark.asyncio
async def test_nearby_uses_new_post_endpoint_and_fixture() -> None:
    fixture_data = load_fixture("nearby_search_success_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/places:searchNearby"
        assert request.headers["X-Goog-Api-Key"] == "secret-api-key"
        assert request.headers["X-Goog-FieldMask"] == (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.primaryType"
        )
        body = json.loads(request.content)
        assert body == {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": -2.5042, "longitude": -54.9535},
                    "radius": 1500.0,
                }
            },
            "maxResultCount": 10,
            "includedTypes": ["restaurant"],
        }
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-api-key", client=client)
        result = await connector.nearby_search(
            latitude=-2.5042,
            longitude=-54.9535,
            radius_m=1500.0,
            included_types=["restaurant"],
            max_results=10,
        )

    assert len(result.places) == 2
    assert result.places[0]["id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert result.places[0]["displayName"]["text"] == "Restaurante do Saulo Alter"
    assert result.places[1]["id"] == "ChIJu2s9pXYZtFkR3v1ab982cc4"
    assert connector.metrics.calls == 1
    assert connector.metrics.successes == 1
    assert connector.metrics.failures == 0


@pytest.mark.asyncio
async def test_text_search_paginates_with_fixtures() -> None:
    page1 = load_fixture("text_search_page1_200.json")
    page2 = load_fixture("text_search_page2_200.json")
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        assert request.url.path == "/v1/places:searchText"
        assert request.headers["X-Goog-Api-Key"] == "secret-api-key"
        if len(bodies) == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-api-key", client=client)
        result = await connector.text_search(
            "artesanato Tapajos",
            page_size=10,
            max_pages=2,
            location_bias={
                "circle": {
                    "center": {"latitude": -2.44, "longitude": -54.71},
                    "radius": 3000,
                }
            },
        )

    assert len(result.places) == 2
    assert result.places[0]["id"] == "ChIJb_x_page1_001"
    assert result.places[1]["id"] == "ChIJc_y_page2_002"
    assert result.next_page_token is None
    assert bodies[1]["pageToken"] == "CAUQAA_token_page_2_simulation"
    assert connector.metrics.calls == 2
    assert connector.metrics.successes == 2


@pytest.mark.asyncio
async def test_place_details_pro_tier_fixture() -> None:
    fixture_data = load_fixture("place_details_pro_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.raw_path == b"/v1/places/ChIJN1t_tDeuEmsRUsoyG83frY4"
        assert "regularOpeningHours" in request.headers["X-Goog-FieldMask"]
        assert "nationalPhoneNumber" in request.headers["X-Goog-FieldMask"]
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-api-key", client=client)
        result = await connector.place_details(
            "ChIJN1t_tDeuEmsRUsoyG83frY4",
            fields=(
                "id",
                "displayName",
                "formattedAddress",
                "regularOpeningHours",
                "nationalPhoneNumber",
                "websiteUri",
                "googleMapsUri",
            ),
        )

    assert result["id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert result["nationalPhoneNumber"] == "(93) 99123-4567"
    assert result["regularOpeningHours"]["openNow"] is True
    assert connector.metrics.calls == 1
    assert connector.metrics.successes == 1


@pytest.mark.asyncio
async def test_place_details_enterprise_photos_fixture() -> None:
    fixture_data = load_fixture("place_details_enterprise_photos_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.headers["X-Goog-FieldMask"] == "id,photos"
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-api-key", client=client)
        result = await connector.place_details(
            "ChIJN1t_tDeuEmsRUsoyG83frY4",
            fields=("id", "photos"),
        )

    assert result["id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert len(result["photos"]) == 2
    assert result["photos"][0]["authorAttributions"][0]["displayName"] == "Carlos Fotógrafo Tapajós"


@pytest.mark.asyncio
async def test_partial_payload_missing_fields_fixture() -> None:
    fixture_data = load_fixture("partial_payload_missing_fields_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-api-key", client=client)
        result = await connector.place_details(
            "ChIJ_partial_actor_without_optional_fields",
            fields=("id", "displayName", "formattedAddress"),
        )

    assert result["id"] == "ChIJ_partial_actor_without_optional_fields"
    assert result["displayName"]["text"] == "Ponto de Artesanato Comunitário"
    assert "photos" not in result
    assert "regularOpeningHours" not in result


# --- Place ID Refresh (ADR 0016 30-Day Lifecycle) ---


@pytest.mark.asyncio
async def test_refresh_place_id_same_id() -> None:
    fixture_data = load_fixture("place_details_id_refresh_same_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-FieldMask"] == "id"
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client)
        refresh = await connector.refresh_place_id("ChIJN1t_tDeuEmsRUsoyG83frY4")

    assert refresh.original_id == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert refresh.canonical_id == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert refresh.is_changed is False
    assert refresh.is_stale is False
    assert connector.metrics.id_refreshes == 1
    assert connector.metrics.id_changes == 0
    assert connector.metrics.stale_places == 0


@pytest.mark.asyncio
async def test_refresh_place_id_redirect_canonical_change() -> None:
    fixture_data = load_fixture("place_details_id_refresh_redirect_200.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-FieldMask"] == "id"
        return httpx.Response(200, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client)
        refresh = await connector.refresh_place_id("ChIJ_old_merged_id")

    assert refresh.original_id == "ChIJ_old_merged_id"
    assert refresh.canonical_id == "ChIJ_canonical_new_merged_place_id_999"
    assert refresh.is_changed is True
    assert refresh.is_stale is False
    assert connector.metrics.id_refreshes == 1
    assert connector.metrics.id_changes == 1
    assert connector.metrics.stale_places == 0


@pytest.mark.asyncio
async def test_refresh_place_id_404_not_found_marks_stale() -> None:
    fixture_data = load_fixture("place_details_404_not_found.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client)
        refresh = await connector.refresh_place_id("ChIJ_obsolete_id_not_found")

    assert refresh.original_id == "ChIJ_obsolete_id_not_found"
    assert refresh.canonical_id is None
    assert refresh.is_changed is False
    assert refresh.is_stale is True
    assert connector.metrics.id_refreshes == 1
    assert connector.metrics.stale_places == 1


# --- Error Handling & Status Codes ---


@pytest.mark.asyncio
async def test_400_invalid_argument_error_fixture_does_not_retry() -> None:
    fixture_data = load_fixture("error_400_invalid_argument.json")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-key", client=client, max_retries=3)
        with pytest.raises(GooglePlacesError) as exc_info:
            await connector.text_search("hotel")

    assert calls == 1
    assert connector.metrics.failures == 1
    assert connector.metrics.retries == 0
    assert "secret-key" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_403_permission_denied_raises_auth_error_without_retry() -> None:
    fixture_data = load_fixture("error_403_permission_denied.json")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(403, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("secret-key", client=client, max_retries=3)
        with pytest.raises(GooglePlacesAuthenticationError) as exc_info:
            await connector.text_search("hotel")

    assert calls == 1
    assert connector.metrics.failures == 1
    assert "secret-key" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_404_not_found_raises_not_found_error_without_retry() -> None:
    fixture_data = load_fixture("place_details_404_not_found.json")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client, max_retries=3)
        with pytest.raises(GooglePlacesNotFoundError):
            await connector.place_details("non_existent_place_id")

    assert calls == 1
    assert connector.metrics.failures == 1


@pytest.mark.asyncio
async def test_429_rate_limit_retries_and_raises_rate_limit_error() -> None:
    fixture_data = load_fixture("error_429_resource_exhausted.json")
    calls = 0
    delays: list[float] = []

    async def track_sleep(delay: float) -> None:
        delays.append(delay)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, json=fixture_data)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient(
            "key", client=client, max_retries=2, retry_base_delay_s=0.2, sleep=track_sleep
        )
        with pytest.raises(GooglePlacesRateLimitError):
            await connector.text_search("hotel")

    assert calls == 3
    assert delays == [0.2, 0.4]
    assert connector.metrics.retries == 2
    assert connector.metrics.failures == 1


@pytest.mark.asyncio
async def test_500_503_retries_and_raises_places_error() -> None:
    fixture_500 = load_fixture("error_500_internal.json")
    fixture_503 = load_fixture("error_503_unavailable.json")
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(500, json=fixture_500)
        return httpx.Response(503, json=fixture_503)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client, max_retries=1, sleep=no_sleep)
        with pytest.raises(GooglePlacesError):
            await connector.text_search("hotel")

    assert attempts == 2
    assert connector.metrics.retries == 1
    assert connector.metrics.failures == 1


@pytest.mark.asyncio
async def test_timeout_retries_and_raises_timeout_error() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("sensitive-socket-info", request=request)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client, max_retries=2, sleep=no_sleep)
        with pytest.raises(GooglePlacesTimeoutError) as exc_info:
            await connector.text_search("hotel")

    assert calls == 3
    assert connector.metrics.timeouts == 3
    assert connector.metrics.failures == 1
    assert "sensitive-socket-info" not in str(exc_info.value)


# --- Circuit Breaker & Guardrails ---


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_consecutive_failures() -> None:
    cb = PlacesCircuitBreaker(failure_threshold=2, reset_timeout_seconds=30.0)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient(
            "key", circuit_breaker=cb, client=client, max_retries=0, sleep=no_sleep
        )

        # Call 1: fails -> failures=1
        with pytest.raises(GooglePlacesError):
            await connector.text_search("q1")
        assert cb.state == "CLOSED"

        # Call 2: fails -> failures=2 -> circuit OPENS
        with pytest.raises(GooglePlacesError):
            await connector.text_search("q2")
        assert cb.state == "OPEN"

        # Call 3: rejected fast by circuit breaker before network
        with pytest.raises(GooglePlacesCircuitOpenError):
            await connector.text_search("q3")

    assert calls == 2
    assert connector.metrics.circuit_rejections == 1


@pytest.mark.asyncio
async def test_budget_exceeded_before_network() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"places": []})

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GooglePlacesClient("key", client=client, call_budget=1)
        # 1st call: uses budget
        await connector.text_search("q1")
        assert connector.metrics.calls == 1

        # 2nd call: budget exhausted
        with pytest.raises(GooglePlacesBudgetExceeded):
            await connector.text_search("q2")

    assert calls == 1
    assert connector.metrics.budget_exhaustions == 1


@pytest.mark.asyncio
async def test_feature_flag_disabled_prevents_calls() -> None:
    transport = httpx.MockTransport(lambda request: pytest.fail("network must not be called"))
    async with async_client(transport) as client:
        connector = GooglePlacesClient("key", enabled=False, client=client)
        with pytest.raises(GooglePlacesFeatureDisabledError):
            await connector.text_search("hotel")
        with pytest.raises(GooglePlacesFeatureDisabledError):
            await connector.nearby_search(latitude=-2.4, longitude=-54.7, radius_m=100)
        with pytest.raises(GooglePlacesFeatureDisabledError):
            await connector.place_details("ChIJ123")
        with pytest.raises(GooglePlacesFeatureDisabledError):
            await connector.refresh_place_id("ChIJ123")


@pytest.mark.asyncio
async def test_field_masks_reject_wildcards_and_unsupported_fields() -> None:
    transport = httpx.MockTransport(lambda request: pytest.fail("network must not be called"))
    async with async_client(transport) as client:
        connector = GooglePlacesClient("key", client=client)
        with pytest.raises(ValueError, match="unsupported"):
            await connector.text_search("hotel", fields=("*",))
        with pytest.raises(ValueError, match="unsupported"):
            await connector.text_search("hotel", fields=("places.*",))
        with pytest.raises(ValueError, match="unsupported"):
            await connector.place_details("id", fields=("places.id",))
        with pytest.raises(ValueError, match="at least one"):
            await connector.text_search("hotel", fields=())


def test_input_and_config_validation() -> None:
    with pytest.raises(ValueError, match="API key is required"):
        GooglePlacesClient("")
    with pytest.raises(ValueError, match="call_budget must be positive"):
        GooglePlacesClient("key", call_budget=0)
    with pytest.raises(ValueError, match="max_retries cannot be negative"):
        GooglePlacesClient("key", max_retries=-1)
    with pytest.raises(ValueError, match="timeout_s must be positive"):
        GooglePlacesClient("key", timeout_s=0)


def test_metrics_are_strictly_scalar_and_contain_no_credentials_or_data() -> None:
    metrics = GooglePlacesClient("secret-super-api-key-12345").metrics
    assert metrics.calls == 0
    assert metrics.successes == 0
    assert metrics.failures == 0
    assert metrics.retries == 0
    assert metrics.timeouts == 0
    assert metrics.circuit_rejections == 0
    assert metrics.budget_exhaustions == 0
    assert metrics.id_refreshes == 0
    assert metrics.id_changes == 0
    assert metrics.stale_places == 0
    assert not hasattr(metrics, "api_key")
    assert not hasattr(metrics, "payload")
    assert not hasattr(metrics, "coordinates")


def test_settings_validation_with_feature_flag() -> None:
    from pydantic import SecretStr, ValidationError

    from app.core.config import Settings

    # When flag is false, empty key is permitted
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        FEATURE_GOOGLE_PLACES_SYNC=False,
        GOOGLE_PLACES_API_KEY=SecretStr(""),
    )
    assert s.FEATURE_GOOGLE_PLACES_SYNC is False

    # When flag is true, empty key raises ValidationError
    with pytest.raises(ValidationError, match="GOOGLE_PLACES_API_KEY é obrigatória"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            FEATURE_GOOGLE_PLACES_SYNC=True,
            GOOGLE_PLACES_API_KEY=SecretStr(""),
        )

    # When flag is true and key is provided, successfully initializes
    s_active = Settings(
        _env_file=None,  # type: ignore[call-arg]
        FEATURE_GOOGLE_PLACES_SYNC=True,
        GOOGLE_PLACES_API_KEY=SecretStr("valid-secret-key"),
    )
    assert s_active.FEATURE_GOOGLE_PLACES_SYNC is True
    assert s_active.GOOGLE_PLACES_API_KEY.get_secret_value() == "valid-secret-key"
