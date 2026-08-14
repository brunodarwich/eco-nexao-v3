"""Administrative API router for territorial domain management (ECO-1602)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.admin_territorial import (
    AdminRegionCreateSchema,
    AdminRegionEnvelope,
    AdminRegionListEnvelope,
    AdminRegionUpdateSchema,
    AdminRouteCreateSchema,
    AdminRouteEnvelope,
    AdminRouteGeometryCreateSchema,
    AdminRouteGeometryEnvelope,
    AdminRouteGeometryUpdateSchema,
    AdminRouteListEnvelope,
    AdminRouteOriginCreateSchema,
    AdminRouteOriginEnvelope,
    AdminRouteOriginListEnvelope,
    AdminRouteOriginUpdateSchema,
    AdminRouteUpdateSchema,
)
from app.schemas.error import ErrorResponse
from app.services.dependencies import get_territorial_admin_service
from app.services.editorial_authorization import AuthorizationContext
from app.services.territorial_admin import TerritorialAdminService

router = APIRouter(prefix="/admin/territory", tags=["Admin Territorial"])

CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
TerritorialAdminDep = Annotated[
    TerritorialAdminService, Depends(get_territorial_admin_service)
]


def _build_context(user: AuthenticatedUser) -> AuthorizationContext:
    return AuthorizationContext(actor_id=user.id)


# -----------------------------------------------------------------------------
# Admin Regions API
# -----------------------------------------------------------------------------


@router.get(
    "/regions",
    response_model=AdminRegionListEnvelope,
    summary="Listar regiões administrativas",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
    },
)
async def list_regions(
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
    include_inactive: Annotated[bool, Query(description="Incluir regiões inativas")] = True,
) -> AdminRegionListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_regions(ctx, include_inactive=include_inactive)


@router.get(
    "/regions/{region_id}",
    response_model=AdminRegionEnvelope,
    summary="Obter detalhe administrativo de uma região",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Região não encontrada."},
    },
)
async def get_region(
    region_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRegionEnvelope:
    ctx = _build_context(current_user)
    return await service.get_region(ctx, region_id)


@router.post(
    "/regions",
    response_model=AdminRegionEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar região administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        409: {"model": ErrorResponse, "description": "Slug de região já existe."},
    },
)
async def create_region(
    body: AdminRegionCreateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRegionEnvelope:
    ctx = _build_context(current_user)
    return await service.create_region(ctx, body)


@router.put(
    "/regions/{region_id}",
    response_model=AdminRegionEnvelope,
    summary="Atualizar região administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Região não encontrada."},
    },
)
async def update_region(
    region_id: uuid.UUID,
    body: AdminRegionUpdateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRegionEnvelope:
    ctx = _build_context(current_user)
    return await service.update_region(ctx, region_id, body)


# -----------------------------------------------------------------------------
# Admin Routes API
# -----------------------------------------------------------------------------


@router.get(
    "/routes",
    response_model=AdminRouteListEnvelope,
    summary="Listar rotas administrativas",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
    },
)
async def list_routes(
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
    region_id: Annotated[uuid.UUID | None, Query(description="Filtrar por ID de região")] = None,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filtrar por status")
    ] = None,
    q: Annotated[str | None, Query(description="Busca textual por título ou cidade")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminRouteListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_routes(
        ctx,
        region_id=region_id,
        status_filter=status_filter,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/routes/{route_id}",
    response_model=AdminRouteEnvelope,
    summary="Obter detalhe administrativo de uma rota",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Rota não encontrada."},
    },
)
async def get_route(
    route_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteEnvelope:
    ctx = _build_context(current_user)
    return await service.get_route(ctx, route_id)


@router.post(
    "/routes",
    response_model=AdminRouteEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        409: {"model": ErrorResponse, "description": "Slug de rota já existe."},
    },
)
async def create_route(
    body: AdminRouteCreateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteEnvelope:
    ctx = _build_context(current_user)
    return await service.create_route(ctx, body)


@router.put(
    "/routes/{route_id}",
    response_model=AdminRouteEnvelope,
    summary="Atualizar rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Rota não encontrada."},
        409: {"model": ErrorResponse, "description": "Conflito de concorrência ou slug."},
    },
)
async def update_route(
    route_id: uuid.UUID,
    body: AdminRouteUpdateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteEnvelope:
    ctx = _build_context(current_user)
    return await service.update_route(ctx, route_id, body)


@router.delete(
    "/routes/{route_id}",
    response_model=AdminRouteEnvelope,
    summary="Arquivar rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Rota não encontrada."},
    },
)
async def archive_route(
    route_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteEnvelope:
    ctx = _build_context(current_user)
    return await service.archive_route(ctx, route_id)


# -----------------------------------------------------------------------------
# Admin Route Origins API
# -----------------------------------------------------------------------------


@router.get(
    "/routes/{route_id}/origins",
    response_model=AdminRouteOriginListEnvelope,
    summary="Listar origens de uma rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Rota não encontrada."},
    },
)
async def list_origins(
    route_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteOriginListEnvelope:
    ctx = _build_context(current_user)
    return await service.list_origins(ctx, route_id)


@router.post(
    "/routes/{route_id}/origins",
    response_model=AdminRouteOriginEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar origem de rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Rota não encontrada."},
        409: {"model": ErrorResponse, "description": "Código de origem duplicado para a rota."},
    },
)
async def create_origin(
    route_id: uuid.UUID,
    body: AdminRouteOriginCreateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteOriginEnvelope:
    ctx = _build_context(current_user)
    return await service.create_origin(ctx, route_id, body)


@router.put(
    "/routes/{route_id}/origins/{origin_id}",
    response_model=AdminRouteOriginEnvelope,
    summary="Atualizar origem de rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Origem ou rota não encontrada."},
    },
)
async def update_origin(
    route_id: uuid.UUID,
    origin_id: uuid.UUID,
    body: AdminRouteOriginUpdateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteOriginEnvelope:
    ctx = _build_context(current_user)
    return await service.update_origin(ctx, route_id, origin_id, body)


@router.delete(
    "/routes/{route_id}/origins/{origin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir origem de rota administrativa",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Origem não encontrada."},
    },
)
async def delete_origin(
    route_id: uuid.UUID,
    origin_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> None:
    ctx = _build_context(current_user)
    await service.delete_origin(ctx, route_id, origin_id)


# -----------------------------------------------------------------------------
# Admin Route Geometries API
# -----------------------------------------------------------------------------


@router.post(
    "/routes/{route_id}/origins/{origin_id}/geometries",
    response_model=AdminRouteGeometryEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Criar geometria espacial de rota",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Origem ou rota não encontrada."},
        409: {"model": ErrorResponse, "description": "Geometria já existe para este provedor."},
        422: {"model": ErrorResponse, "description": "Geometria espacial malformada."},
    },
)
async def create_geometry(
    route_id: uuid.UUID,
    origin_id: uuid.UUID,
    body: AdminRouteGeometryCreateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteGeometryEnvelope:
    ctx = _build_context(current_user)
    return await service.create_geometry(ctx, route_id, origin_id, body)


@router.put(
    "/routes/{route_id}/geometries/{geometry_id}",
    response_model=AdminRouteGeometryEnvelope,
    summary="Atualizar geometria espacial de rota",
    responses={
        401: {"model": ErrorResponse, "description": "JWT ausente ou inválido."},
        403: {"model": ErrorResponse, "description": "Permissão negada."},
        404: {"model": ErrorResponse, "description": "Geometria não encontrada."},
    },
)
async def update_geometry(
    route_id: uuid.UUID,
    geometry_id: uuid.UUID,
    body: AdminRouteGeometryUpdateSchema,
    current_user: CurrentUserDep,
    service: TerritorialAdminDep,
) -> AdminRouteGeometryEnvelope:
    ctx = _build_context(current_user)
    return await service.update_geometry(ctx, route_id, geometry_id, body)
