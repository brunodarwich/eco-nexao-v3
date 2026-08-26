"""Unit tests for RoutingRepository (ECO-2314)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.routing import RoutingRepository


@pytest.mark.asyncio
async def test_routing_repo_get_active_route_region_id() -> None:
    db = AsyncMock()
    repo = RoutingRepository(db)

    region_id = uuid.uuid4()
    db.scalar.return_value = region_id

    route_id = uuid.uuid4()
    result = await repo.get_active_route_region_id(route_id)
    assert result == region_id
    assert db.scalar.called


@pytest.mark.asyncio
async def test_routing_repo_list_official_destination_endpoints() -> None:
    db = AsyncMock()
    repo = RoutingRepository(db)

    mock_result = MagicMock()
    mock_result.all.return_value = [
        (-2.558521, -54.978506),
        (None, -54.97),
        (-2.558521, None),
    ]
    db.execute.return_value = mock_result

    route_id = uuid.uuid4()
    endpoints = await repo.list_official_destination_endpoints(route_id)
    assert len(endpoints) == 1
    assert endpoints[0] == (-2.558521, -54.978506)
