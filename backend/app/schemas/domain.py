"""Pydantic v2 schemas for internal ECOnexão domain entities and ORM mappings
(ECO-0201 to ECO-0206).

Note:
    Public and edge API contract envelopes are defined in `app.schemas.envelopes`,
    `app.schemas.admin_territorial`, `app.schemas.admin_actors`, and `app.schemas.admin_workflow`.
    Schemas in this module represent canonical internal domain entity representations.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# Common Base Model
# -----------------------------------------------------------------------------


class DomainBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# ECO-0201: Regiões, Rotas, Origens e Geometrias
# -----------------------------------------------------------------------------


class RegionBase(DomainBaseSchema):
    slug: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    state_code: str = Field(..., max_length=2)
    is_active: bool = True


class RegionCreate(RegionBase):
    center: dict[str, Any] | None = None


class RegionRead(RegionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RouteBase(DomainBaseSchema):
    slug: str = Field(..., max_length=150)
    title: str = Field(..., max_length=255)
    summary: str | None = None
    city: str = Field(..., max_length=100)
    state_code: str = Field(..., max_length=2)
    status: str = "active"
    is_verified: bool = False
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None


class RouteCreate(RouteBase):
    region_id: uuid.UUID


class RouteRead(RouteBase):
    id: uuid.UUID
    region_id: uuid.UUID
    verified_at: datetime | None = None
    cover_media_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class RouteOriginRead(DomainBaseSchema):
    id: uuid.UUID
    route_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    distance_m: int | None = None
    duration_s: int | None = None
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


class RouteGeometryRead(DomainBaseSchema):
    id: uuid.UUID
    route_origin_id: uuid.UUID
    provider: str = "osrm"
    encoded_polyline: str | None = None
    distance_m: int | None = None
    duration_s: int | None = None
    source_collected_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# ECO-0202: Atores, Categorias e Acessibilidade
# -----------------------------------------------------------------------------


class ActorCategoryRead(DomainBaseSchema):
    id: uuid.UUID
    slug: str
    label: str
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


class ActorRead(DomainBaseSchema):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    category_id: uuid.UUID
    sub_category: str | None = None
    address: str | None = None
    city: str | None = None
    state_code: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None
    website: str | None = None
    opening_hours: dict[str, Any] = Field(default_factory=dict)
    payment_methods: list[Any] = Field(default_factory=list)
    green_badge_status: str = "none"
    verification_status: str = "unverified"
    google_rating: float | None = None
    google_review_count: int | None = None
    created_at: datetime
    updated_at: datetime


class AccessibilityFeatureRead(DomainBaseSchema):
    id: uuid.UUID
    slug: str
    label: str
    description: str | None = None
    icon: str | None = None


# -----------------------------------------------------------------------------
# ECO-0203: Alertas e Mídia
# -----------------------------------------------------------------------------


class RouteAlertRead(DomainBaseSchema):
    id: uuid.UUID
    route_id: uuid.UUID
    title: str
    message: str
    severity: str = "info"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime
    source: str | None = None
    is_active: bool = True


class MediaAssetRead(DomainBaseSchema):
    id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    storage_key: str | None = None
    mime_type: str
    alt_text: str | None = None
    credit: str | None = None
    license_code: str | None = None
    processing_status: str = "pending"
    checksum_sha256: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    derivatives: dict[str, Any] = Field(default_factory=dict)
    location: dict[str, Any] | None = None
    processed_at: datetime | None = None
    rejected_reason: str | None = None
    deleted_at: datetime | None = None
    media_kind: str = "stored"
    external_photo_reference: str | None = None
    external_attributions: list[Any] | None = None
    external_cache_expires_at: datetime | None = None
    sort_order: int = 0


# -----------------------------------------------------------------------------
# ECO-0205: Usuário, Preferências e Favoritos
# -----------------------------------------------------------------------------


class ProfileRead(DomainBaseSchema):
    id: uuid.UUID
    name: str | None = None
    location: str | None = None
    avatar_media_id: uuid.UUID | None = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class UserPreferenceRead(DomainBaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    active_region_id: uuid.UUID | None = None
    screen_reader_mode: bool = False
    high_contrast: bool = False
    text_scale: float = 1.0
    locale: str = "pt-BR"
    created_at: datetime
    updated_at: datetime


class FavoriteRouteRead(DomainBaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    route_id: uuid.UUID
    created_at: datetime


class FavoriteActorRead(DomainBaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    actor_id: uuid.UUID
    created_at: datetime


# -----------------------------------------------------------------------------
# ECO-0206: Viagens, Visitas e Selos
# -----------------------------------------------------------------------------


class TripRead(DomainBaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    route_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "in_progress"
    created_at: datetime
    updated_at: datetime


class UserBadgeRead(DomainBaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    badge_code: str
    awarded_at: datetime
    evidence: dict[str, Any] = Field(default_factory=dict)
