"""Supabase Auth JWT verification and FastAPI security dependencies."""

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(security_scheme),
]

ALLOWED_JWT_ALGORITHMS = ("RS256", "ES256", "EdDSA")


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Validated user identity extracted from a Supabase access token."""

    id: uuid.UUID
    email: str | None
    is_anonymous: bool
    role: str
    claims: dict[str, Any]


class JWTValidationError(Exception):
    """Safe authentication failure that may be returned as a 401 response."""


@lru_cache(maxsize=1)
def get_supabase_jwks_client() -> PyJWKClient:
    """Return the process-wide JWKS client with PyJWT's bounded key cache."""
    return PyJWKClient(
        settings.SUPABASE_JWKS_URL,
        cache_keys=True,
        lifespan=600,
        timeout=5,
    )


def verify_supabase_jwt(
    token: str,
    *,
    jwks_client: PyJWKClient | None = None,
) -> AuthenticatedUser:
    """Validate an asymmetric Supabase access token and return its identity."""
    if not token or not token.strip():
        raise JWTValidationError("Token ausente ou em branco.")

    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise JWTValidationError("Algoritmo de assinatura JWT não permitido.")
        if not header.get("kid"):
            raise JWTValidationError("Token JWT não informa a chave de assinatura.")

        client = jwks_client or get_supabase_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token).key
        payload: dict[str, Any] = jwt.decode(
            token,
            key=signing_key,
            algorithms=[algorithm],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=settings.SUPABASE_JWT_ISSUER,
            options={"require": ["iss", "aud", "exp", "iat", "sub", "role"]},
        )

        role = payload["role"]
        if role != "authenticated":
            raise JWTValidationError("Token JWT não representa uma sessão de usuário.")

        try:
            user_id = uuid.UUID(payload["sub"])
        except (TypeError, ValueError) as exc:
            raise JWTValidationError("Identificador 'sub' não é um UUID válido.") from exc

        app_metadata = payload.get("app_metadata")
        provider = app_metadata.get("provider") if isinstance(app_metadata, dict) else None
        return AuthenticatedUser(
            id=user_id,
            email=payload.get("email"),
            is_anonymous=bool(payload.get("is_anonymous", False) or provider == "anonymous"),
            role=role,
            claims=payload,
        )
    except JWTValidationError:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise JWTValidationError("Token JWT expirado.") from exc
    except (jwt.PyJWTError, ValueError) as exc:
        raise JWTValidationError("Token JWT inválido.") from exc


async def get_current_user(credentials: BearerCredentials) -> AuthenticatedUser:
    """Require a valid Supabase Auth Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou malformado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await run_in_threadpool(verify_supabase_jwt, credentials.credentials)
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_optional_current_user(credentials: BearerCredentials) -> AuthenticatedUser | None:
    """Return a validated identity when a Bearer token is present."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await run_in_threadpool(verify_supabase_jwt, credentials.credentials)
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
