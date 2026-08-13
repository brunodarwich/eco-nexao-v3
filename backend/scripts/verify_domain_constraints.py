"""Exercise core territorial constraints in Supabase test with rollback."""

import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def base_route(connection: AsyncConnection, suffix: str) -> tuple[str, str]:
    """Insert a region and route and return their UUID strings."""
    region_id = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.regions (slug, name, state_code) "
                    "values (:slug, 'Smoke Region', 'PA') returning id"
                ),
                {"slug": f"smoke-region-{suffix}"},
            )
        ).scalar_one()
    )
    route_id = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.routes "
                    "(region_id, slug, title, city, state_code) "
                    "values (:region_id, :slug, 'Smoke Route', 'Belterra', 'PA') returning id"
                ),
                {"region_id": region_id, "slug": f"smoke-route-{suffix}"},
            )
        ).scalar_one()
    )
    return region_id, route_id


async def duplicate_origin_is_rejected(connection: AsyncConnection) -> bool:
    """Verify the route/code unique constraint with an actual conflicting insert."""
    _, route_id = await base_route(connection, "duplicate")
    statement = text(
        "insert into app_private.route_origins "
        "(route_id, code, name, location) values "
        "(:route_id, 'porto', 'Porto', "
        "extensions.ST_GeogFromText('SRID=4326;POINT(-54.7 -2.4)'))"
    )
    await connection.execute(statement, {"route_id": route_id})
    savepoint = await connection.begin_nested()
    try:
        await connection.execute(statement, {"route_id": route_id})
    except SQLAlchemyError:
        await savepoint.rollback()
        return True
    await savepoint.rollback()
    return False


async def invalid_geometry_is_rejected(connection: AsyncConnection) -> bool:
    """Verify a Point cannot be stored in the LineString geography column."""
    _, route_id = await base_route(connection, "geometry")
    origin_id = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.route_origins "
                    "(route_id, code, name, location) values "
                    "(:route_id, 'porto', 'Porto', "
                    "extensions.ST_GeogFromText('SRID=4326;POINT(-54.7 -2.4)')) returning id"
                ),
                {"route_id": route_id},
            )
        ).scalar_one()
    )
    savepoint = await connection.begin_nested()
    try:
        await connection.execute(
            text(
                "insert into app_private.route_geometries "
                "(route_origin_id, geometry) values "
                "(:origin_id, extensions.ST_GeogFromText('SRID=4326;POINT(-54.7 -2.4)'))"
            ),
            {"origin_id": origin_id},
        )
    except SQLAlchemyError:
        await savepoint.rollback()
        return True
    await savepoint.rollback()
    return False


async def actor_can_belong_to_multiple_routes(connection: AsyncConnection) -> bool:
    """Verify the route-actor model allows distinct route memberships."""
    region_id, route_a = await base_route(connection, "actor-a")
    route_b = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.routes "
                    "(region_id, slug, title, city, state_code) values "
                    "(:region_id, 'smoke-route-actor-b', 'Route B', 'Belterra', 'PA') "
                    "returning id"
                ),
                {"region_id": region_id},
            )
        ).scalar_one()
    )
    category_id = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.actor_categories (slug, label) "
                    "values ('smoke-category', 'Smoke') returning id"
                )
            )
        ).scalar_one()
    )
    actor_id = str(
        (
            await connection.execute(
                text(
                    "insert into app_private.actors (slug, name, category_id) "
                    "values ('smoke-actor', 'Smoke Actor', :category_id) returning id"
                ),
                {"category_id": category_id},
            )
        ).scalar_one()
    )
    await connection.execute(
        text(
            "insert into app_private.route_actors (route_id, actor_id) values "
            "(:route_a, :actor_id), (:route_b, :actor_id)"
        ),
        {"route_a": route_a, "route_b": route_b, "actor_id": actor_id},
    )
    count = int(
        (
            await connection.execute(
                text("select count(*) from app_private.route_actors where actor_id = :actor_id"),
                {"actor_id": actor_id},
            )
        ).scalar_one()
    )
    return count == 2


async def alert_window_is_respected(connection: AsyncConnection) -> bool:
    """Verify the normative active-alert predicate returns only current alerts."""
    _, route_id = await base_route(connection, "alerts")
    await connection.execute(
        text(
            "insert into app_private.route_alerts "
            "(route_id, title, message, starts_at, ends_at, published_at, is_active) values "
            "(:route_id, 'Current', 'Current', now() - interval '1 hour', "
            "now() + interval '1 hour', now() - interval '2 hours', true), "
            "(:route_id, 'Future', 'Future', now() + interval '1 hour', null, now(), true), "
            "(:route_id, 'Inactive', 'Inactive', null, null, now(), false)"
        ),
        {"route_id": route_id},
    )
    count = int(
        (
            await connection.execute(
                text(
                    "select count(*) from app_private.route_alerts where route_id = :route_id "
                    "and is_active and published_at <= now() "
                    "and (starts_at is null or starts_at <= now()) "
                    "and (ends_at is null or ends_at > now())"
                ),
                {"route_id": route_id},
            )
        ).scalar_one()
    )
    return count == 1


async def run_rolled_back(
    connection_url: str,
    check: Callable[[AsyncConnection], Awaitable[bool]],
) -> bool:
    """Run one constraint check in an isolated transaction and always roll it back."""
    engine = create_async_engine(connection_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                return await check(connection)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


async def verify() -> int:
    """Execute all current territorial acceptance checks."""
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    connection_url = Settings().DATABASE_URL.get_secret_value()
    checks = {
        "duplicate origin rejected": duplicate_origin_is_rejected,
        "invalid geometry rejected": invalid_geometry_is_rejected,
        "actor on multiple routes": actor_can_belong_to_multiple_routes,
        "alert window": alert_window_is_respected,
    }
    failures: list[str] = []
    for name, check in checks.items():
        if not await run_rolled_back(connection_url, check):
            failures.append(name)
    if failures:
        print("DOMAIN_CONSTRAINTS=ERROR")
        for failure in failures:
            print(f"- categoria: {failure.upper().replace(' ', '_')}")
        return 1
    print("DOMAIN_CONSTRAINTS=OK")
    print("- origem duplicada rejeitada")
    print("- tipo geográfico inválido rejeitado")
    print("- ator relacionado a múltiplas rotas")
    print("- janela temporal de alertas confirmada")
    print("- todas as escritas revertidas")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
