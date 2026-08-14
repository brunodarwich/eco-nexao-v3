"""Verify ECO-1604 workflow persistence in Supabase test with rollback."""

import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def archive_metadata_is_enforced(connection: AsyncConnection, link_id: uuid.UUID) -> bool:
    savepoint = await connection.begin_nested()
    try:
        await connection.execute(
            text(
                "update app_private.route_actors set archived_at = now() "
                "where id = :link_id"
            ),
            {"link_id": link_id},
        )
    except SQLAlchemyError:
        await savepoint.rollback()
        return True
    await savepoint.rollback()
    return False


async def verify_transaction(connection: AsyncConnection) -> dict[str, bool]:
    actor_id = (
        await connection.execute(
            text("select id from auth.users order by created_at desc limit 1")
        )
    ).scalar_one_or_none()
    link = (
        await connection.execute(
            text(
                "select id, route_id, actor_id from app_private.route_actors "
                "where archived_at is null order by created_at limit 1"
            )
        )
    ).mappings().first()
    if actor_id is None or link is None:
        return {"test identity and active route link available": False}

    metadata_enforced = await archive_metadata_is_enforced(connection, link["id"])
    await connection.execute(
        text(
            "update app_private.route_actors set archived_at = now(), archived_by = :actor_id, "
            "archive_reason = 'ECO-1604 smoke rollback' where id = :link_id"
        ),
        {"actor_id": actor_id, "link_id": link["id"]},
    )
    hidden_while_archived = (
        await connection.execute(
            text(
                "select count(*) from app_private.route_actors "
                "where id = :link_id and archived_at is null"
            ),
            {"link_id": link["id"]},
        )
    ).scalar_one() == 0
    await connection.execute(
        text(
            "update app_private.route_actors set archived_at = null, archived_by = null, "
            "archive_reason = null where id = :link_id"
        ),
        {"link_id": link["id"]},
    )
    restored = (
        await connection.execute(
            text(
                "select count(*) from app_private.route_actors where id = :link_id "
                "and actor_id = :linked_actor_id and archived_at is null"
            ),
            {"link_id": link["id"], "linked_actor_id": link["actor_id"]},
        )
    ).scalar_one() == 1
    return {
        "archive metadata constraint": metadata_enforced,
        "archived link excluded from active set": hidden_while_archived,
        "archived link restored without identity loss": restored,
    }


async def verify() -> int:
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    engine = create_async_engine(Settings().DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                results = await verify_transaction(connection)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()

    failures = [name for name, passed in results.items() if not passed]
    if failures:
        print("EDITORIAL_WORKFLOW=ERROR")
        for failure in failures:
            print(f"- categoria: {failure.upper().replace(' ', '_')}")
        return 1
    print("EDITORIAL_WORKFLOW=OK")
    for name in results:
        print(f"- {name}: OK")
    print("- synthetic writes: rolled back")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
