"""Bounded, safe server-side client for Google Places API (New) (ECO-2508 / ADR 0016).

Complies with Google Maps Platform Terms of Service:
- Mandatory X-Goog-FieldMask with surgical fields (no wildcards).
- Secret-only credential handling (never logged or leaked in exceptions/metrics).
- Bounded retries with exponential backoff on 429/5xx and network timeouts.
- Thread-safe Circuit Breaker and call budget cost guard.
- Place ID refresh helper for 30-day lifecycle verification.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable
from urllib.parse import quote, urlparse

import httpx

logger = logging.getLogger(__name__)

PLACES_BASE_URL = "https://places.googleapis.com/v1"

# Allowed surgical fields for search endpoints (prefixed with places. or root pagination)
SEARCH_FIELD_ALLOWLIST = frozenset(
    {
        "places.id",
        "places.name",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.primaryType",
        "places.types",
        "places.businessStatus",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.regularOpeningHours",
        "places.currentOpeningHours",
        "places.googleMapsUri",
        "places.googleMapsLinks.placeUri",
        "places.photos",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "nextPageToken",
    }
)

# Allowed surgical fields for Place Details (unprefixed)
DETAIL_FIELD_ALLOWLIST = frozenset(
    field.removeprefix("places.") for field in SEARCH_FIELD_ALLOWLIST if field.startswith("places.")
)

DEFAULT_NEARBY_FIELDS = (
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.primaryType",
)
DEFAULT_TEXT_FIELDS = (*DEFAULT_NEARBY_FIELDS, "nextPageToken")
DEFAULT_DETAIL_FIELDS = tuple(field.removeprefix("places.") for field in DEFAULT_NEARBY_FIELDS)


class GooglePlacesError(Exception):
    """Safe upstream failure which never includes credentials, coordinates or response payloads."""


class GooglePlacesBudgetExceeded(GooglePlacesError):
    """Raised before an HTTP call would exceed the configured request budget."""


class GooglePlacesCircuitOpenError(GooglePlacesError):
    """Raised when the circuit breaker is open due to consecutive failures."""


class GooglePlacesRateLimitError(GooglePlacesError):
    """Raised when upstream returns HTTP 429 / RESOURCE_EXHAUSTED."""


class GooglePlacesNotFoundError(GooglePlacesError):
    """Raised when a place resource is not found (HTTP 404)."""


class GooglePlacesAuthenticationError(GooglePlacesError):
    """Raised when authentication fails or API key is rejected (HTTP 401/403)."""


class GooglePlacesTimeoutError(GooglePlacesError):
    """Raised when an HTTP request exceeds the configured timeout."""


class GooglePlacesFeatureDisabledError(GooglePlacesError):
    """Raised when Places API synchronization is disabled via feature flag."""


@dataclass(frozen=True, slots=True)
class GooglePlacesMetrics:
    """Local counters suitable for a job report; no request or credential data is retained."""

    calls: int
    successes: int
    failures: int
    retries: int
    timeouts: int = 0
    circuit_rejections: int = 0
    budget_exhaustions: int = 0
    id_refreshes: int = 0
    id_changes: int = 0
    stale_places: int = 0


@dataclass(frozen=True, slots=True)
class GooglePlacesSearchResult:
    """A provider response split into places and an optional continuation token."""

    places: tuple[Mapping[str, Any], ...]
    next_page_token: str | None = None


@dataclass(frozen=True, slots=True)
class PlaceIdRefreshResult:
    """Outcome of a Place ID refresh query (ADR 0016 30-day lifecycle check)."""

    original_id: str
    canonical_id: str | None
    is_changed: bool
    is_stale: bool


class PlacesCircuitBreaker:
    """Thread-safe circuit breaker shared by Google Places connector instances."""

    def __init__(self, failure_threshold: int = 5, reset_timeout_seconds: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.consecutive_failures = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        with self._lock:
            if self.state == "OPEN":
                if time.monotonic() - self.last_failure_time >= self.reset_timeout_seconds:
                    self.state = "HALF_OPEN"
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.consecutive_failures = 0
            self.state = "CLOSED"

    def record_failure(self) -> None:
        with self._lock:
            self.consecutive_failures += 1
            self.last_failure_time = time.monotonic()
            if self.consecutive_failures >= self.failure_threshold:
                self.state = "OPEN"


@runtime_checkable
class PlacesConnectorProtocol(Protocol):
    """Structural protocol for Google Places connectors."""

    async def nearby_search(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        included_types: Sequence[str] = (),
        max_results: int = 20,
        fields: Sequence[str] = DEFAULT_NEARBY_FIELDS,
    ) -> GooglePlacesSearchResult: ...

    async def text_search(
        self,
        query: str,
        *,
        page_size: int = 20,
        max_pages: int = 1,
        fields: Sequence[str] = DEFAULT_TEXT_FIELDS,
        location_bias: Mapping[str, Any] | None = None,
    ) -> GooglePlacesSearchResult: ...

    async def place_details(
        self,
        place_id: str,
        *,
        fields: Sequence[str] = DEFAULT_DETAIL_FIELDS,
    ) -> Mapping[str, Any]: ...

    async def refresh_place_id(
        self,
        place_id: str,
    ) -> PlaceIdRefreshResult: ...

    @property
    def metrics(self) -> GooglePlacesMetrics: ...


Sleep = Callable[[float], Awaitable[None]]


class GooglePlacesClient:
    """Bounded, safe client for Places API (New) with circuit breaker and cost guardrails."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = PLACES_BASE_URL,
        timeout_s: float = 5.0,
        max_retries: int = 2,
        retry_base_delay_s: float = 0.25,
        call_budget: int = 100,
        circuit_breaker: PlacesCircuitBreaker | None = None,
        enabled: bool = True,
        client: httpx.AsyncClient | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Google Places API key is required")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if retry_base_delay_s < 0:
            raise ValueError("retry_base_delay_s cannot be negative")
        if call_budget <= 0:
            raise ValueError("call_budget must be positive")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_s)
        self._max_retries = max_retries
        self._retry_base_delay_s = retry_base_delay_s
        self._call_budget = call_budget
        self._circuit_breaker = circuit_breaker or PlacesCircuitBreaker()
        self._enabled = enabled
        self._client = client
        self._sleep = sleep

        self._calls = 0
        self._successes = 0
        self._failures = 0
        self._retries = 0
        self._timeouts = 0
        self._circuit_rejections = 0
        self._budget_exhaustions = 0
        self._id_refreshes = 0
        self._id_changes = 0
        self._stale_places = 0

    @property
    def metrics(self) -> GooglePlacesMetrics:
        """Return an immutable snapshot of non-sensitive local counters."""
        return GooglePlacesMetrics(
            calls=self._calls,
            successes=self._successes,
            failures=self._failures,
            retries=self._retries,
            timeouts=self._timeouts,
            circuit_rejections=self._circuit_rejections,
            budget_exhaustions=self._budget_exhaustions,
            id_refreshes=self._id_refreshes,
            id_changes=self._id_changes,
            stale_places=self._stale_places,
        )

    async def nearby_search(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        included_types: Sequence[str] = (),
        max_results: int = 20,
        fields: Sequence[str] = DEFAULT_NEARBY_FIELDS,
    ) -> GooglePlacesSearchResult:
        """Run Nearby Search (New), whose response is not paginated."""
        self._ensure_enabled()
        self._validate_location(latitude, longitude, radius_m)
        if not 1 <= max_results <= 20:
            raise ValueError("max_results must be between 1 and 20")
        body: dict[str, Any] = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_m,
                }
            },
            "maxResultCount": max_results,
        }
        if included_types:
            body["includedTypes"] = list(included_types)
        payload = await self._request_json(
            "POST", "/places:searchNearby", fields=fields, json_body=body, search=True
        )
        return self._parse_search_result(payload)

    async def text_search(
        self,
        query: str,
        *,
        page_size: int = 20,
        max_pages: int = 1,
        fields: Sequence[str] = DEFAULT_TEXT_FIELDS,
        location_bias: Mapping[str, Any] | None = None,
    ) -> GooglePlacesSearchResult:
        """Run Text Search (New), following nextPageToken up to ``max_pages``."""
        self._ensure_enabled()
        if not query.strip():
            raise ValueError("query is required")
        if not 1 <= page_size <= 20:
            raise ValueError("page_size must be between 1 and 20")
        if max_pages <= 0:
            raise ValueError("max_pages must be positive")

        base_body: dict[str, Any] = {"textQuery": query, "pageSize": page_size}
        if location_bias is not None:
            base_body["locationBias"] = dict(location_bias)
        places: list[Mapping[str, Any]] = []
        token: str | None = None
        for _ in range(max_pages):
            body = dict(base_body)
            if token is not None:
                body["pageToken"] = token
            payload = await self._request_json(
                "POST", "/places:searchText", fields=fields, json_body=body, search=True
            )
            page = self._parse_search_result(payload)
            places.extend(page.places)
            token = page.next_page_token
            if token is None:
                break
        return GooglePlacesSearchResult(tuple(places), token)

    async def fetch_photo(
        self, resource_name: str, *, max_height_px: int, max_width_px: int
    ) -> tuple[bytes, str]:
        """Fetch a photo only for immediate proxying; never return or retain its redirect URL."""
        self._ensure_enabled()
        if not resource_name.startswith("places/") or "/photos/" not in resource_name:
            raise ValueError("invalid Google photo resource name")
        if not 1 <= max_height_px <= 4800 or not 1 <= max_width_px <= 4800:
            raise ValueError("photo dimensions must be between 1 and 4800")
        self._consume_budget()
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout, follow_redirects=False)
        try:
            response = await client.get(
                f"{self._base_url}/{quote(resource_name, safe='/')}/media",
                params={"maxHeightPx": max_height_px, "maxWidthPx": max_width_px},
                headers={"X-Goog-Api-Key": self._api_key},
                timeout=self._timeout,
                follow_redirects=False,
            )
            if response.is_redirect:
                location = response.headers.get("location")
                if not self._is_allowed_photo_redirect(location):
                    raise GooglePlacesError("Google Places photo request failed")
                # The Google API key is deliberately scoped to places.googleapis.com.
                # Photo CDN hosts receive a clean, separate request.
                response = await client.get(
                    location,
                    headers={"Accept": "image/*"},
                    timeout=self._timeout,
                    follow_redirects=False,
                )
            if response.status_code == 404:
                raise GooglePlacesNotFoundError("Google Places resource not found (HTTP 404)")
            if response.status_code in {401, 403}:
                raise GooglePlacesAuthenticationError("Google Places authentication failed")
            if response.status_code == 429:
                raise GooglePlacesRateLimitError("Google Places rate limit exceeded (HTTP 429)")
            if response.is_error:
                raise GooglePlacesError("Google Places photo request failed")
            content_type = response.headers.get("content-type", "").split(";", 1)[0]
            if content_type not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
                raise GooglePlacesError("Google Places returned an invalid photo")
            self._successes += 1
            return response.content, content_type
        except httpx.HTTPError as exc:
            self._failures += 1
            raise GooglePlacesError("Google Places photo request failed") from exc
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _is_allowed_photo_redirect(location: str | None) -> bool:
        """Allow only HTTPS Google photo CDN redirects; never follow arbitrary hosts."""
        if not location:
            return False
        parsed = urlparse(location)
        try:
            port = parsed.port
        except ValueError:
            return False
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and port in (None, 443)
            and (host == "googleusercontent.com" or host.endswith(".googleusercontent.com"))
        )

    async def place_details(
        self,
        place_id: str,
        *,
        fields: Sequence[str] = DEFAULT_DETAIL_FIELDS,
    ) -> Mapping[str, Any]:
        """Fetch Place Details (New) using a URL-encoded resource identifier."""
        self._ensure_enabled()
        if not place_id.strip():
            raise ValueError("place_id is required")
        payload = await self._request_json(
            "GET", f"/places/{quote(place_id, safe='')}", fields=fields, search=False
        )
        return MappingProxyType(payload)

    async def refresh_place_id(
        self,
        place_id: str,
    ) -> PlaceIdRefreshResult:
        """Validate or update a stored Place ID using zero-cost ID-only mask (ADR 0016)."""
        self._ensure_enabled()
        if not place_id.strip():
            raise ValueError("place_id is required")

        self._id_refreshes += 1
        try:
            payload = await self.place_details(place_id, fields=("id",))
            returned_id = payload.get("id")
            if not isinstance(returned_id, str) or not returned_id.strip():
                raise GooglePlacesError("Google Places returned an invalid response")

            if returned_id != place_id:
                self._id_changes += 1
                return PlaceIdRefreshResult(
                    original_id=place_id,
                    canonical_id=returned_id,
                    is_changed=True,
                    is_stale=False,
                )
            return PlaceIdRefreshResult(
                original_id=place_id,
                canonical_id=returned_id,
                is_changed=False,
                is_stale=False,
            )
        except GooglePlacesNotFoundError:
            self._stale_places += 1
            return PlaceIdRefreshResult(
                original_id=place_id,
                canonical_id=None,
                is_changed=False,
                is_stale=True,
            )

    def _ensure_enabled(self) -> None:
        if not self._enabled:
            raise GooglePlacesFeatureDisabledError(
                "Google Places synchronization is disabled (FEATURE_GOOGLE_PLACES_SYNC=false)"
            )

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        fields: Sequence[str],
        search: bool,
        json_body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._circuit_breaker.is_available():
            self._circuit_rejections += 1
            raise GooglePlacesCircuitOpenError(
                "Google Places circuit breaker is open; upstream calls paused"
            )

        mask = self._field_mask(fields, search=search)
        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": mask,
            "Content-Type": "application/json",
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            for attempt in range(self._max_retries + 1):
                self._consume_budget()
                try:
                    response = await client.request(
                        method,
                        f"{self._base_url}{path}",
                        headers=headers,
                        json=json_body,
                        timeout=self._timeout,
                    )
                except httpx.TimeoutException as exc:
                    self._timeouts += 1
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesTimeoutError("Google Places request timed out") from exc
                except httpx.TransportError as exc:
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesError("Google Places request failed") from exc

                # Status code handling
                if response.status_code == 429:
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesRateLimitError("Google Places rate limit exceeded (HTTP 429)")

                if 500 <= response.status_code <= 599:
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesError("Google Places request failed")

                if response.status_code in {401, 403}:
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesAuthenticationError(
                        "Google Places authentication failed or permission denied"
                    )

                if response.status_code == 404:
                    self._failures += 1
                    raise GooglePlacesNotFoundError("Google Places resource not found (HTTP 404)")

                if response.is_error:
                    self._failures += 1
                    raise GooglePlacesError("Google Places rejected the request")

                try:
                    payload = response.json()
                except ValueError as exc:
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesError("Google Places returned an invalid response") from exc

                if not isinstance(payload, dict):
                    self._failures += 1
                    self._circuit_breaker.record_failure()
                    raise GooglePlacesError("Google Places returned an invalid response")

                self._successes += 1
                self._circuit_breaker.record_success()
                return payload
        finally:
            if owns_client:
                await client.aclose()
        raise AssertionError("retry loop did not return or raise")

    async def _backoff(self, attempt: int) -> None:
        self._retries += 1
        await self._sleep(self._retry_base_delay_s * (2**attempt))

    def _consume_budget(self) -> None:
        if self._calls >= self._call_budget:
            self._budget_exhaustions += 1
            raise GooglePlacesBudgetExceeded("Google Places call budget exhausted")
        self._calls += 1

    @staticmethod
    def _field_mask(fields: Sequence[str], *, search: bool) -> str:
        allowed = SEARCH_FIELD_ALLOWLIST if search else DETAIL_FIELD_ALLOWLIST
        unique_fields = tuple(dict.fromkeys(fields))
        if not unique_fields:
            raise ValueError("at least one response field is required")
        if any(field not in allowed for field in unique_fields):
            raise ValueError("unsupported Google Places response field")
        return ",".join(unique_fields)

    @staticmethod
    def _validate_location(latitude: float, longitude: float, radius_m: float) -> None:
        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not 0 < radius_m <= 50_000:
            raise ValueError("radius_m must be between 0 and 50000")

    @staticmethod
    def _parse_search_result(payload: Mapping[str, Any]) -> GooglePlacesSearchResult:
        raw_places = payload.get("places", [])
        has_invalid_place = isinstance(raw_places, list) and any(
            not isinstance(place, dict) for place in raw_places
        )
        if not isinstance(raw_places, list) or has_invalid_place:
            raise GooglePlacesError("Google Places returned an invalid response")
        raw_token = payload.get("nextPageToken")
        if raw_token is not None and not isinstance(raw_token, str):
            raise GooglePlacesError("Google Places returned an invalid response")
        return GooglePlacesSearchResult(
            tuple(MappingProxyType(place) for place in raw_places),
            raw_token or None,
        )


GooglePlacesConnector = GooglePlacesClient
