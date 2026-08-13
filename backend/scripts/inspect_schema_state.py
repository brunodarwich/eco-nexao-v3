"""Inspect non-sensitive migration/schema state without modifying the database."""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def inspect_schema(env_file: Path) -> int:
    """Report migration versions and custom table count using read-only queries."""
    load_dotenv(env_file, override=True)
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            history_exists = bool(
                (
                    await connection.execute(
                        text(
                            "select to_regclass('supabase_migrations.schema_migrations') "
                            "is not null"
                        )
                    )
                ).scalar_one()
            )
            versions: list[str] = []
            if history_exists:
                versions = list(
                    (
                        await connection.execute(
                            text(
                                "select version from supabase_migrations.schema_migrations "
                                "order by version"
                            )
                        )
                    ).scalars()
                )
            tables = list(
                (
                    await connection.execute(
                        text(
                            "select table_schema || '.' || table_name "
                            "from information_schema.tables "
                            "where table_schema in ('public', 'private', 'app_private') "
                            "and table_name not like 'pg_%' "
                            "order by table_schema, table_name"
                        )
                    )
                ).scalars()
            )
    except Exception as exc:
        print("SCHEMA_INSPECTION=ERROR")
        print(f"- categoria: {type(exc).__name__}")
        return 1
    finally:
        await engine.dispose()

    print("SCHEMA_INSPECTION=OK")
    print(f"- migration history presente: {'sim' if history_exists else 'não'}")
    print(f"- migrations registradas: {len(versions)}")
    for version in versions:
        print(f"  - {version}")
    print(f"- tabelas customizadas public/private/app_private: {len(tables)}")
    for table in tables:
        print(f"  - {table}")
    return 0


def main() -> int:
    """Select a local env file and execute the read-only inspection."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    env_file = (BACKEND_DIR / args.env_file).resolve()
    if env_file.parent != BACKEND_DIR or not env_file.is_file():
        print("SCHEMA_INSPECTION=ERROR")
        print("- categoria: ENV_FILE_INVALID")
        return 1
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(inspect_schema(env_file))


if __name__ == "__main__":
    raise SystemExit(main())
