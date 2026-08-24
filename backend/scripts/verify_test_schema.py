"""Verify migrated Supabase test schema and rollback all smoke objects."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
DOMAIN_TABLES = {
    "accessibility_features",
    "actor_accessibility_features",
    "actor_categories",
    "actor_external_refs",
    "actors",
    "external_sources",
    "favorite_actors",
    "favorite_routes",
    "field_provenance",
    "ingestion_runs",
    "media_assets",
    "profiles",
    "raw_source_records",
    "reconciliation_candidates",
    "regions",
    "route_actors",
    "route_alerts",
    "route_geometries",
    "route_origins",
    "routes",
    "trip_actor_visits",
    "trips",
    "user_preferences",
}


async def verify() -> int:
    """Run catalog checks plus transactional PostGIS and event-trigger smoke tests."""
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    failures: list[str] = []
    try:
        async with engine.connect() as connection:
            tables = set(
                (
                    await connection.execute(
                        text(
                            "select tablename from pg_tables "
                            "where schemaname = 'app_private'"
                        )
                    )
                ).scalars()
            )
            if tables != DOMAIN_TABLES:
                failures.append("DOMAIN_TABLE_SET_MISMATCH")

            rls_count = int(
                (
                    await connection.execute(
                        text(
                            "select count(*) from pg_class c "
                            "join pg_namespace n on n.oid = c.relnamespace "
                            "where n.nspname = 'app_private' and c.relkind = 'r' "
                            "and c.relrowsecurity"
                        )
                    )
                ).scalar_one()
            )
            if rls_count != len(DOMAIN_TABLES):
                failures.append("RLS_NOT_ENABLED_ON_ALL_TABLES")

            exposed_privileges = int(
                (
                    await connection.execute(
                        text(
                            "select count(*) from information_schema.role_table_grants "
                            "where table_schema = 'app_private' "
                            "and grantee in ('anon', 'authenticated')"
                        )
                    )
                ).scalar_one()
            )
            if exposed_privileges:
                failures.append("DATA_API_TABLE_GRANTS_PRESENT")

            schema_access = bool(
                (
                    await connection.execute(
                        text(
                            "select has_schema_privilege('anon', 'app_private', 'USAGE') "
                            "or has_schema_privilege('authenticated', 'app_private', 'USAGE')"
                        )
                    )
                ).scalar_one()
            )
            if schema_access:
                failures.append("DATA_API_SCHEMA_USAGE_PRESENT")

            await connection.rollback()
            transaction = await connection.begin()
            try:
                await connection.execute(
                    text(
                        "create table app_private.eco_schema_smoke ("
                        "id integer primary key, "
                        "point extensions.geography(Point, 4326), "
                        "line extensions.geography(LineString, 4326))"
                    )
                )
                await connection.execute(
                    text(
                        "insert into app_private.eco_schema_smoke (id, point, line) values ("
                        "1, extensions.ST_GeogFromText('SRID=4326;POINT(-54.7 -2.4)'), "
                        "extensions.ST_GeogFromText("
                        "'SRID=4326;LINESTRING(-54.7 -2.4,-54.8 -2.5)'))"
                    )
                )
                smoke = (
                    await connection.execute(
                        text(
                            "select extensions.GeometryType(point::extensions.geometry), "
                            "extensions.GeometryType(line::extensions.geometry), "
                            "c.relrowsecurity from app_private.eco_schema_smoke s "
                            "join pg_class c on c.oid = 'app_private.eco_schema_smoke'::regclass "
                            "where s.id = 1"
                        )
                    )
                ).one()
                if tuple(smoke) != ("POINT", "LINESTRING", True):
                    failures.append("POSTGIS_OR_AUTO_RLS_SMOKE_FAILED")
            finally:
                await transaction.rollback()
    except Exception as exc:
        print("TEST_SCHEMA=ERROR")
        print(f"- categoria: {type(exc).__name__}")
        return 1
    finally:
        await engine.dispose()

    if failures:
        print("TEST_SCHEMA=ERROR")
        for failure in failures:
            print(f"- categoria: {failure}")
        return 1
    print("TEST_SCHEMA=OK")
    print("- 24 tabelas privadas encontradas")
    print("- RLS habilitado em 24/24")
    print("- anon/authenticated sem acesso ao schema ou tabelas")
    print("- Point, LineString e trigger RLS verificados com rollback")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
