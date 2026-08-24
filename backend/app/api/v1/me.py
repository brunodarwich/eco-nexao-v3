"""FastAPI router for user profile, preferences, and favorites (/me)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.auth import AuthUser, get_current_user, get_current_user_allow_deleted
from app.schemas.envelopes import (
    ActorListEnvelope,
    AvatarUploadResponseData,
    AvatarUploadResponseEnvelope,
    RouteListEnvelope,
    StandardSuccessData,
    StandardSuccessResponse,
    TripCreate,
    TripEnvelope,
    TripListEnvelope,
    UserPreferencesEnvelope,
    UserPreferencesUpdate,
    UserProfileEnvelope,
    UserProfileUpdate,
)
from app.schemas.error import ErrorResponse
from app.services.account_lifecycle import AccountDeletionError, AccountLifecycleService
from app.services.avatar_lifecycle import AvatarLifecycleError, AvatarLifecycleService
from app.services.dependencies import (
    get_account_lifecycle_service,
    get_avatar_lifecycle_service,
    get_user_service,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/me", tags=["User - Profile & Preferences"])
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AvatarLifecycleDep = Annotated[AvatarLifecycleService, Depends(get_avatar_lifecycle_service)]
AccountLifecycleDep = Annotated[AccountLifecycleService, Depends(get_account_lifecycle_service)]



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
    "/avatar",
    response_model=AvatarUploadResponseEnvelope,
    summary="Substituir avatar",
    description=(
        "Recebe uma imagem multipart, sanitiza e gera derivados WebP no backend, "
        "publicando-os no Supabase Storage sem expor credenciais privilegiadas."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": "JWT ausente, inválido ou bloqueado por exclusão de conta.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Imagem ausente, inválida, incompatível ou acima do limite.",
        },
    },
)
async def replace_avatar(
    file: Annotated[UploadFile, File(description="Imagem JPEG, PNG ou WebP; máximo 5 MiB")],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    service: AvatarLifecycleDep,
) -> AvatarUploadResponseEnvelope:
    try:
        content = await file.read(5 * 1024 * 1024 + 1)
        result = await service.replace_avatar(
            user_id=current_user.id,
            content=content,
            declared_mime=file.content_type,
        )
    except AvatarLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    finally:
        await file.close()
    return AvatarUploadResponseEnvelope(
        data=AvatarUploadResponseData(
            media_asset_id=result.media_asset_id,
            url=result.public_url,
            derivatives=result.derivatives,
            alt_text=result.alt_text,
        )
    )


@router.delete(
    "/account",
    response_model=StandardSuccessResponse,
    summary="Excluir a conta atual",
    description=(
        "Remove avatares, dados de domínio e identidade Auth. É idempotente enquanto "
        "o JWT residual ainda for válido."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        503: {
            "model": ErrorResponse,
            "description": "Saga de exclusão incompleta e segura para nova tentativa.",
        },
    },
)
async def delete_my_account(
    current_user: Annotated[AuthUser, Depends(get_current_user_allow_deleted)],
    service: AccountLifecycleDep,
) -> StandardSuccessResponse:
    try:
        await service.delete_account(current_user.id)
    except AccountDeletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return StandardSuccessResponse(
        data=StandardSuccessData(
            success=True, message="Conta excluída permanentemente."
        )
    )



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
