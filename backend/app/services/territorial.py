"""Service layer for territorial domain logic with async DB access (ECO-0501 to ECO-0506)."""

import time
import uuid
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.taxonomy import get_canonical_category
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
    MapLegendItemSchema,
    MapPinSchema,
    PaginationMeta,
    RegionListEnvelope,
    RegionSchema,
    RouteAlertListEnvelope,
    RouteAlertSchema,
    RouteBoundsSchema,
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
from app.services.media_resolution import MediaResolutionService

# In-memory simple cache dictionaries with TTL
_REGIONS_CACHE: dict[str, Any] = {"data": None, "expires_at": 0.0}
_CATEGORIES_CACHE: dict[str, Any] = {"data": None, "expires_at": 0.0}


class TerritorialService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = TerritorialRepository(db)
        self.media_resolver = MediaResolutionService(db)

    # -------------------------------------------------------------------------
    # ECO-0501: Regions & Bootstrap
    # -------------------------------------------------------------------------

    async def get_regions(self) -> RegionListEnvelope:
        now = time.monotonic()
        if _REGIONS_CACHE["data"] is not None and _REGIONS_CACHE["expires_at"] > now:
            return cast(RegionListEnvelope, _REGIONS_CACHE["data"])

        regions = await self.repo.get_active_regions()
        result = RegionListEnvelope(
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
        _REGIONS_CACHE["data"] = result
        _REGIONS_CACHE["expires_at"] = now + 300.0
        return result

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
                "dynamic_routing": settings.ENABLE_DYNAMIC_ROUTING,
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

        route_ids = [r.id for r in routes]
        covers = await self.media_resolver.batch_resolve_covers_for_owners("route", route_ids)

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
                cover_image_url=covers[r.id].url if r.id in covers else None,
                cover_media=covers.get(r.id),
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

        cover_item, gallery_items = await self.media_resolver.resolve_media_for_owner(
            "route", route.id
        )

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
            cover_image_url=cover_item.url if cover_item else None,
            cover_media=cover_item,
            gallery=gallery_items,
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
        self,
        route_id: uuid.UUID,
        origin_id: uuid.UUID | None = None,
        layer: str | None = None,
        category: str | None = None,
        simplify_tolerance: float | None = 0.0001,
    ) -> RouteMapPayloadEnvelope | None:
        route = await self.repo.get_route_by_id(route_id)
        if not route:
            return None
        if origin_id is not None and not await self.repo.origin_belongs_to_route(
            route_id, origin_id
        ):
            return None

        geom, geojson_obj = await self.repo.get_route_geometry(
            route_id, origin_id, simplify_tolerance=simplify_tolerance
        )

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
        elif selected_origin_id is None and route.origins:
            # Fallback to first origin if geometry is missing
            selected_origin_id = route.origins[0].id

        corridor_actors_data: list[tuple[Any, str, float | None, float | None, bool, int]] = []
        if geojson_obj is not None and layer in (None, "route_corridor", "both"):
            corridor_actors_data = await self.repo.find_route_corridor_actors(
                geojson_geom=geojson_obj,
                region_id=route.region_id,
                route_id=route_id,
                origin_id=selected_origin_id,
                category_slug=category,
                buffer_m=settings.ROUTE_CORRIDOR_BUFFER_METERS,
                limit=settings.STATIC_MAP_MAX_PINS,
            )

        # Fetch region essential actors (saude, seguranca, transporte)
        essential_actors_data: list[tuple[Any, str, float | None, float | None]] = []
        if layer in (None, "citywide_essential", "both"):
            essential_categories = ["saude", "seguranca", "transporte"]
            if category:
                essential_categories = [category]
            essential_actors_data = await self.repo.list_region_essential_actors(
                region_id=route.region_id,
                categories=essential_categories,
                limit=settings.STATIC_MAP_MAX_PINS,
            )

        # Merge actors and determine layer
        combined_actors: dict[
            uuid.UUID, tuple[Any, str, float | None, float | None, str, bool, int]
        ] = {}

        for actor, cat_slug, lat, lon, is_featured, sort_order in corridor_actors_data:
            actor_layer = str(get_canonical_category(cat_slug)["spatial_scope"])
            if layer is None or layer == actor_layer:
                combined_actors[actor.id] = (
                    actor, cat_slug, lat, lon, actor_layer, is_featured, sort_order
                )

        for actor, cat_slug, lat, lon in essential_actors_data:
            actor_layer = str(get_canonical_category(cat_slug)["spatial_scope"])
            if actor.id not in combined_actors and (layer is None or layer == actor_layer):
                combined_actors[actor.id] = (actor, cat_slug, lat, lon, actor_layer, False, 0)

        # Deterministic sorting: is_featured DESC, green_badge_status DESC, sort_order ASC, name ASC
        def get_priority_key(
            item: tuple[Any, str, float | None, float | None, str, bool, int],
        ) -> tuple[int, int, int, str, str]:
            act, _, _, _, _, route_is_featured, route_sort_order = item
            is_featured = 1 if route_is_featured else 0
            has_badge = getattr(act, "green_badge_status", "none") in ("verified", "provisional")
            green_badge = 1 if has_badge else 0
            name = getattr(act, "name", "")
            return (-is_featured, -green_badge, route_sort_order, name, str(act.id))

        sorted_actors = sorted(combined_actors.values(), key=get_priority_key)[
            : settings.STATIC_MAP_MAX_PINS
        ]

        pins: list[MapPinSchema] = []
        corridor_lats: list[float] = []
        corridor_lons: list[float] = []
        category_counts: dict[str, int] = {}

        for actor, cat_slug, lat, lon, actor_layer, _, _ in sorted_actors:
            if lat is not None and lon is not None:
                canonical_cat = get_canonical_category(cat_slug)
                canonical_slug = canonical_cat["slug"]
                pins.append(
                    MapPinSchema(
                        id=actor.id,
                        actor_id=actor.id,
                        name=actor.name,
                        category_slug=canonical_slug,
                        category_label=canonical_cat["label"],
                        color=canonical_cat["color"],
                        icon=canonical_cat["icon"],
                        latitude=lat,
                        longitude=lon,
                        layer=actor_layer,  # type: ignore[arg-type]
                    )
                )
                if actor_layer in ("route_corridor", "both"):
                    corridor_lats.append(lat)
                    corridor_lons.append(lon)
                category_counts[canonical_slug] = category_counts.get(canonical_slug, 0) + 1

        legend: list[MapLegendItemSchema] = []
        for cat_slug, count in category_counts.items():
            cat_meta = get_canonical_category(cat_slug)
            legend.append(
                MapLegendItemSchema(
                    category_slug=cat_slug,
                    label=cat_meta["label"],
                    color=cat_meta["color"],
                    icon=cat_meta["icon"],
                    count=count,
                    sort_order=cat_meta["sort_order"],
                )
            )
        legend.sort(key=lambda item: (item.sort_order, item.label))

        # route_bounds strictly derived from geometry or corridor pins
        bounds: dict[str, float] | None = None
        if geojson_obj is not None:
            bounds = await self.repo.get_buffered_route_bounds(
                geojson_obj, settings.ROUTE_CORRIDOR_BUFFER_METERS
            )
        elif geom and geom.bounds:
            raw_bounds = geom.bounds
            min_lng = raw_bounds.get("min_lng", raw_bounds.get("min_lon"))
            max_lng = raw_bounds.get("max_lng", raw_bounds.get("max_lon"))
            if min_lng is None or max_lng is None:
                raise ValueError("Route geometry bounds are missing longitude limits")
            bounds = {
                "min_lat": raw_bounds["min_lat"],
                "max_lat": raw_bounds["max_lat"],
                "min_lng": min_lng,
                "max_lng": max_lng,
            }
        elif corridor_lats and corridor_lons:
            bounds = {
                "min_lat": min(corridor_lats),
                "max_lat": max(corridor_lats),
                "min_lng": min(corridor_lons),
                "max_lng": max(corridor_lons),
            }

        # city_bounds derived from region
        city_bounds = await self.repo.get_region_bounds(route.region_id)

        payload = RouteMapPayloadSchema(
            route_id=route_id,
            selected_origin_id=selected_origin_id,
            bounds=RouteBoundsSchema.model_validate(bounds) if bounds is not None else None,
            city_bounds=(
                RouteBoundsSchema.model_validate(city_bounds) if city_bounds is not None else None
            ),
            geometry=geom_schema,
            pins=pins,
            legend=legend,
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
        now = time.monotonic()
        if _CATEGORIES_CACHE["data"] is not None and _CATEGORIES_CACHE["expires_at"] > now:
            return cast(ActorCategoryListEnvelope, _CATEGORIES_CACHE["data"])

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
        result = ActorCategoryListEnvelope(data=schemas)
        _CATEGORIES_CACHE["data"] = result
        _CATEGORIES_CACHE["expires_at"] = now + 300.0
        return result

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

        actor_ids = [actor.id for actor, _, _, _ in actors_data]
        covers = await self.media_resolver.batch_resolve_covers_for_owners("actor", actor_ids)

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
                cover_image_url=covers[actor.id].url if actor.id in covers else None,
                cover_media=covers.get(actor.id),
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

        cover_item, gallery_items = await self.media_resolver.resolve_media_for_owner(
            "actor", actor.id
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
            cover_image_url=cover_item.url if cover_item else None,
            cover_media=cover_item,
            gallery=gallery_items,
            accessibility_features=features,
        )
        return ActorDetailEnvelope(data=detail)
