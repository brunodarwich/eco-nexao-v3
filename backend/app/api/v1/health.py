"""Health check router providing /health/live and /health/ready endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import check_database_readiness
from app.schemas.error import ErrorResponse
from app.schemas.health import HealthStatus

router = APIRouter(prefix="/health", tags=["Health"])


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
    return HealthStatus(status="ok", timestamp=datetime.now(UTC))


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
    return HealthStatus(status="ok", timestamp=datetime.now(UTC))
