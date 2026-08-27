"""Integration and behavior tests for user preferences referential integrity (ECO-1903, ECO-1902).

Validates:
1. Fresh authenticated/anonymous users without prior profile records can fetch and update
   preferences without foreign key constraint violations (HTTP 500).
2. Concurrency handling on get_or_create_profile and get_or_create_preferences when
   IntegrityError occurs under race conditions.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.api.v1.auth import AuthUser, get_current_user
from app.db.session import get_db
from app.main import app
from app.models.domain import Profile, UserPreference
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_get_or_create_preferences_auto_provisions_profile():
    """Verify that get_or_create_preferences creates a profile first if none exists."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    user_id = uuid.uuid4()

    # 1st scalar: check UserPreference -> None
    # 2nd scalar: check Profile in get_or_create_profile -> None (fresh user)
    mock_db.scalar.side_effect = [None, None]

    repo = UserRepository(mock_db)
    pref = await repo.get_or_create_preferences(user_id)

    assert pref.user_id == user_id
    assert pref.screen_reader_mode is False
    assert pref.high_contrast is False
    assert pref.text_scale == 1.0
    assert pref.locale == "pt-BR"

    # mock_db.add should have been called twice: 1 for Profile, 1 for UserPreference
    assert mock_db.add.call_count == 2
    added_objects = [call[0][0] for call in mock_db.add.call_args_list]
    assert any(isinstance(obj, Profile) and obj.id == user_id for obj in added_objects)
    assert any(isinstance(obj, UserPreference) and obj.user_id == user_id for obj in added_objects)
    assert mock_db.commit.call_count == 2


@pytest.mark.asyncio
async def test_get_or_create_preferences_with_existing_profile():
    """Verify that get_or_create_preferences does not re-create an existing profile."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    user_id = uuid.uuid4()
    existing_profile = Profile(id=user_id, status="active")

    # 1st scalar: check UserPreference -> None
    # 2nd scalar: check Profile in get_or_create_profile -> existing_profile
    mock_db.scalar.side_effect = [None, existing_profile]

    repo = UserRepository(mock_db)
    pref = await repo.get_or_create_preferences(user_id)

    assert pref.user_id == user_id
    # Only UserPreference was added to session
    assert mock_db.add.call_count == 1
    added_obj = mock_db.add.call_args[0][0]
    assert isinstance(added_obj, UserPreference)
    assert added_obj.user_id == user_id


@pytest.mark.asyncio
async def test_concurrent_profile_creation_recovers_via_rollback_and_select():
    """Simulate concurrent profile insertion race condition: commit fails with IntegrityError,
    recovers via re-query.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_id = uuid.uuid4()

    concurrent_profile = Profile(id=user_id, status="active", name="Criado Concorrentemente")
    # 1st scalar (initial check): None
    # 2nd scalar (re-query after IntegrityError rollback): concurrent_profile
    mock_db.scalar.side_effect = [None, concurrent_profile]
    mock_db.commit.side_effect = [IntegrityError("duplicate key", None, None)]

    repo = UserRepository(mock_db)
    profile = await repo.get_or_create_profile(user_id)

    assert profile == concurrent_profile
    mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_profile_creation_propagates_exception_if_record_absent():
    """Verify that if rollback occurs and re-select fails to find the record,
    IntegrityError is re-raised.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_id = uuid.uuid4()

    # 1st scalar: None, 2nd scalar after rollback: None (anomalous failure)
    mock_db.scalar.side_effect = [None, None]
    mock_db.commit.side_effect = [IntegrityError("foreign key or disk error", None, None)]

    repo = UserRepository(mock_db)
    with pytest.raises(IntegrityError):
        await repo.get_or_create_profile(user_id)

    mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_preferences_creation_recovers_via_rollback_and_select():
    """Simulate concurrent user_preferences insertion race condition: commit fails with
    IntegrityError, recovers via re-query.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_id = uuid.uuid4()

    existing_profile = Profile(id=user_id, status="active")
    concurrent_pref = UserPreference(id=uuid.uuid4(), user_id=user_id, high_contrast=True)

    # 1st scalar (check pref): None
    # 2nd scalar (check profile in get_or_create_profile): existing_profile
    # 3rd scalar (re-query pref after IntegrityError rollback): concurrent_pref
    mock_db.scalar.side_effect = [None, existing_profile, concurrent_pref]
    mock_db.commit.side_effect = [
        IntegrityError("duplicate key user_preferences_user_id_key", None, None)
    ]

    repo = UserRepository(mock_db)
    pref = await repo.get_or_create_preferences(user_id)

    assert pref == concurrent_pref
    mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_preferences_creation_propagates_exception_if_record_absent():
    """Verify that if preferences rollback occurs and re-select returns None,
    IntegrityError is re-raised.
    """
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_id = uuid.uuid4()

    existing_profile = Profile(id=user_id, status="active")
    # 1st scalar: None (pref check), 2nd scalar: existing_profile, 3rd scalar (after rollback): None
    mock_db.scalar.side_effect = [None, existing_profile, None]
    mock_db.commit.side_effect = [IntegrityError("anomaly", None, None)]

    repo = UserRepository(mock_db)
    with pytest.raises(IntegrityError):
        await repo.get_or_create_preferences(user_id)

    mock_db.rollback.assert_called_once()


def test_api_get_my_preferences_anonymous_user_returns_200():
    """Verify GET /api/v1/me/preferences returns 200 with envelope for anonymous guest."""
    user_id = uuid.uuid4()
    guest_user = AuthUser(
        id=user_id,
        email=None,
        is_anonymous=True,
        role="authenticated",
        claims={"sub": str(user_id), "role": "authenticated", "is_anonymous": True},
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    pref = UserPreference(
        id=uuid.uuid4(),
        user_id=user_id,
        active_region_id=None,
        screen_reader_mode=False,
        high_contrast=False,
        text_scale=1.0,
        locale="pt-BR",
    )
    mock_db.scalar.side_effect = [pref]

    app.dependency_overrides[get_current_user] = lambda: guest_user
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        client = TestClient(app)
        response = client.get("/api/v1/me/preferences")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["user_id"] == str(user_id)
        assert data["screen_reader_mode"] is False
        assert data["high_contrast"] is False
        assert data["text_scale"] == 1.0
        assert data["locale"] == "pt-BR"
        assert "X-Request-ID" in response.headers
    finally:
        app.dependency_overrides.clear()
