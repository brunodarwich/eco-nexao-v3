"""FastAPI router for actor categories and actor details (ECO-0506) with AsyncSession."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.envelopes import ActorCategoryListEnvelope, ActorDetailEnvelope
from app.services.dependencies import get_territorial_service
from app.services.territorial import TerritorialService

router = APIRouter(tags=["Territorial - Actors"])
TerritorialServiceDep = Annotated[TerritorialService, Depends(get_territorial_service)]


@router.get(
    "/actor-categories",
    response_model=ActorCategoryListEnvelope,
    summary="Categorias de atores",
    description="Retorna a taxonomia oficial de categorias de estabelecimentos e atrações.",
)
async def list_actor_categories(service: TerritorialServiceDep) -> ActorCategoryListEnvelope:
    return await service.list_actor_categories()


@router.get(
    "/actors/{actor_id}",
    response_model=ActorDetailEnvelope,
    summary="Detalhes de um ator",
    description="Retorna informações completas de um ator ou estabelecimento específico.",
)
async def get_actor_detail(
    actor_id: uuid.UUID,
    service: TerritorialServiceDep,
) -> ActorDetailEnvelope:
    detail = await service.get_actor_detail(actor_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O ator solicitado não foi encontrado.",
        )
    return detail
