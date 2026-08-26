"""Transactional PostGIS verification for ECO-2306 against Supabase test."""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def verify(env_file: Path) -> int:
    load_dotenv(env_file, override=True)
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    ids = {name: uuid.uuid4() for name in ("region_a", "region_b", "route", "origin")}
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                category_rows = (
                    await connection.execute(
                        text(
                            "select slug, id from app_private.actor_categories "
                            "where slug in ('alimentacao', 'saude', 'transporte')"
                        )
                    )
                ).all()
                categories: dict[str, uuid.UUID] = {str(row[0]): row[1] for row in category_rows}
                if len(categories) != 3:
                    raise AssertionError("canonical categories missing")
                await connection.execute(
                    text(
                        "insert into app_private.regions(id, slug, name, state_code) values "
                        "(:ra, :sa, 'Region A', 'PA'), (:rb, :sb, 'Region B', 'PA')"
                    ),
                    {
                        "ra": ids["region_a"],
                        "rb": ids["region_b"],
                        "sa": f"eco2306-a-{ids['region_a']}",
                        "sb": f"eco2306-b-{ids['region_b']}",
                    },
                )
                await connection.execute(
                    text(
                        "insert into app_private.routes"
                        "(id, region_id, slug, title, city, state_code) "
                        "values (:route, :region, :slug, 'ECO-2306', 'Test', 'PA')"
                    ),
                    {
                        "route": ids["route"],
                        "region": ids["region_a"],
                        "slug": f"eco2306-route-{ids['route']}",
                    },
                )
                await connection.execute(
                    text(
                        "insert into app_private.route_origins(id, route_id, code, name, location) "
                        "values (:origin, :route, 'test', 'Test', "
                        "extensions.ST_GeogFromText('SRID=4326;POINT(-54.90 -2.50)'))"
                    ),
                    ids,
                )
                actors = {
                    "featured": uuid.uuid4(),
                    "ordinary": uuid.uuid4(),
                    "outside": uuid.uuid4(),
                    "other_region": uuid.uuid4(),
                    "health": uuid.uuid4(),
                    "transport": uuid.uuid4(),
                }
                actor_rows = [
                    ("featured", "alimentacao", ids["region_a"], -54.9000, -2.5000),
                    ("ordinary", "alimentacao", ids["region_a"], -54.9005, -2.5000),
                    ("outside", "alimentacao", ids["region_a"], -54.9300, -2.5000),
                    ("other_region", "alimentacao", ids["region_b"], -54.9000, -2.5000),
                    ("health", "saude", ids["region_a"], -54.9500, -2.5000),
                    ("transport", "transporte", ids["region_a"], -54.9002, -2.5000),
                ]
                for name, slug, region_id, lng, lat in actor_rows:
                    await connection.execute(
                        text(
                            "insert into app_private.actors"
                            "(id, slug, name, category_id, region_id, location) values "
                            "(:id, :slug, :name, :category, :region, "
                            "extensions.ST_SetSRID(extensions.ST_MakePoint(:lng, :lat), 4326)"
                            "::extensions.geography)"
                        ),
                        {
                            "id": actors[name],
                            "slug": f"eco2306-{name}-{actors[name]}",
                            "name": name,
                            "category": categories[slug],
                            "region": region_id,
                            "lng": lng,
                            "lat": lat,
                        },
                    )
                for name, featured, order in (
                    ("featured", True, 99),
                    ("ordinary", False, 1),
                    ("outside", False, 2),
                    ("other_region", True, 0),
                    ("transport", False, 3),
                ):
                    await connection.execute(
                        text(
                            "insert into app_private.route_actors"
                            "(route_id, actor_id, origin_flags, is_featured, sort_order) "
                            "values (:route, :actor, '{\"test\": true}'::jsonb, "
                            ":featured, :sort_order)"
                        ),
                        {
                            "route": ids["route"],
                            "actor": actors[name],
                            "featured": featured,
                            "sort_order": order,
                        },
                    )
                query = text(
                    "select a.id from app_private.actors a "
                    "join app_private.route_actors ra on ra.actor_id = a.id "
                    "join app_private.actor_categories c on c.id = a.category_id "
                    "where ra.route_id = :route and ra.archived_at is null "
                    "and a.region_id = :region and a.deleted_at is null "
                    "and c.spatial_scope in ('route_corridor', 'both') "
                    "and extensions.ST_DWithin(a.location, "
                    "extensions.ST_GeogFromText("
                    "'SRID=4326;LINESTRING(-54.91 -2.50,-54.89 -2.50)'), :buffer) "
                    "order by ra.is_featured desc, ra.sort_order asc, a.id asc"
                )
                returned = list(
                    (
                        await connection.execute(
                            query,
                            {
                                "route": ids["route"],
                                "region": ids["region_a"],
                                "buffer": settings.ROUTE_CORRIDOR_BUFFER_METERS,
                            },
                        )
                    ).scalars()
                )
                assert returned == [actors["featured"], actors["ordinary"], actors["transport"]]
                citywide = set(
                    (
                        await connection.execute(
                            text(
                                "select a.id from app_private.actors a "
                                "join app_private.actor_categories c on c.id=a.category_id "
                                "where a.region_id=:region and a.deleted_at is null "
                                "and c.spatial_scope in ('citywide_essential','both')"
                            ),
                            {"region": ids["region_a"]},
                        )
                    ).scalars()
                )
                assert citywide == {actors["health"], actors["transport"]}
                try:
                    async with connection.begin_nested():
                        await connection.execute(
                            text(
                                "update app_private.actor_categories set spatial_scope='both' "
                                "where slug='saude'"
                            )
                        )
                except IntegrityError:
                    pass
                else:
                    raise AssertionError("non-transport category accepted spatial_scope=both")
                index_names = set(
                    (
                        await connection.execute(
                            text(
                                "select indexname from pg_indexes "
                                "where schemaname='app_private' and indexname in "
                                "('idx_actors_location','idx_actors_region_category_active',"
                                "'idx_route_actors_map_priority')"
                            )
                        )
                    ).scalars()
                )
                assert len(index_names) == 3
                await transaction.rollback()
            except Exception:
                await transaction.rollback()
                raise
    except Exception as exc:
        print("ECO2306_POSTGIS=ERROR")
        print(f"- categoria: {type(exc).__name__}")
        return 1
    finally:
        await engine.dispose()
    print("ECO2306_POSTGIS=OK")
    print("- corredor, prioridade, outra região, citywide, both e índices: aprovados")
    print("- todas as fixtures sofreram rollback")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env.test")
    args = parser.parse_args()
    env_file = (BACKEND_DIR / args.env_file).resolve()
    if env_file.parent != BACKEND_DIR or not env_file.is_file():
        return 1
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(verify(env_file))


if __name__ == "__main__":
    raise SystemExit(main())
