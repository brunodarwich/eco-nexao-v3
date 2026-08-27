"""Pydantic v2 envelope schemas for OpenAPI v1 response envelopes (ECO-0501 to ECO-0506)."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(SchemaBase):
    total: int
    limit: int
    next_cursor: str | None = None


# -----------------------------------------------------------------------------
# Regions & Bootstrap
# -----------------------------------------------------------------------------


class RegionSchema(SchemaBase):
    id: uuid.UUID
    slug: str
    name: str
    state_code: str
    is_active: bool


class RegionListEnvelope(SchemaBase):
    data: list[RegionSchema]


class BootstrapDataSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["feature_flags", "supported_regions"]},
    )
    active_region: RegionSchema | None = None
    feature_flags: dict[str, bool] = Field(
        default_factory=lambda: {
            "google_business_profile": False,
            "green_badge_verification": True,
            "anonymous_signin": True,
            "dynamic_routing": False,
        }
    )
    supported_regions: list[RegionSchema] = Field(default_factory=list)


class BootstrapResponseEnvelope(SchemaBase):
    data: BootstrapDataSchema


# -----------------------------------------------------------------------------
# Routes & Origins
# -----------------------------------------------------------------------------


class ResolvedMediaItemSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["id", "owner_type", "owner_id", "url"]},
    )
    id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    url: str
    derivatives: dict[str, str] = Field(default_factory=dict)
    alt_text: str | None = None
    credit: str | None = None
    license_code: str | None = None
    media_kind: str = "stored"
    sort_order: int = 0


class RouteSummarySchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": ["id", "slug", "title", "city", "state_code", "status", "is_verified"]
        },
    )
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None = None
    city: str
    state_code: str
    status: str = "active"
    is_verified: bool = False
    best_season: str | None = None
    cover_image_url: str | None = None
    cover_media: ResolvedMediaItemSchema | None = None
    is_favorite: bool = False


class RouteListEnvelope(SchemaBase):
    data: list[RouteSummarySchema]
    meta: PaginationMeta


class RouteOriginSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["id", "route_id", "code", "name", "sort_order"]},
    )
    id: uuid.UUID
    route_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    distance_m: int | None = None
    duration_s: int | None = None
    sort_order: int = 0


class RouteOriginListEnvelope(SchemaBase):
    data: list[RouteOriginSchema]


class RouteDetailSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": [
                "id",
                "slug",
                "title",
                "city",
                "state_code",
                "status",
                "is_verified",
                "origins",
            ]
        },
    )
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None = None
    description: str | None = None
    city: str
    state_code: str
    status: str = "active"
    is_verified: bool = False
    verified_at: datetime | None = None
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None
    cover_image_url: str | None = None
    cover_media: ResolvedMediaItemSchema | None = None
    is_favorite: bool = False
    gallery: list[ResolvedMediaItemSchema] = Field(default_factory=list)
    origins: list[RouteOriginSchema] = Field(default_factory=list)


class RouteDetailEnvelope(SchemaBase):
    data: RouteDetailSchema


# -----------------------------------------------------------------------------
# Geometry & Maps
# -----------------------------------------------------------------------------


class RouteGeometrySchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["id", "provider", "route_origin_id"]},
    )
    id: uuid.UUID
    route_origin_id: uuid.UUID
    provider: str = "osrm"
    encoded_polyline: str | None = None
    geojson: dict[str, Any] | None = None
    distance_m: int | None = None
    duration_s: int | None = None


class RouteGeometryEnvelope(SchemaBase):
    data: RouteGeometrySchema


class RouteBoundsSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["min_lat", "max_lat", "min_lng", "max_lng"]},
    )
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class MapPinSchema(SchemaBase):
    id: uuid.UUID
    actor_id: uuid.UUID
    name: str
    category_slug: str
    category_label: str
    color: str
    icon: str
    latitude: float
    longitude: float
    distance_from_origin_m: int | None = None
    layer: Literal["route_corridor", "citywide_essential", "both"] = "route_corridor"


class MapLegendItemSchema(SchemaBase):
    category_slug: str
    label: str
    color: str
    icon: str
    count: int
    sort_order: int


class RouteMapPayloadSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["pins", "route_id", "legend"]},
    )
    route_id: uuid.UUID
    selected_origin_id: uuid.UUID | None = None
    bounds: RouteBoundsSchema | None = None
    city_bounds: RouteBoundsSchema | None = None
    geometry: RouteGeometrySchema | None = None
    pins: list[MapPinSchema] = Field(default_factory=list)
    legend: list[MapLegendItemSchema] = Field(default_factory=list)


class RouteMapPayloadEnvelope(SchemaBase):
    data: RouteMapPayloadSchema


class RoutePreviewRequest(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["latitude", "longitude"]},
    )
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude da origem do usuário")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude da origem do usuário")
    travel_mode: Literal["DRIVE"] = "DRIVE"


class RoutePreviewDataSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": [
                "route_id",
                "route_kind",
                "is_verified",
                "provider",
                "distance_m",
                "duration_s",
                "geojson",
                "bounds",
                "pins",
                "legend",
            ]
        },
    )
    route_id: uuid.UUID
    route_kind: Literal["dynamic_preview"] = "dynamic_preview"
    is_verified: bool = False
    provider: Literal["fake_deterministic", "google_routes"]
    distance_m: int
    duration_s: int
    geojson: dict[str, Any]
    encoded_polyline: str | None = None
    bounds: RouteBoundsSchema
    pins: list[MapPinSchema] = Field(default_factory=list)
    legend: list[MapLegendItemSchema] = Field(default_factory=list)
    city_bounds: RouteBoundsSchema | None = None


class RoutePreviewEnvelope(SchemaBase):
    data: RoutePreviewDataSchema


# -----------------------------------------------------------------------------
# Alerts
# -----------------------------------------------------------------------------


class RouteAlertSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": [
                "id",
                "is_active",
                "message",
                "published_at",
                "route_id",
                "severity",
                "title",
            ]
        },
    )
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


class RouteAlertListEnvelope(SchemaBase):
    data: list[RouteAlertSchema]


# -----------------------------------------------------------------------------
# Actors & Categories
# -----------------------------------------------------------------------------


class ActorCategorySchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["id", "label", "slug", "sort_order"]},
    )
    id: uuid.UUID
    slug: str
    label: str
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0


class ActorCategoryListEnvelope(SchemaBase):
    data: list[ActorCategorySchema]


class ActorSummarySchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": [
                "category_label",
                "category_slug",
                "green_badge_status",
                "id",
                "name",
                "slug",
                "verification_status",
            ]
        },
    )
    id: uuid.UUID
    slug: str
    name: str
    category_slug: str
    category_label: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    green_badge_status: str = "none"
    verification_status: str = "unverified"
    google_rating: float | None = None
    cover_image_url: str | None = None
    cover_media: ResolvedMediaItemSchema | None = None
    is_favorite: bool = False


class ActorListEnvelope(SchemaBase):
    data: list[ActorSummarySchema]
    meta: PaginationMeta


class ActorDetailSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": [
                "accessibility_features",
                "category",
                "green_badge_status",
                "id",
                "name",
                "opening_hours",
                "payment_methods",
                "slug",
                "verification_status",
            ]
        },
    )
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    category: ActorCategorySchema
    sub_category: str | None = None
    address: str | None = None
    city: str | None = None
    state_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None
    website: str | None = None
    opening_hours: dict[str, Any] = Field(default_factory=dict)
    payment_methods: list[Any] = Field(default_factory=list)
    green_badge_status: str = "none"
    verification_status: str = "unverified"
    google_place_id: str | None = None
    google_rating: float | None = None
    google_review_count: int | None = None
    cover_image_url: str | None = None
    cover_media: ResolvedMediaItemSchema | None = None
    is_favorite: bool = False
    gallery: list[ResolvedMediaItemSchema] = Field(default_factory=list)
    accessibility_features: list[dict[str, Any]] = Field(default_factory=list)


class ActorDetailEnvelope(SchemaBase):
    data: ActorDetailSchema


# -----------------------------------------------------------------------------
# User Profile, Preferences & Favorites (ECO-0604, ECO-0605)
# -----------------------------------------------------------------------------


class UserProfileSchema(SchemaBase):
    id: uuid.UUID
    name: str | None = None
    location: str | None = None
    avatar_media_id: uuid.UUID | None = None
    avatar: ResolvedMediaItemSchema | None = None
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfileEnvelope(SchemaBase):
    data: UserProfileSchema


class UserProfileUpdate(BaseModel):
    name: str | None = None
    location: str | None = None


class UserPreferencesSchema(SchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    active_region_id: uuid.UUID | None = None
    screen_reader_mode: bool = False
    high_contrast: bool = False
    text_scale: float = Field(default=1.0, ge=0.5, le=3.0)
    locale: str = Field(default="pt-BR", max_length=10)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserPreferencesEnvelope(SchemaBase):
    data: UserPreferencesSchema


class UserPreferencesUpdate(BaseModel):
    active_region_id: uuid.UUID | None = None
    screen_reader_mode: bool | None = None
    high_contrast: bool | None = None
    text_scale: float | None = Field(default=None, ge=0.5, le=3.0)
    locale: str | None = Field(default=None, max_length=10)


class StandardSuccessData(SchemaBase):
    success: bool = True
    message: str | None = None


class StandardSuccessResponse(SchemaBase):
    success: bool = True
    data: StandardSuccessData | None = None


# -----------------------------------------------------------------------------
# Server-side Avatar Upload (ECO-1701)
# -----------------------------------------------------------------------------


class AvatarUploadResponseData(SchemaBase):
    media_asset_id: uuid.UUID
    url: str
    derivatives: dict[str, str]
    alt_text: str


class AvatarUploadResponseEnvelope(SchemaBase):
    data: AvatarUploadResponseData


# -----------------------------------------------------------------------------
# Auth Session & Token Verification (ECO-0602)
# -----------------------------------------------------------------------------


class AuthUserSchema(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["id", "is_anonymous", "role"]},
    )
    id: uuid.UUID
    email: str | None = None
    is_anonymous: bool = False
    role: str = "authenticated"


class AuthSessionEnvelope(SchemaBase):
    data: AuthUserSchema


# -----------------------------------------------------------------------------
# Administrative API foundation (ECO-1601)
# -----------------------------------------------------------------------------


class AdminScopeAccessSchema(SchemaBase):
    """Roles and capabilities that are valid together in one authorization scope."""

    scope_type: str
    scope_id: uuid.UUID | None = None
    roles: list[str]
    capabilities: list[str]


class AdminAccessSchema(SchemaBase):
    """Database-backed editorial identity; JWT metadata never grants capabilities."""

    user_id: uuid.UUID
    scopes: list[AdminScopeAccessSchema]


class AdminVersionSchema(SchemaBase):
    version: int = Field(ge=1)
    updated_at: datetime


class AdminAuditMetadataSchema(SchemaBase):
    request_id: str
    reason: str | None = None
    idempotency_key: str | None = None


class AdminJobReferenceSchema(SchemaBase):
    job_id: uuid.UUID
    status: str
    status_url: str


class AdminUploadReferenceSchema(SchemaBase):
    upload_id: uuid.UUID
    status: str
    upload_url: str | None = None
    expires_at: datetime | None = None


class AdminContractSchema(SchemaBase):
    """Cross-cutting mutation contract for subsequent administrative CRUD tasks."""

    concurrency_header: str = "If-Match"
    version_field: str = "version"
    idempotency_header: str = "Idempotency-Key"
    audit_request_header: str = "X-Request-ID"
    version: AdminVersionSchema | None = None
    audit: AdminAuditMetadataSchema | None = None
    job_reference: AdminJobReferenceSchema | None = None
    upload_reference: AdminUploadReferenceSchema | None = None


class AdminContextDataSchema(SchemaBase):
    access: AdminAccessSchema
    contract: AdminContractSchema = Field(default_factory=AdminContractSchema)


class AdminContextEnvelope(SchemaBase):
    data: AdminContextDataSchema


class TokenVerifyRequest(BaseModel):
    token: str


class TokenVerifyData(SchemaBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"required": ["valid", "user"]},
    )
    valid: bool = True
    user: AuthUserSchema


class TokenVerifyEnvelope(SchemaBase):
    data: TokenVerifyData


# -----------------------------------------------------------------------------
# Trips & Support (ECO-0606, ECO-0607)
# -----------------------------------------------------------------------------


class TripSchema(SchemaBase):
    id: str
    user_id: str
    route_id: str
    started_at: str | None = None
    completed_at: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    route_title: str | None = None


class TripListEnvelope(SchemaBase):
    data: list[TripSchema]


class TripCreate(BaseModel):
    route_id: uuid.UUID


class TripEnvelope(SchemaBase):
    data: TripSchema


class FAQItemSchema(SchemaBase):
    id: str
    question: str
    answer: str
    category: str = "Geral"


class ContactInfoSchema(SchemaBase):
    email: str
    phone: str = ""
    whatsapp: str = ""
    operating_hours: str = ""


class HelpLinkSchema(SchemaBase):
    title: str
    url: str


class EditorialInfoSchema(SchemaBase):
    version: str = "1.0.0"
    last_updated: str = ""
    publisher: str = "SEMTUR"


class SupportContentData(SchemaBase):
    faq: list[FAQItemSchema] = Field(default_factory=list)
    contacts: ContactInfoSchema
    help_links: list[HelpLinkSchema] = Field(default_factory=list)
    editorial_info: EditorialInfoSchema = Field(default_factory=EditorialInfoSchema)


class SupportContentEnvelope(SchemaBase):
    data: SupportContentData
