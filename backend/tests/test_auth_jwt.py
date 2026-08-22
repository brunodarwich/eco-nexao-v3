"""Network-free tests for Supabase JWT validation."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import (
    AuthenticatedUser,
    JWTValidationError,
    get_current_user,
    get_current_user_allow_deleted,
    get_optional_current_user,
    verify_supabase_jwt,
)


def claims(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "authenticated",
        "is_anonymous": False,
        "iat": 1,
        "exp": 4_102_444_800,
        "iss": "https://unit-test.supabase.co/auth/v1",
        "aud": "authenticated",
    }
    result.update(overrides)
    return result


@pytest.fixture
def jwks_client() -> Mock:
    client = Mock()
    client.get_signing_key_from_jwt.return_value = SimpleNamespace(key="public-key")
    return client


def configure_decode(monkeypatch: pytest.MonkeyPatch, payload: object) -> Mock:
    monkeypatch.setattr(jwt, "get_unverified_header", lambda _token: {"alg": "RS256", "kid": "k1"})
    decode = Mock(return_value=payload)
    monkeypatch.setattr(jwt, "decode", decode)
    return decode


def test_verify_valid_token(monkeypatch: pytest.MonkeyPatch, jwks_client: Mock) -> None:
    user_id = uuid.uuid4()
    decode = configure_decode(monkeypatch, claims(sub=str(user_id)))
    user = verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)
    assert isinstance(user, AuthenticatedUser)
    assert user.id == user_id
    assert user.role == "authenticated"
    jwks_client.get_signing_key_from_jwt.assert_called_once()
    assert decode.call_args.kwargs["issuer"] == "https://unit-test.supabase.co/auth/v1"
    assert decode.call_args.kwargs["audience"] == "authenticated"
    assert decode.call_args.kwargs["algorithms"] == ["RS256"]


def test_verify_anonymous_token(monkeypatch: pytest.MonkeyPatch, jwks_client: Mock) -> None:
    configure_decode(monkeypatch, claims(email=None, is_anonymous=True))
    user = verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)
    assert user.email is None
    assert user.is_anonymous is True


@pytest.mark.parametrize("algorithm", ["none", "HS512", None])
def test_rejects_disallowed_algorithm(
    monkeypatch: pytest.MonkeyPatch, jwks_client: Mock, algorithm: str | None
) -> None:
    monkeypatch.setattr(
        jwt,
        "get_unverified_header",
        lambda _token: {"alg": algorithm, "kid": "k1"},
    )
    with pytest.raises(JWTValidationError, match="Algoritmo"):
        verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)


def test_requires_kid(monkeypatch: pytest.MonkeyPatch, jwks_client: Mock) -> None:
    monkeypatch.setattr(jwt, "get_unverified_header", lambda _token: {"alg": "RS256"})
    with pytest.raises(JWTValidationError, match="chave"):
        verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (jwt.ExpiredSignatureError(), "expirado"),
        (jwt.InvalidIssuerError(), "inválido"),
        (jwt.InvalidAudienceError(), "inválido"),
        (jwt.InvalidSignatureError(), "inválido"),
    ],
)
def test_rejects_invalid_claim_or_signature(
    monkeypatch: pytest.MonkeyPatch,
    jwks_client: Mock,
    error: Exception,
    message: str,
) -> None:
    configure_decode(monkeypatch, claims())
    monkeypatch.setattr(jwt, "decode", Mock(side_effect=error))
    with pytest.raises(JWTValidationError, match=message):
        verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)


def test_rejects_invalid_sub(monkeypatch: pytest.MonkeyPatch, jwks_client: Mock) -> None:
    configure_decode(monkeypatch, claims(sub="not-a-uuid"))
    with pytest.raises(JWTValidationError, match="UUID"):
        verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)


def test_rejects_non_user_role(monkeypatch: pytest.MonkeyPatch, jwks_client: Mock) -> None:
    configure_decode(monkeypatch, claims(role="service_role"))
    with pytest.raises(JWTValidationError, match="sessão de usuário"):
        verify_supabase_jwt("header.payload.signature", jwks_client=jwks_client)


@pytest.mark.asyncio
async def test_current_user_requires_credentials() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_allow_deleted(None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_current_user_verification_runs_off_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = AuthenticatedUser(
        id=uuid.uuid4(), email=None, is_anonymous=True, role="authenticated", claims={}
    )
    run = AsyncMock(return_value=user)
    monkeypatch.setattr("app.core.security.run_in_threadpool", run)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    assert await get_current_user_allow_deleted(credentials) == user
    run.assert_awaited_once()


@pytest.mark.asyncio
async def test_optional_user_allows_absent_credentials() -> None:
    assert await get_optional_current_user(None, AsyncMock()) is None


@pytest.mark.asyncio
async def test_optional_user_rejects_invalid_present_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.security.verify_supabase_jwt",
        Mock(side_effect=JWTValidationError("Token JWT inválido.")),
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
    with pytest.raises(HTTPException) as exc_info:
        await get_optional_current_user(credentials, AsyncMock())
    assert exc_info.value.status_code == 401


def test_auth_session_endpoint_authenticated(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email="test@example.com",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr(
        "app.core.security.verify_supabase_jwt", lambda token, jwks_client=None: mock_user
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/auth/session", headers={"Authorization": "Bearer valid_token"}
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(user_id)
    assert data["email"] == "test@example.com"
    assert data["is_anonymous"] is False
    assert data["role"] == "authenticated"


def test_auth_session_endpoint_unauthorized() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 401


def test_auth_verify_endpoint_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email=None,
        is_anonymous=True,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr(
        "app.api.v1.auth.verify_supabase_jwt", lambda token, jwks_client=None: mock_user
    )

    client = TestClient(app)
    response = client.post("/api/v1/auth/verify", json={"token": "valid_token"})
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert res_data["valid"] is True
    assert res_data["user"]["id"] == str(user_id)
    assert res_data["user"]["is_anonymous"] is True


def test_auth_verify_endpoint_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    def mock_fail(token: str) -> None:
        raise JWTValidationError("Token JWT expirado.")

    monkeypatch.setattr("app.api.v1.auth.verify_supabase_jwt", mock_fail)

    client = TestClient(app)
    response = client.post("/api/v1/auth/verify", json={"token": "expired_token"})
    assert response.status_code == 401
    assert "expirado" in response.json()["error"]["message"]
