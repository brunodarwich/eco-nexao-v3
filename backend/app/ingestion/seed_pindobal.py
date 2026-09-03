"""Run the Pindobal ingestion pipeline (ECO-0308)."""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.ingestion.google_snapshot_importer import process_google_snapshot
from app.ingestion.manifest import MANIFEST_ENTRIES, verify_manifest
from app.ingestion.osrm_importer import process_osrm_origin
from app.ingestion.pindobal_cutout_importer import process_pindobal_cutout
from app.ingestion.pindobal_repository import PindobalPersistenceRepository
from app.ingestion.reconciler import reconcile_semtur_and_google
from app.ingestion.semtur_importer import process_semtur_inventory
from app.ingestion.spatial_assigner import calculate_actor_spatial_metrics
from scripts.check_test_isolation import BACKEND_DIR, require_test_isolation

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")


def run_seed_pindobal(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute complete Pindobal seed pipeline and produce JSON summary report."""
    if not dry_run:
        raise RuntimeError("Use run_seed_pindobal_apply com uma sessão DB explícita.")

    run_started_at = datetime.now(UTC).isoformat()

    # Step 1: Verify Manifest
    manifest_report = verify_manifest(snapshot_dir)
    if not manifest_report.is_valid:
        return {
            "status": "error",
            "message": "Manifest checksum verification failed",
            "manifest": {
                "total": manifest_report.total_files,
                "valid": manifest_report.valid_files,
                "invalid": [
                    {
                        "file": f.filename,
                        "expected_hash": f.expected_hash,
                        "actual_hash": f.actual_hash,
                    }
                    for f in manifest_report.invalid_files
                ],
            },
        }

    # Step 2: Import OSRM Geometries
    osrm_results = {}
    for code in ["porto", "aeroporto", "rodoviaria"]:
        osrm_results[code] = process_osrm_origin(code, snapshot_dir)

    # Step 3: Import SEMTUR Inventory
    semtur_records, semtur_stats = process_semtur_inventory(snapshot_dir)

    # Step 4: Import Pindobal Cutout
    cutout_records, cutout_stats = process_pindobal_cutout(snapshot_dir)

    # Step 5: Import Google Snapshot
    google_records, google_stats = process_google_snapshot(snapshot_dir)

    # Step 6: Reconciliation
    matches = reconcile_semtur_and_google(semtur_records, google_records)
    candidate_google_ids = {
        match.google_id for match in matches if match.match_type == "fuzzy_candidate"
    }
    total_read = len(semtur_records) + len(cutout_records) + len(google_records)
    rejected = (
        sum(not record.is_valid for record in semtur_records)
        + sum(not record.is_valid for record in cutout_records)
        + sum(not record.is_valid for record in google_records)
    )
    candidates = len(candidate_google_ids)
    created = total_read - rejected - candidates

    # Step 7: Calculate Spatial Metrics sample
    spatial_sample_count = 0
    for rec in cutout_records:
        if rec.is_valid:
            calculate_actor_spatial_metrics(rec.latitude, rec.longitude, osrm_results)
            spatial_sample_count += 1

    run_finished_at = datetime.now(UTC).isoformat()

    report = {
        "status": "success",
        "dry_run": dry_run,
        "run_started_at": run_started_at,
        "run_finished_at": run_finished_at,
        "snapshot_dir": str(snapshot_dir),
        "manifest": {
            "total_files": manifest_report.total_files,
            "valid_files": manifest_report.valid_files,
            "is_valid": manifest_report.is_valid,
            "files": [
                {"name": name, "bytes": size, "sha256": sha256}
                for name, (size, sha256) in MANIFEST_ENTRIES.items()
            ],
        },
        "rules": {
            "importer_version": "eco-1502-v1",
            "rules_version": "pindobal-contract-1.0",
        },
        "counts": {
            "read": total_read,
            "created": created,
            "updated": 0,
            "unchanged": 0,
            "rejected": rejected,
            "candidates": candidates,
            "reconciled": total_read == created + rejected + candidates,
        },
        "osrm_routes": {
            code: {
                "points_count": res.points_count,
                "distance_m": res.distance_m,
                "is_valid": res.is_valid,
            }
            for code, res in osrm_results.items()
        },
        "semtur_inventory": semtur_stats,
        "pindobal_cutout": cutout_stats,
        "google_snapshot": google_stats,
        "reconciliation": {
            "matches_count": len(matches),
            "deterministic_count": sum(
                1 for m in matches if m.match_type.startswith("deterministic")
            ),
            "fuzzy_candidate_count": sum(1 for m in matches if m.match_type == "fuzzy_candidate"),
            "candidate_google_record_count": candidates,
            "candidate_counting_rule": "unique_google_snapshot_record",
            "candidate_persistence": "blocked_without_trusted_google_actor_identity",
        },
        "spatial": {
            "processed_cutout_points": spatial_sample_count,
        },
    }

    return report


async def run_seed_pindobal_apply(
    snapshot_dir: Path,
    session: AsyncSession,
    *,
    fail_after: str | None = None,
) -> dict[str, Any]:
    """Validate the snapshot, then persist the territorial slice atomically."""
    report = run_seed_pindobal(snapshot_dir=snapshot_dir, dry_run=True)
    if report["status"] != "success":
        return report
    osrm_results = {
        code: process_osrm_origin(code, snapshot_dir)
        for code in ("porto", "aeroporto", "rodoviaria")
    }
    if not all(result.is_valid for result in osrm_results.values()):
        return {**report, "status": "error", "message": "Invalid OSRM geometry"}

    started_at = datetime.fromisoformat(cast(str, report["run_started_at"]))
    finished_at = datetime.fromisoformat(cast(str, report["run_finished_at"]))
    repository = PindobalPersistenceRepository(session)
    semtur_records, _ = process_semtur_inventory(snapshot_dir)
    google_records, _ = process_google_snapshot(snapshot_dir)
    cutout_records, _ = process_pindobal_cutout(snapshot_dir)
    matches = reconcile_semtur_and_google(semtur_records, google_records)
    run_id, persistence_stats = await repository.persist(
        report=report,
        osrm_results=osrm_results,
        started_at=started_at,
        finished_at=finished_at,
        semtur_records=semtur_records,
        google_records=google_records,
        cutout_records=cutout_records,
        matches=matches,
        fail_after=fail_after,
    )
    return {
        **report,
        "dry_run": False,
        "ingestion_run_id": str(run_id),
        "persistence": persistence_stats,
    }


async def apply_from_test_environment(snapshot_dir: Path, env_file: Path) -> dict[str, Any]:
    """Load an explicit test environment and refuse every other target."""
    canonical_test_file = (BACKEND_DIR / ".env.test").resolve()
    if env_file.resolve() != canonical_test_file:
        raise RuntimeError("--apply aceita somente o arquivo canônico backend/.env.test.")
    if not env_file.is_file():
        raise RuntimeError("Arquivo de ambiente de test não encontrado.")
    require_test_isolation(test_path=env_file)
    load_dotenv(env_file, override=True)
    from app.core.config import Settings

    settings = Settings()
    if settings.APP_ENV != "test":
        raise RuntimeError("--apply é permitido somente com APP_ENV=test.")
    database_url = settings.DATABASE_URL.get_secret_value()
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            return await run_seed_pindobal_apply(snapshot_dir, session)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Pindobal Seed Ingestion Runner")
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help="Path to snapshot source directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry-run validation without DB commit",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to database",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Explicit test dotenv file required by --apply",
    )
    args = parser.parse_args()

    try:
        if args.apply:
            if args.env_file is None:
                parser.error("--apply exige --env-file apontando explicitamente para test")
            report = asyncio.run(apply_from_test_environment(args.snapshot_dir, args.env_file))
        else:
            report = run_seed_pindobal(snapshot_dir=args.snapshot_dir, dry_run=True)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(main())
