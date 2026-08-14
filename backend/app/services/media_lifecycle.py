"""Orchestrate safe editorial image processing, persistence and compensation."""

import re
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.models.domain import MediaAsset
from app.repositories.media_lifecycle import MediaLifecycleRepository
from app.services.editorial_authorization import AuthorizationContext, EditorialAuthorizationService
from app.services.editorial_storage import EditorialStorageError, SupabaseEditorialStorage
from app.services.media_processor import MediaProcessingError, MediaProcessor

LICENSE_CODES = frozenset({"CC-BY-4.0", "SEMTUR_INSTITUTIONAL", "PROPRIETARY"})
OWNER_TYPES = frozenset({"route", "origin", "actor"})


class EditorialStorage(Protocol):
    async def upload(self, path: str, content: bytes, *, content_type: str) -> None: ...
    async def remove(self, paths: list[str]) -> None: ...


class MediaLifecycleFailure(RuntimeError):
    def __init__(self, message: str, *, asset_id: uuid.UUID) -> None:
        super().__init__(message)
        self.asset_id = asset_id


@dataclass(frozen=True, slots=True)
class EditorialMediaInput:
    owner_type: str
    owner_id: uuid.UUID
    content: bytes
    declared_mime: str
    alt_text: str
    credit: str
    license_code: str
    request_id: uuid.UUID | None = None


class MediaLifecycleService:
    def __init__(
        self,
        repository: MediaLifecycleRepository,
        authorization: EditorialAuthorizationService,
        *,
        storage: EditorialStorage | None = None,
        processor: MediaProcessor | None = None,
    ) -> None:
        self.repository = repository
        self.authorization = authorization
        self.storage = storage or SupabaseEditorialStorage()
        self.processor = processor or MediaProcessor()

    async def process_editorial_image(
        self, context: AuthorizationContext, payload: EditorialMediaInput
    ) -> MediaAsset:
        if context.scope_type != "global" or context.scope_id is not None:
            raise ValueError(
                "Uploads editoriais com escopo regional exigem resolução territorial do recurso."
            )
        await self.authorization.require_capability(context, "content.draft.create")
        self._validate_metadata(payload)
        if not await self.repository.owner_exists(payload.owner_type, payload.owner_id):
            raise ValueError("Recurso proprietário da mídia não encontrado.")
        asset_id = uuid.uuid4()
        await self.repository.create_processing(
            asset_id=asset_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            mime_type=payload.declared_mime.lower().strip(),
            alt_text=payload.alt_text.strip(),
            credit=payload.credit.strip(),
            license_code=payload.license_code,
            actor_id=context.actor_id,
            request_id=payload.request_id,
        )

        uploaded: list[str] = []
        try:
            processed = self.processor.process(
                payload.content, declared_mime=payload.declared_mime
            )
            base = (
                f"{payload.owner_type}/{payload.owner_id}/{asset_id}/"
                f"{processed.source_checksum_sha256}"
            )
            metadata: dict[str, dict[str, str | int]] = {}
            for name, derivative in processed.derivatives.items():
                path = f"{base}/{name}-{derivative.checksum_sha256}.webp"
                await self.storage.upload(
                    path, derivative.content, content_type=derivative.mime_type
                )
                uploaded.append(path)
                metadata[name] = {
                    "storage_key": f"editorial-media/{path}",
                    "checksum_sha256": derivative.checksum_sha256,
                    "width_px": derivative.width,
                    "height_px": derivative.height,
                    "mime_type": derivative.mime_type,
                }
            hero_key = str(metadata["hero"]["storage_key"])
            hero = processed.derivatives["hero"]
            return await self.repository.mark_ready(
                asset_id=asset_id,
                storage_key=hero_key,
                checksum_sha256=hero.checksum_sha256,
                width_px=hero.width,
                height_px=hero.height,
                derivatives=metadata,
                actor_id=context.actor_id,
                request_id=payload.request_id,
            )
        except (MediaProcessingError, EditorialStorageError, OSError, LookupError) as exc:
            cleanup_pending = not await self._compensate(uploaded)
            reason = self._public_reason(exc, cleanup_pending=cleanup_pending)
            await self.repository.mark_rejected(
                asset_id=asset_id,
                reason=reason,
                actor_id=context.actor_id,
                request_id=payload.request_id,
                cleanup_pending=cleanup_pending,
                orphan_storage_paths=uploaded if cleanup_pending else [],
            )
            raise MediaLifecycleFailure(reason, asset_id=asset_id) from exc
        except Exception as exc:
            cleanup_pending = not await self._compensate(uploaded)
            reason = self._public_reason(exc, cleanup_pending=cleanup_pending)
            await self.repository.mark_rejected(
                asset_id=asset_id,
                reason=reason,
                actor_id=context.actor_id,
                request_id=payload.request_id,
                cleanup_pending=cleanup_pending,
                orphan_storage_paths=uploaded if cleanup_pending else [],
            )
            raise MediaLifecycleFailure(reason, asset_id=asset_id) from exc

    async def recover_pending_cleanup(
        self,
        context: AuthorizationContext,
        *,
        limit: int = 50,
        request_id: uuid.UUID | None = None,
    ) -> tuple[int, int]:
        """Retry previously audited compensations; safe to run repeatedly."""
        if context.scope_type != "global" or context.scope_id is not None:
            raise ValueError("A limpeza de mídia exige escopo editorial global.")
        await self.authorization.require_capability(context, "content.archive")
        completed = 0
        failed = 0
        for asset_id, paths in await self.repository.list_cleanup_pending(limit=limit):
            if await self.repository.cleanup_already_completed(asset_id):
                continue
            try:
                await self.storage.remove(paths)
            except (EditorialStorageError, OSError):
                failed += 1
                continue
            await self.repository.mark_cleanup_completed(
                asset_id=asset_id,
                paths=paths,
                actor_id=context.actor_id,
                request_id=request_id,
            )
            completed += 1
        return completed, failed

    async def _compensate(self, uploaded: list[str]) -> bool:
        if not uploaded:
            return True
        try:
            await self.storage.remove(uploaded)
        except (EditorialStorageError, OSError):
            return False
        return True

    @staticmethod
    def _validate_metadata(payload: EditorialMediaInput) -> None:
        if payload.owner_type not in OWNER_TYPES:
            raise ValueError("Tipo de proprietário de mídia inválido.")
        if payload.license_code not in LICENSE_CODES:
            raise ValueError("Licença editorial inválida.")
        if not payload.alt_text.strip() or not payload.credit.strip():
            raise ValueError("Texto alternativo e crédito são obrigatórios.")
        if len(payload.alt_text.strip()) > 500 or len(payload.credit.strip()) > 500:
            raise ValueError("Metadados editoriais excedem o limite permitido.")

    @staticmethod
    def _public_reason(exc: Exception, *, cleanup_pending: bool) -> str:
        if isinstance(exc, MediaProcessingError):
            reason = str(exc)
        elif isinstance(exc, EditorialStorageError):
            reason = "Falha ao armazenar derivados processados."
        else:
            reason = "Falha interna ao concluir o processamento da mídia."
        reason = re.sub(r"[\r\n]+", " ", reason)[:500]
        if cleanup_pending:
            reason = f"{reason} Limpeza compensatória pendente."
        return reason
