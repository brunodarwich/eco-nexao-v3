from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.editorial_authorization import EditorialAuthorizationRepository
from app.services.content_service import ContentService
from app.services.editorial_authorization import EditorialAuthorizationService
from app.services.storage_service import StorageService
from app.services.territorial import TerritorialService
from app.services.user_service import UserService

if TYPE_CHECKING:
    from app.services.actor_admin import ActorAdminService
    from app.services.media_lifecycle import MediaLifecycleService
    from app.services.territorial_admin import TerritorialAdminService
    from app.services.workflow_admin import WorkflowAdminService

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


def get_editorial_authorization_service(
    db: DatabaseSession,
) -> EditorialAuthorizationService:
    """Build database-backed editorial authorization for one request."""
    return EditorialAuthorizationService(EditorialAuthorizationRepository(db))


def get_territorial_admin_service(
    db: DatabaseSession,
) -> "TerritorialAdminService":
    """Build the administrative territorial service for one request."""
    from app.services.territorial_admin import TerritorialAdminService

    return TerritorialAdminService(db)


def get_actor_admin_service(
    db: DatabaseSession,
) -> "ActorAdminService":
    """Build the administrative actor service for one request."""
    from app.services.actor_admin import ActorAdminService

    return ActorAdminService(db)


def get_workflow_admin_service(
    db: DatabaseSession,
) -> "WorkflowAdminService":
    """Build the administrative workflow service for one request."""
    from app.repositories.workflow_admin import WorkflowAdminRepository
    from app.services.workflow_admin import WorkflowAdminService

    return WorkflowAdminService(WorkflowAdminRepository(db))


def get_media_lifecycle_service(db: DatabaseSession) -> "MediaLifecycleService":
    """Build the server-side editorial media lifecycle for one request."""
    from app.repositories.media_lifecycle import MediaLifecycleRepository
    from app.services.media_lifecycle import MediaLifecycleService

    return MediaLifecycleService(
        MediaLifecycleRepository(db),
        EditorialAuthorizationService(EditorialAuthorizationRepository(db)),
    )
