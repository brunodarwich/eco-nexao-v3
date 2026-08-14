"""Supabase Storage Service for Avatars and Editorial Media (ECO-0406)."""

from app.core.config import settings


class StorageService:
    """Service managing file upload security policies and URL signatures for Supabase Storage."""

    def __init__(self, supabase_url: str | None = None) -> None:
        self.supabase_url = (supabase_url or settings.SUPABASE_URL).rstrip("/")

    def get_public_url(self, bucket: str, path: str) -> str:
        """Construct the public URL for a given bucket and path."""
        clean_path = path.lstrip("/")
        return f"{self.supabase_url}/storage/v1/object/public/{bucket}/{clean_path}"
