"""Repository layer for user domain data access (ECO-0604, ECO-0605) with AsyncSession."""

import uuid
from typing import Any

from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.domain import (
    Actor,
    ActorCategory,
    FavoriteActor,
    FavoriteRoute,
    Profile,
    Route,
    Trip,
    UserPreference,
)


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_profile(self, user_id: uuid.UUID) -> Profile:
        stmt = select(Profile).where(Profile.id == user_id)
        profile = await self.db.scalar(stmt)
        if not profile:
            profile = Profile(id=user_id, status="active")
            self.db.add(profile)
            try:
                await self.db.commit()
                await self.db.refresh(profile)
            except IntegrityError:
                await self.db.rollback()
                profile = await self.db.scalar(stmt)
                if not profile:
                    raise
        return profile

    async def update_profile(
        self, user_id: uuid.UUID, update_data: dict[str, Any]
    ) -> Profile:
        profile = await self.get_or_create_profile(user_id)
        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_or_create_preferences(self, user_id: uuid.UUID) -> UserPreference:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        pref = await self.db.scalar(stmt)
        if not pref:
            await self.get_or_create_profile(user_id)
            pref = UserPreference(
                id=uuid.uuid4(),
                user_id=user_id,
                screen_reader_mode=False,
                high_contrast=False,
                text_scale=1.0,
                locale="pt-BR",
            )
            self.db.add(pref)
            try:
                await self.db.commit()
                await self.db.refresh(pref)
            except IntegrityError:
                await self.db.rollback()
                pref = await self.db.scalar(stmt)
                if not pref:
                    raise
        return pref


    async def update_preferences(
        self, user_id: uuid.UUID, update_data: dict[str, Any]
    ) -> UserPreference:
        pref = await self.get_or_create_preferences(user_id)
        for key, value in update_data.items():
            if hasattr(pref, key):
                setattr(pref, key, value)
        await self.db.commit()
        await self.db.refresh(pref)
        return pref

    async def get_favorite_routes(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[Route], int]:
        stmt = (
            select(Route)
            .join(
                FavoriteRoute,
                (FavoriteRoute.route_id == Route.id) & (FavoriteRoute.user_id == user_id),
            )
            .where(Route.deleted_at.is_(None), Route.status == "active")
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.scalar(count_stmt)) or 0

        stmt = stmt.order_by(FavoriteRoute.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def add_favorite_route(self, user_id: uuid.UUID, route_id: uuid.UUID) -> bool:
        route_stmt = select(Route).where(Route.id == route_id, Route.deleted_at.is_(None))
        route = await self.db.scalar(route_stmt)
        if not route:
            return False

        fav_stmt = select(FavoriteRoute).where(
            FavoriteRoute.user_id == user_id, FavoriteRoute.route_id == route_id
        )
        fav = await self.db.scalar(fav_stmt)
        if fav:
            return True

        await self.get_or_create_profile(user_id)
        new_fav = FavoriteRoute(user_id=user_id, route_id=route_id)
        self.db.add(new_fav)
        await self.db.commit()
        return True

    async def remove_favorite_route(self, user_id: uuid.UUID, route_id: uuid.UUID) -> bool:
        fav_stmt = select(FavoriteRoute).where(
            FavoriteRoute.user_id == user_id, FavoriteRoute.route_id == route_id
        )
        fav = await self.db.scalar(fav_stmt)
        if fav:
            await self.db.delete(fav)
            await self.db.commit()
        return True

    async def get_favorite_actors(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[tuple[Actor, str, float | None, float | None]], int]:
        stmt = (
            select(
                Actor,
                ActorCategory.slug,
                ST_Y(Actor.location).label("lat"),
                ST_X(Actor.location).label("lon"),
            )
            .join(
                FavoriteActor,
                (FavoriteActor.actor_id == Actor.id) & (FavoriteActor.user_id == user_id),
            )
            .join(ActorCategory, Actor.category_id == ActorCategory.id)
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.scalar(count_stmt)) or 0

        stmt = stmt.order_by(FavoriteActor.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        rows = res.all()
        result: list[tuple[Actor, str, float | None, float | None]] = [
            (
                row[0],
                row[1],
                float(row[2]) if row[2] is not None else None,
                float(row[3]) if row[3] is not None else None,
            )
            for row in rows
        ]
        return result, total

    async def add_favorite_actor(self, user_id: uuid.UUID, actor_id: uuid.UUID) -> bool:
        actor_stmt = select(Actor).where(Actor.id == actor_id)
        actor = await self.db.scalar(actor_stmt)
        if not actor:
            return False

        fav_stmt = select(FavoriteActor).where(
            FavoriteActor.user_id == user_id, FavoriteActor.actor_id == actor_id
        )
        fav = await self.db.scalar(fav_stmt)
        if fav:
            return True

        await self.get_or_create_profile(user_id)
        new_fav = FavoriteActor(user_id=user_id, actor_id=actor_id)
        self.db.add(new_fav)
        await self.db.commit()
        return True

    async def remove_favorite_actor(self, user_id: uuid.UUID, actor_id: uuid.UUID) -> bool:
        fav_stmt = select(FavoriteActor).where(
            FavoriteActor.user_id == user_id, FavoriteActor.actor_id == actor_id
        )
        fav = await self.db.scalar(fav_stmt)
        if fav:
            await self.db.delete(fav)
            await self.db.commit()
        return True

    async def get_trips(self, user_id: uuid.UUID) -> list[Trip]:
        stmt = (
            select(Trip)
            .options(joinedload(Trip.route))
            .where(Trip.user_id == user_id)
            .order_by(Trip.started_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.unique().all())

    async def create_trip(self, user_id: uuid.UUID, route_id: uuid.UUID) -> Trip | None:
        route_stmt = select(Route).where(Route.id == route_id, Route.deleted_at.is_(None))
        route = await self.db.scalar(route_stmt)
        if not route:
            return None

        await self.get_or_create_profile(user_id)

        new_trip = Trip(
            user_id=user_id,
            route_id=route_id,
            status="in_progress",
        )
        self.db.add(new_trip)
        await self.db.commit()
        await self.db.refresh(new_trip)

        stmt = select(Trip).options(joinedload(Trip.route)).where(Trip.id == new_trip.id)
        created = await self.db.scalar(stmt)
        return created or new_trip
