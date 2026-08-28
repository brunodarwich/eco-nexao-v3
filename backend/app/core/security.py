"""Supabase Auth JWT verification and FastAPI security dependencies."""

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.session import get_db
from app.models.domain import DeletedUserTombstone

security_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(security_scheme),
]

ALLOWED_JWT_ALGORITHMS = ("RS256", "ES256", "EdDSA", "HS256")


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
        if not algorithm or algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise JWTValidationError("Algoritmo de assinatura JWT não permitido.")

        if algorithm == "HS256":
            signing_key = (
                settings.SUPABASE_JWT_SECRET.get_secret_value()
                if hasattr(settings.SUPABASE_JWT_SECRET, "get_secret_value")
                else str(settings.SUPABASE_JWT_SECRET)
            )
            if not signing_key:
                raise JWTValidationError("SUPABASE_JWT_SECRET não configurado no servidor.")
        else:
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


async def get_current_user_allow_deleted(credentials: BearerCredentials) -> AuthenticatedUser:
    """Require a valid token without applying the deletion tombstone gate.

    This dependency is intentionally limited to the idempotent account-deletion
    retry route. Normal application routes must use ``get_current_user``.
    """
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


async def _reject_deleted_user(user: AuthenticatedUser, db: AsyncSession) -> None:
    marker = await db.scalar(
        select(DeletedUserTombstone.user_id).where(DeletedUserTombstone.user_id == user.id)
    )
    if marker is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esta conta foi excluída ou está em processo de exclusão.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: BearerCredentials,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthenticatedUser:
    """Require a valid Supabase token whose account is not tombstoned."""
    user = await get_current_user_allow_deleted(credentials)
    await _reject_deleted_user(user, db)
    return user


async def get_optional_current_user(
    credentials: BearerCredentials,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthenticatedUser | None:
    """Return a validated identity when a Bearer token is present."""
    if not credentials or not credentials.credentials:
        return None
    try:
        user = await run_in_threadpool(verify_supabase_jwt, credentials.credentials)
        await _reject_deleted_user(user, db)
        return user
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
