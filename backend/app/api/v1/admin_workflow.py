"""Administrative API endpoints for workflow, alerts, and reconciliation (ECO-1604)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.admin_workflow import (
    AlertResolveRequest,
    EditorialAlertCreateRequest,
    EditorialAlertEnvelope,
    EditorialAlertListEnvelope,
    EditorialAlertUpdateRequest,
    PublishGuardResultEnvelope,
    ReconciliationCandidateListEnvelope,
    ReconciliationCompensationRequest,
    ReconciliationDecisionEnvelope,
    ReconciliationDecisionRequest,
    StatusTransitionEnvelope,
    StatusTransitionRequest,
)
from app.services.dependencies import (
    get_editorial_authorization_service,
    get_workflow_admin_service,
)
from app.services.editorial_authorization import (
    AuthorizationContext,
    EditorialAuthorizationService,
)
from app.services.workflow_admin import WorkflowAdminService

router = APIRouter(prefix="/admin", tags=["Admin Workflow"])

CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
EditorialAuthDep = Annotated[
    EditorialAuthorizationService, Depends(get_editorial_authorization_service)
]
WorkflowAdminServiceDep = Annotated[WorkflowAdminService, Depends(get_workflow_admin_service)]


def _build_context(user: AuthenticatedUser) -> AuthorizationContext:
    if user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A identidade não possui acesso editorial.",
        )
    return AuthorizationContext(actor_id=user.id)


# -----------------------------------------------------------------------------
# Workflow Transitions & Publish Guard
# -----------------------------------------------------------------------------


@router.post(
    "/workflow/{resource_type}/{resource_id}/transition",
    response_model=StatusTransitionEnvelope,
    summary="Transicionar estado editorial",
    description=(
        "Transicionar o estado de um recurso na máquina de estados editorial "
        "com validação de publish guard e concorrência."
    ),
)
async def transition_resource_status(
    resource_type: str,
    resource_id: uuid.UUID,
    body: StatusTransitionRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> StatusTransitionEnvelope:
    ctx = _build_context(current_user)

    try:
        current_state = await service.get_authorization_state(
            resource_type, resource_id, actor_id=ctx.actor_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Validate transition & capabilities in database-backed EditorialAuthorizationService
    await editorial_auth.authorize_transition(
        context=ctx,
        resource=current_state,
        target_status=body.target_status,
        reason=body.reason,
    )

    try:
        result = await service.transition_status(
            resource_type=resource_type,
            resource_id=resource_id,
            target_status=body.target_status,
            actor_id=ctx.actor_id,
            reason=body.reason,
            expected_version=body.expected_version or current_state.version,
        )
        return StatusTransitionEnvelope(data=result)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        msg = str(exc)
        if "não foi" in msg and "encontrado" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        elif "Conflito de concorrência" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from exc
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg
            ) from exc


@router.get(
    "/workflow/{resource_type}/{resource_id}/publish-guard",
    response_model=PublishGuardResultEnvelope,
    summary="Consultar Publish Guard",
    description="Consultar os critérios e elegibilidade do Publish Guard para um recurso.",
)
async def get_publish_guard_status(
    resource_type: str,
    resource_id: uuid.UUID,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> PublishGuardResultEnvelope:
    ctx = _build_context(current_user)
    # Require basic content capability to view publish guard
    await editorial_auth.require_capability(ctx, "content.review.submit")
    result = await service.get_publish_guard(resource_type, resource_id)
    return PublishGuardResultEnvelope(data=result)


# -----------------------------------------------------------------------------
# Editorial Alerts
# -----------------------------------------------------------------------------


@router.get(
    "/alerts",
    response_model=EditorialAlertListEnvelope,
    summary="Listar alertas editoriais",
    description=(
        "Listar alertas editoriais ativos ou resolvidos com suporte a filtros de rota e severidade."
    ),
)
async def list_editorial_alerts(
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
    route_id: uuid.UUID | None = Query(None, description="Filtrar por rota"),  # noqa: B008
    severity: str | None = Query(None, description="Filtrar por severidade"),  # noqa: B008
    is_active: bool | None = Query(None, description="Filtrar por estado ativo"),  # noqa: B008
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> EditorialAlertListEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "content.review.submit")
    data, meta = await service.list_alerts(
        route_id=route_id,
        severity=severity,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return EditorialAlertListEnvelope(data=list(data), meta=meta)


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=EditorialAlertEnvelope,
    summary="Resolver alerta editorial",
    description="Resolver um alerta editorial ativo fornecendo uma nota explicativa de resolução.",
)
async def resolve_editorial_alert(
    alert_id: uuid.UUID,
    body: AlertResolveRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> EditorialAlertEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "content.publish")
    try:
        result = await service.resolve_alert(
            alert_id=alert_id,
            actor_id=ctx.actor_id,
            resolution_note=body.resolution_note,
        )
        return EditorialAlertEnvelope(data=result)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# -----------------------------------------------------------------------------
# Reconciliation Candidates
# -----------------------------------------------------------------------------


@router.get(
    "/reconciliation/candidates",
    response_model=ReconciliationCandidateListEnvelope,
    summary="Listar candidatos de reconciliação",
    description="Listar candidatos a duplicata para revisão humana e reconciliação editorial.",
)
async def list_reconciliation_candidates(
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ReconciliationCandidateListEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "actor.write")
    data, meta = await service.list_reconciliation_candidates(
        status=status_filter, limit=limit, offset=offset
    )
    return ReconciliationCandidateListEnvelope(data=list(data), meta=meta)


@router.post(
    "/reconciliation/{candidate_id}/decision",
    response_model=ReconciliationDecisionEnvelope,
    summary="Decidir reconciliação",
    description=(
        "Registrar decisão editorial (accept, reject, merge) sobre candidato de "
        "reconciliação com justificativa auditada."
    ),
)
async def decide_reconciliation_candidate(
    candidate_id: uuid.UUID,
    body: ReconciliationDecisionRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> ReconciliationDecisionEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "actor.write")
    try:
        result = await service.decide_reconciliation(
            candidate_id=candidate_id,
            actor_id=ctx.actor_id,
            decision=body.decision,
            reason=body.reason,
            target_actor_id=body.target_actor_id,
        )
        return ReconciliationDecisionEnvelope(data=result)
    except ValueError as exc:
        msg = str(exc)
        if "não encontrado" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg) from exc


@router.post(
    "/reconciliation/{candidate_id}/compensate",
    response_model=ReconciliationDecisionEnvelope,
    summary="Compensar merge de reconciliação",
)
async def compensate_reconciliation_merge(
    candidate_id: uuid.UUID,
    body: ReconciliationCompensationRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> ReconciliationDecisionEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "actor.write")
    try:
        result = await service.compensate_reconciliation_merge(
            candidate_id=candidate_id, actor_id=ctx.actor_id, reason=body.reason
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ReconciliationDecisionEnvelope(data=result)
@router.post(
    "/alerts", response_model=EditorialAlertEnvelope, status_code=status.HTTP_201_CREATED,
    summary="Criar alerta editorial",
)
async def create_editorial_alert(
    body: EditorialAlertCreateRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> EditorialAlertEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "content.publish")
    try:
        result = await service.create_alert(
            actor_id=ctx.actor_id, values=body.model_dump()
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return EditorialAlertEnvelope(data=result)


@router.put(
    "/alerts/{alert_id}", response_model=EditorialAlertEnvelope,
    summary="Atualizar alerta editorial",
)
async def update_editorial_alert(
    alert_id: uuid.UUID,
    body: EditorialAlertUpdateRequest,
    current_user: CurrentUserDep,
    editorial_auth: EditorialAuthDep,
    service: WorkflowAdminServiceDep,
) -> EditorialAlertEnvelope:
    ctx = _build_context(current_user)
    await editorial_auth.require_capability(ctx, "content.publish")
    try:
        result = await service.update_alert(
            alert_id=alert_id,
            actor_id=ctx.actor_id,
            values=body.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        code = (
            status.HTTP_409_CONFLICT
            if "Conflito" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return EditorialAlertEnvelope(data=result)
