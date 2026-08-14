"""Authorization matrix for the ECO-1601 administrative boundary."""

import uuid
from unittest.mock import AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.services.dependencies import get_editorial_authorization_service
from app.services.editorial_authorization import ScopedEditorialAccess


def authenticated_user(*, anonymous: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid.uuid4(),
        email=None,
        is_anonymous=anonymous,
        role="authenticated",
        claims={},
    )


def test_admin_context_requires_bearer_token() -> None:
    response = TestClient(app).get("/api/v1/admin/context")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_context_denies_anonymous_or_ordinary_member_without_leaking_data() -> None:
    user = authenticated_user(anonymous=True)
    authorization = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: authorization
    try:
        response = TestClient(app).get(
            "/api/v1/admin/context",
            headers={"Authorization": "Bearer ignored-by-override"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "FORBIDDEN",
        "message": "A identidade não possui acesso editorial.",
        "details": None,
    }
    assert str(user.id) not in response.text
    authorization.access_summary.assert_not_awaited()


def test_admin_context_denies_authenticated_user_without_membership() -> None:
    user = authenticated_user()
    authorization = AsyncMock()
    authorization.access_summary.side_effect = HTTPException(
        status_code=403,
        detail="A identidade não possui acesso editorial.",
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: authorization
    try:
        response = TestClient(app).get(
            "/api/v1/admin/context",
            headers={"Authorization": "Bearer ignored-by-override"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert str(user.id) not in response.text
    authorization.access_summary.assert_awaited_once()


def test_admin_context_returns_sorted_database_backed_access_and_contract() -> None:
    user = authenticated_user()
    authorization = AsyncMock()
    authorization.access_summary.return_value = [
        ScopedEditorialAccess(
            scope_type="global",
            scope_id=None,
            roles=frozenset({"publisher", "editor"}),
            capabilities=frozenset({"content.publish", "content.draft.update"}),
        )
    ]
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editorial_authorization_service] = lambda: authorization
    try:
        response = TestClient(app).get(
            "/api/v1/admin/context",
            headers={"Authorization": "Bearer ignored-by-override"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["access"]["scopes"][0]["roles"] == ["editor", "publisher"]
    assert payload["access"]["scopes"][0]["capabilities"] == [
        "content.draft.update",
        "content.publish",
    ]
    assert payload["contract"] == {
        "concurrency_header": "If-Match",
        "version_field": "version",
        "idempotency_header": "Idempotency-Key",
        "audit_request_header": "X-Request-ID",
        "version": None,
        "audit": None,
        "job_reference": None,
        "upload_reference": None,
    }
    authorization.access_summary.assert_awaited_once()
