"""Idempotent account deletion across Storage, domain data and Supabase Auth."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.account_lifecycle import AccountLifecycleRepository
from app.services.avatar_lifecycle import AvatarLifecycleService
from app.services.avatar_storage import AvatarStorageError, SupabaseAvatarStorage
from app.services.supabase_auth_admin import SupabaseAuthAdmin, SupabaseAuthAdminError


class AccountStorage(Protocol):
    async def list_user_paths(self, user_id: str) -> list[str]: ...
    async def remove(self, paths: list[str]) -> None: ...


class AuthAdmin(Protocol):
    async def delete_user(self, user_id: uuid.UUID) -> None: ...


class AccountDeletionError(RuntimeError):
    """A retryable, non-sensitive account deletion failure."""


class AccountLifecycleService:
    def __init__(
        self,
        repository: AccountLifecycleRepository,
        *,
        storage: AccountStorage | None = None,
        auth_admin: AuthAdmin | None = None,
    ) -> None:
        self.repository = repository
        self.storage = storage or SupabaseAvatarStorage()
        self.auth_admin = auth_admin or SupabaseAuthAdmin()

    async def delete_account(self, user_id: uuid.UUID) -> None:
        # Sequence is deliberate: tombstone blocks residual JWTs at FastAPI;
        # avatar client mutation policies are removed by migration, so those JWTs
        # cannot recreate Storage objects. Supabase exposes no separate Admin API
        # operation that revokes already-issued access JWTs; deleting the Auth user
        # invalidates refresh credentials, while the tombstone covers token expiry.
        # Commit the marker first. Every normal authenticated dependency rejects it,
        # while this endpoint has a dedicated retry dependency.
        try:
            await self.repository.start_deletion(user_id)
            assets = await self.repository.avatar_assets(user_id)
            known_paths = {
                path for asset in assets for path in AvatarLifecycleService.storage_paths(asset)
            }
            listed_paths = await self.storage.list_user_paths(str(user_id))
            paths = sorted(known_paths.union(listed_paths))
            await self.storage.remove(paths)
            await self.repository.purge_domain_data(user_id)
            await self.auth_admin.delete_user(user_id)
            await self.repository.complete_deletion(user_id)
        except (
            AvatarStorageError,
            SupabaseAuthAdminError,
            OSError,
            RuntimeError,
            SQLAlchemyError,
        ) as exc:
            await self.repository.rollback()
            raise AccountDeletionError(
                "A exclusão não pôde ser concluída; tente novamente com a mesma conta."
            ) from exc
