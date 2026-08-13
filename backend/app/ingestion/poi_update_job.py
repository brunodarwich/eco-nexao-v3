"""Incremental POI Update Job for Google Places integration (ECO-0403)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.google_places import (
    GooglePlacesConnector,
    GooglePlacesError,
)
from app.models.domain import (
    Actor,
    ActorExternalRef,
    ExternalSource,
    IngestionRun,
    RawSourceRecord,
)

logger = logging.getLogger(__name__)


class PoiUpdateConcurrencyError(Exception):
    """Raised when an update job execution is attempted concurrently."""


@dataclass(frozen=True, slots=True)
class PoiUpdateJobReport:
    """Snapshot report summarizing execution results for a POI update job."""

    run_id: uuid.UUID
    status: str
    total_scanned: int
    updated_count: int
    failed_count: int
    skipped_count: int
    total_cost: float
    started_at: datetime
    finished_at: datetime | None
    checkpoint_timestamp: datetime | None = None
    error_message: str | None = None


class PoiUpdateJob:
    """Resilient and idempotent job updating POIs via Google Places (New)."""

    ingestion_runs: set[str] = set()
    _JOB_LOCK_KEY = "poi_update_job"

    def __init__(
        self,
        db_session: Session,
        places_connector: GooglePlacesConnector,
        *,
        max_cost_limit: float = 10.0,
        cost_per_request: float = 0.017,
        request_timeout_s: float = 10.0,
        batch_size: int = 50,
    ) -> None:
        if max_cost_limit < 0:
            raise ValueError("max_cost_limit cannot be negative")
        if cost_per_request < 0:
            raise ValueError("cost_per_request cannot be negative")
        if request_timeout_s <= 0:
            raise ValueError("request_timeout_s must be positive")

        self.db_session = db_session
        self.places_connector = places_connector
        self.max_cost_limit = max_cost_limit
        self.cost_per_request = cost_per_request
        self.request_timeout_s = request_timeout_s
        self.batch_size = batch_size

    async def run(
        self,
        *,
        checkpoint_timestamp: datetime | None = None,
        target_actor_ids: Sequence[uuid.UUID] | None = None,
    ) -> PoiUpdateJobReport:
        """Execute incremental POI update with concurrency lock, cost bounds, and checkpointing."""
        if self._JOB_LOCK_KEY in PoiUpdateJob.ingestion_runs:
            raise PoiUpdateConcurrencyError("POI update job is already running")

        PoiUpdateJob.ingestion_runs.add(self._JOB_LOCK_KEY)
        started_at = datetime.now(UTC)
        source = self._get_or_create_external_source()

        run_record = IngestionRun(
            source_id=source.id,
            status="running",
            parameters={
                "max_cost_limit": self.max_cost_limit,
                "cost_per_request": self.cost_per_request,
                "request_timeout_s": self.request_timeout_s,
                "checkpoint_timestamp": (
                    checkpoint_timestamp.isoformat() if checkpoint_timestamp else None
                ),
            },
            stats={
                "total_scanned": 0,
                "updated": 0,
                "failed": 0,
                "skipped": 0,
            },
            estimated_cost=0.0,
            started_at=started_at,
        )
        self.db_session.add(run_record)
        self.db_session.commit()
        self.db_session.refresh(run_record)

        total_scanned = 0
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        current_cost = 0.0
        final_status = "completed"
        error_msg: str | None = None

        try:
            query = (
                select(ActorExternalRef, Actor)
                .join(Actor, ActorExternalRef.actor_id == Actor.id)
                .where(ActorExternalRef.source_id == source.id)
            )

            if checkpoint_timestamp:
                query = query.where(
                    (ActorExternalRef.last_seen_at < checkpoint_timestamp)
                    | (ActorExternalRef.last_seen_at.is_(None))
                )

            if target_actor_ids:
                query = query.where(Actor.id.in_(target_actor_ids))

            query = query.order_by(
                ActorExternalRef.last_seen_at.asc().nulls_first(),
                ActorExternalRef.created_at.asc(),
            )

            results = self.db_session.execute(query).all()
            refs_to_update = [(ref, actor) for ref, actor in results]
            total_scanned = len(refs_to_update)

            for ref, actor in refs_to_update:
                if current_cost + self.cost_per_request > self.max_cost_limit:
                    logger.warning(
                        "Max cost limit reached (%s / %s). Stopping POI update run early.",
                        current_cost,
                        self.max_cost_limit,
                    )
                    final_status = "partial"
                    skipped_count = total_scanned - (updated_count + failed_count)
                    break

                try:
                    payload = await asyncio.wait_for(
                        self.places_connector.place_details(
                            ref.external_id,
                            fields=(
                                "id",
                                "nationalPhoneNumber",
                                "internationalPhoneNumber",
                                "websiteUri",
                                "rating",
                                "userRatingCount",
                                "regularOpeningHours",
                            ),
                        ),
                        timeout=self.request_timeout_s,
                    )
                    payload_dict = dict(payload)
                    self._update_actor_from_payload(actor, payload_dict)

                    now = datetime.now(UTC)
                    ref.last_seen_at = now
                    ref.updated_at = now

                    payload_hash = hashlib.sha256(
                        json.dumps(payload_dict, sort_keys=True, default=str).encode("utf-8")
                    ).hexdigest()

                    raw_record = RawSourceRecord(
                        ingestion_run_id=run_record.id,
                        external_id=ref.external_id,
                        payload=payload_dict,
                        payload_hash=payload_hash,
                    )
                    self.db_session.add(raw_record)
                    self.db_session.commit()

                    updated_count += 1
                    current_cost += self.cost_per_request

                except (TimeoutError, GooglePlacesError, Exception) as exc:
                    self.db_session.rollback()
                    logger.error(
                        "Failed to update POI external_id=%s actor_id=%s: %s",
                        ref.external_id,
                        actor.id,
                        exc,
                    )
                    failed_count += 1

            finished_at = datetime.now(UTC)
            run_record.status = final_status
            run_record.finished_at = finished_at
            run_record.estimated_cost = current_cost
            run_record.stats = {
                "total_scanned": total_scanned,
                "updated": updated_count,
                "failed": failed_count,
                "skipped": skipped_count,
            }
            self.db_session.commit()

            return PoiUpdateJobReport(
                run_id=run_record.id,
                status=final_status,
                total_scanned=total_scanned,
                updated_count=updated_count,
                failed_count=failed_count,
                skipped_count=skipped_count,
                total_cost=round(current_cost, 4),
                started_at=started_at,
                finished_at=finished_at,
                checkpoint_timestamp=checkpoint_timestamp,
                error_message=error_msg,
            )

        except Exception as exc:
            self.db_session.rollback()
            finished_at = datetime.now(UTC)
            error_msg = str(exc)
            run_record.status = "failed"
            run_record.finished_at = finished_at
            run_record.error_log = error_msg
            run_record.estimated_cost = current_cost
            run_record.stats = {
                "total_scanned": total_scanned,
                "updated": updated_count,
                "failed": failed_count,
                "skipped": total_scanned - (updated_count + failed_count),
            }
            try:
                self.db_session.commit()
            except Exception:
                self.db_session.rollback()

            return PoiUpdateJobReport(
                run_id=run_record.id,
                status="failed",
                total_scanned=total_scanned,
                updated_count=updated_count,
                failed_count=failed_count,
                skipped_count=total_scanned - (updated_count + failed_count),
                total_cost=round(current_cost, 4),
                started_at=started_at,
                finished_at=finished_at,
                checkpoint_timestamp=checkpoint_timestamp,
                error_message=error_msg,
            )
        finally:
            PoiUpdateJob.ingestion_runs.discard(self._JOB_LOCK_KEY)

    def _get_or_create_external_source(self) -> ExternalSource:
        """Fetch or insert the Google Places external source record."""
        source = self.db_session.execute(
            select(ExternalSource).where(ExternalSource.slug == "google_places")
        ).scalar_one_or_none()

        if source is None:
            source = ExternalSource(
                slug="google_places",
                name="Google Places API (New)",
                description="Google Places API connector source for POIs",
            )
            self.db_session.add(source)
            self.db_session.commit()
            self.db_session.refresh(source)

        return source

    @staticmethod
    def _update_actor_from_payload(actor: Actor, payload: dict[str, Any]) -> None:
        """Update Actor entity fields from valid Place Details response."""
        now = datetime.now(UTC)
        actor.google_data_refreshed_at = now
        actor.updated_at = now

        phone = payload.get("internationalPhoneNumber") or payload.get("nationalPhoneNumber")
        if phone:
            actor.phone = phone

        website = payload.get("websiteUri")
        if website:
            actor.website = website

        if "rating" in payload and payload["rating"] is not None:
            actor.google_rating = float(payload["rating"])

        if "userRatingCount" in payload and payload["userRatingCount"] is not None:
            actor.google_review_count = int(payload["userRatingCount"])

        if "regularOpeningHours" in payload and isinstance(
            payload["regularOpeningHours"], dict
        ):
            actor.opening_hours = payload["regularOpeningHours"]
