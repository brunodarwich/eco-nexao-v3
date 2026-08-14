"""Administrative API boundary and database-backed authorization context."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.envelopes import (
    AdminAccessSchema,
    AdminContextDataSchema,
    AdminContextEnvelope,
    AdminScopeAccessSchema,
)
from app.schemas.error import ErrorResponse
from app.services.dependencies import get_editorial_authorization_service
from app.services.editorial_authorization import (
    EditorialAuthorizationService,
    authorization_context_for,
)

router = APIRouter(prefix="/admin", tags=["Admin"])
CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
EditorialAuthorizationDep = Annotated[
    EditorialAuthorizationService,
    Depends(get_editorial_authorization_service),
]


@router.get(
    "/context",
    response_model=AdminContextEnvelope,
    summary="Obter contexto administrativo",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "JWT Supabase ausente ou inválido.",
        },
        403: {
            "model": ErrorResponse,
            "description": "Identidade sem membership/capability editorial ativa.",
        },
    },
)
async def get_admin_context(
    current_user: CurrentUserDep,
    authorization: EditorialAuthorizationDep,
) -> AdminContextEnvelope:
    """Expose only current editorial access; ordinary/anonymous users are denied."""
    if current_user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A identidade não possui acesso editorial.",
        )
    context = authorization_context_for(current_user.id)
    scopes = await authorization.access_summary(context)
    return AdminContextEnvelope(
        data=AdminContextDataSchema(
            access=AdminAccessSchema(
                user_id=current_user.id,
                scopes=[
                    AdminScopeAccessSchema(
                        scope_type=scope.scope_type,
                        scope_id=scope.scope_id,
                        roles=sorted(scope.roles),
                        capabilities=sorted(scope.capabilities),
                    )
                    for scope in scopes
                ],
            )
        )
    )
