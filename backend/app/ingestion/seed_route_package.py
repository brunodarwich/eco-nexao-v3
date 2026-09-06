"""CLI entrypoint for Route Data Package Ingestion (ECO-2605).

Supports --package-file, --dry-run (default), and --apply with strict requirement
for --env-file pointing to backend/.env.test (APP_ENV=test).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.ingestion.route_package_importer import (
    run_route_package_apply,
    run_route_package_dry_run,
)
from scripts.check_test_isolation import BACKEND_DIR, require_test_isolation


async def apply_route_package_from_test_env(
    package_file: Path,
    env_file: Path,
    *,
    fail_after: str | None = None,
) -> dict[str, Any]:
    """Execute route package apply inside isolated test environment only."""
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
            return await run_route_package_apply(package_file, session, fail_after=fail_after)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="ECOnexão Route Package Ingestion Runner")
    parser.add_argument(
        "--package-file",
        type=Path,
        required=True,
        help="Path to route package markdown file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry-run validation without DB commit (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to database (requires test environment)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Explicit test dotenv file required by --apply",
    )
    parser.add_argument(
        "--fail-after",
        type=str,
        choices=["route", "geometries", "actors"],
        help="Induce transactional failure at specific step to verify rollback",
    )

    args = parser.parse_args()

    try:
        if args.apply:
            if args.env_file is None:
                parser.error("--apply exige --env-file apontando explicitamente para test")
            report = asyncio.run(
                apply_route_package_from_test_env(
                    args.package_file, args.env_file, fail_after=args.fail_after
                )
            )
        else:
            report = run_route_package_dry_run(args.package_file)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("status") == "success" else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(main())
