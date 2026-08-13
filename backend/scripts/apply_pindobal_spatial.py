"""Backfill ECO-1503 geometry metadata and actor-route metrics in isolated test."""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.ingestion.manifest import MANIFEST_ENTRIES, verify_manifest
from app.ingestion.osrm_importer import EXPECTED_ORIGINS, process_osrm_origin
from scripts.check_test_isolation import require_test_isolation

BACKEND_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")


async def apply() -> int:
    env_file = BACKEND_DIR / ".env.test"
    require_test_isolation(test_path=env_file)
    manifest = verify_manifest(SNAPSHOT_DIR)
    if not manifest.is_valid:
        raise RuntimeError("Snapshot Pindobal não passou no manifesto canônico.")
    load_dotenv(env_file, override=True)
    settings = Settings()
    if settings.APP_ENV != "test":
        raise RuntimeError("Backfill espacial permitido somente em test.")

    results = {
        code: process_osrm_origin(code, SNAPSHOT_DIR)
        for code in ("porto", "aeroporto", "rodoviaria")
    }
    if not all(result.is_valid for result in results.values()):
        raise RuntimeError("Geometria OSRM inválida.")

    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    try:
        async with engine.begin() as connection:
            for code, result in results.items():
                filename = str(EXPECTED_ORIGINS[code]["filename"])
                await connection.execute(
                    text(
                        "UPDATE app_private.route_geometries g SET "
                        "bounds=CAST(:bounds AS jsonb), "
                        "source_hash=:source_hash FROM app_private.route_origins o, "
                        "app_private.routes r WHERE g.route_origin_id=o.id "
                        "AND o.route_id=r.id AND r.slug='rota-pindobal' AND o.code=:code "
                        "AND g.provider='osrm-snapshot'"
                    ),
                    {
                        "bounds": json.dumps(result.bounds, sort_keys=True),
                        "source_hash": MANIFEST_ENTRIES[filename][1],
                        "code": code,
                    },
                )
            changed = await connection.execute(
                text(
                    """
                    WITH route_line AS (
                      SELECT r.id route_id, g.geometry,
                        extensions.ST_NPoints(g.geometry::extensions.geometry) points
                      FROM app_private.routes r
                      JOIN app_private.route_origins o ON o.route_id=r.id
                      JOIN app_private.route_geometries g ON g.route_origin_id=o.id
                      WHERE r.slug='rota-pindobal' AND o.code='porto'
                    ), metrics AS (
                      SELECT a.id actor_id, rl.route_id,
                        extensions.ST_Distance(a.location, rl.geometry) distance_m,
                        extensions.ST_LineLocatePoint(rl.geometry::extensions.geometry,
                          a.location::extensions.geometry) fraction, rl.points,
                        jsonb_build_object(
                          'porto', bool_or(o.code='porto' AND extensions.ST_DWithin(
                            a.location,g.geometry,1000)),
                          'aeroporto', bool_or(o.code='aeroporto' AND extensions.ST_DWithin(
                            a.location,g.geometry,1000)),
                          'rodoviaria', bool_or(o.code='rodoviaria' AND extensions.ST_DWithin(
                            a.location,g.geometry,1000)),
                          'km_porto', round((extensions.ST_LineLocatePoint(
                            rl.geometry::extensions.geometry,a.location::extensions.geometry)
                            * extensions.ST_Length(rl.geometry)/1000.0)::numeric,3)) flags
                      FROM app_private.actors a CROSS JOIN route_line rl
                      JOIN app_private.route_origins o ON o.route_id=rl.route_id
                      JOIN app_private.route_geometries g ON g.route_origin_id=o.id
                      WHERE a.location IS NOT NULL
                        AND extensions.ST_DWithin(a.location,rl.geometry,1000)
                      GROUP BY a.id,rl.route_id,rl.geometry,rl.points
                    )
                    INSERT INTO app_private.route_actors
                      (id,route_id,actor_id,distance_to_route_m,route_segment_index,origin_flags)
                    SELECT gen_random_uuid(),route_id,actor_id,distance_m,
                      LEAST(points-2,floor(fraction*(points-1))::integer),flags FROM metrics
                    ON CONFLICT (route_id,actor_id) DO UPDATE SET
                      distance_to_route_m=excluded.distance_to_route_m,
                      route_segment_index=excluded.route_segment_index,
                      origin_flags=excluded.origin_flags
                    WHERE (route_actors.distance_to_route_m,route_actors.route_segment_index,
                      route_actors.origin_flags) IS DISTINCT FROM
                      (excluded.distance_to_route_m,excluded.route_segment_index,
                      excluded.origin_flags)
                    RETURNING id
                    """
                )
            )
            changed_count = len(changed.all())
    finally:
        await engine.dispose()
    print("PINDOBAL_SPATIAL=OK")
    print(f"- relações inseridas/atualizadas: {changed_count}")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(apply()))
