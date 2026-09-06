"""Database package initialization."""

from typing import Any

from app.db.base import Base

__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db"]


def __getattr__(name: str) -> Any:
    if name in {"engine", "AsyncSessionLocal", "get_db"}:
        import app.db.session as db_session

        return getattr(db_session, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
