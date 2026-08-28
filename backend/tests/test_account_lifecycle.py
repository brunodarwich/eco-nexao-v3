"""Ordering, retry and private tombstone tests for account deletion."""

import uuid
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.services.account_lifecycle import AccountDeletionError, AccountLifecycleService
from app.services.avatar_storage import AvatarStorageError
from app.services.supabase_auth_admin import SupabaseAuthAdmin, SupabaseAuthAdminError


class Repository:
    def __init__(self, fail_complete: bool = False) -> None:
        self.calls: list[str] = []
        self.rolled_back = False
        self.fail_complete = fail_complete

    async def start_deletion(self, _user_id: uuid.UUID) -> None:
        self.calls.append("tombstone")

    async def avatar_assets(self, _user_id: uuid.UUID) -> list[object]:
        self.calls.append("assets")
        return []

    async def purge_domain_data(self, _user_id: uuid.UUID) -> None:
        self.calls.append("purge")

    async def complete_deletion(self, _user_id: uuid.UUID) -> None:
        if self.fail_complete:
            raise RuntimeError("failure")
        self.calls.append("complete")

    async def rollback(self) -> None:
        self.rolled_back = True


class Storage:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.removed: list[str] = []

    async def list_user_paths(self, user_id: str) -> list[str]:
        return [f"{user_id}/avatar.webp"]

    async def remove(self, paths: list[str]) -> None:
        if self.fail:
            raise AvatarStorageError("failure")
        self.removed = paths


class AuthAdmin:
    def __init__(self, fail: bool = False) -> None:
        self.deleted: list[uuid.UUID] = []
        self.fail = fail

    async def delete_user(self, user_id: uuid.UUID) -> None:
        if self.fail:
            raise SupabaseAuthAdminError("failure")
        self.deleted.append(user_id)


async def test_deletion_marks_first_then_removes_storage_domain_auth_and_completes() -> None:
    repository, storage, auth = Repository(), Storage(), AuthAdmin()
    service = AccountLifecycleService(repository, storage=storage, auth_admin=auth)
    user_id = uuid.uuid4()

    await service.delete_account(user_id)

    assert repository.calls == ["tombstone", "assets", "purge", "complete"]
    assert storage.removed == [f"{user_id}/avatar.webp"]
    assert auth.deleted == [user_id]


async def test_storage_failure_keeps_tombstone_and_prevents_destructive_followups() -> None:
    repository = Repository()
    service = AccountLifecycleService(
        repository, storage=Storage(fail=True), auth_admin=AuthAdmin()
    )
    with pytest.raises(AccountDeletionError, match="mesma conta"):
        await service.delete_account(uuid.uuid4())
    assert repository.calls == ["tombstone", "assets"]
    assert repository.rolled_back is True


def test_tombstone_migration_is_private_and_has_no_auth_foreign_key() -> None:
    migration = next(
        Path(__file__)
        .resolve()
        .parents[2]
        .glob("supabase/migrations/*_add_deleted_user_tombstones.sql")
    ).read_text(encoding="utf-8")
    assert "app_private.deleted_user_tombstones" in migration
    assert "REVOKE ALL" in migration
    assert "REFERENCES auth.users" not in migration


def test_concurrent_deletion_start_uses_database_conflict_resolution() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "app" / "repositories" / "account_lifecycle.py"
    ).read_text(encoding="utf-8")
    assert "on_conflict_do_nothing" in source
    assert "with_for_update" in source


async def test_auth_failure_is_retryable_after_storage_and_domain_purge() -> None:
    repository = Repository()
    service = AccountLifecycleService(
        repository, storage=Storage(), auth_admin=AuthAdmin(fail=True)
    )
    with pytest.raises(AccountDeletionError):
        await service.delete_account(uuid.uuid4())
    assert repository.calls == ["tombstone", "assets", "purge"]
    assert repository.rolled_back is True


async def test_completion_failure_is_retryable_after_auth_deletion() -> None:
    repository = Repository(fail_complete=True)
    auth = AuthAdmin()
    service = AccountLifecycleService(repository, storage=Storage(), auth_admin=auth)
    with pytest.raises(AccountDeletionError):
        await service.delete_account(uuid.uuid4())
    assert len(auth.deleted) == 1
    assert repository.calls == ["tombstone", "assets", "purge"]
    assert repository.rolled_back is True


async def test_auth_admin_treats_missing_user_as_idempotent_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.supabase_auth_admin.settings.SUPABASE_SECRET_KEY",
        SecretStr("secret"),
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404))
    ) as client:
        await SupabaseAuthAdmin(client=client).delete_user(uuid.uuid4())
