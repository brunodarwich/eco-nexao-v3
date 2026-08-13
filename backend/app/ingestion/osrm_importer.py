"""Parse OSRM CSV files into route geometries and bounds (ECO-0302)."""

import csv
import math
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")

EXPECTED_ORIGINS: dict[str, dict[str, str | float | int]] = {
    "porto": {
        "code": "porto",
        "name": "Porto de Santarém",
        "filename": "rota_porto_OSRM_01.csv",
        "expected_points": 884,
        "expected_distance_km": 45.229046638,
        "start_lat": -2.428482,
        "start_lon": -54.701835,
        "end_lat": -2.558521,
        "end_lon": -54.978506,
    },
    "aeroporto": {
        "code": "aeroporto",
        "name": "Aeroporto Maestro Wilson Fonseca",
        "filename": "rota_aeroporto_OSRM_01.csv",
        "expected_points": 777,
        "expected_distance_km": 41.451542278,
        "start_lat": -2.42478,
        "start_lon": -54.78583,
        "end_lat": -2.558521,
        "end_lon": -54.978506,
    },
    "rodoviaria": {
        "code": "rodoviaria",
        "name": "Terminal Rodoviário de Santarém",
        "filename": "rota_rodoviaria_OSRM_01.csv",
        "expected_points": 866,
        "expected_distance_km": 42.318508540,
        "start_lat": -2.443185,
        "start_lon": -54.730652,
        "end_lat": -2.558521,
        "end_lon": -54.978506,
    },
}


@dataclass
class OSRMPoint:
    ordem: int
    latitude: float
    longitude: float
    distancia_acumulada_km: float


@dataclass
class OSRMRouteResult:
    origin_code: str
    origin_name: str
    points_count: int
    start_point: tuple[float, float]  # (lat, lon)
    end_point: tuple[float, float]  # (lat, lon)
    distance_m: int
    wkt_linestring: str
    wkt_start_point: str
    bounds: dict[str, float]  # min_lat, max_lat, min_lon, max_lon
    points: list[OSRMPoint]
    is_valid: bool
    error: str | None = None


def parse_osrm_csv(file_path: Path) -> list[OSRMPoint]:
    """Parse OSRM CSV file and return ordered list of OSRMPoints."""
    points: list[OSRMPoint] = []
    with open(file_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ordem = int(row["ordem"])
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            dist_km = float(row["distancia_acumulada_km"])

            if not all(math.isfinite(value) for value in (lat, lon, dist_km)):
                raise ValueError(f"Non-finite route value at row {ordem}")
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                raise ValueError(f"Invalid coordinates at row {ordem}: lat={lat}, lon={lon}")
            if dist_km < 0:
                raise ValueError(f"Negative accumulated distance at row {ordem}")
            if points and ordem <= points[-1].ordem:
                raise ValueError("Route order must be unique and strictly increasing")
            if points and dist_km < points[-1].distancia_acumulada_km:
                raise ValueError("Accumulated distance must be monotonic")

            points.append(
                OSRMPoint(
                    ordem=ordem,
                    latitude=lat,
                    longitude=lon,
                    distancia_acumulada_km=dist_km,
                )
            )

    return points


def process_osrm_origin(
    origin_code: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    tolerance_pct: float = 1.0,
) -> OSRMRouteResult:
    """Parse OSRM route for given origin code and validate specs against contract."""
    if origin_code not in EXPECTED_ORIGINS:
        raise ValueError(f"Unknown origin_code: {origin_code}")

    config = EXPECTED_ORIGINS[origin_code]
    file_path = snapshot_dir / str(config["filename"])

    if not file_path.exists():
        return OSRMRouteResult(
            origin_code=origin_code,
            origin_name=str(config["name"]),
            points_count=0,
            start_point=(0.0, 0.0),
            end_point=(0.0, 0.0),
            distance_m=0,
            wkt_linestring="",
            wkt_start_point="",
            bounds={},
            points=[],
            is_valid=False,
            error=f"File not found: {file_path}",
        )

    points = parse_osrm_csv(file_path)

    if len(points) < 2:
        return OSRMRouteResult(
            origin_code=origin_code,
            origin_name=str(config["name"]),
            points_count=len(points),
            start_point=(0.0, 0.0),
            end_point=(0.0, 0.0),
            distance_m=0,
            wkt_linestring="",
            wkt_start_point="",
            bounds={},
            points=points,
            is_valid=False,
            error="Route has fewer than 2 points.",
        )

    start_pt = (points[0].latitude, points[0].longitude)
    end_pt = (points[-1].latitude, points[-1].longitude)
    total_dist_km = points[-1].distancia_acumulada_km
    distance_m = int(round(total_dist_km * 1000.0))

    # WKT representations (PostGIS format is POINT(lon lat), LINESTRING(lon lat, lon lat, ...))
    wkt_coords = [f"{p.longitude} {p.latitude}" for p in points]
    wkt_linestring = f"LINESTRING({', '.join(wkt_coords)})"
    wkt_start_point = f"POINT({points[0].longitude} {points[0].latitude})"

    lats = [p.latitude for p in points]
    lons = [p.longitude for p in points]
    bounds = {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons),
    }

    # Validate count, endpoints and distance against the immutable contract.
    expected_dist = float(config["expected_distance_km"])
    diff_pct = abs(total_dist_km - expected_dist) / expected_dist * 100.0
    coordinate_tolerance = 1e-6
    count_valid = len(points) == int(config["expected_points"])
    endpoints_valid = all(
        abs(actual - float(expected)) <= coordinate_tolerance
        for actual, expected in zip(
            (*start_pt, *end_pt),
            (
                config["start_lat"],
                config["start_lon"],
                config["end_lat"],
                config["end_lon"],
            ),
            strict=True,
        )
    )
    valid = count_valid and endpoints_valid and diff_pct <= tolerance_pct

    error_msg = None
    if not count_valid:
        error_msg = f"Point count mismatch: {len(points)} vs {config['expected_points']}"
    elif not endpoints_valid:
        error_msg = "Route endpoints do not match the contract"
    elif not valid:
        error_msg = (
            f"Distance discrepancy: calculated {total_dist_km:.6f} km vs "
            f"expected {expected_dist:.6f} km ({diff_pct:.2f}% diff)"
        )

    return OSRMRouteResult(
        origin_code=origin_code,
        origin_name=str(config["name"]),
        points_count=len(points),
        start_point=start_pt,
        end_point=end_pt,
        distance_m=distance_m,
        wkt_linestring=wkt_linestring,
        wkt_start_point=wkt_start_point,
        bounds=bounds,
        points=points,
        is_valid=valid,
        error=error_msg,
    )
