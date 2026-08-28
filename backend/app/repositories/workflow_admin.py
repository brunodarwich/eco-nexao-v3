"""Repository layer for administrative workflow, alerts, and reconciliation (ECO-1604)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parseaddr
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    Actor,
    ActorExternalRef,
    AuditLog,
    EditorialResourceState,
    MediaAsset,
    ReconciliationCandidate,
    Region,
    Route,
    RouteActor,
    RouteAlert,
    RouteGeometry,
    RouteOrigin,
)


class WorkflowAdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Audit Logs
    # -------------------------------------------------------------------------

    async def log_action(
        self,
        actor_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        changes: dict[str, Any],
        reason: str | None = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            reason=reason,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    # -------------------------------------------------------------------------
    # Resource State & Transitions
    # -------------------------------------------------------------------------

    async def get_resource_state(
        self, resource_type: str, resource_id: uuid.UUID, *, for_update: bool = False
    ) -> EditorialResourceState | None:
        stmt = select(EditorialResourceState).where(
            EditorialResourceState.resource_type == resource_type,
            EditorialResourceState.resource_id == resource_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_or_create_resource_state(
        self, resource_type: str, resource_id: uuid.UUID, author_id: uuid.UUID
    ) -> EditorialResourceState:
        # Serialize first-state creation as well as later transitions. Row locking
        # alone cannot protect the gap before the unique row exists.
        lock_key = f"{resource_type}:{resource_id}"
        await self.db.execute(
            select(func.pg_advisory_xact_lock(func.hashtextextended(lock_key, 0)))
        )
        state = await self.get_resource_state(resource_type, resource_id, for_update=True)
        if not state:
            state = EditorialResourceState(
                id=uuid.uuid4(),
                resource_type=resource_type,
                resource_id=resource_id,
                status="draft",
                author_id=author_id,
                version=1,
            )
            self.db.add(state)
            await self.db.flush()
        return state

    async def check_resource_exists(self, resource_type: str, resource_id: uuid.UUID) -> bool:
        id_column_by_type = {
            "region": Region.id,
            "route": Route.id,
            "origin": RouteOrigin.id,
            "actor": Actor.id,
            "media": MediaAsset.id,
        }
        id_column = id_column_by_type.get(resource_type)
        if id_column is None:
            return False
        stmt = select(func.count()).where(id_column == resource_id)
        res = await self.db.execute(stmt)
        return (res.scalar_one() or 0) > 0

    async def get_publish_guard_status(
        self, resource_type: str, resource_id: uuid.UUID
    ) -> tuple[bool, str, list[str], list[str]]:
        """Returns (is_eligible, current_status, missing_requirements, warnings)."""
        state = await self.get_resource_state(resource_type, resource_id)
        current_status = state.status if state else "draft"
        missing: list[str] = []
        warnings: list[str] = []

        if resource_type == "region":
            result = await self.db.execute(select(Region).where(Region.id == resource_id))
            region = result.scalar_one_or_none()
            if not region:
                return False, current_status, ["Região não encontrada"], []
            if region.center is None:
                missing.append("A região deve possuir coordenadas centrais válidas em SRID 4326.")
            missing.append(
                "Descrição, origem, geometria e capa licenciada ainda não estão "
                "modeladas para regiões; a região não pode ser publicada."
            )

        elif resource_type == "route":
            stmt_route = select(Route).where(Route.id == resource_id)
            res_route = await self.db.execute(stmt_route)
            route = res_route.scalar_one_or_none()
            if not route:
                return False, current_status, ["Rota não encontrada"], []

            stmt_origins = select(func.count()).where(RouteOrigin.route_id == resource_id)
            res_origins = await self.db.execute(stmt_origins)
            origin_count = res_origins.scalar_one() or 0
            if origin_count == 0:
                missing.append("A rota deve possuir pelo menos 1 origem configurada.")

            stmt_geometries = (
                select(func.count())
                .select_from(RouteGeometry)
                .join(RouteOrigin, RouteOrigin.id == RouteGeometry.route_origin_id)
                .where(
                    RouteOrigin.route_id == resource_id,
                    RouteGeometry.geometry.is_not(None),
                )
            )
            geometry_count = (await self.db.execute(stmt_geometries)).scalar_one() or 0
            if geometry_count == 0:
                missing.append("A rota deve possuir geometria LineString válida em SRID 4326.")

            if not route.summary or not route.summary.strip():
                missing.append("A rota deve possuir texto descritivo.")

            if not route.cover_media_id:
                missing.append("A rota deve possuir mídia de capa definida.")
            else:
                media_result = await self.db.execute(
                    select(MediaAsset).where(MediaAsset.id == route.cover_media_id)
                )
                cover = media_result.scalar_one_or_none()
                if not cover or not cover.alt_text or not cover.alt_text.strip():
                    missing.append("A mídia de capa deve possuir texto alternativo.")
                if not cover or not cover.credit or not cover.credit.strip():
                    missing.append("A mídia de capa deve possuir crédito registrado.")
                if not cover or cover.owner_type != "route" or cover.owner_id != resource_id:
                    missing.append("A mídia de capa deve pertencer à rota.")
                if not cover or not cover.license_code:
                    missing.append("A mídia de capa deve possuir licença estruturada.")
                if not cover or not self._media_is_publishable(cover):
                    missing.append("A mídia de capa deve estar processada e pronta.")

        elif resource_type == "origin":
            origin_result = await self.db.execute(
                select(RouteOrigin).where(RouteOrigin.id == resource_id)
            )
            origin = origin_result.scalar_one_or_none()
            if not origin:
                return False, current_status, ["Origem não encontrada"], []
            if origin.location is None:
                missing.append("A origem deve possuir coordenadas válidas em SRID 4326.")
            geometry_count = (
                await self.db.execute(
                    select(func.count()).where(
                        RouteGeometry.route_origin_id == resource_id,
                        RouteGeometry.geometry.is_not(None),
                    )
                )
            ).scalar_one() or 0
            if geometry_count == 0:
                missing.append("A origem deve possuir geometria LineString válida em SRID 4326.")

        elif resource_type == "actor":
            stmt_actor = select(Actor).where(Actor.id == resource_id)
            res_actor = await self.db.execute(stmt_actor)
            actor = res_actor.scalar_one_or_none()
            if not actor:
                return False, current_status, ["Ator não encontrado"], []

            if not actor.category_id:
                missing.append("O ator deve possuir uma categoria vinculada.")

            if actor.location is None:
                missing.append("O ator deve possuir coordenadas geográficas válidas.")

            active_links = (
                await self.db.execute(
                    select(func.count())
                    .select_from(RouteActor)
                    .join(Route, Route.id == RouteActor.route_id)
                    .where(
                        RouteActor.actor_id == resource_id,
                        RouteActor.archived_at.is_(None),
                        Route.deleted_at.is_(None),
                        Route.status.in_(("active", "published")),
                    )
                )
            ).scalar_one() or 0
            if active_links == 0:
                missing.append("O ator deve estar vinculado a pelo menos 1 rota ativa.")

            phone_digits = "".join(ch for ch in (actor.phone or "") if ch.isdigit())
            email = parseaddr(actor.email or "")[1]
            formatted_contact = len(phone_digits) >= 10 or (
                bool(email) and "@" in email and "." in email.rsplit("@", 1)[-1]
            )
            if not formatted_contact or actor.verification_status != "verified":
                missing.append("O ator deve possuir telefone ou e-mail formatado e verificado.")

        elif resource_type == "media":
            standalone_media_result = await self.db.execute(
                select(MediaAsset).where(MediaAsset.id == resource_id)
            )
            media = standalone_media_result.scalar_one_or_none()
            if not media:
                return False, current_status, ["Mídia não encontrada"], []
            if not media.alt_text or not media.alt_text.strip():
                missing.append("A mídia deve possuir texto alternativo.")
            if not media.credit or not media.credit.strip():
                missing.append("A mídia deve possuir crédito e licença registrados.")
            if not media.license_code:
                missing.append("A mídia deve possuir licença estruturada.")
            if not self._media_is_publishable(media):
                missing.append("A mídia deve estar processada e pronta.")

        else:
            missing.append(
                f"Tipo de recurso '{resource_type}' não possui regras de publish guard registradas."
            )

        is_eligible = len(missing) == 0
        return is_eligible, current_status, missing, warnings

    @staticmethod
    def _media_is_publishable(media: MediaAsset) -> bool:
        if media.processing_status != "ready" or media.deleted_at:
            return False
        required = {"thumb", "card", "hero"}
        if not required <= set(media.derivatives):
            return False
        return all(
            isinstance(media.derivatives.get(name), dict)
            and bool(media.derivatives[name].get("storage_key"))
            and len(str(media.derivatives[name].get("checksum_sha256", ""))) == 64
            for name in required
        )

    async def transition_resource_state(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        target_status: str,
        actor_id: uuid.UUID,
        reason: str | None = None,
        expected_version: int | None = None,
    ) -> tuple[EditorialResourceState, AuditLog]:
        state = await self.get_or_create_resource_state(
            resource_type, resource_id, author_id=actor_id
        )

        if expected_version is not None and state.version != expected_version:
            raise ValueError(
                f"Conflito de concorrência: versão atual é {state.version}, "
                f"esperada {expected_version}."
            )

        if target_status == "published" and state.author_id == actor_id:
            raise PermissionError(
                "Segregação de funções: o autor não pode publicar o próprio conteúdo."
            )

        if target_status in {"review", "published"}:
            eligible, _, missing, _ = await self.get_publish_guard_status(
                resource_type, resource_id
            )
            if not eligible:
                raise ValueError(
                    "Recurso não atende aos requisitos de publicação: " + "; ".join(missing)
                )

        previous_status = state.status
        state.status = target_status
        state.version += 1
        state.updated_at = datetime.now(UTC)

        if target_status == "published":
            state.reviewed_by = actor_id
            state.published_by = actor_id

        # Also update root domain entity status if applicable
        if resource_type == "route":
            stmt_route = select(Route).where(Route.id == resource_id)
            res_route = await self.db.execute(stmt_route)
            route = res_route.scalar_one_or_none()
            if route:
                route.status = "active" if target_status == "published" else target_status
                route.updated_at = datetime.now(UTC)

        audit_entry = await self.log_action(
            actor_id=actor_id,
            action="TRANSITION_STATUS",
            resource_type=resource_type,
            resource_id=resource_id,
            changes={
                "before": {"status": previous_status, "version": state.version - 1},
                "after": {"status": target_status, "version": state.version},
            },
            reason=reason,
        )

        await self.db.flush()
        return state, audit_entry

    # -------------------------------------------------------------------------
    # Route Alerts
    # -------------------------------------------------------------------------

    async def list_alerts(
        self,
        route_id: uuid.UUID | None = None,
        severity: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[RouteAlert], int]:
        stmt = select(RouteAlert)

        if route_id is not None:
            stmt = stmt.where(RouteAlert.route_id == route_id)
        if severity is not None:
            stmt = stmt.where(RouteAlert.severity == severity)
        if is_active is not None:
            stmt = stmt.where(RouteAlert.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        paginated_stmt = stmt.order_by(RouteAlert.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(paginated_stmt)
        return res.scalars().all(), total

    async def get_alert_by_id(
        self, alert_id: uuid.UUID, *, for_update: bool = False
    ) -> RouteAlert | None:
        stmt = select(RouteAlert).where(RouteAlert.id == alert_id)
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_alert(
        self, *, actor_id: uuid.UUID, values: dict[str, Any]
    ) -> tuple[RouteAlert, AuditLog] | None:
        route_id = values["route_id"]
        if not await self.check_resource_exists("route", route_id):
            return None
        alert = RouteAlert(id=uuid.uuid4(), **values)
        self.db.add(alert)
        await self.db.flush()
        audit = await self.log_action(
            actor_id,
            "CREATE",
            "route_alert",
            alert.id,
            {"before": None, "after": self._alert_snapshot(alert)},
        )
        return alert, audit

    async def update_alert(
        self, *, alert_id: uuid.UUID, actor_id: uuid.UUID, values: dict[str, Any]
    ) -> tuple[RouteAlert, AuditLog] | None:
        alert = await self.get_alert_by_id(alert_id, for_update=True)
        if not alert:
            return None
        if not alert.is_active:
            raise ValueError("Conflito: alerta resolvido não pode ser atualizado.")
        before = self._alert_snapshot(alert)
        for key, value in values.items():
            setattr(alert, key, value)
        alert.updated_at = datetime.now(UTC)
        await self.db.flush()
        audit = await self.log_action(
            actor_id,
            "UPDATE",
            "route_alert",
            alert.id,
            {"before": before, "after": self._alert_snapshot(alert)},
        )
        return alert, audit

    @staticmethod
    def _alert_snapshot(alert: RouteAlert) -> dict[str, Any]:
        return {
            "route_id": str(alert.route_id),
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "source": alert.source,
            "starts_at": alert.starts_at.isoformat() if alert.starts_at else None,
            "ends_at": alert.ends_at.isoformat() if alert.ends_at else None,
            "published_at": alert.published_at.isoformat(),
            "is_active": alert.is_active,
        }

    async def resolve_alert(
        self, alert_id: uuid.UUID, actor_id: uuid.UUID, resolution_note: str
    ) -> tuple[RouteAlert, AuditLog] | None:
        alert = await self.get_alert_by_id(alert_id, for_update=True)
        if not alert:
            return None

        if not alert.is_active:
            raise ValueError("Conflito: alerta já foi resolvido.")

        before = self._alert_snapshot(alert)
        alert.is_active = False
        alert.updated_at = datetime.now(UTC)

        audit_entry = await self.log_action(
            actor_id=actor_id,
            action="UPDATE",
            resource_type="route_alert",
            resource_id=alert_id,
            changes={
                "before": before,
                "after": self._alert_snapshot(alert),
                "route_id": str(alert.route_id),
            },
            reason=resolution_note,
        )

        await self.db.flush()
        return alert, audit_entry

    # -------------------------------------------------------------------------
    # Reconciliation Candidates
    # -------------------------------------------------------------------------

    async def list_reconciliation_candidates(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[ReconciliationCandidate], int]:
        stmt = select(ReconciliationCandidate)
        if status is not None:
            stmt = stmt.where(ReconciliationCandidate.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        paginated_stmt = (
            stmt.order_by(
                ReconciliationCandidate.score.desc(),
                ReconciliationCandidate.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(paginated_stmt)
        return res.scalars().all(), total

    async def get_reconciliation_candidate_by_id(
        self, candidate_id: uuid.UUID, *, for_update: bool = False
    ) -> ReconciliationCandidate | None:
        stmt = select(ReconciliationCandidate).where(ReconciliationCandidate.id == candidate_id)
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def decide_reconciliation(
        self,
        candidate_id: uuid.UUID,
        actor_id: uuid.UUID,
        decision: str,
        reason: str,
        target_actor_id: uuid.UUID | None = None,
    ) -> tuple[ReconciliationCandidate, AuditLog] | None:
        candidate = await self.get_reconciliation_candidate_by_id(candidate_id, for_update=True)
        if not candidate:
            return None
        if candidate.status != "pending":
            raise ValueError("Conflito: candidato já possui uma decisão editorial.")
        if target_actor_id not in {None, candidate.actor_id_a, candidate.actor_id_b}:
            raise ValueError("O ator primário deve pertencer ao par candidato.")

        previous_status = candidate.status
        new_status = (
            "accepted"
            if decision == "accept"
            else ("rejected" if decision == "reject" else "merged")
        )
        merge_snapshot: dict[str, Any] | None = None
        # If decision is merge, handle transfer of links from candidate B to target_actor_id
        if decision == "merge":
            primary_id = target_actor_id or candidate.actor_id_a
            secondary_id = (
                candidate.actor_id_b if primary_id == candidate.actor_id_a else candidate.actor_id_a
            )

            # Transfer route_actors links if not existing
            stmt_links = (
                select(RouteActor)
                .where(
                    RouteActor.actor_id == secondary_id,
                    RouteActor.archived_at.is_(None),
                )
                .with_for_update()
            )
            res_links = await self.db.execute(stmt_links)
            secondary_links = list(res_links.scalars().all())
            transferred_link_ids: list[str] = []
            archived_link_ids: list[str] = []
            for link in secondary_links:
                stmt_dup = select(RouteActor).where(
                    RouteActor.route_id == link.route_id,
                    RouteActor.actor_id == primary_id,
                    RouteActor.archived_at.is_(None),
                )
                res_dup = await self.db.execute(stmt_dup)
                if res_dup.scalar_one_or_none():
                    archived_at = datetime.now(UTC)
                    link.archived_at = archived_at
                    link.archived_by = actor_id
                    link.archive_reason = reason
                    link.updated_at = archived_at
                    archived_link_ids.append(str(link.id))
                    continue
                link.actor_id = primary_id
                link.updated_at = datetime.now(UTC)
                transferred_link_ids.append(str(link.id))

            # Transfer external refs
            stmt_refs = select(ActorExternalRef).where(ActorExternalRef.actor_id == secondary_id)
            res_refs = await self.db.execute(stmt_refs)
            transferred_ref_ids: list[str] = []
            for ref in res_refs.scalars().all():
                ref.actor_id = primary_id
                ref.updated_at = datetime.now(UTC)
                transferred_ref_ids.append(str(ref.id))

            # Soft delete secondary actor
            stmt_sec = select(Actor).where(Actor.id == secondary_id)
            res_sec = await self.db.execute(stmt_sec)
            sec_actor = res_sec.scalar_one_or_none()
            previous_deleted_at = sec_actor.deleted_at if sec_actor else None
            merged_deleted_at = datetime.now(UTC)
            if sec_actor:
                sec_actor.deleted_at = merged_deleted_at
                sec_actor.updated_at = merged_deleted_at
            merge_snapshot = {
                "primary_actor_id": str(primary_id),
                "secondary_actor_id": str(secondary_id),
                "route_actor_link_ids": transferred_link_ids,
                "archived_route_actor_link_ids": archived_link_ids,
                "external_ref_ids": transferred_ref_ids,
                "secondary_deleted_at_before": (
                    previous_deleted_at.isoformat() if previous_deleted_at else None
                ),
                "secondary_deleted_at_after": merged_deleted_at.isoformat() if sec_actor else None,
            }

        candidate.status = new_status
        candidate.decision_notes = reason
        candidate.updated_at = datetime.now(UTC)

        audit_entry = await self.log_action(
            actor_id=actor_id,
            action="RECONCILE",
            resource_type="reconciliation_candidate",
            resource_id=candidate_id,
            changes={
                "actor_id_a": str(candidate.actor_id_a),
                "actor_id_b": str(candidate.actor_id_b),
                "before": {"status": previous_status},
                "after": {"status": new_status},
                "decision": decision,
                "reason": reason,
                "target_actor_id": str(target_actor_id) if target_actor_id else None,
                "merge_snapshot": merge_snapshot,
            },
            reason=reason,
        )

        await self.db.flush()
        return candidate, audit_entry

    async def compensate_reconciliation_merge(
        self, *, candidate_id: uuid.UUID, actor_id: uuid.UUID, reason: str
    ) -> tuple[ReconciliationCandidate, AuditLog] | None:
        candidate = await self.get_reconciliation_candidate_by_id(candidate_id, for_update=True)
        if not candidate:
            return None
        if candidate.status != "merged":
            raise ValueError("Conflito: candidato não está no estado merged.")

        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.resource_type == "reconciliation_candidate",
                AuditLog.resource_id == candidate_id,
                AuditLog.action == "RECONCILE",
            )
            .order_by(AuditLog.timestamp.desc())
        )
        merge_audit = next(
            (entry for entry in result.scalars().all() if entry.changes.get("decision") == "merge"),
            None,
        )
        if not merge_audit or not merge_audit.changes.get("merge_snapshot"):
            raise ValueError("Conflito: snapshot do merge não está disponível.")
        snapshot = merge_audit.changes["merge_snapshot"]
        primary_id = uuid.UUID(snapshot["primary_actor_id"])
        secondary_id = uuid.UUID(snapshot["secondary_actor_id"])

        link_ids = [uuid.UUID(value) for value in snapshot["route_actor_link_ids"]]
        archived_link_ids = [
            uuid.UUID(value) for value in snapshot.get("archived_route_actor_link_ids", [])
        ]
        ref_ids = [uuid.UUID(value) for value in snapshot["external_ref_ids"]]
        links_result = await self.db.execute(
            select(RouteActor).where(RouteActor.id.in_(link_ids)).with_for_update()
        )
        archived_links_result = await self.db.execute(
            select(RouteActor).where(RouteActor.id.in_(archived_link_ids)).with_for_update()
        )
        refs_result = await self.db.execute(
            select(ActorExternalRef).where(ActorExternalRef.id.in_(ref_ids)).with_for_update()
        )
        links = list(links_result.scalars().all())
        archived_links = list(archived_links_result.scalars().all())
        refs = list(refs_result.scalars().all())
        if len(links) != len(link_ids) or any(link.actor_id != primary_id for link in links):
            raise ValueError("Conflito: vínculos de rota mudaram após o merge.")
        if len(archived_links) != len(archived_link_ids) or any(
            link.actor_id != secondary_id or link.archived_at is None for link in archived_links
        ):
            raise ValueError("Conflito: vínculos arquivados mudaram após o merge.")
        if len(refs) != len(ref_ids) or any(ref.actor_id != primary_id for ref in refs):
            raise ValueError("Conflito: referências externas mudaram após o merge.")

        actor_result = await self.db.execute(
            select(Actor).where(Actor.id == secondary_id).with_for_update()
        )
        secondary = actor_result.scalar_one_or_none()
        expected_deleted_at = snapshot["secondary_deleted_at_after"]
        if (
            not secondary
            or not secondary.deleted_at
            or secondary.deleted_at.isoformat() != expected_deleted_at
        ):
            raise ValueError("Conflito: ator secundário mudou após o merge.")

        now = datetime.now(UTC)
        for link in links:
            link.actor_id = secondary_id
            link.updated_at = now
        for link in archived_links:
            link.archived_at = None
            link.archived_by = None
            link.archive_reason = None
            link.updated_at = now
        for ref in refs:
            ref.actor_id = secondary_id
            ref.updated_at = now
        previous_deleted_at = snapshot["secondary_deleted_at_before"]
        secondary.deleted_at = (
            datetime.fromisoformat(previous_deleted_at) if previous_deleted_at else None
        )
        secondary.updated_at = now
        before_status = candidate.status
        restored_status = merge_audit.changes.get("before", {}).get("status", "pending")
        candidate.status = restored_status
        candidate.updated_at = now
        audit = await self.log_action(
            actor_id,
            "RECONCILE",
            "reconciliation_candidate",
            candidate_id,
            {
                "before": {"status": before_status, "merge_audit_id": str(merge_audit.id)},
                "after": {"status": restored_status, "snapshot_restored": snapshot},
                "decision": "compensate",
            },
            reason,
        )
        await self.db.flush()
        return candidate, audit
