"""Read-only ECO-1503 verification against isolated Supabase test."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from scripts.check_test_isolation import require_test_isolation

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def verify() -> int:
    env_file = BACKEND_DIR / ".env.test"
    require_test_isolation(test_path=env_file)
    load_dotenv(env_file, override=True)
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            rows = (
                await connection.execute(
                    text(
                        """
                        SELECT o.code, extensions.ST_NPoints(g.geometry::extensions.geometry),
                          g.distance_m, g.bounds IS NOT NULL,
                          g.source_hash ~ '^[0-9a-f]{64}$',
                          extensions.ST_SRID(g.geometry::extensions.geometry)
                        FROM app_private.route_geometries g
                        JOIN app_private.route_origins o ON o.id=g.route_origin_id
                        JOIN app_private.routes r ON r.id=o.route_id
                        WHERE r.slug='rota-pindobal' ORDER BY o.sort_order
                        """
                    )
                )
            ).all()
            relation = (
                await connection.execute(
                    text(
                        """
                        SELECT count(*), count(DISTINCT actor_id),
                          count(*) FILTER (WHERE distance_to_route_m BETWEEN 0 AND 1000),
                          count(*) FILTER (WHERE route_segment_index >= 0),
                          count(*) FILTER (WHERE origin_flags ?&
                            ARRAY['porto','aeroporto','rodoviaria','km_porto'])
                        FROM app_private.route_actors ra
                        JOIN app_private.routes r ON r.id=ra.route_id
                        WHERE r.slug='rota-pindobal'
                        """
                    )
                )
            ).one()
            indexes = (
                await connection.execute(
                    text(
                        """
                        SELECT count(*) FROM pg_indexes WHERE schemaname='app_private'
                          AND indexname IN ('idx_actors_location',
                            'idx_route_geometries_geometry') AND indexdef LIKE '%gist%'
                        """
                    )
                )
            ).scalar_one()
    finally:
        await engine.dispose()

    expected = {
        "porto": (884, 45229),
        "aeroporto": (777, 41452),
        "rodoviaria": (866, 42319),
    }
    geometry_ok = len(rows) == 3 and all(
        expected[row[0]] == (row[1], row[2]) and row[3] and row[4] and row[5] == 4326
        for row in rows
    )
    total = int(relation[0])
    relation_ok = total > 0 and all(int(value) == total for value in relation[1:])
    if not geometry_ok or not relation_ok or int(indexes) != 2:
        print("PINDOBAL_SPATIAL=ERROR")
        return 1
    print("PINDOBAL_SPATIAL=OK")
    print("- geometry points: porto=884, aeroporto=777, rodoviaria=866")
    print("- geometry SRID/bounds/hash/distance: valid 3/3")
    print(f"- unique actor-route relations within 1000m: {total}")
    print("- required GiST indexes: 2/2")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
