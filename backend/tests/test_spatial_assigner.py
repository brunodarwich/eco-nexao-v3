"""Unit and spatial verification tests for ECO-2506 (spatial assigner and layer scopes)."""


from app.core.taxonomy import (
    get_canonical_category,
)
from app.ingestion.osrm_importer import OSRMPoint, OSRMRouteResult
from app.ingestion.spatial_assigner import (
    calculate_actor_spatial_metrics,
    dist_point_to_segment_m,
    math_point_dist_m,
)


def sample_route_result(code: str, points: list[tuple[float, float]]) -> OSRMRouteResult:
    osrm_pts = [
        OSRMPoint(
            ordem=i + 1,
            latitude=pt[0],
            longitude=pt[1],
            distancia_acumulada_km=i * 10.0,
        )
        for i, pt in enumerate(points)
    ]
    wkt_coords = [f"{p.longitude} {p.latitude}" for p in osrm_pts]
    wkt_linestring = f"LINESTRING({', '.join(wkt_coords)})"
    return OSRMRouteResult(
        origin_code=code,
        origin_name=code.title(),
        points_count=len(osrm_pts),
        start_point=points[0],
        end_point=points[-1],
        distance_m=int(len(points) * 10000),
        wkt_linestring=wkt_linestring,
        wkt_start_point=f"POINT({points[0][1]} {points[0][0]})",
        bounds={"min_lat": -2.6, "max_lat": -2.4, "min_lon": -55.0, "max_lon": -54.7},
        points=osrm_pts,
        is_valid=True,
    )


def test_math_point_dist_m_same_point() -> None:
    d = math_point_dist_m(-2.428482, -54.701835, -2.428482, -54.701835)
    assert d == 0.0


def test_dist_point_to_segment_m_on_segment() -> None:
    # Segment from (0, 0) to (0, 10)
    # Point at (0, 5) is exactly on the segment
    dist, t = dist_point_to_segment_m(0.0, 5.0, 0.0, 0.0, 0.0, 10.0)
    assert dist < 1.0  # within 1 meter
    assert abs(t - 0.5) < 0.01


def test_calculate_actor_spatial_metrics_on_route() -> None:
    # 3-point route: start, middle, end
    porto_pts = [(-2.428482, -54.701835), (-2.500000, -54.800000), (-2.558521, -54.978506)]
    aeroporto_pts = [(-2.424780, -54.785830), (-2.500000, -54.800000), (-2.558521, -54.978506)]
    rodoviaria_pts = [(-2.443185, -54.730652), (-2.500000, -54.800000), (-2.558521, -54.978506)]

    routes = {
        "porto": sample_route_result("porto", porto_pts),
        "aeroporto": sample_route_result("aeroporto", aeroporto_pts),
        "rodoviaria": sample_route_result("rodoviaria", rodoviaria_pts),
    }

    # Point directly at middle point (-2.500000, -54.800000)
    metrics = calculate_actor_spatial_metrics(
        actor_lat=-2.500000,
        actor_lon=-54.800000,
        route_results=routes,
        threshold_m=1000.0,
    )

    assert metrics.distance_to_route_m < 5.0
    assert metrics.route_segment_index == 1
    assert metrics.origin_flags["porto"] is True
    assert metrics.origin_flags["aeroporto"] is True
    assert metrics.origin_flags["rodoviaria"] is True
    assert metrics.km_along_route > 0.0


def test_calculate_actor_spatial_metrics_outside_buffer() -> None:
    porto_pts = [(-2.428482, -54.701835), (-2.558521, -54.978506)]
    routes = {"porto": sample_route_result("porto", porto_pts)}

    # Distant point (e.g. 15 km away)
    metrics = calculate_actor_spatial_metrics(
        actor_lat=-2.300000,
        actor_lon=-54.500000,
        route_results=routes,
        threshold_m=1000.0,
    )

    assert metrics.distance_to_route_m > 5000.0
    assert metrics.origin_flags["porto"] is False


def test_spatial_scopes_in_canonical_taxonomy() -> None:
    """Validate that every canonical category conforms to ADR 0011 / ADR 0015 spatial scopes."""
    expected_scopes = {
        "alimentacao": "route_corridor",
        "atrativos": "route_corridor",
        "hospedagem": "route_corridor",
        "artesanato": "route_corridor",
        "transporte": "both",
        "saude": "citywide_essential",
        "seguranca": "citywide_essential",
        "outros": "route_corridor",
    }

    for slug, expected_scope in expected_scopes.items():
        cat = get_canonical_category(slug)
        assert cat["spatial_scope"] == expected_scope


def test_citywide_essential_does_not_belong_to_route_corridor() -> None:
    """Citywide essential categories (saude, seguranca) are excluded from corridor-only filters."""
    saude = get_canonical_category("saude")
    seguranca = get_canonical_category("seguranca")
    assert saude["spatial_scope"] == "citywide_essential"
    assert seguranca["spatial_scope"] == "citywide_essential"
    assert saude["spatial_scope"] != "route_corridor"
    assert seguranca["spatial_scope"] != "route_corridor"


def test_transport_scope_is_both() -> None:
    """Transport category participates in both route corridor and citywide essential layers."""
    transporte = get_canonical_category("transporte")
    assert transporte["spatial_scope"] == "both"
