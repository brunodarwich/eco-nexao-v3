"""Ephemeral, non-persistent Google Place Photos proxy (ECO-2510)."""

from __future__ import annotations

import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from math import ceil
from urllib.parse import urlparse


class PhotoProxyError(Exception):
    """Safe error that intentionally contains no Google URL or resource name."""


class PhotoProxyExpired(PhotoProxyError):
    pass


class PhotoProxyNotFound(PhotoProxyError):
    pass


@dataclass(frozen=True, slots=True)
class GooglePhotoGrant:
    token: str
    expires_at: int
    attributions: tuple[Mapping[str, str], ...]
    google_maps_uri: str
    width_px: int
    height_px: int


@dataclass(slots=True)
class _PendingPhoto:
    resource_name: str
    expires_at: int
    attributions: tuple[Mapping[str, str], ...]
    google_maps_uri: str
    width_px: int
    height_px: int


PhotoFetcher = Callable[[str, int, int], Awaitable[tuple[bytes, str]]]


class GooglePhotoProxyService:
    """One-time memory grants; nothing photo-related is written to database or Storage."""

    def __init__(self, fetcher: PhotoFetcher, *, ttl_seconds: int = 300) -> None:
        if not 1 <= ttl_seconds <= 600:
            raise ValueError("ttl_seconds must be between 1 and 600")
        self._fetcher = fetcher
        self._ttl_seconds = ttl_seconds
        self._pending: dict[str, _PendingPhoto] = {}

    def grant(
        self,
        *,
        resource_name: str,
        attributions: list[Mapping[str, str]],
        google_maps_uri: str,
        width_px: int,
        height_px: int,
        now: int | None = None,
    ) -> GooglePhotoGrant:
        if not resource_name.startswith("places/") or "/photos/" not in resource_name:
            raise ValueError("invalid Google photo resource name")
        if not _is_google_uri(google_maps_uri):
            raise ValueError("invalid Google Maps URI")
        if not 1 <= width_px <= 4800 or not 1 <= height_px <= 4800:
            raise ValueError("photo dimensions must be between 1 and 4800")
        # Rounding up avoids issuing a nominal one-second grant that disappears
        # immediately when it is created late in a wall-clock second.
        current = ceil(time.time()) if now is None else now
        token = secrets.token_urlsafe(32)
        expires_at = current + self._ttl_seconds
        authors = tuple(attributions)
        self._pending[token] = _PendingPhoto(
            resource_name, expires_at, authors, google_maps_uri, width_px, height_px
        )
        return GooglePhotoGrant(token, expires_at, authors, google_maps_uri, width_px, height_px)

    def metadata(self, token: str, *, now: int | None = None) -> GooglePhotoGrant:
        """Return safe client metadata without revealing the upstream resource name."""
        current = int(time.time()) if now is None else now
        pending = self._pending.get(token)
        if pending is None:
            raise PhotoProxyNotFound("photo is unavailable")
        if pending.expires_at <= current:
            self._pending.pop(token, None)
            raise PhotoProxyExpired("photo grant expired")
        return GooglePhotoGrant(
            token,
            pending.expires_at,
            pending.attributions,
            pending.google_maps_uri,
            pending.width_px,
            pending.height_px,
        )

    async def consume(
        self, token: str, *, max_height_px: int, max_width_px: int, now: int | None = None
    ) -> tuple[bytes, str]:
        if not 1 <= max_height_px <= 4800 or not 1 <= max_width_px <= 4800:
            raise ValueError("photo dimensions must be between 1 and 4800")
        current = int(time.time()) if now is None else now
        pending = self._pending.pop(token, None)  # one time also limits replay/caching
        if pending is None:
            raise PhotoProxyNotFound("photo is unavailable")
        if pending.expires_at <= current:
            raise PhotoProxyExpired("photo grant expired")
        try:
            return await self._fetcher(pending.resource_name, max_height_px, max_width_px)
        except Exception as exc:
            raise PhotoProxyError("Google photo is temporarily unavailable") from exc


def _is_google_uri(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (
        host in {"google.com", "www.google.com", "maps.google.com", "maps.app.goo.gl"}
        or host.endswith(".google.com")
    )
