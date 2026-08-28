"""Calculate actor spatial metrics and route relationships with PostGIS and fallback (ECO-2506)."""

import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ingestion.osrm_importer import OSRMPoint, OSRMRouteResult

DEFAULT_CORRIDOR_BUFFER_METERS = 1000.0


@dataclass
class ActorSpatialMetrics:
    actor_id: str
    route_id: str
    distance_to_route_m: float
    route_segment_index: int
    km_along_route: float
    origin_flags: dict[str, Any]


def math_point_dist_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters between two coordinates."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def dist_point_to_segment_m(
    p_lat: float, p_lon: float, a_lat: float, a_lon: float, b_lat: float, b_lon: float
) -> tuple[float, float]:
    """Calculate distance in meters from point P to segment AB, and fraction t in [0,1]."""
    # Flat projection approximation centered at segment
    lat_mid = math.radians((a_lat + b_lat) / 2.0)
    kx = 111320.0 * math.cos(lat_mid)
    ky = 110574.0

    px, py = p_lon * kx, p_lat * ky
    ax, ay = a_lon * kx, a_lat * ky
    bx, by = b_lon * kx, b_lat * ky

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq == 0.0:
        return math_point_dist_m(p_lat, p_lon, a_lat, a_lon), 0.0

    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy

    dist = math.hypot(px - proj_x, py - proj_y)
    return dist, t


def calculate_distance_to_polyline_m(
    lat: float, lon: float, points: list[OSRMPoint]
) -> tuple[float, int, float]:
    """Calculate minimum distance to polyline, closest segment index, and fraction."""
    if not points:
        return float("inf"), 0, 0.0
    if len(points) == 1:
        return math_point_dist_m(lat, lon, points[0].latitude, points[0].longitude), 0, 0.0

    min_dist = float("inf")
    best_segment = 0
    best_seg_t = 0.0

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        dist, t = dist_point_to_segment_m(
            lat, lon, p1.latitude, p1.longitude, p2.latitude, p2.longitude
        )
        if dist < min_dist:
            min_dist = dist
            best_segment = i
            best_seg_t = t

    total_pts = len(points)
    fraction = (best_segment + best_seg_t) / max(1, total_pts - 1)
    return min_dist, best_segment, fraction


def calculate_actor_spatial_metrics(
    actor_lat: float,
    actor_lon: float,
    route_results: dict[str, OSRMRouteResult],
    db_session: Session | None = None,
    threshold_m: float = DEFAULT_CORRIDOR_BUFFER_METERS,
) -> ActorSpatialMetrics:
    """Calculate route distance, segment index, and origin flags for Porto, Aeroporto, etc."""
    canonical_route = route_results.get("porto")

    if db_session and canonical_route:
        # PostGIS query with geography for high precision
        query = text(
            """
            SELECT 
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    ST_GeomFromText(:wkt_line, 4326)::geography
                ) as dist_m,
                ST_LineLocatePoint(
                    ST_GeomFromText(:wkt_line, 4326),
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                ) as frac
            """
        )
        res = db_session.execute(
            query,
            {
                "lat": actor_lat,
                "lon": actor_lon,
                "wkt_line": canonical_route.wkt_linestring,
            },
        ).fetchone()

        dist_m = float(res[0]) if res and res[0] is not None else 0.0
        frac = float(res[1]) if res and res[1] is not None else 0.0
        n_points = len(canonical_route.points) if canonical_route.points else 884
        segment_idx = min(max(0, int(frac * (n_points - 1))), max(0, n_points - 2))
    else:
        # High precision pure-python calculation
        if canonical_route and canonical_route.points:
            dist_m, _, frac = calculate_distance_to_polyline_m(
                actor_lat, actor_lon, canonical_route.points
            )
            n_points = len(canonical_route.points)
            segment_idx = min(max(0, int(frac * (n_points - 1))), max(0, n_points - 2))
        else:
            dist_m, segment_idx, frac = 0.0, 0, 0.0

    total_dist_km = canonical_route.distance_m / 1000.0 if canonical_route else 45.229046638
    km_along_route = round(frac * total_dist_km, 3)

    # Origin flags calculation per individual route geometry
    origin_flags: dict[str, Any] = {
        "km_porto": km_along_route,
    }

    for origin_code in ("porto", "aeroporto", "rodoviaria"):
        route = route_results.get(origin_code)
        if route and route.points:
            if db_session:
                q_dwithin = text(
                    """
                    SELECT ST_DWithin(
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        ST_GeomFromText(:wkt_line, 4326)::geography,
                        :threshold
                    )
                    """
                )
                flag_res = db_session.execute(
                    q_dwithin,
                    {
                        "lat": actor_lat,
                        "lon": actor_lon,
                        "wkt_line": route.wkt_linestring,
                        "threshold": threshold_m,
                    },
                ).scalar()
                origin_flags[origin_code] = bool(flag_res)
            else:
                d_orig, _, _ = calculate_distance_to_polyline_m(actor_lat, actor_lon, route.points)
                origin_flags[origin_code] = bool(d_orig <= threshold_m)
        else:
            origin_flags[origin_code] = False

    return ActorSpatialMetrics(
        actor_id="",
        route_id="",
        distance_to_route_m=round(dist_m, 2),
        route_segment_index=segment_idx,
        km_along_route=km_along_route,
        origin_flags=origin_flags,
    )
