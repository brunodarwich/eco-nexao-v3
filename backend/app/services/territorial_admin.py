"""Service layer for administrative territorial domain CRUD (ECO-1602)."""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.editorial_authorization import EditorialAuthorizationRepository
from app.repositories.territorial_admin import TerritorialAdminRepository
from app.schemas.admin_territorial import (
    AdminRegionCreateSchema,
    AdminRegionEnvelope,
    AdminRegionListEnvelope,
    AdminRegionSchema,
    AdminRegionUpdateSchema,
    AdminRouteCreateSchema,
    AdminRouteEnvelope,
    AdminRouteGeometryCreateSchema,
    AdminRouteGeometryEnvelope,
    AdminRouteGeometrySchema,
    AdminRouteGeometryUpdateSchema,
    AdminRouteListEnvelope,
    AdminRouteOriginCreateSchema,
    AdminRouteOriginEnvelope,
    AdminRouteOriginListEnvelope,
    AdminRouteOriginSchema,
    AdminRouteOriginUpdateSchema,
    AdminRouteSchema,
    AdminRouteUpdateSchema,
)
from app.schemas.envelopes import PaginationMeta
from app.services.editorial_authorization import (
    AuthorizationContext,
    EditorialAuthorizationService,
)


class TerritorialAdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TerritorialAdminRepository(db)
        self.auth_repo = EditorialAuthorizationRepository(db)
        self.auth_service = EditorialAuthorizationService(self.auth_repo)

    # -------------------------------------------------------------------------
    # Region Admin Operations
    # -------------------------------------------------------------------------

    async def list_regions(
        self, context: AuthorizationContext, include_inactive: bool = True
    ) -> AdminRegionListEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        regions = await self.repo.list_regions(include_inactive=include_inactive)

        schemas = []
        for r in regions:
            lat, lon = await self.repo.get_region_coordinates(r)
            schemas.append(
                AdminRegionSchema(
                    id=r.id,
                    slug=r.slug,
                    name=r.name,
                    state_code=r.state_code,
                    latitude=lat,
                    longitude=lon,
                    is_active=r.is_active,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )
        return AdminRegionListEnvelope(data=schemas)

    async def get_region(
        self, context: AuthorizationContext, region_id: uuid.UUID
    ) -> AdminRegionEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        region = await self.repo.get_region_by_id(region_id)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Região com ID {region_id} não foi encontrada.",
            )

        lat, lon = await self.repo.get_region_coordinates(region)
        return AdminRegionEnvelope(
            data=AdminRegionSchema(
                id=region.id,
                slug=region.slug,
                name=region.name,
                state_code=region.state_code,
                latitude=lat,
                longitude=lon,
                is_active=region.is_active,
                created_at=region.created_at,
                updated_at=region.updated_at,
            )
        )

    async def create_region(
        self, context: AuthorizationContext, body: AdminRegionCreateSchema
    ) -> AdminRegionEnvelope:
        await self.auth_service.require_capability(context, "territory.write")

        existing = await self.repo.get_region_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma região com o slug '{body.slug}'.",
            )

        region = await self.repo.create_region(
            slug=body.slug,
            name=body.name,
            state_code=body.state_code,
            latitude=body.latitude,
            longitude=body.longitude,
            is_active=body.is_active,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="region",
            resource_id=region.id,
            changes={
                "slug": region.slug,
                "name": region.name,
                "state_code": region.state_code,
                "is_active": region.is_active,
            },
        )

        lat, lon = await self.repo.get_region_coordinates(region)
        return AdminRegionEnvelope(
            data=AdminRegionSchema(
                id=region.id,
                slug=region.slug,
                name=region.name,
                state_code=region.state_code,
                latitude=lat,
                longitude=lon,
                is_active=region.is_active,
                created_at=region.created_at,
                updated_at=region.updated_at,
            )
        )

    async def update_region(
        self,
        context: AuthorizationContext,
        region_id: uuid.UUID,
        body: AdminRegionUpdateSchema,
    ) -> AdminRegionEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        region = await self.repo.get_region_by_id(region_id)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Região com ID {region_id} não foi encontrada.",
            )

        updated = await self.repo.update_region(
            region_id=region_id,
            name=body.name,
            state_code=body.state_code,
            latitude=body.latitude,
            longitude=body.longitude,
            is_active=body.is_active,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Região com ID {region_id} não foi encontrada.",
            )

        changes: dict[str, Any] = {}
        if body.name is not None:
            changes["name"] = body.name
        if body.state_code is not None:
            changes["state_code"] = body.state_code
        if body.is_active is not None:
            changes["is_active"] = body.is_active

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="region",
            resource_id=region_id,
            changes=changes,
        )

        lat, lon = await self.repo.get_region_coordinates(updated)
        return AdminRegionEnvelope(
            data=AdminRegionSchema(
                id=updated.id,
                slug=updated.slug,
                name=updated.name,
                state_code=updated.state_code,
                latitude=lat,
                longitude=lon,
                is_active=updated.is_active,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    # -------------------------------------------------------------------------
    # Route Admin Operations
    # -------------------------------------------------------------------------

    async def list_routes(
        self,
        context: AuthorizationContext,
        region_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminRouteListEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        routes, total = await self.repo.list_routes(
            region_id=region_id,
            status=status_filter,
            q=q,
            limit=limit,
            offset=offset,
        )

        schemas = [
            AdminRouteSchema(
                id=r.id,
                region_id=r.region_id,
                slug=r.slug,
                title=r.title,
                summary=r.summary,
                city=r.city,
                state_code=r.state_code,
                status=r.status,
                is_verified=r.is_verified,
                verified_at=r.verified_at,
                best_season=r.best_season,
                connectivity=r.connectivity,
                road_access=r.road_access,
                payment_info=r.payment_info,
                cover_media_id=r.cover_media_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in routes
        ]

        next_cursor = str(offset + limit) if (offset + limit) < total else None
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)
        return AdminRouteListEnvelope(data=schemas, meta=meta)

    async def get_route(
        self, context: AuthorizationContext, route_id: uuid.UUID
    ) -> AdminRouteEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        return AdminRouteEnvelope(
            data=AdminRouteSchema(
                id=route.id,
                region_id=route.region_id,
                slug=route.slug,
                title=route.title,
                summary=route.summary,
                city=route.city,
                state_code=route.state_code,
                status=route.status,
                is_verified=route.is_verified,
                verified_at=route.verified_at,
                best_season=route.best_season,
                connectivity=route.connectivity,
                road_access=route.road_access,
                payment_info=route.payment_info,
                cover_media_id=route.cover_media_id,
                created_at=route.created_at,
                updated_at=route.updated_at,
            )
        )

    async def create_route(
        self, context: AuthorizationContext, body: AdminRouteCreateSchema
    ) -> AdminRouteEnvelope:
        await self.auth_service.require_capability(context, "territory.write")

        # Check region exists
        region = await self.repo.get_region_by_id(body.region_id)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Região vinculada (ID: {body.region_id}) não foi encontrada.",
            )

        # Check slug conflict
        existing = await self.repo.get_route_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma rota com o slug '{body.slug}'.",
            )

        # If user wants to set status="published", check capability "content.publish"
        if body.status in ("published", "active"):
            await self.auth_service.require_capability(context, "content.publish")

        route = await self.repo.create_route(
            region_id=body.region_id,
            slug=body.slug,
            title=body.title,
            summary=body.summary,
            city=body.city,
            state_code=body.state_code,
            status=body.status,
            is_verified=body.is_verified,
            best_season=body.best_season,
            connectivity=body.connectivity,
            road_access=body.road_access,
            payment_info=body.payment_info,
            cover_media_id=body.cover_media_id,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="route",
            resource_id=route.id,
            changes={
                "slug": route.slug,
                "title": route.title,
                "region_id": str(route.region_id),
                "status": route.status,
            },
        )

        return AdminRouteEnvelope(
            data=AdminRouteSchema(
                id=route.id,
                region_id=route.region_id,
                slug=route.slug,
                title=route.title,
                summary=route.summary,
                city=route.city,
                state_code=route.state_code,
                status=route.status,
                is_verified=route.is_verified,
                verified_at=route.verified_at,
                best_season=route.best_season,
                connectivity=route.connectivity,
                road_access=route.road_access,
                payment_info=route.payment_info,
                cover_media_id=route.cover_media_id,
                created_at=route.created_at,
                updated_at=route.updated_at,
            )
        )

    async def update_route(
        self,
        context: AuthorizationContext,
        route_id: uuid.UUID,
        body: AdminRouteUpdateSchema,
    ) -> AdminRouteEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        # Optimistic concurrency check if expected_version is provided
        if body.expected_version:
            current_version = route.updated_at.isoformat()
            if body.expected_version != current_version:
                msg = (
                    "A rota foi alterada por outro usuário. "
                    "Por favor recarregue antes de salvar."
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=msg,
                )

        if body.status in ("published", "active") and route.status not in ("published", "active"):
            await self.auth_service.require_capability(context, "content.publish")

        updated = await self.repo.update_route(
            route_id=route_id,
            region_id=body.region_id,
            title=body.title,
            summary=body.summary,
            city=body.city,
            state_code=body.state_code,
            status=body.status,
            is_verified=body.is_verified,
            best_season=body.best_season,
            connectivity=body.connectivity,
            road_access=body.road_access,
            payment_info=body.payment_info,
            cover_media_id=body.cover_media_id,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        changes: dict[str, Any] = {}
        if body.title is not None:
            changes["title"] = body.title
        if body.status is not None:
            changes["status"] = body.status

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="route",
            resource_id=route_id,
            changes=changes,
        )

        return AdminRouteEnvelope(
            data=AdminRouteSchema(
                id=updated.id,
                region_id=updated.region_id,
                slug=updated.slug,
                title=updated.title,
                summary=updated.summary,
                city=updated.city,
                state_code=updated.state_code,
                status=updated.status,
                is_verified=updated.is_verified,
                verified_at=updated.verified_at,
                best_season=updated.best_season,
                connectivity=updated.connectivity,
                road_access=updated.road_access,
                payment_info=updated.payment_info,
                cover_media_id=updated.cover_media_id,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    async def archive_route(
        self, context: AuthorizationContext, route_id: uuid.UUID
    ) -> AdminRouteEnvelope:
        await self.auth_service.require_capability(context, "content.archive")
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        archived = await self.repo.archive_route(route_id)
        if not archived:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="archive",
            resource_type="route",
            resource_id=route_id,
            changes={"status": "archived"},
        )

        return AdminRouteEnvelope(
            data=AdminRouteSchema(
                id=archived.id,
                region_id=archived.region_id,
                slug=archived.slug,
                title=archived.title,
                summary=archived.summary,
                city=archived.city,
                state_code=archived.state_code,
                status=archived.status,
                is_verified=archived.is_verified,
                verified_at=archived.verified_at,
                best_season=archived.best_season,
                connectivity=archived.connectivity,
                road_access=archived.road_access,
                payment_info=archived.payment_info,
                cover_media_id=archived.cover_media_id,
                created_at=archived.created_at,
                updated_at=archived.updated_at,
            )
        )

    # -------------------------------------------------------------------------
    # Route Origin Admin Operations
    # -------------------------------------------------------------------------

    async def list_origins(
        self, context: AuthorizationContext, route_id: uuid.UUID
    ) -> AdminRouteOriginListEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        origins = await self.repo.list_origins_by_route(route_id)
        schemas = []
        for o in origins:
            lat, lon = await self.repo.get_origin_coordinates(o)
            schemas.append(
                AdminRouteOriginSchema(
                    id=o.id,
                    route_id=o.route_id,
                    code=o.code,
                    name=o.name,
                    description=o.description,
                    latitude=lat,
                    longitude=lon,
                    distance_m=o.distance_m,
                    duration_s=o.duration_s,
                    sort_order=o.sort_order,
                    created_at=o.created_at,
                    updated_at=o.updated_at,
                )
            )
        return AdminRouteOriginListEnvelope(data=schemas)

    async def create_origin(
        self,
        context: AuthorizationContext,
        route_id: uuid.UUID,
        body: AdminRouteOriginCreateSchema,
    ) -> AdminRouteOriginEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rota com ID {route_id} não foi encontrada.",
            )

        existing = await self.repo.get_origin_by_code(route_id, body.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma origem com o código '{body.code}' nesta rota.",
            )

        origin = await self.repo.create_origin(
            route_id=route_id,
            code=body.code,
            name=body.name,
            latitude=body.latitude,
            longitude=body.longitude,
            description=body.description,
            distance_m=body.distance_m,
            duration_s=body.duration_s,
            sort_order=body.sort_order,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="route_origin",
            resource_id=origin.id,
            changes={"route_id": str(route_id), "code": origin.code, "name": origin.name},
        )

        lat, lon = await self.repo.get_origin_coordinates(origin)
        return AdminRouteOriginEnvelope(
            data=AdminRouteOriginSchema(
                id=origin.id,
                route_id=origin.route_id,
                code=origin.code,
                name=origin.name,
                description=origin.description,
                latitude=lat,
                longitude=lon,
                distance_m=origin.distance_m,
                duration_s=origin.duration_s,
                sort_order=origin.sort_order,
                created_at=origin.created_at,
                updated_at=origin.updated_at,
            )
        )

    async def update_origin(
        self,
        context: AuthorizationContext,
        route_id: uuid.UUID,
        origin_id: uuid.UUID,
        body: AdminRouteOriginUpdateSchema,
    ) -> AdminRouteOriginEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        origin = await self.repo.get_origin_by_id(origin_id)
        if not origin or origin.route_id != route_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origem com ID {origin_id} não foi encontrada para a rota informada.",
            )

        updated = await self.repo.update_origin(
            origin_id=origin_id,
            name=body.name,
            description=body.description,
            latitude=body.latitude,
            longitude=body.longitude,
            distance_m=body.distance_m,
            duration_s=body.duration_s,
            sort_order=body.sort_order,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origem com ID {origin_id} não foi encontrada.",
            )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="route_origin",
            resource_id=origin_id,
            changes={"name": body.name, "sort_order": body.sort_order},
        )

        lat, lon = await self.repo.get_origin_coordinates(updated)
        return AdminRouteOriginEnvelope(
            data=AdminRouteOriginSchema(
                id=updated.id,
                route_id=updated.route_id,
                code=updated.code,
                name=updated.name,
                description=updated.description,
                latitude=lat,
                longitude=lon,
                distance_m=updated.distance_m,
                duration_s=updated.duration_s,
                sort_order=updated.sort_order,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    async def delete_origin(
        self, context: AuthorizationContext, route_id: uuid.UUID, origin_id: uuid.UUID
    ) -> None:
        await self.auth_service.require_capability(context, "territory.write")
        origin = await self.repo.get_origin_by_id(origin_id)
        if not origin or origin.route_id != route_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origem com ID {origin_id} não foi encontrada.",
            )

        await self.repo.delete_origin(origin_id)
        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="delete",
            resource_type="route_origin",
            resource_id=origin_id,
            changes={"route_id": str(route_id)},
        )

    # -------------------------------------------------------------------------
    # Route Geometry Admin Operations
    # -------------------------------------------------------------------------

    async def create_geometry(
        self,
        context: AuthorizationContext,
        route_id: uuid.UUID,
        origin_id: uuid.UUID,
        body: AdminRouteGeometryCreateSchema,
    ) -> AdminRouteGeometryEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        origin = await self.repo.get_origin_by_id(origin_id)
        if not origin or origin.route_id != route_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origem com ID {origin_id} não pertence à rota informada.",
            )

        # Validate coordinates length
        if len(body.coordinates) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A geometria LineString exige pelo menos 2 pontos de coordenadas.",
            )

        # Check existing provider geometry
        existing = await self.repo.get_geometry_by_origin(origin_id, provider=body.provider)
        if existing:
            msg = (
                f"Já existe uma geometria gravada para o provedor '{body.provider}' "
                "nesta origem."
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=msg,
            )

        geom = await self.repo.create_geometry(
            route_origin_id=origin_id,
            coordinates=body.coordinates,
            provider=body.provider,
            encoded_polyline=body.encoded_polyline,
            distance_m=body.distance_m,
            duration_s=body.duration_s,
            bounds=body.bounds,
            source_hash=body.source_hash,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="route_geometry",
            resource_id=geom.id,
            changes={"route_origin_id": str(origin_id), "provider": body.provider},
        )

        geojson_obj = await self.repo.get_geometry_geojson(geom)
        return AdminRouteGeometryEnvelope(
            data=AdminRouteGeometrySchema(
                id=geom.id,
                route_origin_id=geom.route_origin_id,
                provider=geom.provider,
                encoded_polyline=geom.encoded_polyline,
                geojson=geojson_obj,
                distance_m=geom.distance_m,
                duration_s=geom.duration_s,
                bounds=geom.bounds,
                source_hash=geom.source_hash,
                created_at=geom.created_at,
                updated_at=geom.updated_at,
            )
        )

    async def update_geometry(
        self,
        context: AuthorizationContext,
        route_id: uuid.UUID,
        geometry_id: uuid.UUID,
        body: AdminRouteGeometryUpdateSchema,
    ) -> AdminRouteGeometryEnvelope:
        await self.auth_service.require_capability(context, "territory.write")
        geom = await self.repo.get_geometry_by_id(geometry_id)
        if not geom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Geometria com ID {geometry_id} não foi encontrada.",
            )

        updated = await self.repo.update_geometry(
            geometry_id=geometry_id,
            coordinates=body.coordinates,
            encoded_polyline=body.encoded_polyline,
            distance_m=body.distance_m,
            duration_s=body.duration_s,
            bounds=body.bounds,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Geometria com ID {geometry_id} não foi encontrada.",
            )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="route_geometry",
            resource_id=geometry_id,
            changes={"geometry_id": str(geometry_id)},
        )

        geojson_obj = await self.repo.get_geometry_geojson(updated)
        return AdminRouteGeometryEnvelope(
            data=AdminRouteGeometrySchema(
                id=updated.id,
                route_origin_id=updated.route_origin_id,
                provider=updated.provider,
                encoded_polyline=updated.encoded_polyline,
                geojson=geojson_obj,
                distance_m=updated.distance_m,
                duration_s=updated.duration_s,
                bounds=updated.bounds,
                source_hash=updated.source_hash,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )
