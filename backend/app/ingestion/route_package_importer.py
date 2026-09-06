"""High-level importer service for Route Data Packages (ECO-2605).

Provides dry-run validation, reporting with control counts, and atomic database
application via RoutePackageRepository under APP_ENV=test isolation guards.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.route_package_parser import RoutePackageParser
from app.ingestion.route_package_repository import RoutePackageRepository


def run_route_package_dry_run(
    package_file: Path | str,
) -> dict[str, Any]:
    """Execute a dry-run validation on a route package without DB connection.

    Verifies file existence, schema validity, origins/geometries integrity,
    and returns a structured JSON summary report.
    """
    path = Path(package_file)
    started_at = datetime.now(UTC).isoformat()

    try:
        package = RoutePackageParser.parse_file(path)
    except Exception as exc:
        return {
            "status": "error",
            "dry_run": True,
            "package_file": str(path),
            "run_started_at": started_at,
            "run_finished_at": datetime.now(UTC).isoformat(),
            "message": f"Package validation failed: {exc}",
        }

    meta = package.metadata
    finished_at = datetime.now(UTC).isoformat()

    # Tally counts for dry-run report
    total_actors = len(package.actors)
    actors_with_location = sum(
        1
        for a in package.actors
        if a.location.latitude is not None and a.location.longitude is not None
    )
    semtur_count = sum(1 for a in package.actors if a.provenance_and_sources.is_semtur_inventory)

    return {
        "status": "success",
        "dry_run": True,
        "package_file": str(path),
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "route": {
            "id": str(meta.route_id),
            "slug": meta.route_slug,
            "title": meta.title,
            "region_slug": meta.region_slug,
            "region_name": meta.region_name,
            "city": meta.city,
            "state_code": meta.state_code,
            "status": meta.status,
            "is_verified": meta.is_verified,
        },
        "origins_count": len(package.origins),
        "origins": [
            {
                "code": o.origin_code,
                "name": o.origin_name,
                "lat": o.latitude,
                "lon": o.longitude,
            }
            for o in package.origins
        ],
        "geometries_count": len(package.geometries),
        "geometries": [
            {
                "origin_code": g.origin_code,
                "provider": g.provider,
                "distance_m": g.distance_m,
                "points_count": g.points_count,
                "has_bounds": g.bounds is not None,
            }
            for g in package.geometries
        ],
        "actors_summary": {
            "total_read": total_actors,
            "with_location": actors_with_location,
            "semtur_inventory": semtur_count,
            "editorial_only": total_actors - semtur_count,
        },
        "counts": {
            "read": total_actors,
            "created": total_actors,
            "updated": 0,
            "unchanged": 0,
            "rejected": 0,
            "candidates": 0,
            "reconciled": True,
            "is_estimate": True,
            "note": (
                "Estimativa sintética pré-banco (dry-run). "
                "Contagens definitivas (created/updated/unchanged) "
                "exigem execução com --apply no banco."
            ),
        },
        "is_estimate": True,
    }


async def run_route_package_apply(
    package_file: Path | str,
    session: AsyncSession,
    *,
    fail_after: str | None = None,
) -> dict[str, Any]:
    """Validate and atomically persist the route package using the provided session."""
    path = Path(package_file)
    dry_run_report = run_route_package_dry_run(path)
    if dry_run_report["status"] != "success":
        return dry_run_report

    package = RoutePackageParser.parse_file(path)
    started_at = datetime.fromisoformat(cast(str, dry_run_report["run_started_at"]))
    finished_at = datetime.now(UTC)

    repository = RoutePackageRepository(session)
    run_id, persistence_stats = await repository.persist(
        package=package,
        started_at=started_at,
        finished_at=finished_at,
        fail_after=fail_after,
    )

    return {
        **dry_run_report,
        "dry_run": False,
        "run_finished_at": finished_at.isoformat(),
        "ingestion_run_id": str(run_id),
        "persistence": persistence_stats,
    }
