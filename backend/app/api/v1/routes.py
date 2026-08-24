"""FastAPI routes for territorial routes, origins, geometry, alerts, actors and maps."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.security import AuthenticatedUser, get_optional_current_user
from app.schemas.envelopes import (
    ActorListEnvelope,
    RouteAlertListEnvelope,
    RouteDetailEnvelope,
    RouteGeometryEnvelope,
    RouteListEnvelope,
    RouteMapPayloadEnvelope,
    RouteOriginListEnvelope,
)
from app.services.dependencies import get_territorial_service
from app.services.territorial import TerritorialService

router = APIRouter(prefix="/routes", tags=["Territorial - Routes"])
TerritorialServiceDep = Annotated[TerritorialService, Depends(get_territorial_service)]
OptionalUserDep = Annotated[AuthenticatedUser | None, Depends(get_optional_current_user)]


@router.get(
    "",
    response_model=RouteListEnvelope,
    summary="Listar rotas",
    description="Retorna lista paginada de rotas turísticas ativas com suporte a busca e filtros.",
)
async def list_routes(
    service: TerritorialServiceDep,
    current_user: OptionalUserDep,
    region_id: Annotated[uuid.UUID | None, Query(description="Filtrar por UUID da região")] = None,
    q: Annotated[str | None, Query(description="Termo de busca por título ou resumo")] = None,
    saved: Annotated[bool | None, Query(description="Filtrar rotas salvas")] = None,
    verified: Annotated[
        bool | None, Query(description="Filtrar rotas verificadas com selo")
    ] = None,
    cursor: Annotated[
        str | None, Query(description="Cursor de paginação (offset numérico)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Quantidade máxima de itens")] = 20,
) -> RouteListEnvelope:
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    if saved and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="É necessário autenticar para consultar rotas salvas.",
        )
    return await service.list_routes(
        region_id=region_id,
        q=q,
        saved=saved,
        user_id=current_user.id if current_user else None,
        verified=verified,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{route_id}",
    response_model=RouteDetailEnvelope,
    summary="Detalhes de uma rota",
    description="Retorna informações completas e origens de uma rota específica.",
)
async def get_route_detail(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
) -> RouteDetailEnvelope:
    detail = await service.get_route_detail(route_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A rota solicitada não foi encontrada.",
        )
    return detail


@router.get(
    "/{route_id}/origins",
    response_model=RouteOriginListEnvelope,
    summary="Origens de uma rota",
    description="Retorna os pontos de partida registrados para a rota especificada.",
)
async def get_route_origins(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
) -> RouteOriginListEnvelope:
    origins = await service.get_route_origins(route_id)
    if not origins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A rota solicitada não foi encontrada.",
        )
    return origins


@router.get(
    "/{route_id}/geometry",
    response_model=RouteGeometryEnvelope,
    summary="Geometria de uma rota por origem",
    description="Retorna a geometria GeoJSON e detalhes da rota a partir de uma origem específica.",
)
async def get_route_geometry(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
    origin_id: Annotated[uuid.UUID, Query(description="UUID da origem de acesso")],
) -> RouteGeometryEnvelope:
    geometry = await service.get_route_geometry(route_id, origin_id=origin_id)
    if not geometry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geometria da rota não encontrada para os parâmetros informados.",
        )
    return geometry


@router.get(
    "/{route_id}/alerts",
    response_model=RouteAlertListEnvelope,
    summary="Alertas ativos de uma rota",
    description="Retorna alertas ativos e informativos associados à rota.",
)
async def get_route_alerts(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
) -> RouteAlertListEnvelope:
    alerts = await service.get_route_alerts(route_id)
    if alerts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A rota solicitada não foi encontrada.",
        )
    return alerts


@router.get(
    "/{route_id}/actors",
    response_model=ActorListEnvelope,
    summary="Atores associados a uma rota",
    description="Retorna lista paginada de estabelecimentos e pontos turísticos associados à rota.",
)
async def get_route_actors(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
    q: Annotated[str | None, Query(description="Termo de busca por nome de ator")] = None,
    category: Annotated[str | None, Query(description="Slug da categoria do ator")] = None,
    origin_id: Annotated[uuid.UUID | None, Query(description="UUID da origem")] = None,
    cursor: Annotated[
        str | None, Query(description="Cursor de paginação (offset numérico)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Quantidade máxima de itens")] = 20,
) -> ActorListEnvelope:
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    actors = await service.list_route_actors(
        route_id=route_id,
        q=q,
        category_slug=category,
        limit=limit,
        offset=offset,
        origin_id=origin_id,
    )
    if actors is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A rota solicitada não foi encontrada.",
        )
    return actors


@router.get(
    "/{route_id}/map",
    response_model=RouteMapPayloadEnvelope,
    summary="Payload otimizado para renderização do mapa",
    description="Retorna bounds, linha de geometria e pins dos atores para a tela de mapa.",
)
async def get_route_map_payload(
    route_id: uuid.UUID,
    service: TerritorialServiceDep,
    response: Response,
    origin_id: Annotated[uuid.UUID | None, Query(description="UUID da origem selecionada")] = None,
) -> RouteMapPayloadEnvelope:
    payload = await service.get_route_map_payload(route_id, origin_id=origin_id)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payload de mapa não encontrado para a rota especificada.",
        )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
    return payload
