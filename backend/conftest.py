"""Global pytest configuration for the network-free default suite."""

import asyncio
import os
import sys

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "postgresql+psycopg://unit:unit@127.0.0.1:1/unit"
os.environ["SUPABASE_URL"] = "https://unit-test.supabase.co"
os.environ["SUPABASE_JWKS_URL"] = "https://unit-test.supabase.co/auth/v1/.well-known/jwks.json"
os.environ["SUPABASE_JWT_ISSUER"] = "https://unit-test.supabase.co/auth/v1"


def pytest_configure() -> None:
    """Set SelectorEventLoop on Windows for psycopg async compatibility."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
