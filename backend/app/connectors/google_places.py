"""Bounded server-side client for Google Places API (New)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any
from urllib.parse import quote

import httpx

PLACES_BASE_URL = "https://places.googleapis.com/v1"

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
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "nextPageToken",
    }
)
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
    """Safe upstream failure which never includes credentials or response payloads."""


class GooglePlacesBudgetExceeded(GooglePlacesError):
    """Raised before an HTTP call would exceed the configured request budget."""


@dataclass(frozen=True, slots=True)
class GooglePlacesMetrics:
    """Local counters suitable for a job report; no request data is retained."""

    calls: int
    successes: int
    failures: int
    retries: int
    budget_exhaustions: int


@dataclass(frozen=True, slots=True)
class GooglePlacesSearchResult:
    """A provider response split into places and an optional continuation token."""

    places: tuple[Mapping[str, Any], ...]
    next_page_token: str | None = None


Sleep = Callable[[float], Awaitable[None]]


class GooglePlacesClient:
    """Call only Places API (New), with bounded retries and total HTTP-call budget."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = PLACES_BASE_URL,
        timeout_s: float = 10.0,
        max_retries: int = 2,
        retry_base_delay_s: float = 0.25,
        call_budget: int = 100,
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
        self._client = client
        self._sleep = sleep
        self._calls = 0
        self._successes = 0
        self._failures = 0
        self._retries = 0
        self._budget_exhaustions = 0

    @property
    def metrics(self) -> GooglePlacesMetrics:
        """Return an immutable snapshot of non-sensitive local counters."""
        return GooglePlacesMetrics(
            calls=self._calls,
            successes=self._successes,
            failures=self._failures,
            retries=self._retries,
            budget_exhaustions=self._budget_exhaustions,
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

    async def place_details(
        self,
        place_id: str,
        *,
        fields: Sequence[str] = DEFAULT_DETAIL_FIELDS,
    ) -> Mapping[str, Any]:
        """Fetch Place Details (New) using a URL-encoded resource identifier."""
        if not place_id.strip():
            raise ValueError("place_id is required")
        payload = await self._request_json(
            "GET", f"/places/{quote(place_id, safe='')}", fields=fields, search=False
        )
        return MappingProxyType(payload)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        fields: Sequence[str],
        search: bool,
        json_body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
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
                except httpx.TransportError as exc:
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    raise GooglePlacesError("Google Places request failed") from exc

                if response.status_code == 429 or 500 <= response.status_code <= 599:
                    if attempt < self._max_retries:
                        await self._backoff(attempt)
                        continue
                    self._failures += 1
                    raise GooglePlacesError("Google Places request failed")
                if response.is_error:
                    self._failures += 1
                    raise GooglePlacesError("Google Places rejected the request")
                try:
                    payload = response.json()
                except ValueError as exc:
                    self._failures += 1
                    raise GooglePlacesError("Google Places returned an invalid response") from exc
                if not isinstance(payload, dict):
                    self._failures += 1
                    raise GooglePlacesError("Google Places returned an invalid response")
                self._successes += 1
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

