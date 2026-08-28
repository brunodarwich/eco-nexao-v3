"""OSRM (Open Source Routing Machine) connector implementation (ECO-2314)."""

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx

from app.connectors.routing_connector import (
    Coordinate,
    RouteCalculationResult,
    RoutingConnector,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
    RoutingTimeoutError,
)

logger = logging.getLogger(__name__)

PROFILE_MAP: dict[str, str] = {
    "DRIVE": "driving",
    "WALKING": "foot",
    "BICYCLE": "bike",
}


@dataclass
class RoutingMetrics:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    retries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    circuit_rejections: int = 0


class CircuitBreaker:
    """In-memory circuit breaker for routing provider failure protection."""

    def __init__(self, failure_threshold: int = 5, reset_timeout_seconds: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.consecutive_failures = 0
        self.state: str = "CLOSED"  # "CLOSED", "OPEN", "HALF_OPEN"
        self.last_failure_time: float = 0.0

    def is_available(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.reset_timeout_seconds:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = "OPEN"


class OSRMConnector(RoutingConnector):
    """OSRM connector with timeouts, retries, and circuit breaker."""

    def __init__(
        self,
        base_url: str = "http://osrm-backend:5000",
        timeout_seconds: float = 3.5,
        max_retries: int = 2,
        circuit_breaker: CircuitBreaker | None = None,
        circuit_breaker_failures: int = 5,
        circuit_breaker_reset_seconds: float = 60.0,
        http_client: httpx.AsyncClient | None = None,
        cache_ttl_seconds: int = 86400,
        cache_grid_decimals: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            failure_threshold=circuit_breaker_failures,
            reset_timeout_seconds=circuit_breaker_reset_seconds,
        )
        self._http_client = http_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_grid_decimals = cache_grid_decimals
        self.metrics = RoutingMetrics()
        self._cache: dict[
            tuple[float, float, float, float, str], tuple[float, RouteCalculationResult]
        ] = {}

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=self.timeout_seconds)

    async def calculate_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        travel_mode: str = "DRIVE",
    ) -> RouteCalculationResult:
        self.metrics.calls += 1
        cache_key = (
            round(origin.latitude, self.cache_grid_decimals),
            round(origin.longitude, self.cache_grid_decimals),
            round(destination.latitude, self.cache_grid_decimals),
            round(destination.longitude, self.cache_grid_decimals),
            travel_mode.upper(),
        )
        cached = self._cache.get(cache_key)
        now = time.monotonic()
        if cached and cached[0] > now:
            self.metrics.cache_hits += 1
            return cached[1]
        if cached:
            self._cache.pop(cache_key, None)
        self.metrics.cache_misses += 1

        try:
            result = await asyncio.wait_for(
                self._calculate_route_uncached(origin, destination, travel_mode),
                timeout=self.timeout_seconds,
            )
        except (TimeoutError, httpx.TimeoutException) as exc:
            self.metrics.timeouts += 1
            self.metrics.failures += 1
            raise RoutingTimeoutError("O provedor OSRM excedeu o tempo limite.") from exc
        except (RoutingNoRouteFoundError, RoutingProviderUnavailableError):
            self.metrics.failures += 1
            raise
        self.metrics.successes += 1
        self._cache[cache_key] = (now + self.cache_ttl_seconds, result)
        return result

    async def _calculate_route_uncached(
        self,
        origin: Coordinate,
        destination: Coordinate,
        travel_mode: str,
    ) -> RouteCalculationResult:
        if not self.circuit_breaker.is_available():
            self.metrics.circuit_rejections += 1
            logger.warning(
                "Routing request rejected: circuit breaker open",
                extra={"provider": "osrm", "travel_mode": travel_mode, "circuit_state": "OPEN"},
            )
            raise RoutingProviderUnavailableError("Circuito de roteamento temporariamente aberto.")

        profile = PROFILE_MAP.get(travel_mode.upper(), "driving")
        coords = (
            f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        )
        url = f"{self.base_url}/route/v1/{profile}/{coords}?overview=full&geometries=geojson"

        client = self._get_client()
        should_close_client = self._http_client is None

        start_time = time.monotonic()
        attempt = 0
        last_exception: Exception | None = None

        try:
            while attempt <= self.max_retries:
                attempt += 1
                try:
                    req_start = time.monotonic()
                    response = await client.get(url)
                    elapsed_ms = int((time.monotonic() - req_start) * 1000)

                    # Check for 4xx client error (do not retry)
                    if response.status_code in (400, 404):
                        data = response.json() if response.content else {}
                        code = data.get("code")
                        if code in ("NoRoute", "NoSegment"):
                            # Successful provider response meaning no route exists
                            self.circuit_breaker.record_success()
                            logger.info(
                                "OSRM route not found",
                                extra={
                                    "provider": "osrm",
                                    "travel_mode": travel_mode,
                                    "status_code": response.status_code,
                                    "elapsed_ms": elapsed_ms,
                                },
                            )
                            raise RoutingNoRouteFoundError()

                    if response.is_error:
                        logger.warning(
                            "OSRM provider returned error status",
                            extra={
                                "provider": "osrm",
                                "travel_mode": travel_mode,
                                "status_code": response.status_code,
                                "elapsed_ms": elapsed_ms,
                            },
                        )
                        self.circuit_breaker.record_failure()
                        if 400 <= response.status_code < 500 and response.status_code not in (
                            408,
                            429,
                        ):
                            # Non-retryable 4xx client errors
                            raise RoutingProviderUnavailableError(
                                f"Provedor OSRM retornou status de erro: {response.status_code}"
                            )
                        # Retryable status codes (5xx, 429, 408)
                        if attempt <= self.max_retries:
                            self.metrics.retries += 1
                            await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                            continue
                        raise RoutingProviderUnavailableError(
                            f"Provedor OSRM indisponível (status {response.status_code})"
                        )

                    data = response.json()
                    osrm_code = data.get("code")
                    if osrm_code in ("NoRoute", "NoSegment"):
                        self.circuit_breaker.record_success()
                        logger.info(
                            "OSRM route not found (code NoRoute)",
                            extra={
                                "provider": "osrm",
                                "travel_mode": travel_mode,
                                "status_code": response.status_code,
                                "elapsed_ms": elapsed_ms,
                            },
                        )
                        raise RoutingNoRouteFoundError()

                    if osrm_code != "Ok" or "routes" not in data or not data["routes"]:
                        self.circuit_breaker.record_failure()
                        logger.warning(
                            "OSRM returned unexpected payload",
                            extra={
                                "provider": "osrm",
                                "travel_mode": travel_mode,
                                "status_code": response.status_code,
                                "elapsed_ms": elapsed_ms,
                            },
                        )
                        raise RoutingProviderUnavailableError("Resposta inválida do provedor OSRM.")

                    # Route successfully found and parsed
                    self.circuit_breaker.record_success()
                    logger.info(
                        "OSRM route calculated successfully",
                        extra={
                            "provider": "osrm",
                            "travel_mode": travel_mode,
                            "status_code": response.status_code,
                            "elapsed_ms": elapsed_ms,
                        },
                    )

                    primary_route = data["routes"][0]
                    distance_m = int(round(primary_route.get("distance", 0.0)))
                    duration_s = int(round(primary_route.get("duration", 0.0)))
                    geometry = primary_route.get("geometry", {})

                    # Compute bounds from GeoJSON coordinates if available
                    bounds = None
                    coordinates = geometry.get("coordinates", [])
                    if coordinates:
                        lons = [c[0] for c in coordinates]
                        lats = [c[1] for c in coordinates]
                        bounds = {
                            "min_lat": min(lats),
                            "max_lat": max(lats),
                            "min_lng": min(lons),
                            "max_lng": max(lons),
                        }
                    else:
                        bounds = {
                            "min_lat": min(origin.latitude, destination.latitude),
                            "max_lat": max(origin.latitude, destination.latitude),
                            "min_lng": min(origin.longitude, destination.longitude),
                            "max_lng": max(origin.longitude, destination.longitude),
                        }

                    geojson = {
                        "type": "LineString",
                        "coordinates": coordinates,
                    }

                    return RouteCalculationResult(
                        provider="osrm",
                        distance_m=distance_m,
                        duration_s=duration_s,
                        geojson=geojson,
                        encoded_polyline=None,
                        bounds=bounds,
                    )

                except RoutingNoRouteFoundError:
                    raise
                except RoutingProviderUnavailableError as err:
                    last_exception = err
                    if attempt <= self.max_retries and not (
                        hasattr(err, "status_code") and 400 <= err.status_code < 500
                    ):
                        continue
                    raise
                except httpx.TimeoutException:
                    self.circuit_breaker.record_failure()
                    raise
                except (httpx.NetworkError, httpx.RequestError) as exc:
                    last_exception = exc
                    self.circuit_breaker.record_failure()
                    total_elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    logger.warning(
                        "OSRM network/timeout error during request attempt",
                        extra={
                            "provider": "osrm",
                            "travel_mode": travel_mode,
                            "attempt": attempt,
                            "elapsed_ms": total_elapsed_ms,
                        },
                    )
                    if attempt <= self.max_retries:
                        self.metrics.retries += 1
                        await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                        continue
                    raise RoutingProviderUnavailableError(
                        "Falha de conexão ou timeout com o provedor OSRM."
                    ) from exc
                except Exception as exc:
                    self.circuit_breaker.record_failure()
                    logger.error(
                        "Unexpected error during OSRM calculation",
                        extra={"provider": "osrm", "travel_mode": travel_mode},
                    )
                    raise RoutingProviderUnavailableError(
                        "Erro inesperado ao consultar provedor OSRM."
                    ) from exc

            if last_exception:
                raise RoutingProviderUnavailableError(
                    "Falha ao obter resposta válida do provedor OSRM."
                ) from last_exception
            raise RoutingProviderUnavailableError("Provedor OSRM indisponível.")
        finally:
            if should_close_client:
                await client.aclose()
