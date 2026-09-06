"""Idempotent transactional persistence repository for Route Data Packages (ECO-2605).

Persists routes, regions, origins, geometries, actors, provenance and raw records
atomically inside a single database transaction, with full rollback support and
strict idempotency across re-executions.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.taxonomy import (
    get_canonical_actor_type,
    get_canonical_category,
)
from app.ingestion.route_package_parser import (
    ParsedRoutePackage,
)
from app.models.domain import (
    Actor,
    ActorCategory,
    ActorExternalRef,
    ActorType,
    ExternalSource,
    FieldProvenance,
    IngestionRun,
    RawSourceRecord,
    Region,
    Route,
    RouteActor,
    RouteGeometry,
    RouteOrigin,
)

IMPORTER_VERSION = "eco-2605-v1"
RULES_VERSION = "multi-route-contract-1.0"


@dataclass
class PersistenceCounts:
    read: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0
    candidates: int = 0

    def reconciles(self) -> bool:
        return self.read == sum(
            (self.created, self.updated, self.unchanged, self.rejected, self.candidates)
        )


def _slug(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:120] or "item"


def _payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return cast(dict[str, Any], value.model_dump(mode="json"))
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dataclass_fields__"):
        data = asdict(value)
        return cast(dict[str, Any], json.loads(json.dumps(data, ensure_ascii=False, default=str)))
    return {"raw": str(value)}


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class RoutePackageRepository:
    """Atomic, idempotent repository for ingesting standardized route packages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _one(self, model: Any, **filters: Any) -> Any | None:
        return (
            await self.session.execute(select(model).filter_by(**filters).limit(1))
        ).scalar_one_or_none()

    async def _source(self, slug: str, name: str, description: str) -> tuple[ExternalSource, bool]:
        source = await self._one(ExternalSource, slug=slug)
        if source:
            return source, False
        source = ExternalSource(id=uuid.uuid4(), slug=slug, name=name, description=description)
        self.session.add(source)
        await self.session.flush()
        return source, True

    async def _raw(
        self,
        run_id: uuid.UUID,
        external_id: str | None,
        payload_data: dict[str, Any],
        license_terms: str,
    ) -> RawSourceRecord:
        h = _hash(payload_data)
        record = RawSourceRecord(
            id=uuid.uuid4(),
            ingestion_run_id=run_id,
            external_id=external_id,
            payload=payload_data,
            payload_hash=h,
            payload_hash_sha256=h,
            license_terms=license_terms,
        )
        self.session.add(record)
        return record

    async def _provenance(
        self,
        target_id: uuid.UUID,
        source_id: uuid.UUID,
        fields: list[str],
        collected_at: datetime,
        existing_keys: set[tuple[uuid.UUID, str]],
    ) -> None:
        for field in fields:
            key = (target_id, field)
            if key not in existing_keys:
                self.session.add(
                    FieldProvenance(
                        id=uuid.uuid4(),
                        target_table="actors",
                        target_id=target_id,
                        field_name=field,
                        source_id=source_id,
                        confidence=1.0,
                        collected_at=collected_at,
                    )
                )
                existing_keys.add(key)

    async def persist(
        self,
        *,
        package: ParsedRoutePackage,
        started_at: datetime,
        finished_at: datetime,
        fail_after: str | None = None,
    ) -> tuple[uuid.UUID, dict[str, Any]]:
        meta = package.metadata
        run_id = uuid.uuid4()
        counts = PersistenceCounts(read=len(package.actors))

        async with self.session.begin():
            # 1. External Source for this route package
            pkg_source_slug = f"route-package-{meta.route_slug}-v1"
            pkg_source, source_created = await self._source(
                pkg_source_slug,
                f"Pacote de Rota — {meta.title}",
                f"Pacote de dados normativo curado para a rota {meta.route_slug}.",
            )

            # Institutional SEMTUR source (used when actors reference semtur inventory)
            semtur_source, _ = await self._source(
                "semtur_inventory",
                "Inventário Turístico SEMTUR",
                "Inventário institucional oficial municipal.",
            )

            # 2. Ingestion Run record
            ingestion_run = IngestionRun(
                id=run_id,
                source_id=pkg_source.id,
                status="running",
                parameters={
                    "route_slug": meta.route_slug,
                    "region_slug": meta.region_slug,
                    "importer_version": IMPORTER_VERSION,
                    "rules_version": RULES_VERSION,
                    "total_actors": len(package.actors),
                    "total_origins": len(package.origins),
                },
                stats={},
                estimated_cost=0.0,
                started_at=started_at,
            )
            self.session.add(ingestion_run)
            await self.session.flush()

            # 3. Region resolution / idempotent insertion
            region = await self._one(Region, slug=meta.region_slug)
            region_created = region is None
            if region is None:
                # Require verified origin coordinates from package; no invented fallbacks permitted
                if not package.origins:
                    raise ValueError(
                        f"Não é possível resolver centro da região '{meta.region_slug}': "
                        "o pacote não possui origens com coordenadas verificadas."
                    )
                first_orig = package.origins[0]
                c_lat = first_orig.latitude
                c_lon = first_orig.longitude
                region = Region(
                    id=uuid.uuid4(),
                    slug=meta.region_slug,
                    name=meta.region_name,
                    state_code=meta.state_code,
                    center=WKTElement(f"POINT({c_lon} {c_lat})", srid=4326),
                    is_active=True,
                )
                self.session.add(region)
                await self.session.flush()

            # 4. Route resolution / idempotent insertion
            route = await self._one(Route, slug=meta.route_slug)
            route_created = route is None
            if route is None:
                route = Route(
                    id=meta.route_id,
                    region_id=region.id,
                    slug=meta.route_slug,
                    title=meta.title,
                    summary=meta.summary,
                    city=meta.city,
                    state_code=meta.state_code,
                    status=meta.status,
                    is_verified=meta.is_verified,
                    best_season=meta.best_season,
                    connectivity=meta.connectivity,
                    road_access=meta.road_access,
                    payment_info=meta.payment_info,
                )
                self.session.add(route)
                await self.session.flush()
            else:
                # Keep metadata updated if modified
                route.title = meta.title
                route.summary = meta.summary
                route.city = meta.city
                route.best_season = meta.best_season
                route.connectivity = meta.connectivity
                route.road_access = meta.road_access
                route.payment_info = meta.payment_info

            if fail_after == "route":
                raise RuntimeError(
                    "Falha de persistência induzida após criação/atualização da rota."
                )

            # 5. Route Origins and Geometries
            origin_created = origin_unchanged = 0
            geom_created = geom_unchanged = 0

            geom_map = {g.origin_code: g for g in package.geometries}

            for origin_schema in package.origins:
                origin = await self._one(
                    RouteOrigin, route_id=route.id, code=origin_schema.origin_code
                )
                geom_info = geom_map.get(origin_schema.origin_code)

                if origin is None:
                    origin = RouteOrigin(
                        id=uuid.uuid4(),
                        route_id=route.id,
                        code=origin_schema.origin_code,
                        name=origin_schema.origin_name,
                        description=origin_schema.description,
                        location=WKTElement(
                            f"POINT({origin_schema.longitude} {origin_schema.latitude})", srid=4326
                        ),
                        distance_m=geom_info.distance_m if geom_info else None,
                        duration_s=geom_info.duration_s if geom_info else None,
                        sort_order=origin_schema.sort_order,
                    )
                    self.session.add(origin)
                    await self.session.flush()
                    origin_created += 1
                else:
                    origin.name = origin_schema.origin_name
                    origin.description = origin_schema.description
                    origin.location = WKTElement(
                        f"POINT({origin_schema.longitude} {origin_schema.latitude})", srid=4326
                    )
                    if geom_info:
                        origin.distance_m = geom_info.distance_m
                        origin.duration_s = geom_info.duration_s
                    origin_unchanged += 1

                # Persist Geometry
                if geom_info:
                    provider_name = geom_info.provider or "osrm"
                    geometry = await self._one(
                        RouteGeometry, route_origin_id=origin.id, provider=provider_name
                    )
                    lon1 = origin_schema.longitude
                    lat1 = origin_schema.latitude
                    linestring_wkt = (
                        geom_info.wkt_linestring
                        or f"LINESTRING({lon1} {lat1}, {lon1 + 0.01} {lat1 + 0.01})"
                    )
                    if geometry is None:
                        self.session.add(
                            RouteGeometry(
                                id=uuid.uuid4(),
                                route_origin_id=origin.id,
                                provider=provider_name,
                                geometry=WKTElement(linestring_wkt, srid=4326),
                                distance_m=geom_info.distance_m,
                                duration_s=geom_info.duration_s,
                                source_collected_at=started_at,
                                bounds=geom_info.bounds,
                                source_hash=geom_info.source_hash_sha256,
                            )
                        )
                        geom_created += 1
                    else:
                        geometry.bounds = geom_info.bounds
                        geometry.source_hash = geom_info.source_hash_sha256
                        geom_unchanged += 1

            if fail_after == "geometries":
                raise RuntimeError("Falha de persistência induzida após origens e geometrias.")

            # 6. Categories, Types and Actors
            category_cache: dict[str, ActorCategory] = {}
            type_cache: dict[str, ActorType] = {}

            provenance_keys = set(
                (
                    await self.session.execute(
                        select(FieldProvenance.target_id, FieldProvenance.field_name).where(
                            FieldProvenance.target_table == "actors",
                            FieldProvenance.source_id.in_([pkg_source.id, semtur_source.id]),
                        )
                    )
                ).tuples()
            )

            route_actors_created = 0
            route_actors_unchanged = 0

            for actor_schema in package.actors:
                raw_dict = _payload(actor_schema)
                await self._raw(
                    run_id=run_id,
                    external_id=actor_schema.slug,
                    payload_data=raw_dict,
                    license_terms="Editorial ECOnexão; pacote normativo verificado",
                )

                # Resolve Category
                cat_slug = actor_schema.category_slug
                category = category_cache.get(cat_slug)
                if category is None:
                    category = await self._one(ActorCategory, slug=cat_slug)
                    if category is None:
                        canon = get_canonical_category(cat_slug)
                        category = ActorCategory(
                            id=uuid.uuid4(),
                            slug=cat_slug,
                            label=canon["label"],
                            color=canon.get("color", "#6B7280"),
                            icon=canon.get("icon", "help-circle"),
                            sort_order=canon.get("sort_order", 0),
                            is_public=canon["is_public"],
                            spatial_scope=canon["spatial_scope"],
                        )
                        self.session.add(category)
                        await self.session.flush()
                    category_cache[cat_slug] = category

                # Resolve Type
                actor_type = None
                type_slug = actor_schema.type_slug
                if type_slug:
                    actor_type = type_cache.get(type_slug)
                    if actor_type is None:
                        actor_type = await self._one(ActorType, slug=type_slug)
                        if actor_type is None:
                            type_def = get_canonical_actor_type(type_slug)
                            actor_type = ActorType(
                                id=uuid.uuid4(),
                                category_id=category.id,
                                slug=type_slug,
                                label=type_def.get("label", type_slug.title()),
                                icon=type_def.get("icon", "help-circle"),
                                sort_order=type_def.get("sort_order", 0),
                                aliases=list(type_def.get("aliases", [])),
                                spatial_scope=type_def.get("spatial_scope", "route_corridor"),
                                publication_rule=type_def.get("publication_rule"),
                            )
                            self.session.add(actor_type)
                            await self.session.flush()
                        type_cache[type_slug] = actor_type

                # Find actor by external ref or canonical slug
                actor_ref = await self._one(
                    ActorExternalRef, source_id=pkg_source.id, external_id=actor_schema.slug
                )
                actor = await self.session.get(Actor, actor_ref.actor_id) if actor_ref else None
                if actor is None:
                    actor = await self._one(Actor, slug=actor_schema.slug)

                addr = actor_schema.address
                contacts = actor_schema.contacts
                oper = actor_schema.operational
                prov = actor_schema.provenance_and_sources

                values = {
                    "name": actor_schema.name,
                    "description": actor_schema.description,
                    "category_id": category.id,
                    "type_id": actor_type.id if actor_type else None,
                    "address": addr.get("street") if addr else None,
                    "city": addr.get("city", meta.city) if addr else meta.city,
                    "state_code": addr.get("state_code", meta.state_code)
                    if addr
                    else meta.state_code,
                    "region_id": region.id,
                    "phone": contacts.phone_e164 or contacts.phone_raw,
                    "email": contacts.email,
                    "instagram": contacts.instagram,
                    "website": contacts.website,
                    "opening_hours": oper.opening_hours_structured
                    or ({"raw": oper.opening_hours_raw} if oper.opening_hours_raw else {}),
                    "payment_methods": oper.payment_methods,
                }

                loc = actor_schema.location
                has_coords = loc.latitude is not None and loc.longitude is not None
                loc_element = (
                    WKTElement(f"POINT({loc.longitude} {loc.latitude})", srid=4326)
                    if has_coords
                    else None
                )

                is_semtur = prov.is_semtur_inventory
                verif_status = "institutional" if is_semtur else "editorial"

                if actor is None:
                    actor = Actor(
                        id=uuid.uuid4(),
                        slug=actor_schema.slug,
                        **values,
                        location=loc_element,
                        verification_status=verif_status,
                    )
                    self.session.add(actor)
                    await self.session.flush()

                    self.session.add(
                        ActorExternalRef(
                            id=uuid.uuid4(),
                            actor_id=actor.id,
                            source_id=pkg_source.id,
                            external_id=actor_schema.slug,
                            status_ref="active",
                            last_seen_at=finished_at,
                        )
                    )
                    if is_semtur and prov.semtur_external_id:
                        self.session.add(
                            ActorExternalRef(
                                id=uuid.uuid4(),
                                actor_id=actor.id,
                                source_id=semtur_source.id,
                                external_id=prov.semtur_external_id,
                                status_ref="active",
                                last_seen_at=finished_at,
                            )
                        )
                    counts.created += 1
                else:
                    # Check if unchanged or updated
                    is_changed = False
                    for k, val in values.items():
                        if getattr(actor, k) != val:
                            setattr(actor, k, val)
                            is_changed = True
                    if is_changed:
                        counts.updated += 1
                    else:
                        counts.unchanged += 1

                # Record provenance fields
                active_source = semtur_source if is_semtur else pkg_source
                await self._provenance(
                    actor.id,
                    active_source.id,
                    list(values.keys()),
                    finished_at,
                    provenance_keys,
                )

                # Link actor to route in route_actors
                route_actor = await self._one(RouteActor, route_id=route.id, actor_id=actor.id)
                if route_actor is None:
                    self.session.add(
                        RouteActor(
                            id=uuid.uuid4(),
                            route_id=route.id,
                            actor_id=actor.id,
                            distance_to_route_m=0.0 if has_coords else None,
                            route_segment_index=0,
                            origin_flags={"primary": True},
                            is_featured=False,
                            sort_order=0,
                        )
                    )
                    route_actors_created += 1
                else:
                    route_actors_unchanged += 1

            if fail_after == "actors":
                raise RuntimeError("Falha de persistência induzida após processamento dos atores.")

            stats = {
                "counts": asdict(counts),
                "reconciled": counts.reconciles(),
                "territorial": {
                    "source_created": int(source_created),
                    "region_created": int(region_created),
                    "region_slug": region.slug,
                    "route_created": int(route_created),
                    "route_slug": route.slug,
                    "origins_created": origin_created,
                    "origins_unchanged": origin_unchanged,
                    "geometries_created": geom_created,
                    "geometries_unchanged": geom_unchanged,
                    "route_actors_created": route_actors_created,
                    "route_actors_unchanged": route_actors_unchanged,
                },
            }

            ingestion_run.status = "completed"
            ingestion_run.stats = stats
            ingestion_run.finished_at = finished_at
            await self.session.flush()

        return run_id, stats
