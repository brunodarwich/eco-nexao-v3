"""Trusted Supabase Storage adapter for immutable editorial derivatives."""

from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings


class EditorialStorageError(RuntimeError):
    """Raised without exposing credentials or response bodies."""


class SupabaseEditorialStorage:
    bucket = "editorial-media"

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _headers(self) -> dict[str, str]:
        secret = settings.SUPABASE_SECRET_KEY.get_secret_value()
        if not secret:
            raise EditorialStorageError("Credencial segura do Storage não configurada.")
        return {"Authorization": f"Bearer {secret}", "apikey": secret}

    async def upload(self, path: str, content: bytes, *, content_type: str) -> None:
        encoded_path = quote(path.lstrip("/"), safe="/")
        url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}/{encoded_path}"
        headers = {**self._headers(), "Content-Type": content_type, "x-upsert": "false"}
        await self._request("POST", url, headers=headers, content=content)

    async def remove(self, paths: Sequence[str]) -> None:
        if not paths:
            return
        url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}"
        await self._request(
            "DELETE", url, headers=self._headers(), json_body={"prefixes": list(paths)}
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        content: bytes | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> None:
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
        except (httpx.HTTPError, OSError) as exc:
            raise EditorialStorageError("Operação segura no Storage falhou.") from exc
