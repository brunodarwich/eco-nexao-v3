"""Administrative Pydantic schemas for territorial domain CRUD (ECO-1602)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.envelopes import PaginationMeta, SchemaBase

# -----------------------------------------------------------------------------
# Admin Regions
# -----------------------------------------------------------------------------


class AdminRegionCreateSchema(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    state_code: str = Field(..., min_length=2, max_length=2)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    is_active: bool = True


class AdminRegionUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    is_active: bool | None = None


class AdminRegionSchema(SchemaBase):
    id: uuid.UUID
    slug: str
    name: str
    state_code: str
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminRegionEnvelope(SchemaBase):
    data: AdminRegionSchema


class AdminRegionListEnvelope(SchemaBase):
    data: list[AdminRegionSchema]


# -----------------------------------------------------------------------------
# Admin Routes
# -----------------------------------------------------------------------------


class AdminRouteCreateSchema(BaseModel):
    region_id: uuid.UUID
    slug: str = Field(..., min_length=2, max_length=150, pattern=r"^[a-z0-9-]+$")
    title: str = Field(..., min_length=2, max_length=255)
    summary: str | None = None
    city: str = Field(..., min_length=2, max_length=100)
    state_code: str = Field(..., min_length=2, max_length=2)
    status: str = Field("draft", pattern=r"^(draft|review|published|archived|active)$")
    is_verified: bool = False
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None
    cover_media_id: uuid.UUID | None = None


class AdminRouteUpdateSchema(BaseModel):
    region_id: uuid.UUID | None = None
    title: str | None = Field(None, min_length=2, max_length=255)
    summary: str | None = None
    city: str | None = Field(None, min_length=2, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    status: str | None = Field(None, pattern=r"^(draft|review|published|archived|active)$")
    is_verified: bool | None = None
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None
    cover_media_id: uuid.UUID | None = None
    expected_version: str | None = Field(
        None, description="Expected ISO string timestamp or version hash for optimistic concurrency"
    )


class AdminRouteSchema(SchemaBase):
    id: uuid.UUID
    region_id: uuid.UUID
    slug: str
    title: str
    summary: str | None = None
    city: str
    state_code: str
    status: str
    is_verified: bool
    verified_at: datetime | None = None
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None
    cover_media_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class AdminRouteEnvelope(SchemaBase):
    data: AdminRouteSchema


class AdminRouteListEnvelope(SchemaBase):
    data: list[AdminRouteSchema]
    meta: PaginationMeta


# -----------------------------------------------------------------------------
# Admin Route Origins
# -----------------------------------------------------------------------------


class AdminRouteOriginCreateSchema(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    distance_m: int | None = Field(None, ge=0)
    duration_s: int | None = Field(None, ge=0)
    sort_order: int = Field(0, ge=0)


class AdminRouteOriginUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    distance_m: int | None = Field(None, ge=0)
    duration_s: int | None = Field(None, ge=0)
    sort_order: int | None = Field(None, ge=0)


class AdminRouteOriginSchema(SchemaBase):
    id: uuid.UUID
    route_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    latitude: float
    longitude: float
    distance_m: int | None = None
    duration_s: int | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminRouteOriginEnvelope(SchemaBase):
    data: AdminRouteOriginSchema


class AdminRouteOriginListEnvelope(SchemaBase):
    data: list[AdminRouteOriginSchema]


# -----------------------------------------------------------------------------
# Admin Route Geometries
# -----------------------------------------------------------------------------


class AdminRouteGeometryCreateSchema(BaseModel):
    provider: str = Field("osrm", max_length=50)
    coordinates: list[list[float]] = Field(
        ...,
        description="Array of [lat, lon] coordinate pairs",
        min_length=2,
    )
    encoded_polyline: str | None = None
    distance_m: int | None = Field(None, ge=0)
    duration_s: int | None = Field(None, ge=0)
    bounds: dict[str, float] | None = None
    source_hash: str | None = None


class AdminRouteGeometryUpdateSchema(BaseModel):
    coordinates: list[list[float]] | None = Field(None, min_length=2)
    encoded_polyline: str | None = None
    distance_m: int | None = Field(None, ge=0)
    duration_s: int | None = Field(None, ge=0)
    bounds: dict[str, float] | None = None


class AdminRouteGeometrySchema(SchemaBase):
    id: uuid.UUID
    route_origin_id: uuid.UUID
    provider: str
    encoded_polyline: str | None = None
    geojson: dict[str, Any] | None = None
    distance_m: int | None = None
    duration_s: int | None = None
    bounds: dict[str, float] | None = None
    source_hash: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminRouteGeometryEnvelope(SchemaBase):
    data: AdminRouteGeometrySchema
