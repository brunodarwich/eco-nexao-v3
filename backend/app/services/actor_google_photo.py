"""Issue short-lived Google photo grants from fresh Place Details data (ECO-2510)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Protocol
from urllib.parse import urlparse

from app.connectors.google_places import GooglePlacesError, PlacesConnectorProtocol
from app.services.google_photo_proxy import GooglePhotoGrant, GooglePhotoProxyService


class ActorGooglePhotoRepository(Protocol):
    async def get_active_google_place_id(self, actor_id: uuid.UUID) -> str | None: ...


class ActorGooglePhotoUnavailable(Exception):
    """Safe no-photo result; upstream details stay server-side."""


class ActorGooglePhotoUpstreamUnavailable(ActorGooglePhotoUnavailable):
    """Safe transient failure while obtaining fresh Google metadata."""


class ActorGooglePhotoService:
    """Build grants from one fresh response; photo resource names are never persisted."""

    def __init__(
        self,
        repository: ActorGooglePhotoRepository,
        places: PlacesConnectorProtocol,
        proxy: GooglePhotoProxyService,
    ) -> None:
        self._repository = repository
        self._places = places
        self._proxy = proxy

    async def issue(self, actor_id: uuid.UUID) -> GooglePhotoGrant:
        place_id = await self._repository.get_active_google_place_id(actor_id)
        if place_id is None:
            raise ActorGooglePhotoUnavailable("photo unavailable")
        try:
            details = await self._places.place_details(place_id, fields=("photos", "googleMapsUri"))
        except GooglePlacesError as exc:
            raise ActorGooglePhotoUpstreamUnavailable("photo unavailable") from exc

        maps_uri = _google_uri(details.get("googleMapsUri"))
        photos = details.get("photos")
        if maps_uri is None or not isinstance(photos, list):
            raise ActorGooglePhotoUnavailable("photo unavailable")
        for raw_photo in photos:
            if not isinstance(raw_photo, Mapping):
                continue
            resource_name = raw_photo.get("name")
            width = raw_photo.get("widthPx")
            height = raw_photo.get("heightPx")
            if not (
                isinstance(resource_name, str)
                and isinstance(width, int)
                and isinstance(height, int)
            ):
                continue
            try:
                return self._proxy.grant(
                    resource_name=resource_name,
                    attributions=_attributions(raw_photo.get("authorAttributions")),
                    google_maps_uri=maps_uri,
                    width_px=width,
                    height_px=height,
                )
            except ValueError:
                continue
        raise ActorGooglePhotoUnavailable("photo unavailable")


def _attributions(value: Any) -> list[Mapping[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: list[Mapping[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        display_name = item.get("displayName")
        if not isinstance(display_name, str) or not display_name.strip():
            continue
        attribution: dict[str, str] = {"display_name": display_name.strip()}
        uri = _google_uri(item.get("uri"))
        if uri is not None:
            attribution["uri"] = uri
        normalized.append(attribution)
    return normalized


def _google_uri(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or not _is_google_host(host):
        return None
    return candidate


def _is_google_host(host: str) -> bool:
    return (
        host in {"google.com", "maps.google.com", "www.google.com"}
        or host.endswith(".google.com")
        or host == "maps.app.goo.gl"
    )
