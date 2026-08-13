"""Service layer for territorial domain logic with async DB access (ECO-0501 to ECO-0506)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.territorial import TerritorialRepository
from app.schemas.envelopes import (
    ActorCategoryListEnvelope,
    ActorCategorySchema,
    ActorDetailEnvelope,
    ActorDetailSchema,
    ActorListEnvelope,
    ActorSummarySchema,
    BootstrapDataSchema,
    BootstrapResponseEnvelope,
    MapPinSchema,
    PaginationMeta,
    RegionListEnvelope,
    RegionSchema,
    RouteAlertListEnvelope,
    RouteAlertSchema,
    RouteDetailEnvelope,
    RouteDetailSchema,
    RouteGeometryEnvelope,
    RouteGeometrySchema,
    RouteListEnvelope,
    RouteMapPayloadEnvelope,
    RouteMapPayloadSchema,
    RouteOriginListEnvelope,
    RouteOriginSchema,
    RouteSummarySchema,
)


class TerritorialService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = TerritorialRepository(db)

    # -------------------------------------------------------------------------
    # ECO-0501: Regions & Bootstrap
    # -------------------------------------------------------------------------

    async def get_regions(self) -> RegionListEnvelope:
        regions = await self.repo.get_active_regions()
        return RegionListEnvelope(
            data=[
                RegionSchema(
                    id=r.id,
                    slug=r.slug,
                    name=r.name,
                    state_code=r.state_code,
                    is_active=r.is_active,
                )
                for r in regions
            ]
        )

    async def get_bootstrap(
        self, preferred_region_id: uuid.UUID | None = None
    ) -> BootstrapResponseEnvelope:
        regions = await self.repo.get_active_regions()
        active_region: RegionSchema | None = None

        if preferred_region_id:
            reg = await self.repo.get_region_by_id(preferred_region_id)
            if reg:
                active_region = RegionSchema(
                    id=reg.id,
                    slug=reg.slug,
                    name=reg.name,
                    state_code=reg.state_code,
                    is_active=reg.is_active,
                )

        # Fallback to first active region if invalid or unprovided
        if not active_region and regions:
            first = regions[0]
            active_region = RegionSchema(
                id=first.id,
                slug=first.slug,
                name=first.name,
                state_code=first.state_code,
                is_active=first.is_active,
            )

        supported_regions = [
            RegionSchema(
                id=r.id, slug=r.slug, name=r.name, state_code=r.state_code, is_active=r.is_active
            )
            for r in regions
        ]

        data = BootstrapDataSchema(
            active_region=active_region,
            feature_flags={
                "google_business_profile": False,
                "green_badge_verification": True,
                "anonymous_signin": True,
            },
            supported_regions=supported_regions,
        )
        return BootstrapResponseEnvelope(data=data)

    # -------------------------------------------------------------------------
    # ECO-0502 & ECO-0503: Routes & Details
    # -------------------------------------------------------------------------

    async def list_routes(
        self,
        region_id: uuid.UUID | None = None,
        q: str | None = None,
        saved: bool | None = None,
        user_id: uuid.UUID | None = None,
        verified: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> RouteListEnvelope:
        routes, total = await self.repo.list_routes(
            region_id=region_id,
            q=q,
            saved=saved,
            user_id=user_id,
            verified=verified,
            limit=limit,
            offset=offset,
        )

        summaries = [
            RouteSummarySchema(
                id=r.id,
                slug=r.slug,
                title=r.title,
                summary=r.summary,
                city=r.city,
                state_code=r.state_code,
                status=r.status,
                is_verified=r.is_verified,
                best_season=r.best_season,
            )
            for r in routes
        ]

        next_cursor = str(offset + limit) if (offset + limit) < total else None
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)

        return RouteListEnvelope(data=summaries, meta=meta)

    async def get_route_detail(self, route_id: uuid.UUID) -> RouteDetailEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        origins = [
            RouteOriginSchema(
                id=o.id,
                route_id=o.route_id,
                code=o.code,
                name=o.name,
                description=o.description,
                distance_m=o.distance_m,
                duration_s=o.duration_s,
                sort_order=o.sort_order,
            )
            for o in route.origins
        ]

        detail = RouteDetailSchema(
            id=route.id,
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
            origins=origins,
        )
        return RouteDetailEnvelope(data=detail)

    async def get_route_origins(self, route_id: uuid.UUID) -> RouteOriginListEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        origins = await self.repo.get_route_origins(route_id)
        schemas = [
            RouteOriginSchema(
                id=o.id,
                route_id=o.route_id,
                code=o.code,
                name=o.name,
                description=o.description,
                distance_m=o.distance_m,
                duration_s=o.duration_s,
                sort_order=o.sort_order,
            )
            for o in origins
        ]
        return RouteOriginListEnvelope(data=schemas)

    # -------------------------------------------------------------------------
    # ECO-0504: Route Geometry & Map Payload
    # -------------------------------------------------------------------------

    async def get_route_geometry(
        self, route_id: uuid.UUID, origin_id: uuid.UUID | None = None
    ) -> RouteGeometryEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        geom, geojson_obj = await self.repo.get_route_geometry(route_id, origin_id)
        if not geom:
            return None

        schema = RouteGeometrySchema(
            id=geom.id,
            route_origin_id=geom.route_origin_id,
            provider=geom.provider,
            encoded_polyline=geom.encoded_polyline,
            geojson=geojson_obj,
            distance_m=geom.distance_m,
            duration_s=geom.duration_s,
        )
        return RouteGeometryEnvelope(data=schema)

    async def get_route_map_payload(
        self, route_id: uuid.UUID, origin_id: uuid.UUID | None = None
    ) -> RouteMapPayloadEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        geom, geojson_obj = await self.repo.get_route_geometry(route_id, origin_id)

        geom_schema: RouteGeometrySchema | None = None
        selected_origin_id = origin_id
        if geom:
            geom_schema = RouteGeometrySchema(
                id=geom.id,
                route_origin_id=geom.route_origin_id,
                provider=geom.provider,
                encoded_polyline=geom.encoded_polyline,
                geojson=geojson_obj,
                distance_m=geom.distance_m,
                duration_s=geom.duration_s,
            )
            selected_origin_id = geom.route_origin_id

        # Fetch route actors for map pins
        actors_data, _ = await self.repo.list_route_actors(route_id=route_id, limit=200, offset=0)
        pins: list[MapPinSchema] = []
        lats: list[float] = []
        lons: list[float] = []

        for actor, cat_slug, lat, lon in actors_data:
            if lat is not None and lon is not None:
                pins.append(
                    MapPinSchema(
                        id=actor.id,
                        actor_id=actor.id,
                        name=actor.name,
                        category_slug=cat_slug,
                        latitude=lat,
                        longitude=lon,
                    )
                )
                lats.append(lat)
                lons.append(lon)

        bounds: dict[str, float] | None = None
        if lats and lons:
            bounds = {
                "min_lat": min(lats),
                "max_lat": max(lats),
                "min_lng": min(lons),
                "max_lng": max(lons),
            }

        payload = RouteMapPayloadSchema(
            route_id=route_id,
            selected_origin_id=selected_origin_id,
            bounds=bounds,
            geometry=geom_schema,
            pins=pins,
        )
        return RouteMapPayloadEnvelope(data=payload)

    # -------------------------------------------------------------------------
    # ECO-0505: Route Alerts
    # -------------------------------------------------------------------------

    async def get_route_alerts(self, route_id: uuid.UUID) -> RouteAlertListEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        alerts = await self.repo.get_active_route_alerts(route_id)
        schemas = [
            RouteAlertSchema(
                id=a.id,
                route_id=a.route_id,
                title=a.title,
                message=a.message,
                severity=a.severity,
                starts_at=a.starts_at,
                ends_at=a.ends_at,
                published_at=a.published_at,
                source=a.source,
                is_active=a.is_active,
            )
            for a in alerts
        ]
        return RouteAlertListEnvelope(data=schemas)

    # -------------------------------------------------------------------------
    # ECO-0506: Actors & Categories
    # -------------------------------------------------------------------------

    async def list_actor_categories(self) -> ActorCategoryListEnvelope:
        categories = await self.repo.list_actor_categories()
        schemas = [
            ActorCategorySchema(
                id=c.id,
                slug=c.slug,
                label=c.label,
                icon=c.icon,
                color=c.color,
                sort_order=c.sort_order,
            )
            for c in categories
        ]
        return ActorCategoryListEnvelope(data=schemas)

    async def list_route_actors(
        self,
        route_id: uuid.UUID,
        q: str | None = None,
        category_slug: str | None = None,
        origin_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ActorListEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None

        actors_data, total = await self.repo.list_route_actors(
            route_id=route_id,
            q=q,
            category_slug=category_slug,
            origin_id=origin_id,
            limit=limit,
            offset=offset,
        )

        summaries = [
            ActorSummarySchema(
                id=actor.id,
                slug=actor.slug,
                name=actor.name,
                category_slug=cat_slug,
                category_label=getattr(actor, "_transient_cat_label", cat_slug),
                address=actor.address,
                latitude=lat,
                longitude=lon,
                green_badge_status=actor.green_badge_status,
                verification_status=actor.verification_status,
                google_rating=float(actor.google_rating)
                if actor.google_rating is not None
                else None,
            )
            for actor, cat_slug, lat, lon in actors_data
        ]

        next_cursor = str(offset + limit) if (offset + limit) < total else None
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)

        return ActorListEnvelope(data=summaries, meta=meta)

    async def get_actor_detail(self, actor_id: uuid.UUID) -> ActorDetailEnvelope | None:
        actor, lat, lon, features, google_place_id = await self.repo.get_actor_by_id(actor_id)
        if not actor:
            return None

        category_schema = ActorCategorySchema(
            id=actor.category.id,
            slug=actor.category.slug,
            label=actor.category.label,
            icon=actor.category.icon,
            color=actor.category.color,
            sort_order=actor.category.sort_order,
        )

        detail = ActorDetailSchema(
            id=actor.id,
            slug=actor.slug,
            name=actor.name,
            description=actor.description,
            category=category_schema,
            sub_category=actor.sub_category,
            address=actor.address,
            city=actor.city,
            state_code=actor.state_code,
            latitude=lat,
            longitude=lon,
            phone=actor.phone,
            email=actor.email,
            instagram=actor.instagram,
            website=actor.website,
            opening_hours=actor.opening_hours or {},
            payment_methods=actor.payment_methods or [],
            green_badge_status=actor.green_badge_status,
            verification_status=actor.verification_status,
            google_place_id=google_place_id,
            google_rating=float(actor.google_rating) if actor.google_rating is not None else None,
            google_review_count=actor.google_review_count,
            accessibility_features=features,
        )
        return ActorDetailEnvelope(data=detail)
