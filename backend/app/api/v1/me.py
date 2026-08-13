"""FastAPI router for user profile, preferences, and favorites (/me)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.auth import AuthUser, get_current_user
from app.schemas.envelopes import (
    ActorListEnvelope,
    AvatarUploadRequest,
    AvatarUploadResponseData,
    AvatarUploadResponseEnvelope,
    RouteListEnvelope,
    StandardSuccessResponse,
    TripCreate,
    TripEnvelope,
    TripListEnvelope,
    UserImpactEnvelope,
    UserPreferencesEnvelope,
    UserPreferencesUpdate,
    UserProfileEnvelope,
    UserProfileUpdate,
)
from app.services.dependencies import get_storage_service, get_user_service
from app.services.storage_service import StorageService
from app.services.user_service import UserService

router = APIRouter(prefix="/me", tags=["User - Profile & Preferences"])
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]



@router.get(
    "",
    response_model=UserProfileEnvelope,
    summary="Perfil do usuário atual",
    description="Retorna os dados do perfil do usuário autenticado.",
)
async def get_my_profile(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> UserProfileEnvelope:
    return await service.get_profile(user_id=current_user.id)


@router.patch(
    "",
    response_model=UserProfileEnvelope,
    summary="Atualizar perfil do usuário atual",
    description="Atualiza campos do perfil do usuário autenticado.",
)
async def update_my_profile(
    update: UserProfileUpdate,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> UserProfileEnvelope:
    return await service.update_profile(user_id=current_user.id, update=update)


@router.post(
    "/avatar-upload",
    response_model=AvatarUploadResponseEnvelope,
    summary="Solicitacao de URL para upload de avatar",
    description="Gera URL assinada para upload seguro de avatar no Supabase Storage.",
)
async def create_avatar_upload_url(
    request: AvatarUploadRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    storage_service: StorageServiceDep,
) -> AvatarUploadResponseEnvelope:
    data = await storage_service.create_avatar_upload_url(
        user_id=current_user.id,
        filename=request.filename,
        mime_type=request.mime_type,
    )
    return AvatarUploadResponseEnvelope(data=AvatarUploadResponseData(**data))



@router.get(
    "/preferences",
    response_model=UserPreferencesEnvelope,
    summary="Preferências do usuário atual",
    description="Retorna as preferências de acessibilidade, região e navegação do usuário.",
)
async def get_my_preferences(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> UserPreferencesEnvelope:
    return await service.get_preferences(user_id=current_user.id)


@router.patch(
    "/preferences",
    response_model=UserPreferencesEnvelope,
    summary="Atualizar preferências do usuário atual",
    description="Atualiza preferências de acessibilidade e região ativa do usuário.",
)
async def update_my_preferences(
    update: UserPreferencesUpdate,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> UserPreferencesEnvelope:
    return await service.update_preferences(user_id=current_user.id, update=update)


@router.get(
    "/favorite-routes",
    response_model=RouteListEnvelope,
    summary="Rotas salvas pelo usuário atual",
    description="Retorna a lista paginada de rotas favoritadas pelo usuário autenticado.",
)
async def get_my_favorite_routes(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> RouteListEnvelope:
    return await service.get_favorite_routes(user_id=current_user.id)


@router.put(
    "/favorite-routes/{route_id}",
    response_model=StandardSuccessResponse,
    summary="Salvar rota como favorita (Idempotente)",
    description="Adiciona a rota aos favoritos do usuário de forma idempotente.",
)
async def add_favorite_route(
    route_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> StandardSuccessResponse:
    return await service.add_favorite_route(user_id=current_user.id, route_id=route_id)


@router.delete(
    "/favorite-routes/{route_id}",
    response_model=StandardSuccessResponse,
    summary="Remover rota dos favoritos (Idempotente)",
    description="Remove a rota dos favoritos do usuário de forma idempotente.",
)
async def remove_favorite_route(
    route_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> StandardSuccessResponse:
    return await service.remove_favorite_route(user_id=current_user.id, route_id=route_id)


@router.get(
    "/favorite-actors",
    response_model=ActorListEnvelope,
    summary="Atores salvos pelo usuário atual",
    description="Retorna a lista paginada de atores favoritados pelo usuário autenticado.",
)
async def get_my_favorite_actors(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> ActorListEnvelope:
    return await service.get_favorite_actors(user_id=current_user.id)


@router.put(
    "/favorite-actors/{actor_id}",
    response_model=StandardSuccessResponse,
    summary="Salvar ator como favorito (Idempotente)",
    description="Adiciona o ator aos favoritos do usuário de forma idempotente.",
)
async def add_favorite_actor(
    actor_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> StandardSuccessResponse:
    return await service.add_favorite_actor(user_id=current_user.id, actor_id=actor_id)


@router.delete(
    "/favorite-actors/{actor_id}",
    response_model=StandardSuccessResponse,
    summary="Remover ator dos favoritos (Idempotente)",
    description="Remove o ator dos favoritos do usuário de forma idempotente.",
)
async def remove_favorite_actor(
    actor_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> StandardSuccessResponse:
    return await service.remove_favorite_actor(user_id=current_user.id, actor_id=actor_id)


@router.get(
    "/trips",
    response_model=TripListEnvelope,
    summary="Histórico de viagens do usuário",
    description="Retorna o histórico de viagens iniciadas e concluídas pelo usuário autenticado.",
)
async def get_my_trips(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> TripListEnvelope:
    return await service.get_trips(user_id=current_user.id)


@router.post(
    "/trips",
    response_model=TripEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar nova viagem",
    description="Cria um novo registro de viagem para o usuário autenticado na rota informada.",
)
async def create_trip(
    trip_data: TripCreate,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> TripEnvelope:
    return await service.create_trip(user_id=current_user.id, route_id=trip_data.route_id)


@router.get(
    "/impact",
    response_model=UserImpactEnvelope,
    summary="Métricas de impacto e selos do usuário",
    description="Retorna os indicadores de impacto ecológico e selos conquistados pelo usuário.",
)
async def get_my_impact(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: UserServiceDep,
) -> UserImpactEnvelope:
    return await service.get_impact(user_id=current_user.id)

