"""SQLAlchemy declarative base for the private FastAPI domain."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

DOMAIN_SCHEMA = "app_private"


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    metadata = MetaData(schema=DOMAIN_SCHEMA)
