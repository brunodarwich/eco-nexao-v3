"""Provider-isolated OSRM route connector for editorial recalculation."""

from dataclasses import dataclass
from typing import Any, Literal

import httpx


class OsrmConnectorError(Exception):
    """Safe connector failure that does not expose provider payloads or URLs."""


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A WGS84 coordinate expressed in application-friendly latitude/longitude order."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")


@dataclass(frozen=True, slots=True)
class RouteCalculation:
    """Normalized route result with no provider-specific response types."""

    geometry: dict[str, Any]
    distance_m: int
    duration_s: int
    provider: Literal["osrm"] = "osrm"
    profile: str = "driving"


class OsrmConnector:
    """Call OSRM Route v1 with bounded timeouts and a normalized result."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_s: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_s)
        self._client = client

    async def calculate_route(
        self,
        coordinates: list[Coordinate],
        *,
        profile: str = "driving",
    ) -> RouteCalculation:
        """Calculate a route; callers decide when editorial recalculation is allowed."""
        if len(coordinates) < 2:
            raise ValueError("at least two coordinates are required")
        if profile not in {"driving", "car", "bike", "foot"}:
            raise ValueError("unsupported OSRM profile")

        # OSRM's wire contract is longitude,latitude even though the domain API
        # deliberately accepts latitude,longitude.
        coordinate_path = ";".join(
            f"{point.longitude:.7f},{point.latitude:.7f}" for point in coordinates
        )
        url = f"{self._base_url}/route/v1/{profile}/{coordinate_path}"
        params = {
            "alternatives": "false",
            "steps": "false",
            "geometries": "geojson",
            "overview": "full",
            "skip_waypoints": "true",
        }

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OsrmConnectorError("OSRM request failed") from exc
        finally:
            if owns_client:
                await client.aclose()

        if payload.get("code") != "Ok":
            raise OsrmConnectorError("OSRM did not return a route")
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise OsrmConnectorError("OSRM response has no routes")
        route = routes[0]
        geometry = route.get("geometry")
        distance = route.get("distance")
        duration = route.get("duration")
        if (
            not isinstance(geometry, dict)
            or geometry.get("type") != "LineString"
            or not isinstance(geometry.get("coordinates"), list)
            or not isinstance(distance, int | float)
            or not isinstance(duration, int | float)
            or distance < 0
            or duration < 0
        ):
            raise OsrmConnectorError("OSRM response is incomplete")

        return RouteCalculation(
            geometry=geometry,
            distance_m=round(distance),
            duration_s=round(duration),
            profile=profile,
        )
