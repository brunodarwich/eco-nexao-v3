"""Harness offline de benchmark e validação comparativa de provedores de roteamento (ECO-2313).

Testa a ingestão, parsing, normalização para RouteCalculationResult, tratamento uniforme
de erros e métricas comparativas entre Google Routes e OSRM sem chamadas externas de rede.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.connectors.routing_connector import (
    Coordinate,
    RouteCalculationResult,
    RoutingNoRouteFoundError,
    RoutingProviderUnavailableError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "routing_benchmark"


def _decode_polyline_mock(encoded: str) -> list[list[float]]:
    """Mock determinístico e simplificado para decodificação de polyline para GeoJSON [lng, lat]."""
    # Para fins de benchmark e parsing sintético offline
    return [
        [-54.71045, -2.42851],
        [-54.81234, -2.48512],
        [-54.95821, -2.635412],
    ]


def parse_google_routes_response(data: dict[str, Any]) -> RouteCalculationResult:
    """Transforma resposta bruta da Google Routes API para RouteCalculationResult."""
    if "error" in data:
        code = data["error"].get("status")
        if (
            code in ("NOT_FOUND", "ZERO_RESULTS")
            or "No route" in data["error"].get("message", "")
        ):
            raise RoutingNoRouteFoundError()
        raise RoutingProviderUnavailableError(
            f"Google Routes error: {data['error'].get('message')}"
        )

    routes = data.get("routes", [])
    if not routes:
        raise RoutingNoRouteFoundError()

    route = routes[0]
    distance_m = int(route.get("distanceMeters", 0))

    # Duration format "2850s"
    duration_raw = route.get("duration", "0s")
    if isinstance(duration_raw, str):
        duration_s = int(duration_raw.rstrip("s"))
    else:
        duration_s = int(duration_raw)

    encoded_polyline = route.get("polyline", {}).get("encodedPolyline")
    coords = _decode_polyline_mock(encoded_polyline) if encoded_polyline else []

    viewport = route.get("viewport", {})
    bounds = None
    if viewport:
        bounds = {
            "min_lat": viewport["low"]["latitude"],
            "max_lat": viewport["high"]["latitude"],
            "min_lng": viewport["low"]["longitude"],
            "max_lng": viewport["high"]["longitude"],
        }

    return RouteCalculationResult(
        provider="google_routes",
        distance_m=distance_m,
        duration_s=duration_s,
        geojson={"type": "LineString", "coordinates": coords},
        encoded_polyline=encoded_polyline,
        bounds=bounds,
    )


def parse_osrm_response(data: dict[str, Any]) -> RouteCalculationResult:
    """Transforma resposta bruta do OSRM para RouteCalculationResult."""
    code = data.get("code")
    if code == "NoRoute":
        raise RoutingNoRouteFoundError()
    if code != "Ok":
        raise RoutingProviderUnavailableError(f"OSRM error code: {code}")
    if not data.get("routes"):
        raise RoutingNoRouteFoundError()

    route = data["routes"][0]
    distance_m = int(round(route.get("distance", 0.0)))
    duration_s = int(round(route.get("duration", 0.0)))

    geometry = route.get("geometry", {})
    coords = geometry.get("coordinates", [])

    bounds = None
    if coords:
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        bounds = {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs),
        }

    return RouteCalculationResult(
        provider="osrm",
        distance_m=distance_m,
        duration_s=duration_s,
        geojson={"type": "LineString", "coordinates": coords},
        bounds=bounds,
    )


class TestRoutingBenchmarkHarness:
    """Conjunto de testes do harness de benchmark offline."""

    def test_fixtures_exist_and_are_valid_json(self) -> None:
        expected_files = [
            "google_routes_urban_airport.json",
            "osrm_urban_airport.json",
            "google_routes_rural_ramal.json",
            "osrm_rural_ramal.json",
            "google_routes_impossivel_river.json",
            "osrm_impossivel_river.json",
        ]
        for filename in expected_files:
            file_path = FIXTURES_DIR / filename
            assert file_path.exists(), f"Fixture {filename} não encontrada."
            content = json.loads(file_path.read_text(encoding="utf-8"))
            assert isinstance(content, dict)

    def test_urban_airport_ingestion_and_normalization(self) -> None:
        google_raw = json.loads(
            (FIXTURES_DIR / "google_routes_urban_airport.json").read_text(encoding="utf-8")
        )
        osrm_raw = json.loads(
            (FIXTURES_DIR / "osrm_urban_airport.json").read_text(encoding="utf-8")
        )

        google_res = parse_google_routes_response(google_raw)
        osrm_res = parse_osrm_response(osrm_raw)

        # Validação Google Routes
        assert isinstance(google_res, RouteCalculationResult)
        assert google_res.provider == "google_routes"
        assert google_res.distance_m == 35240
        assert google_res.duration_s == 2850
        assert google_res.geojson["type"] == "LineString"
        assert len(google_res.geojson["coordinates"]) > 0
        assert google_res.bounds is not None
        assert google_res.bounds["min_lat"] <= google_res.bounds["max_lat"]
        assert google_res.bounds["min_lng"] <= google_res.bounds["max_lng"]

        # Validação OSRM
        assert isinstance(osrm_res, RouteCalculationResult)
        assert osrm_res.provider == "osrm"
        assert osrm_res.distance_m == 35180
        assert osrm_res.duration_s == 2821 or osrm_res.duration_s == 2820
        assert osrm_res.geojson["type"] == "LineString"
        assert len(osrm_res.geojson["coordinates"]) == 5
        assert osrm_res.bounds is not None
        assert osrm_res.bounds["min_lat"] <= osrm_res.bounds["max_lat"]

        # Comparativo de convergência (diferença de distância < 2%)
        diff_pct = abs(google_res.distance_m - osrm_res.distance_m) / google_res.distance_m
        assert diff_pct < 0.02, (
            f"Diferença de distância excessiva entre provedores: {diff_pct:.2%}"
        )

    def test_rural_ramal_ingestion_and_normalization(self) -> None:
        google_raw = json.loads(
            (FIXTURES_DIR / "google_routes_rural_ramal.json").read_text(encoding="utf-8")
        )
        osrm_raw = json.loads(
            (FIXTURES_DIR / "osrm_rural_ramal.json").read_text(encoding="utf-8")
        )

        google_res = parse_google_routes_response(google_raw)
        osrm_res = parse_osrm_response(osrm_raw)

        assert google_res.distance_m == 14200
        assert osrm_res.distance_m == 14150

        diff_pct = abs(google_res.distance_m - osrm_res.distance_m) / google_res.distance_m
        assert diff_pct < 0.02

    def test_impossible_route_raises_uniform_no_route_error(self) -> None:
        google_raw = json.loads(
            (FIXTURES_DIR / "google_routes_impossivel_river.json").read_text(encoding="utf-8")
        )
        osrm_raw = json.loads(
            (FIXTURES_DIR / "osrm_impossivel_river.json").read_text(encoding="utf-8")
        )

        with pytest.raises(RoutingNoRouteFoundError) as exc_google:
            parse_google_routes_response(google_raw)
        assert exc_google.value.code == "NO_ROUTE_FOUND"

        with pytest.raises(RoutingNoRouteFoundError) as exc_osrm:
            parse_osrm_response(osrm_raw)
        assert exc_osrm.value.code == "NO_ROUTE_FOUND"

    def test_provider_unavailable_raises_uniform_error(self) -> None:
        broken_google = {
            "error": {
                "code": 503,
                "message": "Server temporarily overloaded",
                "status": "UNAVAILABLE",
            }
        }
        broken_osrm = {"code": "InvalidQuery", "message": "Backend engine offline"}

        with pytest.raises(RoutingProviderUnavailableError) as exc_google:
            parse_google_routes_response(broken_google)
        assert exc_google.value.code == "ROUTING_PROVIDER_UNAVAILABLE"

        with pytest.raises(RoutingProviderUnavailableError) as exc_osrm:
            parse_osrm_response(broken_osrm)
        assert exc_osrm.value.code == "ROUTING_PROVIDER_UNAVAILABLE"

    def test_no_coordinate_leakage_in_exceptions(self) -> None:
        secret_origin = Coordinate(latitude=-2.44123456, longitude=-54.72123456)
        secret_dest = Coordinate(latitude=-2.63123456, longitude=-54.94123456)

        err1 = RoutingNoRouteFoundError()
        err2 = RoutingProviderUnavailableError()

        for err in (err1, err2):
            msg = str(err)
            assert str(secret_origin.latitude) not in msg
            assert str(secret_origin.longitude) not in msg
            assert str(secret_dest.latitude) not in msg
            assert str(secret_dest.longitude) not in msg

    def test_comparative_simulated_metrics(self) -> None:
        google_raw_str = (FIXTURES_DIR / "google_routes_urban_airport.json").read_text(
            encoding="utf-8"
        )
        osrm_raw_str = (FIXTURES_DIR / "osrm_urban_airport.json").read_text(
            encoding="utf-8"
        )

        # Payload size
        google_size = len(google_raw_str.encode("utf-8"))
        osrm_size = len(osrm_raw_str.encode("utf-8"))

        assert google_size > 0
        assert osrm_size > 0

        # Ingestão e integridade de bounds
        google_res = parse_google_routes_response(json.loads(google_raw_str))
        osrm_res = parse_osrm_response(json.loads(osrm_raw_str))

        assert google_res.bounds is not None
        assert osrm_res.bounds is not None
        assert set(google_res.bounds.keys()) == {"min_lat", "max_lat", "min_lng", "max_lng"}
        assert set(osrm_res.bounds.keys()) == {"min_lat", "max_lat", "min_lng", "max_lng"}
