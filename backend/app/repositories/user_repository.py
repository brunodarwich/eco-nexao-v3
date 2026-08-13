"""Repository layer for user domain data access (ECO-0604, ECO-0605) with AsyncSession."""

import uuid
from typing import Any

from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import func, select
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
    TripActorVisit,
    UserBadge,
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
            await self.db.commit()
            await self.db.refresh(profile)
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
            pref = UserPreference(user_id=user_id)
            self.db.add(pref)
            await self.db.commit()
            await self.db.refresh(pref)
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

    async def get_user_impact(self, user_id: uuid.UUID) -> dict[str, Any]:
        await self.get_or_create_profile(user_id)

        trips_stmt = select(func.count()).select_from(Trip).where(Trip.user_id == user_id)
        total_trips = (await self.db.scalar(trips_stmt)) or 0

        completed_stmt = (
            select(func.count())
            .select_from(Trip)
            .where(Trip.user_id == user_id, Trip.status == "completed")
        )
        completed_trips = (await self.db.scalar(completed_stmt)) or 0

        visits_stmt = (
            select(func.count())
            .select_from(TripActorVisit)
            .join(Trip, TripActorVisit.trip_id == Trip.id)
            .where(Trip.user_id == user_id)
        )
        visited_actors_count = (await self.db.scalar(visits_stmt)) or 0

        badges_stmt = select(UserBadge).where(UserBadge.user_id == user_id)
        badges_res = await self.db.scalars(badges_stmt)
        user_badges = list(badges_res.all())

        badges_list = [
            {
                "id": str(b.id),
                "badge_code": b.badge_code,
                "awarded_at": b.awarded_at.isoformat() if b.awarded_at else None,
                "evidence": b.evidence,
            }
            for b in user_badges
        ]

        sustainable_score = (completed_trips * 50) + (visited_actors_count * 20)
        co2_saved_kg = round(completed_trips * 12.5, 1)

        return {
            "user_id": str(user_id),
            "completed_trips_count": completed_trips,
            "total_trips_count": total_trips,
            "visited_actors_count": visited_actors_count,
            "sustainable_impact_score": sustainable_score,
            "co2_saved_kg": co2_saved_kg,
            "badges": badges_list,
        }

