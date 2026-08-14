"""Service layer for administrative workflow, alerts, and reconciliation (ECO-1604)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, cast

from app.models.domain import EditorialResourceState, RouteAlert
from app.repositories.workflow_admin import WorkflowAdminRepository
from app.schemas.admin_workflow import (
    EditorialAlertSchema,
    PublishGuardResultSchema,
    ReconciliationCandidateSchema,
    ReconciliationDecisionSchema,
    StatusTransitionSchema,
)
from app.schemas.envelopes import PaginationMeta

VALID_STATUSES = {"draft", "review", "published", "archived"}


class WorkflowAdminService:
    def __init__(self, repository: WorkflowAdminRepository) -> None:
        self.repository = repository

    # -------------------------------------------------------------------------
    # Workflow Transitions & Publish Guard
    # -------------------------------------------------------------------------

    async def get_publish_guard(
        self, resource_type: str, resource_id: uuid.UUID
    ) -> PublishGuardResultSchema:
        is_eligible, current_status, missing, warnings = (
            await self.repository.get_publish_guard_status(resource_type, resource_id)
        )
        return PublishGuardResultSchema(
            resource_type=resource_type,
            resource_id=resource_id,
            current_status=current_status,
            is_eligible=is_eligible,
            missing_requirements=missing,
            warnings=warnings,
        )

    async def get_authorization_state(
        self, resource_type: str, resource_id: uuid.UUID, actor_id: uuid.UUID
    ) -> EditorialResourceState:
        """Return persisted state or an unsaved draft after proving the resource exists."""
        if not await self.repository.check_resource_exists(resource_type, resource_id):
            raise ValueError(
                f"Recurso '{resource_type}' com ID {resource_id} não foi encontrado."
            )
        state = await self.repository.get_resource_state(resource_type, resource_id)
        return state or EditorialResourceState(
            id=uuid.uuid4(),
            resource_type=resource_type,
            resource_id=resource_id,
            status="draft",
            author_id=actor_id,
            version=1,
        )
    async def transition_status(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        target_status: str,
        actor_id: uuid.UUID,
        user_role: str = "admin",
        reason: str | None = None,
        expected_version: int | None = None,
    ) -> StatusTransitionSchema:
        if target_status not in VALID_STATUSES:
            raise ValueError(
                f"Estado de destino '{target_status}' é inválido. Válidos: {VALID_STATUSES}"
            )

        # Check resource exists
        exists = await self.repository.check_resource_exists(resource_type, resource_id)
        if not exists:
            raise ValueError(f"Recurso '{resource_type}' com ID {resource_id} não foi encontrado.")

        # The repository enforces completeness and separation-of-duties after
        # locking the state row, in the same transaction as the transition.
        state, audit_entry = await self.repository.transition_resource_state(
            resource_type=resource_type,
            resource_id=resource_id,
            target_status=target_status,
            actor_id=actor_id,
            reason=reason,
            expected_version=expected_version,
        )

        return StatusTransitionSchema(
            resource_type=state.resource_type,
            resource_id=state.resource_id,
            previous_status=audit_entry.changes.get("before", {}).get("status", "draft"),
            new_status=state.status,
            version=state.version,
            audit_log_id=audit_entry.id,
            updated_at=state.updated_at,
        )

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
    ) -> tuple[Sequence[EditorialAlertSchema], PaginationMeta]:
        alerts, total = await self.repository.list_alerts(
            route_id=route_id,
            severity=severity,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        schemas = [self._alert_schema(alert) for alert in alerts]
        meta = PaginationMeta(total=total, limit=limit)
        return schemas, meta

    async def resolve_alert(
        self, alert_id: uuid.UUID, actor_id: uuid.UUID, resolution_note: str
    ) -> EditorialAlertSchema:
        result = await self.repository.resolve_alert(alert_id, actor_id, resolution_note)
        if not result:
            raise LookupError(f"Alerta editorial com ID {alert_id} não encontrado.")

        alert, _ = result
        return self._alert_schema(alert, resolved_by=actor_id)

    # -------------------------------------------------------------------------
    # Reconciliation Candidates
    # -------------------------------------------------------------------------

    async def list_reconciliation_candidates(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[ReconciliationCandidateSchema], PaginationMeta]:
        candidates, total = await self.repository.list_reconciliation_candidates(
            status=status, limit=limit, offset=offset
        )

        schemas = [
            ReconciliationCandidateSchema(
                id=c.id,
                actor_id_a=c.actor_id_a,
                actor_id_b=c.actor_id_b,
                score=float(c.score),
                status=c.status,
                decision_notes=c.decision_notes,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in candidates
        ]
        meta = PaginationMeta(total=total, limit=limit)
        return schemas, meta

    async def decide_reconciliation(
        self,
        candidate_id: uuid.UUID,
        actor_id: uuid.UUID,
        decision: str,
        reason: str,
        target_actor_id: uuid.UUID | None = None,
    ) -> ReconciliationDecisionSchema:
        if decision not in {"accept", "reject", "merge"}:
            raise ValueError(f"Decisão '{decision}' é inválida. Válidos: accept, reject, merge")

        result = await self.repository.decide_reconciliation(
            candidate_id=candidate_id,
            actor_id=actor_id,
            decision=decision,
            reason=reason,
            target_actor_id=target_actor_id,
        )
        if not result:
            raise ValueError(f"Candidato de reconciliação com ID {candidate_id} não encontrado.")

        candidate, audit_entry = result
        return ReconciliationDecisionSchema(
            candidate_id=candidate.id,
            status=candidate.status,
            decision=decision,
            decision_notes=reason,
            audit_log_id=audit_entry.id,
            updated_at=candidate.updated_at,
        )

    async def compensate_reconciliation_merge(
        self, *, candidate_id: uuid.UUID, actor_id: uuid.UUID, reason: str
    ) -> ReconciliationDecisionSchema:
        result = await self.repository.compensate_reconciliation_merge(
            candidate_id=candidate_id, actor_id=actor_id, reason=reason
        )
        if not result:
            raise LookupError(f"Candidato de reconciliação com ID {candidate_id} não encontrado.")
        candidate, audit = result
        return ReconciliationDecisionSchema(
            candidate_id=candidate.id,
            status=candidate.status,
            decision="compensate",
            decision_notes=reason,
            audit_log_id=audit.id,
            updated_at=candidate.updated_at,
        )
    @staticmethod
    def _alert_schema(
        alert: RouteAlert, *, resolved_by: uuid.UUID | None = None
    ) -> EditorialAlertSchema:
        return EditorialAlertSchema(
            id=alert.id,
            route_id=alert.route_id,
            title=alert.title,
            message=alert.message,
            severity=cast(Literal["info", "warning", "critical"], alert.severity),
            source=alert.source,
            starts_at=alert.starts_at,
            ends_at=alert.ends_at,
            published_at=alert.published_at,
            is_active=alert.is_active,
            resolved_at=alert.updated_at if not alert.is_active else None,
            resolved_by=resolved_by,
            created_at=alert.created_at,
        )

    @staticmethod
    def _validate_alert_window(values: dict[str, Any]) -> None:
        starts_at = values.get("starts_at")
        ends_at = values.get("ends_at")
        published_at = values.get("published_at")
        if starts_at and ends_at and ends_at <= starts_at:
            raise ValueError("ends_at deve ser posterior a starts_at")
        if published_at and ends_at and published_at >= ends_at:
            raise ValueError("published_at deve ser anterior a ends_at")

    async def create_alert(
        self, *, actor_id: uuid.UUID, values: dict[str, Any]
    ) -> EditorialAlertSchema:
        normalized = dict(values)
        normalized["published_at"] = normalized.get("published_at") or datetime.now(UTC)
        self._validate_alert_window(normalized)
        result = await self.repository.create_alert(actor_id=actor_id, values=normalized)
        if not result:
            raise LookupError(f"Rota com ID {normalized['route_id']} não encontrada.")
        return self._alert_schema(result[0])

    async def update_alert(
        self, *, alert_id: uuid.UUID, actor_id: uuid.UUID, values: dict[str, Any]
    ) -> EditorialAlertSchema:
        self._validate_alert_window(values)
        result = await self.repository.update_alert(
            alert_id=alert_id, actor_id=actor_id, values=values
        )
        if not result:
            raise LookupError(f"Alerta editorial com ID {alert_id} não encontrado.")
        return self._alert_schema(result[0])
