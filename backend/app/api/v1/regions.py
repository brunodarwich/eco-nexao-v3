"""FastAPI router for regions and application bootstrap (ECO-0501) with AsyncSession."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.envelopes import BootstrapResponseEnvelope, RegionListEnvelope
from app.services.dependencies import get_territorial_service
from app.services.territorial import TerritorialService

router = APIRouter(tags=["Territorial - Regions"])
TerritorialServiceDep = Annotated[TerritorialService, Depends(get_territorial_service)]
CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]


@router.get(
    "/regions",
    response_model=RegionListEnvelope,
    summary="Lista de regiões ativas",
    description="Retorna todas as regiões turísticas ativas disponíveis na plataforma.",
)
async def list_regions(
    service: TerritorialServiceDep, response: Response
) -> RegionListEnvelope:
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
    return await service.get_regions()


@router.get(
    "/bootstrap",
    response_model=BootstrapResponseEnvelope,
    summary="Bootstrap do aplicativo",
    description=(
        "Retorna informações de inicialização do aplicativo, incluindo região ativa "
        "e feature flags."
    ),
)
async def get_bootstrap(
    service: TerritorialServiceDep,
    _current_user: CurrentUserDep,
    region_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID da região preferida"),
    ] = None,
) -> BootstrapResponseEnvelope:
    return await service.get_bootstrap(preferred_region_id=region_id)
