"""Temporary Google Place Photos endpoint (ECO-2510)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.schemas.envelopes import (
    GooglePhotoAttributionSchema,
    GooglePhotoMetadataEnvelope,
    GooglePhotoMetadataSchema,
)
from app.services.dependencies import get_google_photo_proxy
from app.services.google_photo_proxy import (
    GooglePhotoProxyService,
    PhotoProxyError,
    PhotoProxyExpired,
    PhotoProxyNotFound,
)

router = APIRouter(prefix="/places/photos", tags=["Google Place Photos"])
PhotoProxyDep = Annotated[GooglePhotoProxyService, Depends(get_google_photo_proxy)]


@router.get("/{token}/metadata", response_model=GooglePhotoMetadataEnvelope)
async def get_place_photo_metadata(token: str, proxy: PhotoProxyDep) -> GooglePhotoMetadataEnvelope:
    """Metadata is intentionally only available after a trusted server-side grant."""
    try:
        grant = proxy.metadata(token)
    except PhotoProxyExpired as exc:
        raise HTTPException(status_code=410, detail="Foto temporária expirada.") from exc
    except PhotoProxyNotFound as exc:
        raise HTTPException(status_code=404, detail="Foto indisponível.") from exc
    return GooglePhotoMetadataEnvelope(
        data=GooglePhotoMetadataSchema(
            proxy_url=f"/api/v1/places/photos/{grant.token}",
            expires_at=grant.expires_at,
            width_px=grant.width_px,
            height_px=grant.height_px,
            author_attributions=[
                GooglePhotoAttributionSchema(**item) for item in grant.attributions
            ],
            google_maps_uri=grant.google_maps_uri,
        )
    )


@router.get(
    "/{token}",
    responses={404: {"description": "Foto indisponível"}, 410: {"description": "Foto expirada"}},
)
async def get_place_photo(
    token: str,
    proxy: PhotoProxyDep,
    max_height_px: int = Query(600, alias="maxHeightPx", ge=1, le=4800),
    max_width_px: int = Query(800, alias="maxWidthPx", ge=1, le=4800),
) -> Response:
    try:
        body, media_type = await proxy.consume(
            token, max_height_px=max_height_px, max_width_px=max_width_px
        )
    except PhotoProxyExpired as exc:
        raise HTTPException(status_code=410, detail="Foto temporária expirada.") from exc
    except PhotoProxyNotFound as exc:
        raise HTTPException(status_code=404, detail="Foto indisponível.") from exc
    except PhotoProxyError as exc:
        raise HTTPException(status_code=503, detail="Foto temporariamente indisponível.") from exc
    return Response(content=body, media_type=media_type, headers={"Cache-Control": "no-store"})
