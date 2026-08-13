"""FastAPI dependencies for domain services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.content_service import ContentService
from app.services.storage_service import StorageService
from app.services.territorial import TerritorialService
from app.services.user_service import UserService

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def get_territorial_service(db: DatabaseSession) -> TerritorialService:
    """Build the territorial service for one request."""
    return TerritorialService(db)


def get_user_service(db: DatabaseSession) -> UserService:
    """Build the user service for one request."""
    return UserService(db)


def get_storage_service() -> StorageService:
    """Build the storage service for one request."""
    return StorageService()


def get_content_service() -> ContentService:
    """Build the content service for one request."""
    return ContentService()



