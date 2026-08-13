"""FastAPI router for support and editorial content (/content)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.envelopes import SupportContentEnvelope
from app.services.content_service import ContentService
from app.services.dependencies import get_content_service

router = APIRouter(prefix="/content", tags=["Content & Support"])
ContentServiceDep = Annotated[ContentService, Depends(get_content_service)]


@router.get(
    "/support",
    response_model=SupportContentEnvelope,
    summary="Conteúdo de suporte, ajuda e contatos editoriais",
    description="Retorna FAQ, contatos editoriais e links de ajuda.",
)
async def get_support_content(
    service: ContentServiceDep,
) -> SupportContentEnvelope:
    return await service.get_support_content()
