"""Verify real PostgreSQL role denial and backend access with full rollback."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def role_is_denied(connection_url: str, role: str) -> bool:
    """Return True only when an actual SELECT is rejected for the requested role."""
    engine = create_async_engine(connection_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f"set local role {role}"))
                await connection.execute(text("select count(*) from app_private.regions"))
            except ProgrammingError:
                return True
            finally:
                await transaction.rollback()
        return False
    finally:
        await engine.dispose()


async def backend_can_write_and_read(connection_url: str) -> bool:
    """Exercise backend CRUD inside a transaction that is always rolled back."""
    engine = create_async_engine(connection_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                inserted = (
                    await connection.execute(
                        text(
                            "insert into app_private.regions "
                            "(slug, name, state_code, center) values "
                            "('eco-role-smoke', 'ECO Role Smoke', 'PA', "
                            "extensions.ST_GeogFromText('SRID=4326;POINT(-54.7 -2.4)')) "
                            "returning slug"
                        )
                    )
                ).scalar_one()
                selected = (
                    await connection.execute(
                        text(
                            "select slug from app_private.regions "
                            "where slug = 'eco-role-smoke'"
                        )
                    )
                ).scalar_one()
                return str(inserted) == str(selected) == "eco-role-smoke"
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


async def verify() -> int:
    """Run the minimum real role matrix required by the private API architecture."""
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    settings = Settings()
    connection_url = settings.DATABASE_URL.get_secret_value()
    results = {
        "anon denied": await role_is_denied(connection_url, "anon"),
        "authenticated denied": await role_is_denied(connection_url, "authenticated"),
        "backend read/write": await backend_can_write_and_read(connection_url),
    }
    if not all(results.values()):
        print("TEST_ROLE_MATRIX=ERROR")
        for label, passed in results.items():
            if not passed:
                print(f"- categoria: {label.upper().replace(' ', '_')}")
        return 1
    print("TEST_ROLE_MATRIX=OK")
    print("- anon: acesso negado")
    print("- authenticated: acesso negado")
    print("- backend: leitura/escrita confirmadas com rollback")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
