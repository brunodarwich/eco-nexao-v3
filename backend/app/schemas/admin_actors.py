"""Administrative Pydantic schemas for actor domain CRUD (ECO-1603)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.envelopes import PaginationMeta, SchemaBase

# -----------------------------------------------------------------------------
# Admin Actor Categories
# -----------------------------------------------------------------------------


class AdminCategoryCreateSchema(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    label: str = Field(..., min_length=2, max_length=255)
    icon: str | None = Field(None, max_length=100)
    color: str | None = Field(None, max_length=50)
    sort_order: int = Field(0, ge=0)


class AdminCategoryUpdateSchema(BaseModel):
    label: str | None = Field(None, min_length=2, max_length=255)
    icon: str | None = Field(None, max_length=100)
    color: str | None = Field(None, max_length=50)
    sort_order: int | None = Field(None, ge=0)


class AdminCategorySchema(SchemaBase):
    id: uuid.UUID
    slug: str
    label: str
    icon: str | None = None
    color: str | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminCategoryEnvelope(SchemaBase):
    data: AdminCategorySchema


class AdminCategoryListEnvelope(SchemaBase):
    data: list[AdminCategorySchema]


# -----------------------------------------------------------------------------
# Admin Accessibility Features
# -----------------------------------------------------------------------------


class AdminAccessibilityFeatureCreateSchema(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    label: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=100)


class AdminAccessibilityFeatureUpdateSchema(BaseModel):
    label: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=100)


class AdminAccessibilityFeatureSchema(SchemaBase):
    id: uuid.UUID
    slug: str
    label: str
    description: str | None = None
    icon: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminAccessibilityFeatureEnvelope(SchemaBase):
    data: AdminAccessibilityFeatureSchema


class AdminAccessibilityFeatureListEnvelope(SchemaBase):
    data: list[AdminAccessibilityFeatureSchema]


# -----------------------------------------------------------------------------
# Admin Actors
# -----------------------------------------------------------------------------


class AdminActorCreateSchema(BaseModel):
    category_id: uuid.UUID
    slug: str = Field(..., min_length=2, max_length=150, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    sub_category: str | None = Field(None, max_length=100)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    instagram: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=255)
    opening_hours: dict[str, Any] = Field(default_factory=dict)
    payment_methods: list[Any] = Field(default_factory=list)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    green_badge_status: str = Field("none", pattern=r"^(none|bronze|silver|gold)$")
    verification_status: str = Field("unverified", pattern=r"^(unverified|verified|rejected)$")
    accessibility_feature_ids: list[uuid.UUID] = Field(default_factory=list)


class AdminActorUpdateSchema(BaseModel):
    category_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    sub_category: str | None = Field(None, max_length=100)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    instagram: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=255)
    opening_hours: dict[str, Any] | None = None
    payment_methods: list[Any] | None = None
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    green_badge_status: str | None = Field(None, pattern=r"^(none|bronze|silver|gold)$")
    verification_status: str | None = Field(None, pattern=r"^(unverified|verified|rejected)$")
    accessibility_feature_ids: list[uuid.UUID] | None = None
    expected_version: str | None = Field(
        None, description="Expected ISO string timestamp for optimistic concurrency check"
    )


class AdminActorSchema(SchemaBase):
    id: uuid.UUID
    category_id: uuid.UUID
    category: AdminCategorySchema | None = None
    slug: str
    name: str
    description: str | None = None
    sub_category: str | None = None
    address: str | None = None
    city: str | None = None
    state_code: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None
    website: str | None = None
    opening_hours: dict[str, Any]
    payment_methods: list[Any]
    latitude: float | None = None
    longitude: float | None = None
    green_badge_status: str
    verification_status: str
    google_rating: float | None = None
    google_review_count: int | None = None
    accessibility_features: list[AdminAccessibilityFeatureSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class AdminActorEnvelope(SchemaBase):
    data: AdminActorSchema


class AdminActorListEnvelope(SchemaBase):
    data: list[AdminActorSchema]
    meta: PaginationMeta


# -----------------------------------------------------------------------------
# Admin Route Links (RouteActor)
# -----------------------------------------------------------------------------


class AdminRouteActorCreateSchema(BaseModel):
    route_id: uuid.UUID
    actor_id: uuid.UUID
    distance_to_route_m: float | None = Field(None, ge=0)
    route_segment_index: int | None = Field(None, ge=0)
    origin_flags: dict[str, Any] = Field(default_factory=dict)
    is_featured: bool = False
    sort_order: int = Field(0, ge=0)


class AdminRouteActorUpdateSchema(BaseModel):
    distance_to_route_m: float | None = Field(None, ge=0)
    route_segment_index: int | None = Field(None, ge=0)
    origin_flags: dict[str, Any] | None = None
    is_featured: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class AdminRouteActorSchema(SchemaBase):
    id: uuid.UUID
    route_id: uuid.UUID
    actor_id: uuid.UUID
    distance_to_route_m: float | None = None
    route_segment_index: int | None = None
    origin_flags: dict[str, Any]
    is_featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminRouteActorEnvelope(SchemaBase):
    data: AdminRouteActorSchema


class AdminRouteActorListEnvelope(SchemaBase):
    data: list[AdminRouteActorSchema]
