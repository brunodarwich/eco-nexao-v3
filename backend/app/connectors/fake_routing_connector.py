"""Deterministic fake routing connector for offline development and testing (ECO-2309)."""

import math
from typing import Any

from app.connectors.routing_connector import (
    Coordinate,
    RouteCalculationResult,
    RoutingConnector,
    RoutingNoRouteFoundError,
)


def _haversine_distance_m(origin: Coordinate, destination: Coordinate) -> float:
    """Calculate great-circle distance between two points in meters using Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    lat1_rad = math.radians(origin.latitude)
    lat2_rad = math.radians(destination.latitude)
    delta_lat = math.radians(destination.latitude - origin.latitude)
    delta_lon = math.radians(destination.longitude - origin.longitude)

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class FakeRoutingConnector(RoutingConnector):
    """Deterministic in-memory fake routing connector with zero network calls."""

    def __init__(self, steps: int = 5, average_speed_kmh: float = 40.0) -> None:
        self.steps = max(2, steps)
        self.average_speed_kmh = average_speed_kmh

    async def calculate_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        travel_mode: str = "DRIVE",
    ) -> RouteCalculationResult:
        if travel_mode != "DRIVE":
            raise RoutingNoRouteFoundError("Modo de transporte não suportado.")
        distance_straight = _haversine_distance_m(origin, destination)
        distance_m = int(round(distance_straight * 1.25))

        speed_kmh = self.average_speed_kmh

        speed_ms = (speed_kmh * 1000.0) / 3600.0
        duration_s = max(1, int(round(distance_m / speed_ms))) if speed_ms > 0 else 0

        coordinates: list[list[float]] = []
        for i in range(self.steps):
            fraction = i / (self.steps - 1)
            lat = origin.latitude + fraction * (destination.latitude - origin.latitude)
            lon = origin.longitude + fraction * (destination.longitude - origin.longitude)
            coordinates.append([round(lon, 6), round(lat, 6)])

        geojson: dict[str, Any] = {
            "type": "LineString",
            "coordinates": coordinates,
        }

        bounds: dict[str, float] = {
            "min_lat": min(origin.latitude, destination.latitude),
            "max_lat": max(origin.latitude, destination.latitude),
            "min_lng": min(origin.longitude, destination.longitude),
            "max_lng": max(origin.longitude, destination.longitude),
        }

        return RouteCalculationResult(
            provider="fake_deterministic",
            distance_m=distance_m,
            duration_s=duration_s,
            geojson=geojson,
            encoded_polyline=None,
            bounds=bounds,
        )
