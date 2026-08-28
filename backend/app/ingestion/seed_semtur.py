"""Run the SEMTUR inventory ingestion pipeline (ECO-2505 / ADR 0014 / ADR 0015)."""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.ingestion.semtur_importer import (
    DEFAULT_SNAPSHOT_DIR,
    process_semtur_inventory,
)
from app.ingestion.semtur_repository import SEMTURPersistenceRepository
from scripts.check_test_isolation import BACKEND_DIR, require_test_isolation


def run_seed_semtur(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    csv_path: Path | None = None,
    raw_rows: list[dict[str, str]] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute complete SEMTUR ingestion pipeline in dry-run mode and produce summary report."""
    if not dry_run:
        raise RuntimeError("Use run_seed_semtur_apply com uma sessão DB explícita.")

    run_started_at = datetime.now(UTC).isoformat()

    semtur_records, semtur_stats = process_semtur_inventory(
        snapshot_dir=snapshot_dir,
        csv_path=csv_path,
        raw_rows=raw_rows,
    )

    total_read = len(semtur_records)
    rejected = sum(not record.is_valid for record in semtur_records)
    candidates = 0
    created = total_read - rejected

    run_finished_at = datetime.now(UTC).isoformat()

    report = {
        "status": "success",
        "dry_run": dry_run,
        "run_started_at": run_started_at,
        "run_finished_at": run_finished_at,
        "snapshot_dir": str(snapshot_dir),
        "rules": {
            "importer_version": "eco-2505-v1",
            "rules_version": "semtur-contract-1.0",
        },
        "counts": {
            "read": total_read,
            "created": created,
            "updated": 0,
            "unchanged": 0,
            "rejected": rejected,
            "candidates": candidates,
            "reconciled": total_read == (created + rejected + candidates),
        },
        "semtur_inventory": semtur_stats,
    }

    return report


async def run_seed_semtur_apply(
    snapshot_dir: Path,
    session: AsyncSession,
    *,
    csv_path: Path | None = None,
    raw_rows: list[dict[str, str]] | None = None,
    fail_after: str | None = None,
) -> dict[str, Any]:
    """Validate SEMTUR dataset and persist atomically in database."""
    report = run_seed_semtur(
        snapshot_dir=snapshot_dir,
        csv_path=csv_path,
        raw_rows=raw_rows,
        dry_run=True,
    )
    if report["status"] != "success":
        return report

    started_at = datetime.fromisoformat(cast(str, report["run_started_at"]))
    finished_at = datetime.fromisoformat(cast(str, report["run_finished_at"]))

    semtur_records, _ = process_semtur_inventory(
        snapshot_dir=snapshot_dir,
        csv_path=csv_path,
        raw_rows=raw_rows,
    )

    repository = SEMTURPersistenceRepository(session)
    run_id, persistence_stats = await repository.persist(
        report=report,
        started_at=started_at,
        finished_at=finished_at,
        semtur_records=semtur_records,
        fail_after=fail_after,
    )

    return {
        **report,
        "dry_run": False,
        "ingestion_run_id": str(run_id),
        "persistence": persistence_stats,
    }


async def apply_from_test_environment(
    snapshot_dir: Path,
    env_file: Path,
    csv_path: Path | None = None,
) -> dict[str, Any]:
    """Load an explicit test environment and refuse non-test targets."""
    canonical_test_file = (BACKEND_DIR / ".env.test").resolve()
    if env_file.resolve() != canonical_test_file:
        raise RuntimeError("--apply aceita somente o arquivo canônico backend/.env.test.")
    if not env_file.is_file():
        raise RuntimeError("Arquivo de ambiente de test não encontrado.")
    require_test_isolation(test_path=env_file)
    load_dotenv(env_file, override=True)
    settings = Settings()
    if settings.APP_ENV != "test":
        raise RuntimeError("--apply é permitido somente com APP_ENV=test.")
    database_url = settings.DATABASE_URL.get_secret_value()
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            return await run_seed_semtur_apply(snapshot_dir, session, csv_path=csv_path)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="SEMTUR Inventory Ingestion Runner (ECO-2505)")
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help="Path to snapshot source directory",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=None,
        help="Optional direct path to CSV file",
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
            report = asyncio.run(
                apply_from_test_environment(
                    snapshot_dir=args.snapshot_dir,
                    env_file=args.env_file,
                    csv_path=args.csv_path,
                )
            )
        else:
            report = run_seed_semtur(
                snapshot_dir=args.snapshot_dir,
                csv_path=args.csv_path,
                dry_run=True,
            )
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(main())
