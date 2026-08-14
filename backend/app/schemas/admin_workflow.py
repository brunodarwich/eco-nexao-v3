"""Pydantic schemas for Admin Workflow, Alerts, and Reconciliation (ECO-1604)."""

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.envelopes import PaginationMeta

# -----------------------------------------------------------------------------
# Workflow State Transition Schemas
# -----------------------------------------------------------------------------


class StatusTransitionRequest(BaseModel):
    target_status: Literal["draft", "review", "published", "archived"] = Field(
        ..., description="Novo estado editorial desejado"
    )
    reason: str | None = Field(None, description="Motivo ou justificativa da alteração de estado")
    expected_version: int | None = Field(
        None, ge=1, description="Versão esperada para controle de concorrência otimista"
    )


class StatusTransitionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_type: str
    resource_id: uuid.UUID
    previous_status: str
    new_status: str
    version: int
    audit_log_id: uuid.UUID
    updated_at: datetime


class StatusTransitionEnvelope(BaseModel):
    data: StatusTransitionSchema


# -----------------------------------------------------------------------------
# Publish Guard Schemas
# -----------------------------------------------------------------------------


class PublishGuardResultSchema(BaseModel):
    resource_type: str
    resource_id: uuid.UUID
    current_status: str
    is_eligible: bool
    missing_requirements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PublishGuardResultEnvelope(BaseModel):
    data: PublishGuardResultSchema


# -----------------------------------------------------------------------------
# Editorial Alerts Schemas
# -----------------------------------------------------------------------------


class EditorialAlertSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_id: uuid.UUID
    title: str
    message: str
    severity: Literal["info", "warning", "critical"]
    source: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
    created_at: datetime


class EditorialAlertListEnvelope(BaseModel):
    data: list[EditorialAlertSchema]
    meta: PaginationMeta


class EditorialAlertEnvelope(BaseModel):
    data: EditorialAlertSchema


class EditorialAlertWriteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    severity: Literal["info", "warning", "critical"] = "info"
    source: str | None = Field(None, max_length=100)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_window(self) -> "EditorialAlertWriteRequest":
        values = (self.starts_at, self.ends_at, self.published_at)
        if any(value is not None and value.tzinfo is None for value in values):
            raise ValueError("starts_at, ends_at e published_at devem conter fuso horário")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at deve ser posterior a starts_at")
        if self.published_at and self.ends_at and self.published_at >= self.ends_at:
            raise ValueError("published_at deve ser anterior a ends_at")
        return self


class EditorialAlertCreateRequest(EditorialAlertWriteRequest):
    route_id: uuid.UUID


class EditorialAlertUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    message: str | None = Field(None, min_length=1)
    severity: Literal["info", "warning", "critical"] | None = None
    source: str | None = Field(None, max_length=100)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "EditorialAlertUpdateRequest":
        values = (self.starts_at, self.ends_at, self.published_at)
        if any(value is not None and value.tzinfo is None for value in values):
            raise ValueError("starts_at, ends_at e published_at devem conter fuso horário")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at deve ser posterior a starts_at")
        if self.published_at and self.ends_at and self.published_at >= self.ends_at:
            raise ValueError("published_at deve ser anterior a ends_at")
        return self


class AlertResolveRequest(BaseModel):
    resolution_note: str = Field(
        ..., min_length=3, description="Nota explicativa da resolução do alerta"
    )


# -----------------------------------------------------------------------------
# Reconciliation Schemas
# -----------------------------------------------------------------------------


class ReconciliationCandidateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id_a: uuid.UUID
    actor_id_b: uuid.UUID
    score: float
    status: str
    decision_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ReconciliationCandidateListEnvelope(BaseModel):
    data: list[ReconciliationCandidateSchema]
    meta: PaginationMeta


class ReconciliationDecisionRequest(BaseModel):
    decision: Literal["accept", "reject", "merge"] = Field(
        ..., description="Decisão editorial sobre o candidato"
    )
    reason: str = Field(..., min_length=5, description="Justificativa da decisão editorial")
    target_actor_id: uuid.UUID | None = Field(
        None, description="UUID do ator primário no caso de mesclagem (merge)"
    )


class ReconciliationDecisionSchema(BaseModel):
    candidate_id: uuid.UUID
    status: str
    decision: str
    decision_notes: str
    audit_log_id: uuid.UUID
    updated_at: datetime


class ReconciliationDecisionEnvelope(BaseModel):
    data: ReconciliationDecisionSchema


class ReconciliationCompensationRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Justificativa da compensação")
