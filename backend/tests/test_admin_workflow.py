"""Test suite for ECO-1604 Admin Workflow, Alerts, and Reconciliation."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
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
    RouteOrigin,
)
from app.repositories.workflow_admin import WorkflowAdminRepository
from app.schemas.admin_workflow import (
    EditorialAlertCreateRequest,
    EditorialAlertSchema,
    PublishGuardResultSchema,
    ReconciliationCandidateSchema,
    ReconciliationDecisionSchema,
    StatusTransitionSchema,
)
from app.schemas.envelopes import PaginationMeta
from app.services.dependencies import (
    get_editorial_authorization_service,
    get_workflow_admin_service,
)
from app.services.workflow_admin import WorkflowAdminService


def authenticated_user(*, anonymous: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid.uuid4(),
        email=None,
        is_anonymous=anonymous,
        role="authenticated",
        claims={},
    )


def mock_editorial_auth(forbidden_capability: str | None = None) -> AsyncMock:
    auth = AsyncMock()

    async def require_cap(ctx, capability: str) -> None:
        if forbidden_capability and capability == forbidden_capability:
            raise HTTPException(status_code=403, detail="Permissão negada")

    async def auth_trans(context, resource, target_status, reason=None) -> str:
        if forbidden_capability == "content.publish" and target_status == "published":
            raise HTTPException(status_code=403, detail="Permissão negada para publicar")
        return "content.publish"

    auth.require_capability = AsyncMock(side_effect=require_cap)
    auth.authorize_transition = AsyncMock(side_effect=auth_trans)
    return auth


# -----------------------------------------------------------------------------
# API Route Endpoint Tests
# -----------------------------------------------------------------------------


def test_admin_workflow_transition_forbidden_anonymous() -> None:
    user = authenticated_user(anonymous=True)
    editorial_auth = mock_editorial_auth()
    workflow_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/workflow/route/{uuid.uuid4()}/transition",
            json={"target_status": "published"},
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_workflow_transition_forbidden_capability() -> None:
    user = authenticated_user()
    editorial_auth = mock_editorial_auth(forbidden_capability="content.publish")
    workflow_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/workflow/route/{uuid.uuid4()}/transition",
            json={"target_status": "published"},
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_workflow_transition_success() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    editorial_auth = mock_editorial_auth()
    workflow_service = AsyncMock()

    now = datetime.now(UTC)
    transition_schema = StatusTransitionSchema(
        resource_type="route",
        resource_id=route_id,
        previous_status="draft",
        new_status="published",
        version=2,
        audit_log_id=uuid.uuid4(),
        updated_at=now,
    )

    state_mock = EditorialResourceState(
        id=uuid.uuid4(),
        resource_type="route",
        resource_id=route_id,
        status="draft",
        author_id=user.id,
        version=1,
    )
    workflow_service.get_authorization_state = AsyncMock(return_value=state_mock)
    workflow_service.transition_status = AsyncMock(return_value=transition_schema)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/workflow/route/{route_id}/transition",
            json={"target_status": "published", "reason": "Aprovado"},
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["new_status"] == "published"


def test_admin_workflow_transition_exception_handlers() -> None:
    """Test 404, 409, 422, and PermissionError HTTP exception paths in transition router."""
    user = authenticated_user()
    route_id = uuid.uuid4()
    editorial_auth = mock_editorial_auth()

    state_mock = EditorialResourceState(
        id=uuid.uuid4(),
        resource_type="route",
        resource_id=route_id,
        status="draft",
        author_id=user.id,
        version=1,
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth

    # Test 404
    wf_service_404 = AsyncMock()
    wf_service_404.get_authorization_state = AsyncMock(return_value=state_mock)
    wf_service_404.transition_status = AsyncMock(
        side_effect=ValueError("Recurso não foi encontrado")
    )
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_service_404
    res_404 = TestClient(app).post(
        f"/api/v1/admin/workflow/route/{route_id}/transition",
        json={"target_status": "review"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_404.status_code == 404

    # Test 409
    wf_service_409 = AsyncMock()
    wf_service_409.get_authorization_state = AsyncMock(return_value=state_mock)
    wf_service_409.transition_status = AsyncMock(side_effect=ValueError("Conflito de concorrência"))
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_service_409
    res_409 = TestClient(app).post(
        f"/api/v1/admin/workflow/route/{route_id}/transition",
        json={"target_status": "review"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_409.status_code == 409

    # Test 422
    wf_service_422 = AsyncMock()
    wf_service_422.get_authorization_state = AsyncMock(return_value=state_mock)
    wf_service_422.transition_status = AsyncMock(
        side_effect=ValueError("Requisitos de publicação não atendidos")
    )
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_service_422
    res_422 = TestClient(app).post(
        f"/api/v1/admin/workflow/route/{route_id}/transition",
        json={"target_status": "published"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_422.status_code == 422

    # Test PermissionError (403)
    wf_service_perm = AsyncMock()
    wf_service_perm.get_authorization_state = AsyncMock(return_value=state_mock)
    wf_service_perm.transition_status = AsyncMock(
        side_effect=PermissionError("Segregação de funções")
    )
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_service_perm
    res_perm = TestClient(app).post(
        f"/api/v1/admin/workflow/route/{route_id}/transition",
        json={"target_status": "published"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_perm.status_code == 403

    app.dependency_overrides.clear()


def test_admin_alerts_resolve_404() -> None:
    user = authenticated_user()
    editorial_auth = mock_editorial_auth()
    wf_service = AsyncMock()
    wf_service.resolve_alert = AsyncMock(side_effect=LookupError("Alerta não encontrado"))

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_service
    try:
        res = TestClient(app).post(
            f"/api/v1/admin/alerts/{uuid.uuid4()}/resolve",
            json={"resolution_note": "Resolução"},
            headers={"Authorization": "Bearer token"},
        )
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_reconciliation_decision_exceptions() -> None:
    user = authenticated_user()
    editorial_auth = mock_editorial_auth()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth

    # 404
    wf_404 = AsyncMock()
    wf_404.decide_reconciliation = AsyncMock(side_effect=ValueError("Candidato não encontrado"))
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_404
    res_404 = TestClient(app).post(
        f"/api/v1/admin/reconciliation/{uuid.uuid4()}/decision",
        json={"decision": "accept", "reason": "Justificativa"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_404.status_code == 404

    # 422
    wf_422 = AsyncMock()
    wf_422.decide_reconciliation = AsyncMock(side_effect=ValueError("Decisão inválida"))
    app.dependency_overrides[get_workflow_admin_service] = lambda: wf_422
    res_422 = TestClient(app).post(
        f"/api/v1/admin/reconciliation/{uuid.uuid4()}/decision",
        json={"decision": "accept", "reason": "Justificativa"},
        headers={"Authorization": "Bearer token"},
    )
    assert res_422.status_code == 422

    app.dependency_overrides.clear()


def test_admin_workflow_publish_guard() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    editorial_auth = mock_editorial_auth()
    workflow_service = AsyncMock()

    guard_schema = PublishGuardResultSchema(
        resource_type="route",
        resource_id=route_id,
        current_status="draft",
        is_eligible=False,
        missing_requirements=["Falta origem de rota"],
        warnings=[],
    )
    workflow_service.get_publish_guard = AsyncMock(return_value=guard_schema)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        response = TestClient(app).get(
            f"/api/v1/admin/workflow/route/{route_id}/publish-guard",
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["is_eligible"] is False
    assert len(response.json()["data"]["missing_requirements"]) == 1


def test_admin_alerts_list_and_resolve() -> None:
    user = authenticated_user()
    alert_id = uuid.uuid4()
    route_id = uuid.uuid4()
    editorial_auth = mock_editorial_auth()
    workflow_service = AsyncMock()

    now = datetime.now(UTC)
    alert_schema = EditorialAlertSchema(
        id=alert_id,
        route_id=route_id,
        title="Interdição temporária",
        message="Obras na pista",
        severity="warning",
        is_active=True,
        created_at=now,
    )
    meta = PaginationMeta(total=1, limit=50, offset=0, has_next=False)

    workflow_service.list_alerts = AsyncMock(return_value=([alert_schema], meta))

    resolved_schema = EditorialAlertSchema(
        id=alert_id,
        route_id=route_id,
        title="Interdição temporária",
        message="Obras na pista",
        severity="warning",
        is_active=False,
        resolved_at=now,
        resolved_by=user.id,
        created_at=now,
    )
    workflow_service.resolve_alert = AsyncMock(return_value=resolved_schema)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        # List
        res_list = TestClient(app).get(
            f"/api/v1/admin/alerts?route_id={route_id}",
            headers={"Authorization": "Bearer token"},
        )
        assert res_list.status_code == 200
        assert len(res_list.json()["data"]) == 1

        # Resolve
        res_resolve = TestClient(app).post(
            f"/api/v1/admin/alerts/{alert_id}/resolve",
            json={"resolution_note": "Concluído"},
            headers={"Authorization": "Bearer token"},
        )
        assert res_resolve.status_code == 200
        assert res_resolve.json()["data"]["is_active"] is False
    finally:
        app.dependency_overrides.clear()


def test_alert_window_validation() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="posterior"):
        EditorialAlertCreateRequest(
            route_id=uuid.uuid4(), title="Alerta", message="Mensagem",
            starts_at=now, ends_at=now,
        )
    with pytest.raises(ValueError, match="fuso horário"):
        EditorialAlertCreateRequest(
            route_id=uuid.uuid4(), title="Alerta", message="Mensagem",
            starts_at=datetime.now(),
        )


def test_admin_alert_create_update_and_compensate() -> None:
    user = authenticated_user()
    route_id = uuid.uuid4()
    alert_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    now = datetime.now(UTC)
    alert = EditorialAlertSchema(
        id=alert_id, route_id=route_id, title="Interdição", message="Obras",
        severity="warning", is_active=True, published_at=now, created_at=now,
    )
    compensation = ReconciliationDecisionSchema(
        candidate_id=candidate_id, status="pending", decision="compensate",
        decision_notes="Reverter merge incorreto", audit_log_id=uuid.uuid4(), updated_at=now,
    )
    service = AsyncMock()
    service.create_alert.return_value = alert
    service.update_alert.return_value = alert
    service.compensate_reconciliation_merge.return_value = compensation
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = mock_editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: service
    try:
        client = TestClient(app)
        payload = {
            "route_id": str(route_id), "title": "Interdição", "message": "Obras",
            "severity": "warning", "published_at": now.isoformat(),
        }
        assert client.post("/api/v1/admin/alerts", json=payload).status_code == 201
        payload.pop("route_id")
        assert client.put(f"/api/v1/admin/alerts/{alert_id}", json=payload).status_code == 200
        response = client.post(
            f"/api/v1/admin/reconciliation/{candidate_id}/compensate",
            json={"reason": "Reverter merge incorreto"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["decision"] == "compensate"
    finally:
        app.dependency_overrides.clear()


def test_admin_reconciliation_list_and_decide() -> None:
    user = authenticated_user()
    cand_id = uuid.uuid4()
    editorial_auth = mock_editorial_auth()
    workflow_service = AsyncMock()

    now = datetime.now(UTC)
    cand_schema = ReconciliationCandidateSchema(
        id=cand_id,
        actor_id_a=uuid.uuid4(),
        actor_id_b=uuid.uuid4(),
        score=0.95,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    meta = PaginationMeta(total=1, limit=50, offset=0, has_next=False)
    workflow_service.list_reconciliation_candidates = AsyncMock(return_value=([cand_schema], meta))

    dec_schema = ReconciliationDecisionSchema(
        candidate_id=cand_id,
        status="merged",
        decision="merge",
        decision_notes="Duplicata confirmada",
        audit_log_id=uuid.uuid4(),
        updated_at=now,
    )
    workflow_service.decide_reconciliation = AsyncMock(return_value=dec_schema)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: editorial_auth
    app.dependency_overrides[get_workflow_admin_service] = lambda: workflow_service
    try:
        # List
        res_list = TestClient(app).get(
            "/api/v1/admin/reconciliation/candidates",
            headers={"Authorization": "Bearer token"},
        )
        assert res_list.status_code == 200
        assert len(res_list.json()["data"]) == 1

        # Decide
        res_dec = TestClient(app).post(
            f"/api/v1/admin/reconciliation/{cand_id}/decision",
            json={"decision": "merge", "reason": "Duplicata confirmada"},
            headers={"Authorization": "Bearer token"},
        )
        assert res_dec.status_code == 200
        assert res_dec.json()["data"]["status"] == "merged"
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Service Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_list_alerts_and_reconciliation_candidates() -> None:
    repo = AsyncMock()
    now = datetime.now(UTC)
    alert = RouteAlert(
        id=uuid.uuid4(),
        route_id=uuid.uuid4(),
        title="Alerta",
        message="Msg",
        severity="info",
        is_active=True,
        published_at=now,
        created_at=now,
    )
    repo.list_alerts = AsyncMock(return_value=([alert], 1))

    cand = ReconciliationCandidate(
        id=uuid.uuid4(),
        actor_id_a=uuid.uuid4(),
        actor_id_b=uuid.uuid4(),
        score=0.88,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    repo.list_reconciliation_candidates = AsyncMock(return_value=([cand], 1))

    service = WorkflowAdminService(repo)

    alerts, meta1 = await service.list_alerts()
    assert len(alerts) == 1
    assert meta1.total == 1

    cands, meta2 = await service.list_reconciliation_candidates()
    assert len(cands) == 1
    assert meta2.total == 1


@pytest.mark.asyncio
async def test_service_transition_status_invalid_target() -> None:
    repo = AsyncMock()
    service = WorkflowAdminService(repo)

    with pytest.raises(ValueError) as exc:
        await service.transition_status(
            resource_type="route",
            resource_id=uuid.uuid4(),
            target_status="invalid_status",
            actor_id=uuid.uuid4(),
        )
    assert "inválido" in str(exc.value)


@pytest.mark.asyncio
async def test_service_transition_status_resource_not_found() -> None:
    repo = AsyncMock()
    repo.check_resource_exists = AsyncMock(return_value=False)
    service = WorkflowAdminService(repo)

    with pytest.raises(ValueError) as exc:
        await service.transition_status(
            resource_type="route",
            resource_id=uuid.uuid4(),
            target_status="review",
            actor_id=uuid.uuid4(),
        )
    assert "não foi encontrado" in str(exc.value)


@pytest.mark.asyncio
async def test_service_transition_status_publish_guard_failure() -> None:
    repo = AsyncMock()
    service = WorkflowAdminService(repo)

    route_id = uuid.uuid4()
    repo.check_resource_exists = AsyncMock(return_value=True)
    repo.transition_resource_state = AsyncMock(
        side_effect=ValueError(
            "Recurso não atende aos requisitos de publicação: Falta origem"
        )
    )

    with pytest.raises(ValueError) as exc:
        await service.transition_status(
            resource_type="route",
            resource_id=route_id,
            target_status="published",
            actor_id=uuid.uuid4(),
        )
    assert "requisitos de publicação" in str(exc.value)


@pytest.mark.asyncio
async def test_service_transition_status_editor_self_publish_denied() -> None:
    repo = AsyncMock()
    actor_id = uuid.uuid4()
    route_id = uuid.uuid4()

    repo.check_resource_exists = AsyncMock(return_value=True)
    repo.transition_resource_state = AsyncMock(
        side_effect=PermissionError(
            "Segregação de funções: o autor não pode publicar o próprio conteúdo."
        )
    )
    service = WorkflowAdminService(repo)

    with pytest.raises(PermissionError) as exc:
        await service.transition_status(
            resource_type="route",
            resource_id=route_id,
            target_status="published",
            actor_id=actor_id,
            user_role="editor",
        )
    assert "Segregação de funções" in str(exc.value)


@pytest.mark.asyncio
async def test_service_resolve_alert_not_found() -> None:
    repo = AsyncMock()
    repo.resolve_alert = AsyncMock(return_value=None)
    service = WorkflowAdminService(repo)

    with pytest.raises(LookupError) as exc:
        await service.resolve_alert(uuid.uuid4(), uuid.uuid4(), "Nota")
    assert "não encontrado" in str(exc.value)


@pytest.mark.asyncio
async def test_service_decide_reconciliation_not_found_or_invalid() -> None:
    repo = AsyncMock()
    repo.decide_reconciliation = AsyncMock(return_value=None)
    service = WorkflowAdminService(repo)

    with pytest.raises(ValueError) as exc1:
        await service.decide_reconciliation(
            candidate_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            decision="unknown_decision",
            reason="Motivo de teste",
        )
    assert "inválida" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        await service.decide_reconciliation(
            candidate_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            decision="accept",
            reason="Motivo de teste",
        )
    assert "não encontrado" in str(exc2.value)


# -----------------------------------------------------------------------------
# Repository Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repo_check_resource_exists() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)

    exec_mock = MagicMock()
    exec_mock.scalar_one.return_value = 1
    db.execute = AsyncMock(return_value=exec_mock)

    assert await repo.check_resource_exists("route", uuid.uuid4()) is True
    assert await repo.check_resource_exists("actor", uuid.uuid4()) is True

    exec_mock_zero = MagicMock()
    exec_mock_zero.scalar_one.return_value = 0
    db.execute = AsyncMock(return_value=exec_mock_zero)

    assert await repo.check_resource_exists("unknown_type", uuid.uuid4()) is False


@pytest.mark.asyncio
async def test_repo_publish_guard_status_actor_and_route() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)

    actor_id = uuid.uuid4()
    actor = Actor(
        id=actor_id,
        category_id=None,  # missing category
        name="Ator Sem Categoria",
        address=None,
        city=None,
        location=None,
    )
    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.side_effect = [None, actor]
    exec_mock.scalar_one.return_value = 0
    db.execute = AsyncMock(return_value=exec_mock)

    # Actor guard check
    is_elig, status, missing, warnings = await repo.get_publish_guard_status("actor", actor_id)
    assert is_elig is False
    assert any("categoria" in m for m in missing)
    assert any("coordenadas" in m for m in missing)
    assert any("rota ativa" in m for m in missing)
    assert any("verificado" in m for m in missing)
    assert warnings == []

    # Unknown resource type guard check
    exec_mock_u = MagicMock()
    exec_mock_u.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=exec_mock_u)
    is_elig_u, _, missing_u, _ = await repo.get_publish_guard_status("unknown_type", uuid.uuid4())
    assert is_elig_u is False
    assert len(missing_u) > 0


def _scalar_result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    result.scalar_one.return_value = value
    return result


@pytest.mark.asyncio
async def test_repo_publish_guard_route_complete() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    route_id = uuid.uuid4()
    media_id = uuid.uuid4()
    route = Route(
        id=route_id,
        region_id=uuid.uuid4(),
        slug="rota",
        title="Rota",
        summary="Descrição",
        city="Santarém",
        state_code="PA",
        cover_media_id=media_id,
    )
    media = MediaAsset(
        id=media_id,
        owner_type="route",
        owner_id=route_id,
        storage_key="routes/cover.webp",
        mime_type="image/webp",
        alt_text="Vista da rota",
        credit="SEMTUR — licença institucional",
        license_code="SEMTUR_INSTITUTIONAL",
        processing_status="ready",
        checksum_sha256="a" * 64,
        processed_at=datetime.now(UTC),
        derivatives={
            name: {"storage_key": f"routes/{name}.webp", "checksum_sha256": "b" * 64}
            for name in ("thumb", "card", "hero")
        },
    )
    db.execute = AsyncMock(
        side_effect=[
            _scalar_result(None),
            _scalar_result(route),
            _scalar_result(1),
            _scalar_result(1),
            _scalar_result(media),
        ]
    )

    eligible, status, missing, warnings = await repo.get_publish_guard_status(
        "route", route_id
    )

    assert (eligible, status, missing, warnings) == (True, "draft", [], [])


@pytest.mark.asyncio
async def test_repo_publish_guard_region_origin_and_media_fail_closed() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    region = Region(
        id=uuid.uuid4(), slug="oeste-para", name="Oeste do Pará",
        state_code="PA", center=None,
    )
    db.execute = AsyncMock(side_effect=[_scalar_result(None), _scalar_result(region)])
    eligible, _, missing, _ = await repo.get_publish_guard_status("region", region.id)
    assert eligible is False
    assert any("coordenadas centrais" in item for item in missing)
    assert any("não estão modeladas" in item for item in missing)

    origin = RouteOrigin(
        id=uuid.uuid4(), route_id=uuid.uuid4(), code="porto",
        name="Porto", location=None,
    )
    db.execute = AsyncMock(
        side_effect=[_scalar_result(None), _scalar_result(origin), _scalar_result(0)]
    )
    eligible, _, missing, _ = await repo.get_publish_guard_status("origin", origin.id)
    assert eligible is False
    assert any("coordenadas" in item for item in missing)
    assert any("LineString" in item for item in missing)

    media = MediaAsset(
        id=uuid.uuid4(), owner_type="route", owner_id=uuid.uuid4(),
        storage_key="route/cover.webp", mime_type="image/webp",
        alt_text=None, credit=None,
    )
    db.execute = AsyncMock(side_effect=[_scalar_result(None), _scalar_result(media)])
    eligible, _, missing, _ = await repo.get_publish_guard_status("media", media.id)
    assert eligible is False
    assert any("texto alternativo" in item for item in missing)
    assert any("licença estruturada" in item for item in missing)
    assert any("processada e pronta" in item for item in missing)


@pytest.mark.asyncio
async def test_repo_publish_guard_actor_complete_and_resource_type_lookup() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    actor = Actor(
        id=uuid.uuid4(), category_id=uuid.uuid4(), slug="ator", name="Ator",
        location="POINT(-54 -2)", phone="(93) 99999-9999",
        verification_status="verified",
    )
    db.execute = AsyncMock(
        side_effect=[_scalar_result(None), _scalar_result(actor), _scalar_result(1)]
    )
    eligible, _, missing, warnings = await repo.get_publish_guard_status("actor", actor.id)
    assert (eligible, missing, warnings) == (True, [], [])

    for resource_type in ("region", "route", "origin", "actor", "media"):
        db.execute = AsyncMock(return_value=_scalar_result(1))
        assert await repo.check_resource_exists(resource_type, uuid.uuid4()) is True
    assert await repo.check_resource_exists("unsupported", uuid.uuid4()) is False


@pytest.mark.asyncio
async def test_repo_alert_create_update_resolve_lifecycle() -> None:
    db = MagicMock()
    db.flush = AsyncMock()
    repo = WorkflowAdminRepository(db)
    repo.check_resource_exists = AsyncMock(return_value=True)  # type: ignore[method-assign]
    actor_id = uuid.uuid4()
    route_id = uuid.uuid4()
    now = datetime.now(UTC)

    created = await repo.create_alert(
        actor_id=actor_id,
        values={
            "route_id": route_id,
            "title": "Interdição",
            "message": "Obras na via",
            "severity": "warning",
            "starts_at": now,
            "ends_at": None,
            "published_at": now,
            "source": "SEMTUR",
            "is_active": True,
        },
    )
    assert created is not None
    alert, create_audit = created
    assert create_audit.action == "CREATE"
    assert alert.is_active is True

    repo.get_alert_by_id = AsyncMock(return_value=alert)  # type: ignore[method-assign]
    updated = await repo.update_alert(
        alert_id=alert.id,
        actor_id=actor_id,
        values={"title": "Interdição parcial"},
    )
    assert updated is not None
    assert updated[0].title == "Interdição parcial"
    assert updated[1].action == "UPDATE"

    resolved = await repo.resolve_alert(alert.id, actor_id, "Via liberada")
    assert resolved is not None
    assert resolved[0].is_active is False
    assert resolved[1].reason == "Via liberada"

    with pytest.raises(ValueError, match="já foi resolvido"):
        await repo.resolve_alert(alert.id, actor_id, "Repetido")


@pytest.mark.asyncio
async def test_repo_workflow_resource_state_concurrency_error() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)

    resource_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    now = datetime.now(UTC)

    state = EditorialResourceState(
        id=uuid.uuid4(),
        resource_type="route",
        resource_id=resource_id,
        status="draft",
        author_id=actor_id,
        version=2,
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = state
    db.execute = AsyncMock(return_value=exec_mock)

    with pytest.raises(ValueError) as exc:
        await repo.transition_resource_state(
            resource_type="route",
            resource_id=resource_id,
            target_status="published",
            actor_id=actor_id,
            expected_version=1,  # mismatch with version=2
        )
    assert "Conflito de concorrência" in str(exc.value)


@pytest.mark.asyncio
async def test_repo_transition_runs_publish_guard_after_lock_before_mutation() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    resource_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    state = EditorialResourceState(
        id=uuid.uuid4(), resource_type="route", resource_id=resource_id,
        status="draft", author_id=actor_id, version=1,
    )
    repo.get_or_create_resource_state = AsyncMock(return_value=state)  # type: ignore[method-assign]
    repo.get_publish_guard_status = AsyncMock(  # type: ignore[method-assign]
        return_value=(False, "draft", ["Falta origem"], [])
    )
    repo.log_action = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="Falta origem"):
        await repo.transition_resource_state(
            resource_type="route", resource_id=resource_id, target_status="review",
            actor_id=actor_id, expected_version=1,
        )

    repo.get_or_create_resource_state.assert_awaited_once()
    repo.get_publish_guard_status.assert_awaited_once()
    repo.log_action.assert_not_awaited()
    assert state.status == "draft"
    assert state.version == 1


@pytest.mark.asyncio
async def test_repo_decide_reconciliation_merge() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)

    cand_id = uuid.uuid4()
    actor_a_id = uuid.uuid4()
    actor_b_id = uuid.uuid4()
    now = datetime.now(UTC)

    cand = ReconciliationCandidate(
        id=cand_id,
        actor_id_a=actor_a_id,
        actor_id_b=actor_b_id,
        score=0.9,
        status="pending",
    )
    actor_b = Actor(id=actor_b_id, category_id=uuid.uuid4(), slug="actor-b", name="B")
    route_actor_link = RouteActor(
        id=uuid.uuid4(), route_id=uuid.uuid4(), actor_id=actor_b_id
    )
    ext_ref = ActorExternalRef(
        id=uuid.uuid4(), actor_id=actor_b_id, source_id=uuid.uuid4(), external_id="123"
    )

    audit = AuditLog(
        id=uuid.uuid4(),
        timestamp=now,
        actor_id=uuid.uuid4(),
        action="reconciliation.merge",
        resource_type="reconciliation_candidate",
        resource_id=cand_id,
        changes={},
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.side_effect = [cand, None, actor_b]
    exec_mock.scalars.return_value.all.side_effect = [[route_actor_link], [ext_ref]]
    db.execute = AsyncMock(return_value=exec_mock)
    repo.log_action = AsyncMock(return_value=audit)

    res = await repo.decide_reconciliation(
        candidate_id=cand_id,
        actor_id=uuid.uuid4(),
        decision="merge",
        reason="Duplicata confirmada",
        target_actor_id=actor_a_id,
    )
    assert res is not None
    updated_cand, audit_log = res
    assert updated_cand.status == "merged"
    assert route_actor_link.actor_id == actor_a_id
    assert ext_ref.actor_id == actor_a_id
    assert actor_b.deleted_at is not None
    audit_changes = repo.log_action.await_args.kwargs["changes"]
    assert audit_changes["merge_snapshot"]["route_actor_link_ids"] == [str(route_actor_link.id)]
    assert audit_changes["merge_snapshot"]["external_ref_ids"] == [str(ext_ref.id)]


@pytest.mark.asyncio
async def test_repo_merge_archives_duplicate_route_link_reversibly() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    actor_a_id = uuid.uuid4()
    actor_b_id = uuid.uuid4()
    candidate = ReconciliationCandidate(
        id=uuid.uuid4(),
        actor_id_a=actor_a_id,
        actor_id_b=actor_b_id,
        score=0.9,
        status="pending",
    )
    secondary_link = RouteActor(
        id=uuid.uuid4(), route_id=uuid.uuid4(), actor_id=actor_b_id
    )
    transferable_link = RouteActor(
        id=uuid.uuid4(), route_id=uuid.uuid4(), actor_id=actor_b_id
    )
    primary_link = RouteActor(
        id=uuid.uuid4(), route_id=secondary_link.route_id, actor_id=actor_a_id
    )
    candidate_result = MagicMock()
    candidate_result.scalar_one_or_none.return_value = candidate
    links_result = MagicMock()
    links_result.scalars.return_value.all.return_value = [transferable_link, secondary_link]
    no_duplicate_result = MagicMock()
    no_duplicate_result.scalar_one_or_none.return_value = None
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none.return_value = primary_link
    refs_result = MagicMock()
    refs_result.scalars.return_value.all.return_value = []
    secondary_actor_result = MagicMock()
    secondary_actor_result.scalar_one_or_none.return_value = Actor(
        id=actor_b_id, category_id=uuid.uuid4(), slug="secondary", name="Secondary"
    )
    db.execute = AsyncMock(side_effect=[
        candidate_result,
        links_result,
        no_duplicate_result,
        duplicate_result,
        refs_result,
        secondary_actor_result,
    ])
    audit = AuditLog(
        id=uuid.uuid4(), timestamp=datetime.now(UTC), actor_id=uuid.uuid4(),
        action="RECONCILE", resource_type="reconciliation_candidate",
        resource_id=candidate.id, changes={},
    )
    repo.log_action = AsyncMock(return_value=audit)
    editor_id = uuid.uuid4()

    result = await repo.decide_reconciliation(
        candidate_id=candidate.id,
        actor_id=editor_id,
        decision="merge",
        reason="Duplicata confirmada",
        target_actor_id=actor_a_id,
    )

    assert result is not None
    assert candidate.status == "merged"
    assert transferable_link.actor_id == actor_a_id
    assert secondary_link.actor_id == actor_b_id
    assert secondary_link.archived_at is not None
    assert secondary_link.archived_by == editor_id
    assert secondary_link.archive_reason == "Duplicata confirmada"
    snapshot = repo.log_action.await_args.kwargs["changes"]["merge_snapshot"]
    assert snapshot["route_actor_link_ids"] == [str(transferable_link.id)]
    assert snapshot["archived_route_actor_link_ids"] == [str(secondary_link.id)]


@pytest.mark.asyncio
async def test_repo_compensate_merge_restores_only_snapshot() -> None:
    db = AsyncMock()
    repo = WorkflowAdminRepository(db)
    candidate_id = uuid.uuid4()
    primary_id = uuid.uuid4()
    secondary_id = uuid.uuid4()
    deleted_at = datetime.now(UTC)
    candidate = ReconciliationCandidate(
        id=candidate_id, actor_id_a=primary_id, actor_id_b=secondary_id,
        score=0.9, status="merged",
    )
    link = RouteActor(id=uuid.uuid4(), route_id=uuid.uuid4(), actor_id=primary_id)
    archived_link = RouteActor(
        id=uuid.uuid4(), route_id=uuid.uuid4(), actor_id=secondary_id,
        archived_at=deleted_at, archived_by=uuid.uuid4(), archive_reason="Duplicata",
    )
    ref = ActorExternalRef(
        id=uuid.uuid4(), actor_id=primary_id, source_id=uuid.uuid4(), external_id="123"
    )
    secondary = Actor(
        id=secondary_id, category_id=uuid.uuid4(), slug="secondary", name="Secondary",
        deleted_at=deleted_at,
    )
    merge_audit = AuditLog(
        id=uuid.uuid4(), timestamp=deleted_at, actor_id=uuid.uuid4(), action="RECONCILE",
        resource_type="reconciliation_candidate", resource_id=candidate_id,
        changes={
            "decision": "merge", "before": {"status": "pending"},
            "merge_snapshot": {
                "primary_actor_id": str(primary_id), "secondary_actor_id": str(secondary_id),
                "route_actor_link_ids": [str(link.id)],
                "archived_route_actor_link_ids": [str(archived_link.id)],
                "external_ref_ids": [str(ref.id)],
                "secondary_deleted_at_before": None,
                "secondary_deleted_at_after": deleted_at.isoformat(),
            },
        },
    )
    results = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    results[0].scalars.return_value.all.return_value = [merge_audit]
    results[1].scalars.return_value.all.return_value = [link]
    results[2].scalars.return_value.all.return_value = [archived_link]
    results[3].scalars.return_value.all.return_value = [ref]
    results[4].scalar_one_or_none.return_value = secondary
    db.execute = AsyncMock(side_effect=results)
    repo.get_reconciliation_candidate_by_id = AsyncMock(return_value=candidate)
    audit = AuditLog(
        id=uuid.uuid4(), timestamp=deleted_at, actor_id=uuid.uuid4(),
        action="RECONCILE_COMPENSATE", resource_type="reconciliation_candidate",
        resource_id=candidate_id, changes={},
    )
    repo.log_action = AsyncMock(return_value=audit)

    result = await repo.compensate_reconciliation_merge(
        candidate_id=candidate_id, actor_id=uuid.uuid4(), reason="Merge incorreto"
    )
    assert result is not None
    assert candidate.status == "pending"
    assert link.actor_id == secondary_id
    assert archived_link.archived_at is None
    assert archived_link.archived_by is None
    assert archived_link.archive_reason is None
    assert ref.actor_id == secondary_id
    assert secondary.deleted_at is None
