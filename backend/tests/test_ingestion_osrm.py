"""Unit tests for OSRM Route Geometry Importer (ECO-0302)."""

import csv

import pytest

from app.ingestion.osrm_importer import (
    DEFAULT_SNAPSHOT_DIR,
    EXPECTED_ORIGINS,
    parse_osrm_csv,
    process_osrm_origin,
)


def test_process_osrm_origins_real_snapshot() -> None:
    """Verify OSRM routes parsing and distance tolerances for Porto, Aeroporto, Rodoviaria."""
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    for code, config in EXPECTED_ORIGINS.items():
        res = process_osrm_origin(code, DEFAULT_SNAPSHOT_DIR)

        assert res.is_valid is True, f"Origin {code} failed validation: {res.error}"
        assert res.points_count == config["expected_points"]
        assert res.wkt_linestring.startswith("LINESTRING(")
        assert res.wkt_start_point.startswith("POINT(")
        assert res.distance_m > 40000  # All 3 routes are ~41km - 45km
        assert "min_lat" in res.bounds
        assert "max_lat" in res.bounds


@pytest.mark.parametrize(
    "rows,error",
    [
        ([(1, -2.0, -54.0, 0.0), (1, -2.1, -54.1, 1.0)], "strictly increasing"),
        ([(1, -2.0, -54.0, 1.0), (2, -2.1, -54.1, 0.5)], "monotonic"),
        ([(1, float("nan"), -54.0, 0.0)], "Non-finite"),
    ],
)
def test_parse_osrm_rejects_invalid_sequences(tmp_path, rows, error) -> None:
    path = tmp_path / "route.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("ordem", "latitude", "longitude", "distancia_acumulada_km"))
        writer.writerows(rows)

    with pytest.raises(ValueError, match=error):
        parse_osrm_csv(path)
