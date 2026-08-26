"""Health check router providing /health/live and /health/ready endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.db.session import check_database_readiness
from app.schemas.error import ErrorResponse
from app.schemas.health import HealthDatabaseStatus, HealthStatus

router = APIRouter(prefix="/health", tags=["Health"])


def _get_commit_sha() -> str | None:
    return settings.GIT_COMMIT_SHA or settings.RENDER_GIT_COMMIT


@router.get(
    "",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Health check raiz",
    description="Retorna status HTTP 200 se o serviço estiver respondendo.",
    operation_id="healthRoot",
    include_in_schema=False,
)
@router.get(
    "/live",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Retorna status HTTP 200 se o processo FastAPI estiver executando.",
    operation_id="healthLive",
)
async def health_live() -> HealthStatus:
    """Liveness check endpoint."""
    return HealthStatus(
        status="ok",
        timestamp=datetime.now(UTC),
        version=settings.APP_VERSION,
        commit_sha=_get_commit_sha(),
    )


@router.get(
    "/ready",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description=(
        "Retorna status HTTP 200 se dependências de banco de dados e Supabase estiverem prontas."
    ),
    operation_id="healthReady",
    responses={
        200: {"model": HealthStatus, "description": "Dependências operacionais."},
        503: {"model": ErrorResponse, "description": "Dependência indisponível."},
    },
)
async def health_ready(
    database_ready: Annotated[bool, Depends(check_database_readiness)],
) -> HealthStatus:
    """Readiness check endpoint."""
    if not database_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependências operacionais indisponíveis.",
        )
    return HealthStatus(
        status="ok",
        timestamp=datetime.now(UTC),
        version=settings.APP_VERSION,
        commit_sha=_get_commit_sha(),
        database=HealthDatabaseStatus(status="ok", postgis=True),
    )
