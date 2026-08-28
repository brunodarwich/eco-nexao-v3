import logging
import uuid
from typing import Any, Literal, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.routing_connector import (
    Coordinate,
    RoutingConnector,
    RoutingProviderUnavailableError,
)
from app.core.config import settings
from app.core.taxonomy import get_canonical_category
from app.repositories.routing import RoutingRepository
from app.repositories.territorial import TerritorialRepository
from app.schemas.envelopes import (
    MapLegendItemSchema,
    MapPinSchema,
    RouteBoundsSchema,
    RoutePreviewDataSchema,
    RoutePreviewEnvelope,
    RoutePreviewRequest,
)

logger = logging.getLogger(__name__)


class DynamicRoutingDisabledError(Exception):
    """Raised when the public feature flag disables dynamic previews."""


class RouteNotFoundError(Exception):
    """Raised when the requested active route does not exist."""


class RouteDestinationMissingError(Exception):
    """Raised when official geometry endpoints do not define one destination."""


class RoutingService:
    def __init__(self, db: AsyncSession, connector: RoutingConnector) -> None:
        self.db = db
        self.connector = connector
        self.routing_repo = RoutingRepository(self.db)
        self.territorial_repo = TerritorialRepository(self.db)

    async def _get_route_anchor_coordinate(self, route_id: uuid.UUID) -> Coordinate | None:
        endpoints = await self.routing_repo.list_official_destination_endpoints(route_id)
        if not endpoints:
            return None
        canonical = {(round(latitude, 6), round(longitude, 6)) for latitude, longitude in endpoints}
        if len(canonical) != 1:
            return None
        latitude, longitude = next(iter(canonical))
        return Coordinate(latitude=latitude, longitude=longitude)

    async def preview_route(
        self,
        route_id: uuid.UUID,
        payload: RoutePreviewRequest,
    ) -> RoutePreviewEnvelope:
        if not settings.ENABLE_DYNAMIC_ROUTING:
            raise DynamicRoutingDisabledError

        region_id = await self.routing_repo.get_active_route_region_id(route_id)
        if region_id is None:
            raise RouteNotFoundError

        destination = await self._get_route_anchor_coordinate(route_id)
        if not destination:
            raise RouteDestinationMissingError

        user_origin = Coordinate(latitude=payload.latitude, longitude=payload.longitude)

        logger.info(
            "Calculating route preview: route_id=%s, travel_mode=%s",
            route_id,
            payload.travel_mode,
        )

        result = await self.connector.calculate_route(
            origin=user_origin,
            destination=destination,
            travel_mode=payload.travel_mode,
        )
        if result.provider not in {"fake_deterministic", "google_routes"}:
            raise RoutingProviderUnavailableError("Provider retornou identificador não aprovado.")
        approved_provider = cast(Literal["fake_deterministic", "google_routes"], result.provider)

        if result.bounds:
            bounds = RouteBoundsSchema(
                min_lat=result.bounds["min_lat"],
                max_lat=result.bounds["max_lat"],
                min_lng=result.bounds["min_lng"],
                max_lng=result.bounds["max_lng"],
            )
        else:
            bounds = RouteBoundsSchema(
                min_lat=min(payload.latitude, destination.latitude),
                max_lat=max(payload.latitude, destination.latitude),
                min_lng=min(payload.longitude, destination.longitude),
                max_lng=max(payload.longitude, destination.longitude),
            )

        # ECO-2312: Corridor actors along dynamic geometry (buffer 1km,
        # strictly filtered by region_id)
        corridor_actors_data = await self.territorial_repo.find_corridor_actors_by_geometry(
            result.geojson,
            region_id=region_id,
            buffer_m=settings.ROUTE_CORRIDOR_BUFFER_METERS,
            limit=settings.STATIC_MAP_MAX_PINS,
        )

        # Essential actors in the route's region (health, security, transport)
        essential_actors_data = await self.territorial_repo.list_region_essential_actors(
            region_id,
            categories=["saude", "seguranca", "transporte"],
            limit=settings.STATIC_MAP_MAX_PINS,
        )

        # Region bounding box
        city_bounds = await self.territorial_repo.get_region_bounds(region_id)

        # Merge actors and assign canonical ADR 0011 spatial scopes.
        combined_actors: dict[uuid.UUID, tuple[Any, str, float | None, float | None, str]] = {}

        for actor, cat_slug, lat, lon in corridor_actors_data:
            layer = str(get_canonical_category(cat_slug)["spatial_scope"])
            combined_actors[actor.id] = (actor, cat_slug, lat, lon, layer)

        for actor, cat_slug, lat, lon in essential_actors_data:
            if actor.id not in combined_actors:
                layer = str(get_canonical_category(cat_slug)["spatial_scope"])
                combined_actors[actor.id] = (actor, cat_slug, lat, lon, layer)

        # Deterministic sorting: is_featured DESC, green_badge_status DESC,
        # sort_order ASC, name ASC, id ASC
        def get_priority_key(
            item: tuple[Any, str, float | None, float | None, str],
        ) -> tuple[int, int, int, str, str]:
            act, _, _, _, _ = item
            is_featured = 1 if getattr(act, "is_featured", False) else 0
            has_badge = getattr(act, "green_badge_status", "none") in ("verified", "provisional")
            green_badge = 1 if has_badge else 0
            sort_order = getattr(act, "sort_order", 0)
            name = getattr(act, "name", "")
            return (-is_featured, -green_badge, sort_order, name, str(act.id))

        sorted_actors = sorted(combined_actors.values(), key=get_priority_key)[
            : settings.STATIC_MAP_MAX_PINS
        ]

        pins: list[MapPinSchema] = []
        category_counts: dict[str, int] = {}

        for actor, cat_slug, lat, lon, layer in sorted_actors:
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
                        layer=layer,  # type: ignore[arg-type]
                    )
                )
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

        preview_data = RoutePreviewDataSchema(
            route_id=route_id,
            route_kind="dynamic_preview",
            is_verified=False,
            provider=approved_provider,
            distance_m=result.distance_m,
            duration_s=result.duration_s,
            geojson=result.geojson,
            encoded_polyline=result.encoded_polyline,
            bounds=bounds,
            pins=pins,
            legend=legend,
            city_bounds=(
                RouteBoundsSchema.model_validate(city_bounds) if city_bounds is not None else None
            ),
        )

        return RoutePreviewEnvelope(data=preview_data)
