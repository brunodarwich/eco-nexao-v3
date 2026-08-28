"""Minimal server-only Supabase Auth Admin adapter."""

from __future__ import annotations

import uuid

import httpx

from app.core.config import settings


class SupabaseAuthAdminError(RuntimeError):
    """Safe Auth Admin failure without response bodies or credentials."""


class SupabaseAuthAdmin:
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _headers(self) -> dict[str, str]:
        secret = settings.SUPABASE_SECRET_KEY.get_secret_value()
        if not secret:
            raise SupabaseAuthAdminError("Credencial segura do Auth Admin não configurada.")
        return {"Authorization": f"Bearer {secret}", "apikey": secret}

    async def delete_user(self, user_id: uuid.UUID) -> None:
        url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{user_id}"
        try:
            if self._client is not None:
                response = await self._client.delete(url, headers=self._headers())
            else:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.delete(url, headers=self._headers())
            if response.status_code == 404:
                return
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise SupabaseAuthAdminError("Exclusão da identidade no Auth falhou.") from exc
