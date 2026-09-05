"""Google Routes API v2 connector for approved dynamic previews (ECO-2314).

Coordinates exist only in the POST body sent to Google. They are never placed in
URLs, cache keys, metrics or log records.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.routing_connector import (
    Coordinate,
    RouteCalculationResult,
    RoutingConnector,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
    RoutingQuotaExceededError,
    RoutingTimeoutError,
)

logger = logging.getLogger(__name__)

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GOOGLE_ROUTES_FIELD_MASK = "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"


@dataclass
class RoutingMetrics:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    retries: int = 0
    circuit_rejections: int = 0
    quota_rejections: int = 0


class CircuitBreaker:
    """Thread-safe process-wide circuit breaker shared by connector requests."""

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
class MonthlyUsageGuardProtocol(Protocol):
    """Protocol for monthly usage guards (ADR 0013)."""

    async def reserve(self) -> int: ...

    @property
    def calls(self) -> int: ...


class InMemoryMonthlyUsageGuard:
    """Thread-safe in-memory monthly usage guard for isolated tests/benchmarks."""

    def __init__(self, limit: int = 9000, alert_at: int = 7500) -> None:
        self.limit = limit
        self.alert_at = alert_at
        self._month = self._current_month()
        self._calls = 0
        self._alert_emitted = False
        self._lock = threading.Lock()

    @staticmethod
    def _current_month() -> str:
        return datetime.now(UTC).strftime("%Y-%m")

    @property
    def calls(self) -> int:
        with self._lock:
            return self._calls

    async def reserve(self) -> int:
        with self._lock:
            month = self._current_month()
            if month != self._month:
                self._month = month
                self._calls = 0
                self._alert_emitted = False
            if self._calls >= self.limit:
                raise RoutingQuotaExceededError()
            self._calls += 1
            if self._calls >= self.alert_at and not self._alert_emitted:
                self._alert_emitted = True
                logger.warning(
                    "Routing monthly usage alert threshold reached",
                    extra={"provider": "google_routes", "result": "quota_alert"},
                )
            return self._calls


class DatabaseMonthlyUsageGuard:
    """Shared, atomic PostgreSQL-backed monthly usage guard across workers/instances (ADR 0013)."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        limit: int = 9000,
        alert_at: int = 7500,
    ) -> None:
        if session_factory is None:
            from app.db.session import AsyncSessionLocal

            session_factory = AsyncSessionLocal
        self.session_factory = session_factory
        self.limit = limit
        self.alert_at = alert_at
        self._alert_month: str | None = None
        self._alert_lock = threading.Lock()
        self._cached_calls: int = 0

    @staticmethod
    def _current_month() -> str:
        return datetime.now(UTC).strftime("%Y-%m")

    @property
    def calls(self) -> int:
        return self._cached_calls

    async def reserve(self) -> int:
        month = self._current_month()
        query = text(
            """
            INSERT INTO app_private.routing_monthly_usage (
                year_month, call_count, created_at, updated_at
            )
            VALUES (:year_month, 1, clock_timestamp(), clock_timestamp())
            ON CONFLICT (year_month)
            DO UPDATE SET
                call_count = app_private.routing_monthly_usage.call_count + 1,
                updated_at = clock_timestamp()
            RETURNING call_count;
            """
        )
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(query, {"year_month": month})
                current_count = int(result.scalar_one())

        self._cached_calls = current_count

        if current_count > self.limit:
            raise RoutingQuotaExceededError()

        if current_count >= self.alert_at:
            with self._alert_lock:
                if self._alert_month != month:
                    self._alert_month = month
                    logger.warning(
                        "Routing monthly usage alert threshold reached",
                        extra={"provider": "google_routes", "result": "quota_alert"},
                    )

        return current_count


# Alias for backward compatibility with existing tests
MonthlyUsageGuard = InMemoryMonthlyUsageGuard


def _decode_polyline(encoded: str) -> list[list[float]]:
    """Decode a Google encoded polyline into GeoJSON [longitude, latitude] pairs."""
    coordinates: list[list[float]] = []
    latitude = 0
    longitude = 0
    index = 0
    while index < len(encoded):
        deltas: list[int] = []
        for _ in range(2):
            result = 0
            shift = 0
            while True:
                if index >= len(encoded):
                    raise ValueError("invalid encoded polyline")
                value = ord(encoded[index]) - 63
                index += 1
                result |= (value & 0x1F) << shift
                shift += 5
                if value < 0x20:
                    break
            deltas.append(~(result >> 1) if result & 1 else result >> 1)
        latitude += deltas[0]
        longitude += deltas[1]
        coordinates.append([round(longitude / 1e5, 6), round(latitude / 1e5, 6)])
    return coordinates


def _duration_seconds(raw: str) -> int:
    if not raw.endswith("s"):
        raise ValueError("invalid duration")
    return max(0, int(round(float(raw[:-1]))))


class GoogleRoutesConnector(RoutingConnector):
    """ComputeRoutes Essentials client with minimal fields and bounded retries."""

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 3.5,
        max_retries: int = 2,
        circuit_breaker: CircuitBreaker | None = None,
        circuit_breaker_failures: int = 5,
        circuit_breaker_reset_seconds: float = 60.0,
        monthly_guard: MonthlyUsageGuardProtocol | None = None,
        monthly_limit: int = 9000,
        monthly_alert_at: int = 7500,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            circuit_breaker_failures, circuit_breaker_reset_seconds
        )
        if monthly_guard is not None:
            self.monthly_guard = monthly_guard
        else:
            self.monthly_guard = DatabaseMonthlyUsageGuard(
                limit=monthly_limit, alert_at=monthly_alert_at
            )
        self._http_client = http_client
        self.metrics = RoutingMetrics()

    async def calculate_route(
        self, origin: Coordinate, destination: Coordinate, travel_mode: str = "DRIVE"
    ) -> RouteCalculationResult:
        if not self._api_key:
            raise RoutingProviderUnavailableError("Credencial do provedor não configurada.")
        if travel_mode.upper() != "DRIVE":
            raise RoutingNoRouteFoundError("Modo de viagem não homologado.")
        if not self.circuit_breaker.is_available():
            self.metrics.circuit_rejections += 1
            raise RoutingProviderUnavailableError("Circuito de roteamento temporariamente aberto.")

        payload = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin.latitude,
                        "longitude": origin.longitude,
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination.latitude,
                        "longitude": destination.longitude,
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_UNAWARE",
            "computeAlternativeRoutes": False,
            "polylineQuality": "OVERVIEW",
            "polylineEncoding": "ENCODED_POLYLINE",
            "units": "METRIC",
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": GOOGLE_ROUTES_FIELD_MASK,
        }
        client = self._http_client or httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds))
        close_client = self._http_client is None
        started = time.monotonic()
        try:
            for attempt in range(self.max_retries + 1):
                try:
                    await self.monthly_guard.reserve()
                except RoutingQuotaExceededError:
                    self.metrics.quota_rejections += 1
                    raise
                self.metrics.calls += 1
                try:
                    response = await asyncio.wait_for(
                        client.post(GOOGLE_ROUTES_URL, json=payload, headers=headers),
                        timeout=self.timeout_seconds,
                    )
                except (TimeoutError, httpx.TimeoutException) as exc:
                    if attempt < self.max_retries:
                        self.metrics.retries += 1
                        await asyncio.sleep(0.1 * (2**attempt))
                        continue
                    self.metrics.timeouts += 1
                    self.metrics.failures += 1
                    self.circuit_breaker.record_failure()
                    raise RoutingTimeoutError() from exc
                except httpx.RequestError as exc:
                    if attempt < self.max_retries:
                        self.metrics.retries += 1
                        await asyncio.sleep(0.1 * (2**attempt))
                        continue
                    self.metrics.failures += 1
                    self.circuit_breaker.record_failure()
                    raise RoutingProviderUnavailableError() from exc

                if response.status_code == 429 or response.status_code >= 500:
                    logger.warning(
                        "Routing provider returned retryable error",
                        extra={
                            "provider": "google_routes",
                            "result": "provider_error",
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                        },
                    )
                    if attempt < self.max_retries:
                        self.metrics.retries += 1
                        await asyncio.sleep(0.1 * (2**attempt))
                        continue
                    self.metrics.failures += 1
                    self.circuit_breaker.record_failure()
                    raise RoutingProviderUnavailableError()
                if response.status_code in {400, 404, 422}:
                    logger.warning(
                        "Routing provider rejected request",
                        extra={
                            "provider": "google_routes",
                            "result": "provider_rejected",
                            "status_code": response.status_code,
                        },
                    )
                    self.metrics.failures += 1
                    raise RoutingNoRouteFoundError()
                if response.status_code >= 400:
                    logger.warning(
                        "Routing provider returned client error",
                        extra={
                            "provider": "google_routes",
                            "result": "provider_error",
                            "status_code": response.status_code,
                        },
                    )
                    self.metrics.failures += 1
                    raise RoutingProviderUnavailableError()

                try:
                    body: dict[str, Any] = response.json()
                    route = body["routes"][0]
                    encoded = route["polyline"]["encodedPolyline"]
                    coordinates = _decode_polyline(encoded)
                    if len(coordinates) < 2:
                        raise ValueError("route has insufficient coordinates")
                    result = RouteCalculationResult(
                        provider="google_routes",
                        distance_m=int(route["distanceMeters"]),
                        duration_s=_duration_seconds(route["duration"]),
                        geojson={"type": "LineString", "coordinates": coordinates},
                        encoded_polyline=encoded,
                        bounds={
                            "min_lat": min(point[1] for point in coordinates),
                            "max_lat": max(point[1] for point in coordinates),
                            "min_lng": min(point[0] for point in coordinates),
                            "max_lng": max(point[0] for point in coordinates),
                        },
                    )
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    self.metrics.failures += 1
                    self.circuit_breaker.record_failure()
                    raise RoutingProviderUnavailableError("Resposta inválida do provedor.") from exc

                self.metrics.successes += 1
                self.circuit_breaker.record_success()
                logger.info(
                    "Routing provider request completed",
                    extra={
                        "provider": "google_routes",
                        "result": "success",
                        "latency_ms": int((time.monotonic() - started) * 1000),
                    },
                )
                return result
        finally:
            if close_client:
                await client.aclose()
        raise RoutingProviderUnavailableError()
