from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.fake_routing_connector import FakeRoutingConnector
from app.connectors.google_routes_connector import GoogleRoutesConnector
from app.connectors.routing_connector import RoutingConnector
from app.core.config import settings
from app.db.session import get_db
from app.repositories.editorial_authorization import EditorialAuthorizationRepository
from app.services.content_service import ContentService
from app.services.editorial_authorization import EditorialAuthorizationService
from app.services.routing_service import RoutingService
from app.services.storage_service import StorageService
from app.services.territorial import TerritorialService
from app.services.user_service import UserService

if TYPE_CHECKING:
    from app.services.account_lifecycle import AccountLifecycleService
    from app.services.actor_admin import ActorAdminService
    from app.services.avatar_lifecycle import AvatarLifecycleService
    from app.services.media_lifecycle import MediaLifecycleService
    from app.services.territorial_admin import TerritorialAdminService
    from app.services.workflow_admin import WorkflowAdminService

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@lru_cache(maxsize=8)
def _build_routing_connector(
    provider: str,
    app_env: str,
    api_key: str,
    timeout_seconds: float,
    max_retries: int,
    breaker_failures: int,
    breaker_reset_seconds: int,
    monthly_limit: int,
    monthly_alert_at: int,
) -> RoutingConnector:
    if provider == "fake_deterministic":
        if app_env not in {"development", "test"}:
            raise RuntimeError("FakeRoutingConnector não é permitido neste ambiente.")
        return FakeRoutingConnector()
    if provider == "google_routes":
        return GoogleRoutesConnector(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            circuit_breaker_failures=breaker_failures,
            circuit_breaker_reset_seconds=breaker_reset_seconds,
            monthly_limit=monthly_limit,
            monthly_alert_at=monthly_alert_at,
        )
    raise RuntimeError("Provedor de roteamento configurado não está implementado.")


def get_routing_connector() -> RoutingConnector:
    """Return the process-wide connector so breaker, pool, cache and metrics are shared."""
    return _build_routing_connector(
        settings.ROUTING_PROVIDER,
        settings.APP_ENV,
        settings.GOOGLE_ROUTES_API_KEY.get_secret_value(),
        settings.GOOGLE_ROUTES_TIMEOUT_SECONDS,
        settings.GOOGLE_ROUTES_MAX_RETRIES,
        settings.ROUTING_CIRCUIT_BREAKER_FAILURES,
        settings.ROUTING_CIRCUIT_BREAKER_RESET_SECONDS,
        settings.GOOGLE_ROUTES_MONTHLY_LIMIT,
        settings.GOOGLE_ROUTES_MONTHLY_ALERT_AT,
    )


def get_territorial_service(db: DatabaseSession) -> TerritorialService:
    """Build the territorial service for one request."""
    return TerritorialService(db)


def get_routing_service(
    db: DatabaseSession,
    connector: Annotated[RoutingConnector, Depends(get_routing_connector)],
) -> RoutingService:
    """Build the routing preview service using configured routing connector."""
    return RoutingService(db, connector)


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


def get_avatar_lifecycle_service(db: DatabaseSession) -> "AvatarLifecycleService":
    """Build the trusted server-side avatar lifecycle for one request."""
    from app.core.config import settings
    from app.repositories.avatar_lifecycle import AvatarLifecycleRepository
    from app.services.avatar_lifecycle import AvatarLifecycleService

    return AvatarLifecycleService(
        AvatarLifecycleRepository(db), public_base_url=settings.SUPABASE_URL
    )


def get_account_lifecycle_service(db: DatabaseSession) -> "AccountLifecycleService":
    """Build the idempotent private account-deletion lifecycle."""
    from app.repositories.account_lifecycle import AccountLifecycleRepository
    from app.services.account_lifecycle import AccountLifecycleService

    return AccountLifecycleService(AccountLifecycleRepository(db))
