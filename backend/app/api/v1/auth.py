"""Authentication endpoints and dependencies for API v1 (ECO-0602)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import AuthenticatedUser as AuthUser
from app.core.security import (
    JWTValidationError,
    get_current_user,
    get_current_user_allow_deleted,
    verify_supabase_jwt,
)
from app.schemas.envelopes import (
    AuthSessionEnvelope,
    AuthUserSchema,
    TokenVerifyData,
    TokenVerifyEnvelope,
    TokenVerifyRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/session",
    response_model=AuthSessionEnvelope,
    summary="Obter dados da sessão do usuário autenticado",
    description="Valida o token JWT Supabase e retorna os dados da sessão do usuário.",
)
async def get_auth_session(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> AuthSessionEnvelope:
    user_schema = AuthUserSchema(
        id=current_user.id,
        email=current_user.email,
        is_anonymous=current_user.is_anonymous,
        role=current_user.role,
    )
    return AuthSessionEnvelope(data=user_schema)


@router.post(
    "/verify",
    response_model=TokenVerifyEnvelope,
    summary="Validar token JWT Supabase",
    description=(
        "Verifica a validade, emissor, audiência e assinatura assimétrica do token informado."
    ),
)
async def verify_auth_token(
    request: TokenVerifyRequest,
) -> TokenVerifyEnvelope:
    try:
        user = verify_supabase_jwt(request.token)
        user_schema = AuthUserSchema(
            id=user.id,
            email=user.email,
            is_anonymous=user.is_anonymous,
            role=user.role,
        )
        return TokenVerifyEnvelope(data=TokenVerifyData(valid=True, user=user_schema))
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


__all__ = ["AuthUser", "get_current_user", "get_current_user_allow_deleted", "router"]
