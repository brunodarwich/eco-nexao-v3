"""FastAPI router for actor categories and actor details (ECO-0506) with AsyncSession."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.security import AuthenticatedUser, get_optional_current_user
from app.schemas.envelopes import (
    ActorCategoryListEnvelope,
    ActorDetailEnvelope,
    GooglePhotoAttributionSchema,
    GooglePhotoMetadataEnvelope,
    GooglePhotoMetadataSchema,
)
from app.schemas.error import ErrorResponse
from app.services.actor_google_photo import (
    ActorGooglePhotoService,
    ActorGooglePhotoUnavailable,
    ActorGooglePhotoUpstreamUnavailable,
)
from app.services.dependencies import get_actor_google_photo_service, get_territorial_service
from app.services.territorial import TerritorialService

router = APIRouter(tags=["Territorial - Actors"])
TerritorialServiceDep = Annotated[TerritorialService, Depends(get_territorial_service)]
OptionalUserDep = Annotated[AuthenticatedUser | None, Depends(get_optional_current_user)]
ActorGooglePhotoDep = Annotated[ActorGooglePhotoService, Depends(get_actor_google_photo_service)]


@router.get(
    "/actors/{actor_id}/google-photo",
    response_model=GooglePhotoMetadataEnvelope,
    summary="Foto Google temporária do ator",
    description="Emite um grant opaco a partir de Place Details recente; não expõe URLs Google.",
    responses={
        404: {"model": ErrorResponse, "description": "Foto indisponível."},
        503: {"model": ErrorResponse, "description": "Foto temporariamente indisponível."},
    },
)
async def get_actor_google_photo(
    actor_id: uuid.UUID, service: ActorGooglePhotoDep
) -> GooglePhotoMetadataEnvelope:
    try:
        grant = await service.issue(actor_id)
    except ActorGooglePhotoUpstreamUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Foto temporariamente indisponível.",
        ) from exc
    except ActorGooglePhotoUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Foto indisponível."
        ) from exc
    return GooglePhotoMetadataEnvelope(
        data=GooglePhotoMetadataSchema(
            proxy_url=f"/api/v1/places/photos/{grant.token}",
            expires_at=grant.expires_at,
            width_px=grant.width_px,
            height_px=grant.height_px,
            author_attributions=[
                GooglePhotoAttributionSchema(**item) for item in grant.attributions
            ],
            google_maps_uri=grant.google_maps_uri,
        )
    )


@router.get(
    "/actor-categories",
    response_model=ActorCategoryListEnvelope,
    summary="Categorias de atores",
    description="Retorna a taxonomia oficial de categorias de estabelecimentos e atrações.",
)
async def list_actor_categories(
    service: TerritorialServiceDep, response: Response
) -> ActorCategoryListEnvelope:
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
    return await service.list_actor_categories()


@router.get(
    "/actors/{actor_id}",
    response_model=ActorDetailEnvelope,
    summary="Detalhes de um ator",
    description="Retorna informações completas de um ator ou estabelecimento específico.",
    responses={404: {"model": ErrorResponse, "description": "Ator não encontrado."}},
)
async def get_actor_detail(
    actor_id: uuid.UUID,
    service: TerritorialServiceDep,
    current_user: OptionalUserDep,
) -> ActorDetailEnvelope:
    detail = await service.get_actor_detail(
        actor_id, user_id=current_user.id if current_user else None
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O ator solicitado não foi encontrado.",
        )
    return detail
