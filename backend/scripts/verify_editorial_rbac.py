"""Exercise editorial RBAC and audit invariants in Supabase test with rollback."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def mutation_is_rejected(connection: AsyncConnection, statement: str) -> bool:
    savepoint = await connection.begin_nested()
    try:
        await connection.execute(text(statement))
    except SQLAlchemyError:
        await savepoint.rollback()
        return True
    await savepoint.rollback()
    return False


async def verify_transaction(connection: AsyncConnection) -> dict[str, bool]:
    users = list(
        (
            await connection.execute(
                text("select id from auth.users order by created_at desc limit 2")
            )
        ).scalars()
    )
    if len(users) < 2:
        return {"two test identities available": False}
    admin_id, editor_id = users

    await connection.execute(
        text(
            "insert into app_private.editorial_memberships "
            "(user_id, role, granted_by) values "
            "(:admin_id, 'admin', :admin_id), (:editor_id, 'editor', :admin_id)"
        ),
        {"admin_id": admin_id, "editor_id": editor_id},
    )
    admin_capabilities = set(
        (
            await connection.execute(
                text(
                    "select c.capability from app_private.editorial_memberships m "
                    "join app_private.editorial_role_capabilities c on c.role = m.role "
                    "where m.user_id = :user_id and m.revoked_at is null"
                ),
                {"user_id": admin_id},
            )
        ).scalars()
    )
    editor_capabilities = set(
        (
            await connection.execute(
                text(
                    "select c.capability from app_private.editorial_memberships m "
                    "join app_private.editorial_role_capabilities c on c.role = m.role "
                    "where m.user_id = :user_id and m.revoked_at is null"
                ),
                {"user_id": editor_id},
            )
        ).scalars()
    )
    membership_id = (
        await connection.execute(
            text(
                "update app_private.editorial_memberships set revoked_at = now(), "
                "revoked_by = :admin_id, revoke_reason = 'rbac smoke rollback' "
                "where user_id = :editor_id returning id"
            ),
            {"admin_id": admin_id, "editor_id": editor_id},
        )
    ).scalar_one()
    active_after_revoke = int(
        (
            await connection.execute(
                text(
                    "select count(*) from app_private.editorial_memberships "
                    "where user_id = :editor_id and revoked_at is null"
                ),
                {"editor_id": editor_id},
            )
        ).scalar_one()
    )
    audit_id = (
        await connection.execute(
            text(
                "insert into app_private.audit_logs "
                "(actor_id, action, resource_type, resource_id, changes, reason) values "
                "(:admin_id, 'MEMBERSHIP_REVOKE', 'editorial_membership', "
                ":membership_id, '{\"before\":{},\"after\":{}}'::jsonb, "
                "'rbac smoke rollback') returning id"
            ),
            {"admin_id": admin_id, "membership_id": membership_id},
        )
    ).scalar_one()
    update_denied = await mutation_is_rejected(
        connection,
        f"update app_private.audit_logs set reason = 'tamper' where id = '{audit_id}'",
    )
    delete_denied = await mutation_is_rejected(
        connection, f"delete from app_private.audit_logs where id = '{audit_id}'"
    )
    return {
        "admin capabilities": "memberships.manage" in admin_capabilities,
        "editor least privilege": (
            "content.draft.update" in editor_capabilities
            and "content.publish" not in editor_capabilities
        ),
        "revocation immediate": active_after_revoke == 0,
        "audit update denied": update_denied,
        "audit delete denied": delete_denied,
    }


async def private_role_denied(connection_url: str, role: str) -> bool:
    engine = create_async_engine(connection_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f"set local role {role}"))
                await connection.execute(
                    text("select count(*) from app_private.editorial_memberships")
                )
            except SQLAlchemyError:
                return True
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
    return False


async def verify() -> int:
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    connection_url = Settings().DATABASE_URL.get_secret_value()
    engine = create_async_engine(connection_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                results = await verify_transaction(connection)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()

    results["anon denied"] = await private_role_denied(connection_url, "anon")
    results["authenticated denied"] = await private_role_denied(
        connection_url, "authenticated"
    )
    failures = [name for name, passed in results.items() if not passed]
    if failures:
        print("EDITORIAL_RBAC=ERROR")
        for failure in failures:
            print(f"- categoria: {failure.upper().replace(' ', '_')}")
        return 1
    print("EDITORIAL_RBAC=OK")
    for name in results:
        print(f"- {name}: OK")
    print("- synthetic writes: rolled back")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
