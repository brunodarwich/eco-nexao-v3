"""Administrative upload and recovery endpoints for editorial media."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.admin_media import (
    CleanupRecoveryEnvelope,
    CleanupRecoveryRequest,
    CleanupRecoverySchema,
    EditorialMediaEnvelope,
)
from app.schemas.domain import MediaAssetRead
from app.services.dependencies import get_media_lifecycle_service
from app.services.editorial_authorization import AuthorizationContext, authorization_context_for
from app.services.media_lifecycle import (
    EditorialMediaInput,
    MediaLifecycleFailure,
    MediaLifecycleService,
)

router = APIRouter(prefix="/admin/media", tags=["Admin Media"])
CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
MediaLifecycleDep = Annotated[MediaLifecycleService, Depends(get_media_lifecycle_service)]


def _context(user: AuthenticatedUser) -> AuthorizationContext:
    if user.is_anonymous:
        raise HTTPException(status_code=403, detail="A identidade não possui acesso editorial.")
    return authorization_context_for(user.id)


@router.post("/process", response_model=EditorialMediaEnvelope, status_code=201)
async def process_editorial_media(
    request: Request,
    current_user: CurrentUserDep,
    service: MediaLifecycleDep,
    owner_type: Annotated[Literal["route", "origin", "actor"], Form()],
    owner_id: Annotated[uuid.UUID, Form()],
    alt_text: Annotated[str, Form(min_length=1, max_length=500)],
    credit: Annotated[str, Form(min_length=1, max_length=500)],
    license_code: Annotated[Literal["CC-BY-4.0", "SEMTUR_INSTITUTIONAL", "PROPRIETARY"], Form()],
    image: Annotated[UploadFile, File()],
) -> EditorialMediaEnvelope:
    content = await image.read(10 * 1024 * 1024 + 1)
    try:
        request_id = uuid.UUID(str(request.state.request_id).removeprefix("req_"))
    except ValueError:
        request_id = None
    try:
        asset = await service.process_editorial_image(
            _context(current_user),
            EditorialMediaInput(
                owner_type=owner_type,
                owner_id=owner_id,
                content=content,
                declared_mime=image.content_type or "application/octet-stream",
                alt_text=alt_text,
                credit=credit,
                license_code=license_code,
                request_id=request_id,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MediaLifecycleFailure as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mídia rejeitada ({exc.asset_id}): {exc}",
        ) from exc
    return EditorialMediaEnvelope(data=MediaAssetRead.model_validate(asset))


@router.post("/cleanup/recover", response_model=CleanupRecoveryEnvelope)
async def recover_media_cleanup(
    request: Request,
    body: CleanupRecoveryRequest,
    current_user: CurrentUserDep,
    service: MediaLifecycleDep,
) -> CleanupRecoveryEnvelope:
    try:
        request_id = uuid.UUID(str(request.state.request_id).removeprefix("req_"))
    except ValueError:
        request_id = None
    completed, failed = await service.recover_pending_cleanup(
        _context(current_user), limit=body.limit, request_id=request_id
    )
    return CleanupRecoveryEnvelope(
        data=CleanupRecoverySchema(completed=completed, failed=failed)
    )
