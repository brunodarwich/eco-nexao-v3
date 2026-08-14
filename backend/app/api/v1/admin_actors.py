"""Administrative API router for actor, category and route links (ECO-1603)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.admin_actors import (
    AdminAccessibilityFeatureCreateSchema,
    AdminAccessibilityFeatureEnvelope,
    AdminAccessibilityFeatureListEnvelope,
    AdminAccessibilityFeatureUpdateSchema,
    AdminActorCreateSchema,
    AdminActorEnvelope,
    AdminActorListEnvelope,
    AdminActorUpdateSchema,
    AdminCategoryCreateSchema,
    AdminCategoryEnvelope,
    AdminCategoryListEnvelope,
    AdminCategoryUpdateSchema,
    AdminRouteActorCreateSchema,
    AdminRouteActorEnvelope,
    AdminRouteActorListEnvelope,
    AdminRouteActorUpdateSchema,
)
from app.schemas.error import ErrorResponse
from app.services.actor_admin import ActorAdminService
from app.services.dependencies import get_actor_admin_service
from app.services.editorial_authorization import AuthorizationContext

router = APIRouter(prefix="/admin", tags=["Admin Actors"])

CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
ActorAdminDep = Annotated[ActorAdminService, Depends(get_actor_admin_service)]


def _build_context(user: AuthenticatedUser) -> AuthorizationContext:
    return AuthorizationContext(actor_id=user.id)


# -----------------------------------------------------------------------------
# Admin Categories API
# -----------------------------------------------------------------------------


@router.get(
    "/categories",
    response_model=AdminCategoryListEnvelope,
    summary="Listar categorias administrativas de atores",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
    },
)
async def list_categories(
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminCategoryListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_categories(ctx)


@router.get(
    "/categories/{category_id}",
    response_model=AdminCategoryEnvelope,
    summary="Obter detalhe administrativo de uma categoria",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Categoria não encontrada."},
    },
)
async def get_category(
    category_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminCategoryEnvelope:
    ctx = _build_context(current_user)
    return await service.get_category(ctx, category_id)


@router.post(
    "/categories",
    response_model=AdminCategoryEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar categoria administrativa de atores",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        409: {"model": ErrorResponse, "description": "Slug de categoria já existe."},
    },
)
async def create_category(
    body: AdminCategoryCreateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminCategoryEnvelope:
    ctx = _build_context(current_user)
    return await service.create_category(ctx, body)


@router.patch(
    "/categories/{category_id}",
    response_model=AdminCategoryEnvelope,
    summary="Atualizar categoria administrativa de atores",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Categoria não encontrada."},
    },
)
async def update_category(
    category_id: uuid.UUID,
    body: AdminCategoryUpdateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminCategoryEnvelope:
    ctx = _build_context(current_user)
    return await service.update_category(ctx, category_id, body)


# -----------------------------------------------------------------------------
# Admin Accessibility Features API
# -----------------------------------------------------------------------------


@router.get(
    "/accessibility-features",
    response_model=AdminAccessibilityFeatureListEnvelope,
    summary="Listar funcionalidades de acessibilidade",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
    },
)
async def list_accessibility_features(
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminAccessibilityFeatureListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_accessibility_features(ctx)


@router.get(
    "/accessibility-features/{feature_id}",
    response_model=AdminAccessibilityFeatureEnvelope,
    summary="Obter detalhe de funcionalidade de acessibilidade",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Acessibilidade não encontrada."},
    },
)
async def get_accessibility_feature(
    feature_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminAccessibilityFeatureEnvelope:
    ctx = _build_context(current_user)
    return await service.get_accessibility_feature(ctx, feature_id)


@router.post(
    "/accessibility-features",
    response_model=AdminAccessibilityFeatureEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar funcionalidade de acessibilidade",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        409: {"model": ErrorResponse, "description": "Slug de acessibilidade já existe."},
    },
)
async def create_accessibility_feature(
    body: AdminAccessibilityFeatureCreateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminAccessibilityFeatureEnvelope:
    ctx = _build_context(current_user)
    return await service.create_accessibility_feature(ctx, body)


@router.patch(
    "/accessibility-features/{feature_id}",
    response_model=AdminAccessibilityFeatureEnvelope,
    summary="Atualizar funcionalidade de acessibilidade",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Acessibilidade não encontrada."},
    },
)
async def update_accessibility_feature(
    feature_id: uuid.UUID,
    body: AdminAccessibilityFeatureUpdateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminAccessibilityFeatureEnvelope:
    ctx = _build_context(current_user)
    return await service.update_accessibility_feature(ctx, feature_id, body)


# -----------------------------------------------------------------------------
# Admin Actors API
# -----------------------------------------------------------------------------


@router.get(
    "/actors",
    response_model=AdminActorListEnvelope,
    summary="Listar atores administrativos",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
    },
)
async def list_actors(
    current_user: CurrentUserDep,
    service: ActorAdminDep,
    category_id: Annotated[uuid.UUID | None, Query(description="Filtrar por categoria")] = None,
    include_deleted: Annotated[bool, Query(description="Incluir atores arquivados")] = False,
    q: Annotated[str | None, Query(description="Buscar por nome ou slug")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminActorListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_actors(
        ctx,
        category_id=category_id,
        include_deleted=include_deleted,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/actors/{actor_id}",
    response_model=AdminActorEnvelope,
    summary="Obter detalhe administrativo de um ator",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Ator não encontrado."},
    },
)
async def get_actor(
    actor_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminActorEnvelope:
    ctx = _build_context(current_user)
    return await service.get_actor(ctx, actor_id)


@router.post(
    "/actors",
    response_model=AdminActorEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar ator administrativo",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Categoria vinculada não encontrada."},
        409: {"model": ErrorResponse, "description": "Slug de ator já existe."},
    },
)
async def create_actor(
    body: AdminActorCreateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminActorEnvelope:
    ctx = _build_context(current_user)
    return await service.create_actor(ctx, body)


@router.patch(
    "/actors/{actor_id}",
    response_model=AdminActorEnvelope,
    summary="Atualizar ator administrativo",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Ator ou categoria não encontrada."},
        409: {"model": ErrorResponse, "description": "Conflito de concorrência."},
    },
)
async def update_actor(
    actor_id: uuid.UUID,
    body: AdminActorUpdateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminActorEnvelope:
    ctx = _build_context(current_user)
    return await service.update_actor(ctx, actor_id, body)


@router.delete(
    "/actors/{actor_id}",
    response_model=AdminActorEnvelope,
    summary="Arquivar / soft-delete de ator administrativo",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Ator não encontrado."},
    },
)
async def delete_actor(
    actor_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminActorEnvelope:
    ctx = _build_context(current_user)
    return await service.delete_actor(ctx, actor_id)


# -----------------------------------------------------------------------------
# Admin Route Links API
# -----------------------------------------------------------------------------


@router.get(
    "/actors/{actor_id}/route-links",
    response_model=AdminRouteActorListEnvelope,
    summary="Listar vínculos de rotas de um ator",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Ator não encontrado."},
    },
)
async def list_route_links_by_actor(
    actor_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminRouteActorListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_route_links_by_actor(ctx, actor_id)


@router.post(
    "/actors/{actor_id}/route-links",
    response_model=AdminRouteActorEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar vínculo entre rota e ator",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Ator não encontrado."},
        409: {"model": ErrorResponse, "description": "Ator já vinculado a esta rota."},
        422: {"model": ErrorResponse, "description": "Mismatched actor_id."},
    },
)
async def create_route_link(
    actor_id: uuid.UUID,
    body: AdminRouteActorCreateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminRouteActorEnvelope:
    ctx = _build_context(current_user)
    return await service.create_route_link(ctx, actor_id, body)


@router.patch(
    "/actors/route-links/{link_id}",
    response_model=AdminRouteActorEnvelope,
    summary="Atualizar vínculo entre rota e ator",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Vínculo não encontrado."},
    },
)
async def update_route_link(
    link_id: uuid.UUID,
    body: AdminRouteActorUpdateSchema,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> AdminRouteActorEnvelope:
    ctx = _build_context(current_user)
    return await service.update_route_link(ctx, link_id, body)


@router.delete(
    "/actors/route-links/{link_id}",
    status_code=status.HTTP_200_OK,
    summary="Remover vínculo entre rota e ator",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Vínculo não encontrado."},
    },
)
async def delete_route_link(
    link_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ActorAdminDep,
) -> dict[str, str]:
    ctx = _build_context(current_user)
    await service.delete_route_link(ctx, link_id)
    return {"status": "deleted", "link_id": str(link_id)}
