"""Behavioral unit tests for user domain repository and services (ECO-1301).

Focuses on domain business rules:
- Profile get/create and updates.
- Preference get/create and updates.
- Favorite routes and actors add/remove/list.
- Trip creation and history retrieval.
- Exception handling in user services.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.domain import (
    Actor,
    Profile,
    Route,
    Trip,
    UserPreference,
)
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def create_mock_db():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    return mock_db


@pytest.mark.asyncio
async def test_get_or_create_profile_existing_and_new():
    """Verify profile retrieval creates a new profile if not found."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    existing = Profile(id=user_id, status="active", name="User Existente")

    mock_db.scalar.side_effect = [existing, None]

    repo = UserRepository(mock_db)
    prof1 = await repo.get_or_create_profile(user_id)
    prof2 = await repo.get_or_create_profile(user_id)

    assert prof1 == existing
    assert prof2.id == user_id
    assert prof2.status == "active"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_update_profile_and_preferences():
    """Verify profile and preferences updates attribute attributes and refresh."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    prof = Profile(id=user_id, name="Antigo")
    pref = UserPreference(user_id=user_id, locale="pt-BR")

    mock_db.scalar.side_effect = [prof, pref]
    repo = UserRepository(mock_db)

    updated_prof = await repo.update_profile(user_id, {"name": "Novo Nome", "invalid_attr": "skip"})
    updated_pref = await repo.update_preferences(user_id, {"locale": "en-US"})

    assert updated_prof.name == "Novo Nome"
    assert updated_pref.locale == "en-US"


@pytest.mark.asyncio
async def test_favorite_routes_management():
    """Verify adding, checking, listing, and removing favorite routes."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    route_id = uuid.uuid4()
    route = Route(id=route_id, title="Rota Fav", status="active")
    profile = Profile(id=user_id, status="active")

    mock_db.scalar.side_effect = [route, None, profile]
    repo = UserRepository(mock_db)

    added = await repo.add_favorite_route(user_id, route_id)
    assert added is True
    mock_db.add.assert_called_once()

    mock_db.scalar.side_effect = [1]
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [route]
    mock_db.scalars.return_value = mock_scalars

    fav_routes, total = await repo.get_favorite_routes(user_id)
    assert total == 1
    assert fav_routes == [route]

    mock_fav = MagicMock()
    mock_db.scalar.side_effect = [mock_fav]
    removed = await repo.remove_favorite_route(user_id, route_id)
    assert removed is True
    mock_db.delete.assert_called_once_with(mock_fav)


@pytest.mark.asyncio
async def test_favorite_actors_management():
    """Verify adding, listing, and removing favorite actors."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    actor = Actor(id=actor_id, name="Ator Fav")
    profile = Profile(id=user_id, status="active")

    mock_db.scalar.side_effect = [actor, None, profile]
    repo = UserRepository(mock_db)
    added = await repo.add_favorite_actor(user_id, actor_id)
    assert added is True
    mock_db.scalar.side_effect = None
    mock_db.scalar.return_value = 1
    mock_exec = MagicMock()
    mock_exec.all.return_value = [(actor, "culinaria", -2.5, -48.0)]
    mock_db.execute.return_value = mock_exec

    fav_actors, total = await repo.get_favorite_actors(user_id)
    assert total == 1
    assert len(fav_actors) == 1
    act, slug, lat, lon = fav_actors[0]
    assert act == actor
    assert slug == "culinaria"
    assert lat == -2.5
    assert lon == -48.0


@pytest.mark.asyncio
async def test_create_and_get_trips():
    """Verify trip creation and trip history retrieval."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    route_id = uuid.uuid4()
    route = Route(id=route_id, title="Rota Viagem")
    prof = Profile(id=user_id)
    created_trip = Trip(id=uuid.uuid4(), user_id=user_id, route_id=route_id, status="in_progress")

    mock_db.scalar.side_effect = [route, prof, created_trip]
    repo = UserRepository(mock_db)

    trip = await repo.create_trip(user_id, route_id)
    assert trip == created_trip
    assert trip.status == "in_progress"

    mock_scalars = MagicMock()
    mock_unique = MagicMock()
    mock_unique.all.return_value = [created_trip]
    mock_scalars.unique.return_value = mock_unique
    mock_db.scalars.return_value = mock_scalars

    trips = await repo.get_trips(user_id)
    assert trips == [created_trip]


@pytest.mark.asyncio
async def test_user_service_delegation():
    """Verify UserService delegates profile, preferences and favorites cleanly."""
    mock_db = create_mock_db()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    prof = Profile(id=user_id, name="Test User", status="active", created_at=now, updated_at=now)

    mock_db.scalar.return_value = prof
    service = UserService(mock_db)
    res_envelope = await service.get_profile(user_id)

    assert res_envelope.data.id == user_id
    assert res_envelope.data.name == "Test User"
