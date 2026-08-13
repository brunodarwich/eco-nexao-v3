"""Verify the exact ECO-1501 territorial slice persisted in Supabase test."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def verify() -> int:
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    settings = Settings()
    if settings.APP_ENV != "test":
        print("PINDOBAL_APPLY=ERROR")
        print("- categoria: TARGET_NOT_TEST")
        return 1
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        "select "
                        "(select count(*) from app_private.regions "
                        " where slug = 'santarem-belterra') as regions, "
                        "(select count(*) from app_private.routes "
                        " where slug = 'rota-pindobal') as routes, "
                        "(select count(*) from app_private.route_origins o "
                        " join app_private.routes r "
                        " on r.id = o.route_id where r.slug = 'rota-pindobal') as origins, "
                        "(select count(*) from app_private.route_geometries g "
                        " join app_private.route_origins o on o.id = g.route_origin_id "
                        " join app_private.routes r on r.id = o.route_id "
                        " where r.slug = 'rota-pindobal') as geometries, "
                        "(select count(*) from app_private.external_sources "
                        " where slug = 'pindobal-snapshot-v1') as sources, "
                        "(select count(*) from app_private.ingestion_runs ir "
                        " join app_private.external_sources s on s.id = ir.source_id "
                        " where s.slug = 'pindobal-snapshot-v1' "
                        " and ir.status = 'completed') as runs, "
                        "(select count(*) from app_private.route_geometries g "
                        " join app_private.route_origins o on o.id = g.route_origin_id "
                        " join app_private.routes r on r.id = o.route_id "
                        " where r.slug = 'rota-pindobal' "
                        " and extensions.ST_SRID(g.geometry::extensions.geometry) = 4326"
                        ") as srid_ok, "
                        "(select count(*) from app_private.actors) as actors, "
                        "(select count(*) from app_private.raw_source_records) as raw_records, "
                        "(select count(*) from app_private.field_provenance) as provenance"
                    )
                )
            ).one()
    finally:
        await engine.dispose()
    values = tuple(int(value) for value in row)
    fixed = values[:5] + (values[6],)
    if fixed != (1, 1, 3, 3, 1, 3) or values[5] < 1:
        print("PINDOBAL_APPLY=ERROR")
        print("- categoria: PERSISTED_COUNTS_MISMATCH")
        return 1
    print("PINDOBAL_APPLY=OK")
    print(f"- region/route/source: 1 each; completed runs: {values[5]}")
    print("- origins/geometries: 3 each")
    print("- geometry SRID 4326: 3/3")
    print(f"- actors/raw/provenance: {values[7]}/{values[8]}/{values[9]}")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
