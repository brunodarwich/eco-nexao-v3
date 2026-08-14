"""Trusted Supabase Storage adapter for user avatar derivatives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings


class AvatarStorageError(RuntimeError):
    """Safe Storage failure that never includes credentials or response bodies."""


class SupabaseAvatarStorage:
    bucket = "avatars"

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _headers(self) -> dict[str, str]:
        secret = settings.SUPABASE_SECRET_KEY.get_secret_value()
        if not secret:
            raise AvatarStorageError("Credencial segura do Storage não configurada.")
        return {"Authorization": f"Bearer {secret}", "apikey": secret}

    async def upload(self, path: str, content: bytes) -> None:
        encoded_path = quote(path.lstrip("/"), safe="/")
        url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}/{encoded_path}"
        headers = {**self._headers(), "Content-Type": "image/webp", "x-upsert": "false"}
        await self._request("POST", url, headers=headers, content=content)

    async def remove(self, paths: Sequence[str]) -> None:
        prefixes = [self._without_bucket(path) for path in paths if path]
        if not prefixes:
            return
        url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}"
        await self._request(
            "DELETE", url, headers=self._headers(), json_body={"prefixes": prefixes}
        )

    async def list_user_paths(self, user_id: str) -> list[str]:
        url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/list/{self.bucket}"
        offset = 0
        paths: list[str] = []
        while True:
            payload = {
                "prefix": user_id,
                "limit": 100,
                "offset": offset,
                "sortBy": {"column": "name", "order": "asc"},
            }
            result = await self._request_json(
                "POST", url, headers=self._headers(), json_body=payload
            )
            rows = result if isinstance(result, list) else []
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("name"), str):
                    name = str(row["name"]).lstrip("/")
                    paths.append(name if name.startswith(f"{user_id}/") else f"{user_id}/{name}")
            if len(rows) < 100:
                break
            offset += len(rows)
        return paths

    @staticmethod
    def _without_bucket(path: str) -> str:
        clean = path.lstrip("/")
        prefix = "avatars/"
        return clean[len(prefix) :] if clean.startswith(prefix) else clean

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        content: bytes | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> None:
        await self._perform(method, url, headers=headers, content=content, json_body=json_body)

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any],
    ) -> Any:
        response = await self._perform(method, url, headers=headers, json_body=json_body)
        try:
            return response.json()
        except ValueError as exc:
            raise AvatarStorageError("Resposta inválida do Storage.") from exc

    async def _perform(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        content: bytes | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            if self._client is not None:
                response = await self._client.request(
                    method, url, headers=headers, content=content, json=json_body
                )
            else:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method, url, headers=headers, content=content, json=json_body
                    )
            response.raise_for_status()
            return response
        except (httpx.HTTPError, OSError) as exc:
            raise AvatarStorageError("Operação segura no Storage falhou.") from exc
