"""SQLAlchemy 2.0 ORM models for ECOnexão domain (ECO-0201 to ECO-0206)."""

import uuid
from datetime import datetime
from typing import Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    BOOLEAN,
    DOUBLE_PRECISION,
    INTEGER,
    NUMERIC,
    TEXT,
    VARCHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# -----------------------------------------------------------------------------
# ECO-0201: Regiões, Rotas, Origens e Geometrias
# -----------------------------------------------------------------------------


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    state_code: Mapped[str] = mapped_column(VARCHAR(2), nullable=False)
    center: Mapped[Any | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    routes: Mapped[list["Route"]] = relationship("Route", back_populates="region")
    actors: Mapped[list["Actor"]] = relationship("Actor", back_populates="region")


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(VARCHAR(150), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    city: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    state_code: Mapped[str] = mapped_column(VARCHAR(2), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(50), default="active", nullable=False)
    is_verified: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    best_season: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    connectivity: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    road_access: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    payment_info: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    cover_media_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    region: Mapped["Region"] = relationship("Region", back_populates="routes")
    origins: Mapped[list["RouteOrigin"]] = relationship(
        "RouteOrigin", back_populates="route", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["RouteAlert"]] = relationship(
        "RouteAlert", back_populates="route", cascade="all, delete-orphan"
    )
    route_actors: Mapped[list["RouteActor"]] = relationship(
        "RouteActor", back_populates="route", cascade="all, delete-orphan"
    )


class RouteOrigin(Base):
    __tablename__ = "route_origins"
    __table_args__ = (UniqueConstraint("route_id", "code", name="uq_route_origins_route_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    location: Mapped[Any] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    distance_m: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    sort_order: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    route: Mapped["Route"] = relationship("Route", back_populates="origins")
    geometries: Mapped[list["RouteGeometry"]] = relationship(
        "RouteGeometry", back_populates="origin", cascade="all, delete-orphan"
    )


class RouteGeometry(Base):
    __table_args__ = (
        UniqueConstraint("route_origin_id", "provider", name="uq_route_geometries_origin_provider"),
    )
    __tablename__ = "route_geometries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_origin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_origins.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(VARCHAR(50), default="osrm", nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geography(geometry_type="LINESTRING", srid=4326), nullable=False
    )
    encoded_polyline: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    source_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bounds: Mapped[dict[str, float] | None] = mapped_column(JSONB, nullable=True)
    source_hash: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    origin: Mapped["RouteOrigin"] = relationship("RouteOrigin", back_populates="geometries")


# -----------------------------------------------------------------------------
# ECO-0202: Atores, Categorias e Acessibilidade
# -----------------------------------------------------------------------------


class ActorCategory(Base):
    __tablename__ = "actor_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    icon: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    color: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    is_public: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    spatial_scope: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    actors: Mapped[list["Actor"]] = relationship("Actor", back_populates="category")
    types: Mapped[list["ActorType"]] = relationship("ActorType", back_populates="category")


class ActorType(Base):
    __tablename__ = "actor_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actor_categories.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    icon: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    spatial_scope: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    publication_rule: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    category: Mapped["ActorCategory"] = relationship("ActorCategory", back_populates="types")
    actors: Mapped[list["Actor"]] = relationship("Actor", back_populates="type")


class Actor(Base):
    __tablename__ = "actors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(VARCHAR(150), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actor_categories.id", ondelete="RESTRICT"), nullable=False
    )
    type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actor_types.id", ondelete="RESTRICT"), nullable=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )
    sub_category: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    address: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    city: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    state_code: Mapped[str | None] = mapped_column(VARCHAR(2), nullable=True)
    phone: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    email: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    instagram: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    website: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    opening_hours: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    payment_methods: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    location: Mapped[Any | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    green_badge_status: Mapped[str] = mapped_column(VARCHAR(50), default="none", nullable=False)
    verification_status: Mapped[str] = mapped_column(
        VARCHAR(50), default="unverified", nullable=False
    )
    google_rating: Mapped[float | None] = mapped_column(NUMERIC(3, 2), nullable=True)
    google_review_count: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    google_data_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    category: Mapped["ActorCategory"] = relationship("ActorCategory", back_populates="actors")
    type: Mapped["ActorType | None"] = relationship("ActorType", back_populates="actors")
    region: Mapped["Region | None"] = relationship("Region", back_populates="actors")
    route_actors: Mapped[list["RouteActor"]] = relationship(
        "RouteActor", back_populates="actor", cascade="all, delete-orphan"
    )
    accessibility_features: Mapped[list["ActorAccessibilityFeature"]] = relationship(
        "ActorAccessibilityFeature", back_populates="actor", cascade="all, delete-orphan"
    )
    external_refs: Mapped[list["ActorExternalRef"]] = relationship(
        "ActorExternalRef", back_populates="actor", cascade="all, delete-orphan"
    )


class RouteActor(Base):
    __tablename__ = "route_actors"
    __table_args__ = (UniqueConstraint("route_id", "actor_id", name="uq_route_actors_route_actor"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    distance_to_route_m: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    route_segment_index: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    origin_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_featured: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # The auth.users FK is migration-owned; the ORM does not model managed schemas.
    archived_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    route: Mapped["Route"] = relationship("Route", back_populates="route_actors")
    actor: Mapped["Actor"] = relationship("Actor", back_populates="route_actors")


class AccessibilityFeature(Base):
    __tablename__ = "accessibility_features"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    icon: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    actor_features: Mapped[list["ActorAccessibilityFeature"]] = relationship(
        "ActorAccessibilityFeature", back_populates="feature", cascade="all, delete-orphan"
    )


class ActorAccessibilityFeature(Base):
    __tablename__ = "actor_accessibility_features"
    __table_args__ = (
        UniqueConstraint("actor_id", "feature_id", name="uq_actor_accessibility_actor_feature"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accessibility_features.id", ondelete="CASCADE"),
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        VARCHAR(50), default="self_declared", nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    actor: Mapped["Actor"] = relationship("Actor", back_populates="accessibility_features")
    feature: Mapped["AccessibilityFeature"] = relationship(
        "AccessibilityFeature", back_populates="actor_features"
    )


# -----------------------------------------------------------------------------
# ECO-0203: Alertas e Mídia
# -----------------------------------------------------------------------------


class RouteAlert(Base):
    __tablename__ = "route_alerts"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')", name="chk_route_alerts_severity"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    severity: Mapped[str] = mapped_column(VARCHAR(50), default="info", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    source: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    route: Mapped["Route"] = relationship("Route", back_populates="alerts")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    mime_type: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    credit: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    license_code: Mapped[str | None] = mapped_column(VARCHAR(40), nullable=True)
    processing_status: Mapped[str] = mapped_column(VARCHAR(20), default="pending", nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    width_px: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    height_px: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    derivatives: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    location: Mapped[Any | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sort_order: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


# -----------------------------------------------------------------------------
# ECO-0204: Proveniência e Ingestão
# -----------------------------------------------------------------------------


class ExternalSource(Base):
    __tablename__ = "external_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    external_refs: Mapped[list["ActorExternalRef"]] = relationship(
        "ActorExternalRef", back_populates="source", cascade="all, delete-orphan"
    )


class ActorExternalRef(Base):
    __tablename__ = "actor_external_refs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_actor_external_refs_source_extid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    status_ref: Mapped[str] = mapped_column(VARCHAR(20), default="active", nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    actor: Mapped["Actor"] = relationship("Actor", back_populates="external_refs")
    source: Mapped["ExternalSource"] = relationship(
        "ExternalSource", back_populates="external_refs"
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_sources.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(VARCHAR(50), default="pending", nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_log: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    estimated_cost: Mapped[float] = mapped_column(NUMERIC(10, 4), default=0.0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class RawSourceRecord(Base):
    __tablename__ = "raw_source_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    payload_hash_sha256: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    license_terms: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class ReconciliationCandidate(Base):
    __tablename__ = "reconciliation_candidates"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1", name="chk_reconciliation_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id_a: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    actor_id_b: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(NUMERIC(5, 4), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(50), default="pending", nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class FieldProvenance(Base):
    __tablename__ = "field_provenance"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_field_confidence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_table: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_sources.id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(NUMERIC(5, 4), default=1.0, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


# -----------------------------------------------------------------------------
# ECO-0205: Usuário, Preferências e Favoritos
# -----------------------------------------------------------------------------


class Profile(Base):
    __tablename__ = "profiles"

    # The auth.users FK is migration-owned. The ORM must not model or create objects
    # inside Supabase's managed auth schema.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    location: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(VARCHAR(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    preferences: Mapped[Optional["UserPreference"]] = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    favorite_routes: Mapped[list["FavoriteRoute"]] = relationship(
        "FavoriteRoute", back_populates="user", cascade="all, delete-orphan"
    )
    favorite_actors: Mapped[list["FavoriteActor"]] = relationship(
        "FavoriteActor", back_populates="user", cascade="all, delete-orphan"
    )
    trips: Mapped[list["Trip"]] = relationship(
        "Trip", back_populates="user", cascade="all, delete-orphan"
    )


class DeletedUserTombstone(Base):
    """Private marker that survives deletion of the managed Auth identity."""

    __tablename__ = "deleted_user_tombstones"
    __table_args__ = {"schema": "app_private"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(VARCHAR(20), default="processing", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoutingMonthlyUsage(Base):
    """Shared atomic monthly usage counter across workers/instances (ADR 0013)."""

    __tablename__ = "routing_monthly_usage"
    __table_args__ = {"schema": "app_private"}

    year_month: Mapped[str] = mapped_column(VARCHAR(7), primary_key=True)
    call_count: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    active_region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )
    screen_reader_mode: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    high_contrast: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    text_scale: Mapped[float] = mapped_column(NUMERIC(3, 2), default=1.0, nullable=False)
    locale: Mapped[str] = mapped_column(VARCHAR(10), default="pt-BR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    user: Mapped["Profile"] = relationship("Profile", back_populates="preferences")


class FavoriteRoute(Base):
    __tablename__ = "favorite_routes"
    __table_args__ = (
        UniqueConstraint("user_id", "route_id", name="uq_favorite_routes_user_route"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    user: Mapped["Profile"] = relationship("Profile", back_populates="favorite_routes")
    route: Mapped["Route"] = relationship("Route")


class FavoriteActor(Base):
    __tablename__ = "favorite_actors"
    __table_args__ = (
        UniqueConstraint("user_id", "actor_id", name="uq_favorite_actors_user_actor"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    user: Mapped["Profile"] = relationship("Profile", back_populates="favorite_actors")
    actor: Mapped["Actor"] = relationship("Actor")


# -----------------------------------------------------------------------------
# ECO-0206: Viagens e Visitas
# -----------------------------------------------------------------------------


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(50), default="in_progress", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    user: Mapped["Profile"] = relationship("Profile", back_populates="trips")
    route: Mapped["Route"] = relationship("Route")
    visits: Mapped[list["TripActorVisit"]] = relationship(
        "TripActorVisit", back_populates="trip", cascade="all, delete-orphan"
    )


class TripActorVisit(Base):
    __tablename__ = "trip_actor_visits"
    __table_args__ = (
        UniqueConstraint("trip_id", "actor_id", name="uq_trip_actor_visits_trip_actor"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False
    )
    visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    confirmation_method: Mapped[str | None] = mapped_column(
        VARCHAR(50), default="manual", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="visits")
    actor: Mapped["Actor"] = relationship("Actor")


# -----------------------------------------------------------------------------
# ECO-1403: Editorial RBAC, workflow and audit trail
# -----------------------------------------------------------------------------


class EditorialRoleCapability(Base):
    __tablename__ = "editorial_role_capabilities"

    role: Mapped[str] = mapped_column(VARCHAR(20), primary_key=True)
    capability: Mapped[str] = mapped_column(VARCHAR(80), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class EditorialMembership(Base):
    __tablename__ = "editorial_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    scope_type: Mapped[str] = mapped_column(VARCHAR(20), default="global", nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(TEXT, nullable=True)


class EditorialInvitation(Base):
    __tablename__ = "editorial_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_hash: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    token_hash: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    scope_type: Mapped[str] = mapped_column(VARCHAR(20), default="global", nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(20), default="pending", nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class EditorialResourceState(Base):
    __tablename__ = "editorial_resource_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(20), default="draft", nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    version: Mapped[int] = mapped_column(INTEGER, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(VARCHAR(40), nullable=False)
    resource_type: Mapped[str] = mapped_column(VARCHAR(40), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    reason: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
