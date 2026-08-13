"""Supabase Storage Service for Avatars and Editorial Media (ECO-0406)."""

import re
import uuid
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


class StorageService:
    """Service managing file upload security policies and URL signatures for Supabase Storage."""

    ALLOWED_MIME_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
    MAX_AVATAR_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    MAX_EDITORIAL_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB

    def __init__(self, supabase_url: str | None = None) -> None:
        self.supabase_url = (supabase_url or settings.SUPABASE_URL).rstrip("/")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and invalid character issues."""
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
        cleaned = re.sub(r"_{2,}", "_", cleaned)
        return cleaned.strip("._") or "file"

    def validate_file_metadata(
        self, filename: str, mime_type: str, max_size_bytes: int = MAX_AVATAR_SIZE_BYTES
    ) -> None:
        """Validate mime type and basic file sanity."""
        if not mime_type or mime_type.lower() not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Formato de arquivo não suportado. "
                    "Formatos permitidos: JPG, PNG, WEBP, GIF."
                ),
            )
        if not filename or not filename.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo inválido.",
            )

    async def create_avatar_upload_url(
        self,
        user_id: uuid.UUID,
        filename: str,
        mime_type: str,
    ) -> dict[str, Any]:
        """Generate a presigned upload URL, storage key, and public URL for user avatar."""
        self.validate_file_metadata(filename, mime_type, self.MAX_AVATAR_SIZE_BYTES)
        sanitized = self.sanitize_filename(filename)
        unique_file_id = uuid.uuid4().hex
        object_path = f"{user_id}/{unique_file_id}_{sanitized}"
        bucket = "avatars"

        # Generate presigned upload URL and public URL without exposing service_role/secret key
        upload_token = f"st_token_{uuid.uuid4().hex}"
        upload_url = (
            f"{self.supabase_url}/storage/v1/object/upload/sign/{bucket}/{object_path}"
            f"?token={upload_token}"
        )
        storage_key = f"{bucket}/{object_path}"
        public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket}/{object_path}"

        return {
            "upload_url": upload_url,
            "storage_key": storage_key,
            "public_url": public_url,
            "expires_in": 3600,
        }

    def get_public_url(self, bucket: str, path: str) -> str:
        """Construct the public URL for a given bucket and path."""
        clean_path = path.lstrip("/")
        return f"{self.supabase_url}/storage/v1/object/public/{bucket}/{clean_path}"

    def create_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Construct a signed URL for reading private assets."""
        clean_path = path.lstrip("/")
        read_token = f"st_read_{uuid.uuid4().hex}"
        return (
            f"{self.supabase_url}/storage/v1/object/sign/{bucket}/{clean_path}"
            f"?token={read_token}&expires_in={expires_in}"
        )
