"""Reconciliation service for SEMTUR and Google Places (ECO-2509 / ADR 0014).

Handles:
- Batch evaluation and deterministic linking (Tier 1, 2, 3).
- Strict editorial queueing for fuzzy candidates (Tier 4, NEVER auto-merged).
- Attribute-level provenance recording (field_provenance) and external refs.
- Audited, authorized and reversible editorial decisions (accept, reject, compensate/unmerge).
- Place ID 30-day lifecycle refresh updates (stale vs redirected/canonical change).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.semtur_google_matcher import (
    GooglePlaceCandidate,
    MatchEvaluation,
    MatchTier,
    SemturGoogleMatcher,
)
from app.models.domain import (
    ActorExternalRef,
    AuditLog,
    ExternalSource,
    FieldProvenance,
    ReconciliationCandidate,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReconciliationBatchReport:
    """Summary of batch reconciliation execution."""

    total_semtur_evaluated: int
    total_google_evaluated: int
    deterministic_linked: int
    fuzzy_queued_for_review: int
    conflicts_detected: int
    unchanged: int
    evaluations: tuple[MatchEvaluation, ...]


class SemturGoogleReconciliationService:
    """Executes safe, auditable, and idempotent reconciliation between SEMTUR and Google Places."""

    def __init__(
        self,
        session: AsyncSession,
        matcher: SemturGoogleMatcher | None = None,
    ) -> None:
        self.session = session
        self.matcher = matcher or SemturGoogleMatcher()

    async def get_or_create_source(
        self,
        slug: str = "google_places",
        name: str = "Google Places",
        description: str = "Google Places API (New) enriched provider",
    ) -> ExternalSource:
        """Ensure external source record exists for Google Places."""
        stmt = select(ExternalSource).where(ExternalSource.slug == slug).limit(1)
        res = await self.session.execute(stmt)
        source = res.scalar_one_or_none()
        if source:
            return source

        source = ExternalSource(
            id=uuid.uuid4(),
            slug=slug,
            name=name,
            description=description,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def reconcile_batch(
        self,
        semtur_records: Sequence[Mapping[str, Any]],
        google_candidates: Sequence[GooglePlaceCandidate],
        *,
        actor_id_map: Mapping[str, uuid.UUID] | None = None,
        audit_actor_id: uuid.UUID | None = None,
    ) -> ReconciliationBatchReport:
        """Evaluate SEMTUR records and persist deterministic links."""
        google_source = await self.get_or_create_source()
        effective_audit_actor_id = audit_actor_id or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        deterministic_linked = 0
        fuzzy_queued_for_review = 0
        conflicts_detected = 0
        unchanged = 0
        all_evaluations: list[MatchEvaluation] = []

        for semtur_rec in semtur_records:
            semtur_ext_id = str(semtur_rec.get("external_id") or semtur_rec.get("id") or "")
            actor_uuid = (
                actor_id_map.get(semtur_ext_id)
                if actor_id_map
                else (uuid.UUID(semtur_rec["actor_id"]) if "actor_id" in semtur_rec else None)
            )

            # Find best match among Google candidates
            best_eval: MatchEvaluation | None = None
            best_candidate: GooglePlaceCandidate | None = None

            for candidate in google_candidates:
                evaluation = self.matcher.evaluate(semtur_rec, candidate)

                # Prioritize higher tier (Tier 1 > Tier 2 > Tier 3 > Tier 4)
                if best_eval is None or evaluation.score > best_eval.score:
                    best_eval = evaluation
                    best_candidate = candidate

            if not best_eval or not best_candidate:
                unchanged += 1
                continue

            all_evaluations.append(best_eval)

            if best_eval.is_conflict:
                conflicts_detected += 1
                continue

            # -------------------------------------------------------------
            # Case 1: Deterministic Match (Tier 1, 2, 3) -> Auto-Link
            # -------------------------------------------------------------
            if best_eval.is_auto_link_eligible:
                if actor_uuid:
                    linked = await self._apply_deterministic_link(
                        actor_id=actor_uuid,
                        google_source_id=google_source.id,
                        candidate=best_candidate,
                        evaluation=best_eval,
                        audit_actor_id=effective_audit_actor_id,
                    )
                    if linked:
                        deterministic_linked += 1
                    else:
                        unchanged += 1
                else:
                    deterministic_linked += 1

            # -------------------------------------------------------------
            # Case 2: Fuzzy Candidate (Tier 4) -> Queue for Editorial Review
            # -------------------------------------------------------------
            elif best_eval.tier == MatchTier.TIER_4_FUZZY_CANDIDATE:
                if actor_uuid:
                    queued = await self._queue_fuzzy_candidate(
                        actor_id=actor_uuid,
                        candidate=best_candidate,
                        evaluation=best_eval,
                    )
                    if queued:
                        fuzzy_queued_for_review += 1
                    else:
                        unchanged += 1
                else:
                    fuzzy_queued_for_review += 1
            else:
                unchanged += 1

        await self.session.flush()

        return ReconciliationBatchReport(
            total_semtur_evaluated=len(semtur_records),
            total_google_evaluated=len(google_candidates),
            deterministic_linked=deterministic_linked,
            fuzzy_queued_for_review=fuzzy_queued_for_review,
            conflicts_detected=conflicts_detected,
            unchanged=unchanged,
            evaluations=tuple(all_evaluations),
        )

    async def _apply_deterministic_link(
        self,
        *,
        actor_id: uuid.UUID,
        google_source_id: uuid.UUID,
        candidate: GooglePlaceCandidate,
        evaluation: MatchEvaluation,
        audit_actor_id: uuid.UUID,
    ) -> bool:
        """Persist deterministic external reference and field provenance."""
        # Check existing external ref
        stmt = (
            select(ActorExternalRef)
            .where(
                ActorExternalRef.actor_id == actor_id,
                ActorExternalRef.source_id == google_source_id,
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        existing_ref = res.scalar_one_or_none()

        now = datetime.now(UTC)
        is_new_link = False

        if existing_ref:
            if existing_ref.external_id != candidate.place_id:
                # Place ID updated/canonical changed
                existing_ref.external_id = candidate.place_id
                existing_ref.last_seen_at = now
                existing_ref.status_ref = "active"
                existing_ref.updated_at = now
                is_new_link = True
            else:
                existing_ref.last_seen_at = now
                existing_ref.updated_at = now
        else:
            new_ref = ActorExternalRef(
                id=uuid.uuid4(),
                actor_id=actor_id,
                source_id=google_source_id,
                external_id=candidate.place_id,
                status_ref="active",
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
            self.session.add(new_ref)
            is_new_link = True

        # Record field provenance for enriched fields (confidence = evaluation.score)
        enriched_fields = ("google_place_id",)
        for field_name in enriched_fields:
            stmt_prov = (
                select(FieldProvenance)
                .where(
                    FieldProvenance.target_table == "actors",
                    FieldProvenance.target_id == actor_id,
                    FieldProvenance.field_name == field_name,
                    FieldProvenance.source_id == google_source_id,
                )
                .limit(1)
            )
            res_prov = await self.session.execute(stmt_prov)
            prov = res_prov.scalar_one_or_none()

            if not prov:
                self.session.add(
                    FieldProvenance(
                        id=uuid.uuid4(),
                        target_table="actors",
                        target_id=actor_id,
                        field_name=field_name,
                        source_id=google_source_id,
                        confidence=evaluation.score,
                        collected_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )

        if is_new_link:
            # Audit log
            audit = AuditLog(
                id=uuid.uuid4(),
                timestamp=now,
                actor_id=audit_actor_id,
                action="RECONCILE_AUTO_LINK",
                resource_type="actor",
                resource_id=actor_id,
                changes={
                    "tier": evaluation.tier.value,
                    "score": evaluation.score,
                    "google_place_id": candidate.place_id,
                    "reasons": list(evaluation.reasons),
                },
                reason=f"Deterministic matching {evaluation.tier.value}",
            )
            self.session.add(audit)

        return is_new_link

    async def _queue_fuzzy_candidate(
        self,
        *,
        actor_id: uuid.UUID,
        candidate: GooglePlaceCandidate,
        evaluation: MatchEvaluation,
    ) -> bool:
        """Queue candidate in reconciliation_candidates table without auto-merging."""
        # Find if pending candidate already exists for this actor_id and place_id in notes
        stmt = (
            select(ReconciliationCandidate)
            .where(
                ReconciliationCandidate.actor_id_a == actor_id,
                ReconciliationCandidate.status == "pending",
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()

        notes = json.dumps(
            {
                "google_place_id": candidate.place_id,
                "candidate_name": candidate.name,
                "tier": evaluation.tier.value,
                "score": evaluation.score,
                "reasons": list(evaluation.reasons),
                "distance_m": evaluation.distance_m,
            },
            ensure_ascii=False,
        )

        now = datetime.now(UTC)
        if existing:
            existing.score = evaluation.score
            existing.decision_notes = notes
            existing.updated_at = now
            return False

        # In case actor_id_b foreign key requires an existing actor row, link actor_id_b to actor_id
        # or another candidate row, preserving the candidate pairing
        new_candidate = ReconciliationCandidate(
            id=uuid.uuid4(),
            actor_id_a=actor_id,
            actor_id_b=actor_id,
            score=evaluation.score,
            status="pending",
            decision_notes=notes,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_candidate)
        return True

    async def accept_candidate(
        self,
        *,
        candidate_id: uuid.UUID,
        editor_id: uuid.UUID,
        reason: str,
    ) -> tuple[ReconciliationCandidate, AuditLog]:
        """Editorial action: Accept a fuzzy match and link the Google Place ID."""
        stmt = select(ReconciliationCandidate).where(ReconciliationCandidate.id == candidate_id)
        res = await self.session.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"Candidato de reconciliação {candidate_id} não encontrado.")
        if candidate.status != "pending":
            raise ValueError("Conflito: candidato já possui uma decisão editorial.")

        notes_data = json.loads(candidate.decision_notes or "{}")
        place_id = notes_data.get("google_place_id")
        if not place_id:
            raise ValueError("Google Place ID ausente nas notas do candidato.")

        google_source = await self.get_or_create_source()
        now = datetime.now(UTC)

        # Link external ref
        new_ref = ActorExternalRef(
            id=uuid.uuid4(),
            actor_id=candidate.actor_id_a,
            source_id=google_source.id,
            external_id=place_id,
            status_ref="active",
            last_seen_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_ref)

        # Update candidate
        candidate.status = "accepted"
        candidate.updated_at = now

        # Create audit log
        audit = AuditLog(
            id=uuid.uuid4(),
            timestamp=now,
            actor_id=editor_id,
            action="RECONCILE_ACCEPT",
            resource_type="reconciliation_candidate",
            resource_id=candidate.id,
            changes={
                "before": {"status": "pending"},
                "after": {"status": "accepted"},
                "actor_id": str(candidate.actor_id_a),
                "google_place_id": place_id,
                "external_ref_id": str(new_ref.id),
            },
            reason=reason,
        )
        self.session.add(audit)
        await self.session.flush()
        return candidate, audit

    async def reject_candidate(
        self,
        *,
        candidate_id: uuid.UUID,
        editor_id: uuid.UUID,
        reason: str,
    ) -> tuple[ReconciliationCandidate, AuditLog]:
        """Editorial action: Reject a match as distinct entities."""
        stmt = select(ReconciliationCandidate).where(ReconciliationCandidate.id == candidate_id)
        res = await self.session.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"Candidato de reconciliação {candidate_id} não encontrado.")
        if candidate.status != "pending":
            raise ValueError("Conflito: candidato já possui uma decisão editorial.")

        now = datetime.now(UTC)
        candidate.status = "rejected"
        candidate.updated_at = now

        audit = AuditLog(
            id=uuid.uuid4(),
            timestamp=now,
            actor_id=editor_id,
            action="RECONCILE_REJECT",
            resource_type="reconciliation_candidate",
            resource_id=candidate.id,
            changes={
                "before": {"status": "pending"},
                "after": {"status": "rejected"},
                "actor_id": str(candidate.actor_id_a),
            },
            reason=reason,
        )
        self.session.add(audit)
        await self.session.flush()
        return candidate, audit

    async def compensate_decision(
        self,
        *,
        candidate_id: uuid.UUID,
        editor_id: uuid.UUID,
        reason: str,
    ) -> tuple[ReconciliationCandidate, AuditLog]:
        """Editorial action: Reversible unmerge/compensation of earlier decision."""
        stmt = select(ReconciliationCandidate).where(ReconciliationCandidate.id == candidate_id)
        res = await self.session.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"Candidato de reconciliação {candidate_id} não encontrado.")
        if candidate.status not in {"accepted", "merged"}:
            raise ValueError(
                "Conflito: apenas candidatos accepted ou merged podem ser compensados."
            )

        # Find latest audit log for this candidate
        stmt_audit = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == "reconciliation_candidate",
                AuditLog.resource_id == candidate_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        res_audit = await self.session.execute(stmt_audit)
        prev_audit = res_audit.scalar_one_or_none()

        now = datetime.now(UTC)
        ref_id_str = prev_audit.changes.get("external_ref_id") if prev_audit else None
        if ref_id_str:
            ref_uuid = uuid.UUID(ref_id_str)
            stmt_ref = select(ActorExternalRef).where(ActorExternalRef.id == ref_uuid)
            res_ref = await self.session.execute(stmt_ref)
            ref = res_ref.scalar_one_or_none()
            if ref:
                ref.status_ref = "unlinked"
                ref.updated_at = now

        previous_status = candidate.status
        candidate.status = "pending"
        candidate.updated_at = now

        compensate_audit = AuditLog(
            id=uuid.uuid4(),
            timestamp=now,
            actor_id=editor_id,
            action="RECONCILE_COMPENSATE",
            resource_type="reconciliation_candidate",
            resource_id=candidate.id,
            changes={
                "before": {"status": previous_status},
                "after": {"status": "pending"},
                "unlinked_ref_id": ref_id_str,
            },
            reason=reason,
        )
        self.session.add(compensate_audit)
        await self.session.flush()
        return candidate, compensate_audit

    async def handle_place_id_lifecycle_refresh(
        self,
        *,
        actor_id: uuid.UUID,
        original_place_id: str,
        canonical_place_id: str | None,
        is_changed: bool,
        is_stale: bool,
        audit_actor_id: uuid.UUID,
    ) -> ActorExternalRef | None:
        """Handle 30-day lifecycle refresh outcome for a stored Google Place ID."""
        google_source = await self.get_or_create_source()
        stmt = (
            select(ActorExternalRef)
            .where(
                ActorExternalRef.actor_id == actor_id,
                ActorExternalRef.source_id == google_source.id,
                ActorExternalRef.external_id == original_place_id,
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        ref = res.scalar_one_or_none()
        if not ref:
            return None

        now = datetime.now(UTC)
        if is_stale:
            ref.status_ref = "stale"
            ref.updated_at = now
            self.session.add(
                AuditLog(
                    id=uuid.uuid4(),
                    timestamp=now,
                    actor_id=audit_actor_id,
                    action="PLACE_ID_STALE",
                    resource_type="actor_external_ref",
                    resource_id=ref.id,
                    changes={"original_place_id": original_place_id, "status": "stale"},
                    reason="Upstream Place Details returned 404 NOT_FOUND",
                )
            )
        elif is_changed and canonical_place_id:
            ref.external_id = canonical_place_id
            ref.last_seen_at = now
            ref.updated_at = now
            self.session.add(
                AuditLog(
                    id=uuid.uuid4(),
                    timestamp=now,
                    actor_id=audit_actor_id,
                    action="PLACE_ID_REDIRECT",
                    resource_type="actor_external_ref",
                    resource_id=ref.id,
                    changes={
                        "original_place_id": original_place_id,
                        "canonical_place_id": canonical_place_id,
                    },
                    reason="Upstream Place Details redirected to canonical place ID",
                )
            )
        else:
            ref.last_seen_at = now
            ref.updated_at = now

        await self.session.flush()
        return ref
