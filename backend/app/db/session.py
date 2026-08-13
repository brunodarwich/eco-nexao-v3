"""Database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Engine configuration
engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    echo=settings.DATABASE_ECHO,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency for obtaining an async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_readiness() -> bool:
    """Return whether PostgreSQL is reachable and PostGIS is installed."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
            result = await connection.execute(
                text("select exists(select 1 from pg_extension where extname = 'postgis')")
            )
            return bool(result.scalar_one())
    except SQLAlchemyError:
        return False
