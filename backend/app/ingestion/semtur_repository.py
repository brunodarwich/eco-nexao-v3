"""Idempotent persistence and provenance for SEMTUR inventory ingestion (ECO-2505)."""

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
from app.ingestion.semtur_importer import SEMTURRecord
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
)

IMPORTER_VERSION = "eco-2505-v1"
RULES_VERSION = "semtur-contract-1.0"


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
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:120] or "ator"


def _payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    data = asdict(value)
    return cast(dict[str, Any], json.loads(json.dumps(data, ensure_ascii=False, default=str)))


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class SEMTURPersistenceRepository:
    """Persist the SEMTUR snapshot atomically and leave unchanged content untouched."""

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
        raw_payload: dict[str, Any],
        payload_hash_sha256: str,
        license_terms: str,
    ) -> RawSourceRecord:
        record = RawSourceRecord(
            id=uuid.uuid4(),
            ingestion_run_id=run_id,
            external_id=external_id,
            payload=raw_payload,
            payload_hash=payload_hash_sha256,
            payload_hash_sha256=payload_hash_sha256,
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
        report: dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        semtur_records: list[SEMTURRecord],
        fail_after: str | None = None,
    ) -> tuple[uuid.UUID, dict[str, Any]]:
        run_id = uuid.uuid4()
        counts = PersistenceCounts(read=len(semtur_records))

        async with self.session.begin():
            semtur_source, source_created = await self._source(
                "semtur_inventory",
                "Inventário Turístico SEMTUR Santarém",
                "Inventário oficial da Secretaria Municipal de Turismo de Santarém.",
            )

            ingestion_run = IngestionRun(
                id=run_id,
                source_id=semtur_source.id,
                status="running",
                parameters={
                    "snapshot_version": "semtur-inventory-v1",
                    "importer_version": IMPORTER_VERSION,
                    "rules_version": RULES_VERSION,
                    "total_records": len(semtur_records),
                },
                stats={},
                estimated_cost=0.0,
                started_at=started_at,
            )
            self.session.add(ingestion_run)
            await self.session.flush()

            region = await self._one(Region, slug="santarem-belterra")
            region_created = region is None
            if region is None:
                region = Region(
                    id=uuid.uuid4(),
                    slug="santarem-belterra",
                    name="Santarém e Belterra",
                    state_code="PA",
                    center=WKTElement("POINT(-54.978506 -2.558521)", srid=4326),
                    is_active=True,
                )
                self.session.add(region)
                await self.session.flush()

            if fail_after == "source":
                raise RuntimeError("Falha de persistência induzida após external_source.")

            category_cache: dict[str, ActorCategory] = {}
            type_cache: dict[str, ActorType] = {}

            provenance_keys = set(
                (
                    await self.session.execute(
                        select(FieldProvenance.target_id, FieldProvenance.field_name).where(
                            FieldProvenance.target_table == "actors",
                            FieldProvenance.source_id == semtur_source.id,
                        )
                    )
                ).tuples()
            )

            for record in semtur_records:
                # Always persist raw record with SHA-256 hash
                await self._raw(
                    run_id=run_id,
                    external_id=record.external_id,
                    raw_payload=record.raw_payload,
                    payload_hash_sha256=record.payload_hash_sha256,
                    license_terms=(
                        "SEMTUR; inventário turístico oficial de Santarém (uso institucional)"
                    ),
                )

                if not record.is_valid:
                    counts.rejected += 1
                    continue

                # Resolve Category
                category = category_cache.get(record.categoria_slug)
                if category is None:
                    category = await self._one(ActorCategory, slug=record.categoria_slug)
                    if category is None:
                        canon = get_canonical_category(record.categoria_slug)
                        category = ActorCategory(
                            id=uuid.uuid4(),
                            slug=record.categoria_slug,
                            label=canon["label"],
                            color=canon.get("color"),
                            icon=canon.get("icon"),
                            sort_order=canon.get("sort_order", 0),
                            is_public=canon["is_public"],
                            spatial_scope=canon["spatial_scope"],
                        )
                        self.session.add(category)
                        await self.session.flush()
                    category_cache[record.categoria_slug] = category

                # Resolve Actor Type
                actor_type = type_cache.get(record.tipo_slug)
                if actor_type is None:
                    actor_type = await self._one(ActorType, slug=record.tipo_slug)
                    if actor_type is None:
                        type_def = get_canonical_actor_type(record.tipo_slug)
                        actor_type = ActorType(
                            id=uuid.uuid4(),
                            category_id=category.id,
                            slug=record.tipo_slug,
                            label=type_def["label"],
                            icon=type_def["icon"],
                            sort_order=type_def.get("sort_order", 0),
                            aliases=list(type_def.get("aliases", [])),
                            spatial_scope=type_def.get("spatial_scope", "route_corridor"),
                            publication_rule=type_def.get("publication_rule"),
                        )
                        self.session.add(actor_type)
                        await self.session.flush()
                    type_cache[record.tipo_slug] = actor_type

                # Check external reference
                ref = await self._one(
                    ActorExternalRef, source_id=semtur_source.id, external_id=record.external_id
                )
                actor = await self.session.get(Actor, ref.actor_id) if ref else None

                values = {
                    "name": record.titulo,
                    "category_id": category.id,
                    "type_id": actor_type.id if actor_type else None,
                    "sub_category": record.categoria_raw,
                    "address": record.endereco,
                    "city": "Santarém",
                    "state_code": "PA",
                    "region_id": region.id,
                    "phone": record.telefone,
                    "email": record.email,
                    "instagram": record.instagram,
                    "website": record.website,
                    "opening_hours": {"raw": record.funcionamento} if record.funcionamento else {},
                    "payment_methods": [record.forma_pagamento] if record.forma_pagamento else [],
                }

                if actor is None:
                    actor = Actor(
                        id=uuid.uuid4(),
                        slug=f"semtur-{_slug(record.external_id)}",
                        **values,
                        location=(
                            WKTElement(f"POINT({record.longitude} {record.latitude})", srid=4326)
                            if record.latitude is not None and record.longitude is not None
                            else None
                        ),
                        verification_status="institutional",
                    )
                    self.session.add(actor)
                    await self.session.flush()
                    self.session.add(
                        ActorExternalRef(
                            id=uuid.uuid4(),
                            actor_id=actor.id,
                            source_id=semtur_source.id,
                            external_id=record.external_id,
                            status_ref="active",
                            last_seen_at=finished_at,
                        )
                    )
                    counts.created += 1
                elif all(getattr(actor, key) == value for key, value in values.items()):
                    if ref is not None:
                        ref.last_seen_at = finished_at
                        ref.status_ref = "active"
                    counts.unchanged += 1
                else:
                    for key, value in values.items():
                        setattr(actor, key, value)
                    if ref is not None:
                        ref.last_seen_at = finished_at
                        ref.status_ref = "active"
                    counts.updated += 1

                await self._provenance(
                    actor.id,
                    semtur_source.id,
                    list(values),
                    finished_at,
                    provenance_keys,
                )

            if fail_after == "actors":
                raise RuntimeError("Falha de persistência induzida para teste de rollback.")

            stats = {
                "reconciliation": {
                    **asdict(counts),
                    "reconciled": counts.reconciles(),
                },
                "territorial": {
                    "source_slug": semtur_source.slug,
                    "source_created": int(source_created),
                    "region_created": int(region_created),
                    "total_raw_records": len(semtur_records),
                    "total_actors_with_location": sum(
                        1
                        for r in semtur_records
                        if r.is_valid and r.latitude is not None and r.longitude is not None
                    ),
                    "total_actors_without_location": sum(
                        1
                        for r in semtur_records
                        if r.is_valid and (r.latitude is None or r.longitude is None)
                    ),
                },
            }
            ingestion_run.status = "completed"
            ingestion_run.stats = stats
            ingestion_run.finished_at = finished_at
            await self.session.flush()

        return run_id, stats
