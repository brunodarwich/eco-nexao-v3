"""Prove that an induced Pindobal failure leaves no partial publication in test."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.ingestion.seed_pindobal import DEFAULT_SNAPSHOT_DIR, run_seed_pindobal_apply

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def counts(session: AsyncSession) -> dict[str, int]:
    statements = {
        "regions": "select count(*) from app_private.regions",
        "routes": "select count(*) from app_private.routes",
        "origins": "select count(*) from app_private.route_origins",
        "geometries": "select count(*) from app_private.route_geometries",
        "sources": "select count(*) from app_private.external_sources",
        "runs": "select count(*) from app_private.ingestion_runs",
    }
    return {
        name: int((await session.execute(text(statement))).scalar_one())
        for name, statement in statements.items()
    }


async def verify() -> int:
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    settings = Settings()
    if settings.APP_ENV != "test":
        print("PINDOBAL_TRANSACTION=ERROR")
        print("- categoria: TARGET_NOT_TEST")
        return 1
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            before = await counts(session)
        try:
            async with factory() as session:
                await run_seed_pindobal_apply(
                    DEFAULT_SNAPSHOT_DIR, session, fail_after="route"
                )
        except RuntimeError as exc:
            if "induzida" not in str(exc):
                raise
        else:
            print("PINDOBAL_TRANSACTION=ERROR")
            print("- categoria: INDUCED_FAILURE_DID_NOT_FAIL")
            return 1
        async with factory() as session:
            after = await counts(session)
    finally:
        await engine.dispose()

    if before != after:
        print("PINDOBAL_TRANSACTION=ERROR")
        print("- categoria: PARTIAL_DATA_AFTER_ROLLBACK")
        return 1
    print("PINDOBAL_TRANSACTION=OK")
    print("- induced failure: rolled back")
    print("- territorial/source/run counts: unchanged")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
