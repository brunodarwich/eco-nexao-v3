"""Service layer for user domain logic (ECO-0604, ECO-0605)."""

import uuid
from datetime import datetime
from typing import Any, cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.repositories.user_repository import UserRepository
from app.schemas.envelopes import (
    ActorListEnvelope,
    ActorSummarySchema,
    PaginationMeta,
    RouteListEnvelope,
    RouteSummarySchema,
    StandardSuccessResponse,
    TripEnvelope,
    TripListEnvelope,
    TripSchema,
    UserPreferencesEnvelope,
    UserPreferencesSchema,
    UserPreferencesUpdate,
    UserProfileEnvelope,
    UserProfileSchema,
    UserProfileUpdate,
)
from app.services.media_resolution import MediaResolutionService


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)
        self.media = MediaResolutionService(db)

    async def get_profile(self, user_id: uuid.UUID) -> UserProfileEnvelope:
        profile = await self.repo.get_or_create_profile(user_id)
        avatar = (
            await self.media.resolve_asset_by_id(
                profile.avatar_media_id, owner_type="profile", owner_id=user_id
            )
            if profile.avatar_media_id is not None
            else None
        )
        schema = UserProfileSchema(
            id=profile.id,
            name=profile.name,
            location=profile.location,
            avatar_media_id=profile.avatar_media_id,
            avatar=avatar,
            status=profile.status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
        return UserProfileEnvelope(data=schema)

    async def update_profile(
        self, user_id: uuid.UUID, update: UserProfileUpdate
    ) -> UserProfileEnvelope:
        data_dict = update.model_dump(exclude_unset=True)
        profile = await self.repo.update_profile(user_id, data_dict)
        avatar = (
            await self.media.resolve_asset_by_id(
                profile.avatar_media_id, owner_type="profile", owner_id=user_id
            )
            if profile.avatar_media_id is not None
            else None
        )
        schema = UserProfileSchema(
            id=profile.id,
            name=profile.name,
            location=profile.location,
            avatar_media_id=profile.avatar_media_id,
            avatar=avatar,
            status=profile.status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
        return UserProfileEnvelope(data=schema)

    async def get_preferences(self, user_id: uuid.UUID) -> UserPreferencesEnvelope:
        pref = await self.repo.get_or_create_preferences(user_id)
        schema = UserPreferencesSchema(
            id=pref.id,
            user_id=pref.user_id,
            active_region_id=pref.active_region_id,
            screen_reader_mode=pref.screen_reader_mode,
            high_contrast=pref.high_contrast,
            text_scale=float(pref.text_scale) if pref.text_scale is not None else 1.0,
            locale=pref.locale,
            created_at=pref.created_at,
            updated_at=pref.updated_at,
        )
        return UserPreferencesEnvelope(data=schema)

    async def update_preferences(
        self, user_id: uuid.UUID, update: UserPreferencesUpdate
    ) -> UserPreferencesEnvelope:
        data_dict = update.model_dump(exclude_unset=True)
        pref = await self.repo.update_preferences(user_id, data_dict)
        schema = UserPreferencesSchema(
            id=pref.id,
            user_id=pref.user_id,
            active_region_id=pref.active_region_id,
            screen_reader_mode=pref.screen_reader_mode,
            high_contrast=pref.high_contrast,
            text_scale=float(pref.text_scale) if pref.text_scale is not None else 1.0,
            locale=pref.locale,
            created_at=pref.created_at,
            updated_at=pref.updated_at,
        )
        return UserPreferencesEnvelope(data=schema)

    async def get_favorite_routes(
        self, user_id: uuid.UUID, limit: int = 20, cursor: str | None = None
    ) -> RouteListEnvelope:
        decoded = decode_cursor(cursor, "favorite_routes", 2)
        after = None
        if decoded:
            after = (datetime.fromisoformat(str(decoded[0])), uuid.UUID(str(decoded[1])))
        routes, total, has_more = await self.repo.get_favorite_routes(
            user_id, limit=limit, after=after
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
                is_favorite=True,
            )
            for r in routes
        ]
        last = routes[-1] if routes else None
        next_cursor = (
            encode_cursor(
                "favorite_routes",
                [cast(Any, last)._transient_favorite_created_at.isoformat(), str(last.id)],
            )
            if has_more and last
            else None
        )
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)
        return RouteListEnvelope(data=summaries, meta=meta)

    async def add_favorite_route(
        self, user_id: uuid.UUID, route_id: uuid.UUID
    ) -> StandardSuccessResponse:
        success = await self.repo.add_favorite_route(user_id, route_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A rota solicitada não foi encontrada.",
            )
        return StandardSuccessResponse(success=True)

    async def remove_favorite_route(
        self, user_id: uuid.UUID, route_id: uuid.UUID
    ) -> StandardSuccessResponse:
        await self.repo.remove_favorite_route(user_id, route_id)
        return StandardSuccessResponse(success=True)

    async def get_favorite_actors(
        self, user_id: uuid.UUID, limit: int = 20, cursor: str | None = None
    ) -> ActorListEnvelope:
        decoded = decode_cursor(cursor, "favorite_actors", 2)
        after = None
        if decoded:
            after = (datetime.fromisoformat(str(decoded[0])), uuid.UUID(str(decoded[1])))
        actors_data, total, has_more = await self.repo.get_favorite_actors(
            user_id, limit=limit, after=after
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
                is_favorite=True,
            )
            for actor, cat_slug, lat, lon in actors_data
        ]
        last = actors_data[-1][0] if actors_data else None
        next_cursor = (
            encode_cursor(
                "favorite_actors",
                [cast(Any, last)._transient_favorite_created_at.isoformat(), str(last.id)],
            )
            if has_more and last
            else None
        )
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)
        return ActorListEnvelope(data=summaries, meta=meta)

    async def add_favorite_actor(
        self, user_id: uuid.UUID, actor_id: uuid.UUID
    ) -> StandardSuccessResponse:
        success = await self.repo.add_favorite_actor(user_id, actor_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O ator solicitado não foi encontrado.",
            )
        return StandardSuccessResponse(success=True)

    async def remove_favorite_actor(
        self, user_id: uuid.UUID, actor_id: uuid.UUID
    ) -> StandardSuccessResponse:
        await self.repo.remove_favorite_actor(user_id, actor_id)
        return StandardSuccessResponse(success=True)

    async def get_trips(self, user_id: uuid.UUID) -> TripListEnvelope:
        trips = await self.repo.get_trips(user_id)
        data = [
            TripSchema.model_validate({
                "id": str(t.id),
                "user_id": str(t.user_id),
                "route_id": str(t.route_id),
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "route_title": t.route.title if t.route else None,
            })
            for t in trips
        ]
        return TripListEnvelope(data=data)

    async def create_trip(self, user_id: uuid.UUID, route_id: uuid.UUID) -> TripEnvelope:
        trip = await self.repo.create_trip(user_id=user_id, route_id=route_id)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A rota solicitada não foi encontrada.",
            )
        data = {
            "id": str(trip.id),
            "user_id": str(trip.user_id),
            "route_id": str(trip.route_id),
            "started_at": trip.started_at.isoformat() if trip.started_at else None,
            "completed_at": trip.completed_at.isoformat() if trip.completed_at else None,
            "status": trip.status,
            "created_at": trip.created_at.isoformat() if trip.created_at else None,
            "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
            "route_title": trip.route.title if trip.route else None,
        }
        return TripEnvelope(data=TripSchema.model_validate(data))
