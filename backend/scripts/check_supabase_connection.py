"""Run a read-only Supabase PostgreSQL smoke check without leaking connection details."""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def classify_connection_error(exc: Exception) -> str:
    """Map driver messages to safe categories without returning their contents."""
    message = str(exc).lower()
    categories = (
        (("password authentication failed", "authentication failed"), "AUTHENTICATION_FAILED"),
        (("tenant or user not found",), "POOLER_TENANT_OR_USER_INVALID"),
        (("could not translate host", "name or service not known", "getaddrinfo"), "DNS_FAILED"),
        (("timed out", "timeout", "network is unreachable"), "NETWORK_TIMEOUT_OR_UNREACHABLE"),
        (("connection refused",), "CONNECTION_REFUSED"),
        (("ssl", "certificate"), "SSL_ERROR"),
    )
    for markers, category in categories:
        if any(marker in message for marker in markers):
            return category
    return type(exc).__name__.upper()


async def check_connection(env_file: Path) -> int:
    """Check connectivity, PostgreSQL major version, and PostGIS availability."""
    load_dotenv(env_file, override=True)
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            version_result = await connection.execute(
                text("select current_setting('server_version_num')::integer")
            )
            extension_result = await connection.execute(
                text("select exists(select 1 from pg_extension where extname = 'postgis')")
            )
            version_number = int(version_result.scalar_one())
            postgis_installed = bool(extension_result.scalar_one())
    except Exception as exc:
        print("SUPABASE_CONNECTION=ERROR")
        print(f"- categoria: {classify_connection_error(exc)}")
        return 1
    finally:
        await engine.dispose()

    print("SUPABASE_CONNECTION=OK")
    print(f"- PostgreSQL major: {version_number // 10000}")
    print(f"- PostGIS instalado: {'sim' if postgis_installed else 'não'}")
    return 0 if version_number // 10000 == 17 and postgis_installed else 2


def main() -> int:
    """Parse a local environment filename without ever printing its contents."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    env_file = (BACKEND_DIR / args.env_file).resolve()
    if env_file.parent != BACKEND_DIR or not env_file.is_file():
        print("SUPABASE_CONNECTION=ERROR")
        print("- categoria: ENV_FILE_INVALID")
        return 1
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(check_connection(env_file))


if __name__ == "__main__":
    raise SystemExit(main())
