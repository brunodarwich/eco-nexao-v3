"""Idempotent persistence and provenance for the Pindobal snapshot."""

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.google_snapshot_importer import GooglePOIRecord
from app.ingestion.osrm_importer import OSRMRouteResult
from app.ingestion.pindobal_cutout_importer import PindobalCutoutRecord
from app.ingestion.reconciler import MatchResult
from app.ingestion.semtur_importer import SEMTURRecord
from app.models.domain import (
    Actor,
    ActorCategory,
    ActorExternalRef,
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

SPATIAL_ASSOCIATION_THRESHOLD_M = 1000.0

IMPORTER_VERSION = "eco-1502-v1"
RULES_VERSION = "pindobal-contract-1.0"


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
    data = asdict(value)
    return cast(dict[str, Any], json.loads(json.dumps(data, ensure_ascii=False, default=str)))


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class PindobalPersistenceRepository:
    """Persist the snapshot atomically and leave unchanged content untouched."""

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
        self, run_id: uuid.UUID, external_id: str | None, value: Any, license_terms: str
    ) -> None:
        payload = _payload(value)
        self.session.add(
            RawSourceRecord(
                id=uuid.uuid4(),
                ingestion_run_id=run_id,
                external_id=external_id,
                payload=payload,
                payload_hash=_hash(payload),
                license_terms=license_terms,
            )
        )

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
        osrm_results: dict[str, OSRMRouteResult],
        started_at: datetime,
        finished_at: datetime,
        semtur_records: list[SEMTURRecord] | None = None,
        google_records: list[GooglePOIRecord] | None = None,
        cutout_records: list[PindobalCutoutRecord] | None = None,
        matches: list[MatchResult] | None = None,
        fail_after: str | None = None,
    ) -> tuple[uuid.UUID, dict[str, Any]]:
        semtur_records = semtur_records or []
        google_records = google_records or []
        cutout_records = cutout_records or []
        matches = matches or []
        run_id = uuid.uuid4()
        counts = PersistenceCounts(
            read=len(semtur_records) + len(google_records) + len(cutout_records)
        )

        async with self.session.begin():
            snapshot, snapshot_created = await self._source(
                "pindobal-snapshot-v1",
                "Snapshot Pindobal v1",
                "Snapshot local verificado pelo manifesto canônico.",
            )
            semtur_source, _ = await self._source(
                "semtur-santarem-v1",
                "Inventário SEMTUR Santarém",
                "Fonte institucional SEMTUR do snapshot Pindobal.",
            )
            google_source, _ = await self._source(
                "google-places-legacy-pindobal-v1",
                "Google Places legado — Pindobal",
                "Snapshot legado sem Place IDs; não é chave confiável para merge.",
            )
            ingestion_run = IngestionRun(
                id=run_id,
                source_id=snapshot.id,
                status="running",
                parameters={
                    "snapshot_version": "pindobal-v1",
                    "importer_version": IMPORTER_VERSION,
                    "rules_version": RULES_VERSION,
                    "manifest_valid_files": report["manifest"]["valid_files"],
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

            route = await self._one(Route, slug="rota-pindobal")
            route_created = route is None
            if route is None:
                route = Route(
                    id=uuid.uuid4(),
                    region_id=region.id,
                    slug="rota-pindobal",
                    title="Rota Pindobal",
                    summary="Rota territorial entre Santarém, Belterra e Pindobal.",
                    city="Belterra",
                    state_code="PA",
                    status="active",
                    is_verified=False,
                )
                self.session.add(route)
                await self.session.flush()
            if fail_after == "route":
                raise RuntimeError("Falha de persistência induzida para teste de rollback.")

            origin_created = geometry_created = 0
            origin_unchanged = geometry_unchanged = 0
            for sort_order, code in enumerate(("porto", "aeroporto", "rodoviaria"), start=1):
                result = osrm_results[code]
                filename = {
                    "porto": "rota_porto_OSRM_01.csv",
                    "aeroporto": "rota_aeroporto_OSRM_01.csv",
                    "rodoviaria": "rota_rodoviaria_OSRM_01.csv",
                }[code]
                source_hash = next(
                    item["sha256"]
                    for item in report["manifest"]["files"]
                    if item["name"] == filename
                )
                origin = await self._one(RouteOrigin, route_id=route.id, code=code)
                if origin is None:
                    origin = RouteOrigin(
                        id=uuid.uuid4(),
                        route_id=route.id,
                        code=code,
                        name=result.origin_name,
                        location=WKTElement(result.wkt_start_point, srid=4326),
                        distance_m=result.distance_m,
                        sort_order=sort_order,
                    )
                    self.session.add(origin)
                    await self.session.flush()
                    origin_created += 1
                else:
                    origin_unchanged += 1
                geometry = await self._one(
                    RouteGeometry, route_origin_id=origin.id, provider="osrm-snapshot"
                )
                if geometry is None:
                    self.session.add(
                        RouteGeometry(
                            id=uuid.uuid4(),
                            route_origin_id=origin.id,
                            provider="osrm-snapshot",
                            geometry=WKTElement(result.wkt_linestring, srid=4326),
                            distance_m=result.distance_m,
                            source_collected_at=started_at,
                            bounds=result.bounds,
                            source_hash=source_hash,
                        )
                    )
                    geometry_created += 1
                else:
                    if geometry.bounds != result.bounds or geometry.source_hash != source_hash:
                        geometry.bounds = result.bounds
                        geometry.source_hash = source_hash
                    geometry_unchanged += 1

            category_cache: dict[str, ActorCategory] = {}
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
                await self._raw(
                    run_id, record.external_id, record, "SEMTUR; uso interno controlado"
                )
                if not record.is_valid:
                    counts.rejected += 1
                    continue
                category = category_cache.get(record.categoria_slug)
                if category is None:
                    category = await self._one(ActorCategory, slug=record.categoria_slug)
                    if category is None:
                        category = ActorCategory(
                            id=uuid.uuid4(),
                            slug=record.categoria_slug,
                            label=record.categoria_slug.replace("-", " ").title(),
                            sort_order=0,
                        )
                        self.session.add(category)
                        await self.session.flush()
                    category_cache[record.categoria_slug] = category

                ref = await self._one(
                    ActorExternalRef, source_id=semtur_source.id, external_id=record.external_id
                )
                actor = await self.session.get(Actor, ref.actor_id) if ref else None
                values = {
                    "name": record.titulo,
                    "category_id": category.id,
                    "sub_category": record.categoria_raw,
                    "address": record.endereco,
                    "city": "Santarém",
                    "state_code": "PA",
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
                            last_seen_at=finished_at,
                        )
                    )
                    counts.created += 1
                elif all(getattr(actor, key) == value for key, value in values.items()):
                    counts.unchanged += 1
                else:
                    for key, value in values.items():
                        setattr(actor, key, value)
                    counts.updated += 1
                await self._provenance(
                    actor.id,
                    semtur_source.id,
                    list(values),
                    finished_at,
                    provenance_keys,
                )

            spatial_result = await self.session.execute(
                text(
                    """
                    WITH route_line AS (
                        SELECT r.id AS route_id, g.geometry,
                               extensions.ST_NPoints(g.geometry::extensions.geometry) AS points
                        FROM app_private.routes r
                        JOIN app_private.route_origins o ON o.route_id = r.id
                        JOIN app_private.route_geometries g ON g.route_origin_id = o.id
                        WHERE r.id = :route_id AND o.code = 'porto'
                    ), metrics AS (
                        SELECT a.id AS actor_id, rl.route_id,
                               extensions.ST_Distance(a.location, rl.geometry) AS distance_m,
                               extensions.ST_LineLocatePoint(
                                   rl.geometry::extensions.geometry,
                                   a.location::extensions.geometry
                               ) AS fraction,
                               rl.points,
                               jsonb_build_object(
                                   'porto', bool_or(o.code = 'porto' AND extensions.ST_DWithin(
                                       a.location, g.geometry, :threshold)),
                                   'aeroporto', bool_or(
                                       o.code = 'aeroporto' AND extensions.ST_DWithin(
                                           a.location, g.geometry, :threshold)),
                                   'rodoviaria', bool_or(
                                       o.code = 'rodoviaria' AND extensions.ST_DWithin(
                                           a.location, g.geometry, :threshold)),
                                   'km_porto', round((extensions.ST_LineLocatePoint(
                                       rl.geometry::extensions.geometry,
                                       a.location::extensions.geometry
                                   ) * extensions.ST_Length(rl.geometry) / 1000.0)::numeric, 3)
                               ) AS flags
                        FROM app_private.actors a
                        CROSS JOIN route_line rl
                        JOIN app_private.route_origins o ON o.route_id = rl.route_id
                        JOIN app_private.route_geometries g ON g.route_origin_id = o.id
                        WHERE a.location IS NOT NULL
                          AND a.deleted_at IS NULL
                          AND extensions.ST_DWithin(a.location, rl.geometry, :threshold)
                        GROUP BY a.id, rl.route_id, rl.geometry, rl.points
                    )
                    INSERT INTO app_private.route_actors (
                        id, route_id, actor_id, distance_to_route_m,
                        route_segment_index, origin_flags
                    )
                    SELECT gen_random_uuid(), route_id, actor_id, distance_m,
                           LEAST(points - 2, floor(fraction * (points - 1))::integer), flags
                    FROM metrics
                    ON CONFLICT (route_id, actor_id) DO UPDATE SET
                        distance_to_route_m = EXCLUDED.distance_to_route_m,
                        route_segment_index = EXCLUDED.route_segment_index,
                        origin_flags = EXCLUDED.origin_flags
                    WHERE route_actors.archived_at IS NULL
                      AND (route_actors.distance_to_route_m,
                           route_actors.route_segment_index,
                           route_actors.origin_flags)
                          IS DISTINCT FROM
                          (EXCLUDED.distance_to_route_m,
                           EXCLUDED.route_segment_index,
                           EXCLUDED.origin_flags)
                    RETURNING (xmax = 0) AS inserted
                    """
                ),
                {"route_id": route.id, "threshold": SPATIAL_ASSOCIATION_THRESHOLD_M},
            )
            spatial_rows = [bool(row.inserted) for row in spatial_result.all()]

            # Google legado e recorte são preservados integralmente como raw. A ausência de
            # Place ID impede que sejam usados como chave de upsert ou merge automático.
            candidate_google_ids = {
                match.google_id for match in matches if match.match_type == "fuzzy_candidate"
            }
            for google_record in google_records:
                await self._raw(
                    run_id,
                    None,
                    google_record,
                    "Google Places snapshot legado; retenção controlada",
                )
                if not google_record.is_valid:
                    counts.rejected += 1
                elif google_record.snapshot_id in candidate_google_ids:
                    counts.candidates += 1
                else:
                    counts.unchanged += 1
            for cutout_record in cutout_records:
                await self._raw(
                    run_id,
                    cutout_record.snapshot_id,
                    cutout_record,
                    "Recorte derivado Pindobal v1",
                )
                if cutout_record.is_valid:
                    counts.unchanged += 1
                else:
                    counts.rejected += 1

            fuzzy_match_count = sum(
                1 for match in matches if match.match_type == "fuzzy_candidate"
            )
            stats = {
                "reconciliation": {
                    **asdict(counts),
                    "reconciled": counts.reconciles(),
                    "fuzzy_match_count": fuzzy_match_count,
                    "candidate_google_record_count": len(candidate_google_ids),
                    "candidate_persistence": "blocked_without_trusted_google_actor_identity",
                },
                "territorial": {
                    "sources_created": int(snapshot_created),
                    "regions_created": int(region_created),
                    "regions_unchanged": int(not region_created),
                    "routes_created": int(route_created),
                    "routes_unchanged": int(not route_created),
                    "origins_created": origin_created,
                    "origins_unchanged": origin_unchanged,
                    "geometries_created": geometry_created,
                    "geometries_unchanged": geometry_unchanged,
                    "route_actors_created": sum(spatial_rows),
                    "route_actors_updated": len(spatial_rows) - sum(spatial_rows),
                    "route_actors_total": (
                        await self.session.scalar(
                            select(func.count(RouteActor.id)).where(
                                RouteActor.route_id == route.id,
                                RouteActor.archived_at.is_(None),
                            )
                        )
                    )
                    or 0,
                },
                "raw_records": len(semtur_records) + len(google_records) + len(cutout_records),
                "external_id_missing": sum(r.external_id_missing for r in google_records),
            }
            ingestion_run.status = "completed"
            ingestion_run.stats = stats
            ingestion_run.finished_at = finished_at
            await self.session.flush()
        return run_id, stats
