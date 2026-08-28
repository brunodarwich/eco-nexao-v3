"""Unit tests for SupabaseAuthAdmin adapter (ECO-1902)."""

import uuid
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.services.supabase_auth_admin import (
    SupabaseAuthAdmin,
    SupabaseAuthAdminError,
)


@pytest.mark.asyncio
async def test_supabase_auth_admin_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", SecretStr(""))
    admin = SupabaseAuthAdmin()
    with pytest.raises(SupabaseAuthAdminError, match="não configurada"):
        await admin.delete_user(uuid.uuid4())


@pytest.mark.asyncio
async def test_supabase_auth_admin_success_and_404_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", SecretStr("test-secret"))
    client = AsyncMock(spec=httpx.AsyncClient)

    # 200 OK
    client.delete.return_value = httpx.Response(
        200, request=httpx.Request("DELETE", "https://test.supabase.co")
    )
    admin = SupabaseAuthAdmin(client=client)
    await admin.delete_user(uuid.uuid4())
    assert client.delete.await_count == 1

    # 404 Not Found (idempotent, no error)
    client.delete.return_value = httpx.Response(
        404, request=httpx.Request("DELETE", "https://test.supabase.co")
    )
    await admin.delete_user(uuid.uuid4())
    assert client.delete.await_count == 2


@pytest.mark.asyncio
async def test_supabase_auth_admin_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", SecretStr("test-secret"))
    client = AsyncMock(spec=httpx.AsyncClient)
    client.delete.side_effect = httpx.ConnectError("fail")
    admin = SupabaseAuthAdmin(client=client)
    with pytest.raises(SupabaseAuthAdminError, match="falhou"):
        await admin.delete_user(uuid.uuid4())
