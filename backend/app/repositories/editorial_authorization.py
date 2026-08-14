"""Database access for editorial authorization and immutable audit records."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    AuditLog,
    EditorialInvitation,
    EditorialMembership,
    EditorialResourceState,
    EditorialRoleCapability,
)


class EditorialAuthorizationRepository:
    """Read current memberships from the database, never from stale JWT claims."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def capabilities_for(
        self,
        user_id: uuid.UUID,
        *,
        scope_type: str = "global",
        scope_id: uuid.UUID | None = None,
    ) -> set[str]:
        scope_filter = EditorialMembership.scope_type == "global"
        if scope_type == "region" and scope_id is not None:
            scope_filter = or_(
                scope_filter,
                and_(
                    EditorialMembership.scope_type == "region",
                    EditorialMembership.scope_id == scope_id,
                ),
            )
        statement = (
            select(EditorialRoleCapability.capability)
            .join(EditorialMembership, EditorialMembership.role == EditorialRoleCapability.role)
            .where(
                EditorialMembership.user_id == user_id,
                EditorialMembership.revoked_at.is_(None),
                scope_filter,
            )
        )
        result = await self.db.scalars(statement)
        return set(result.all())

    async def roles_for(self, user_id: uuid.UUID) -> set[str]:
        statement = select(EditorialMembership.role).where(
            EditorialMembership.user_id == user_id,
            EditorialMembership.revoked_at.is_(None),
        )
        result = await self.db.scalars(statement)
        return set(result.all())

    async def scoped_access_for(
        self, user_id: uuid.UUID
    ) -> list[tuple[str, uuid.UUID | None, str, str]]:
        """Return active role/capability rows without mixing authorization scopes."""
        statement = (
            select(
                EditorialMembership.scope_type,
                EditorialMembership.scope_id,
                EditorialMembership.role,
                EditorialRoleCapability.capability,
            )
            .join(
                EditorialRoleCapability,
                EditorialRoleCapability.role == EditorialMembership.role,
            )
            .where(
                EditorialMembership.user_id == user_id,
                EditorialMembership.revoked_at.is_(None),
            )
        )
        result = await self.db.execute(statement)
        return [(row.scope_type, row.scope_id, row.role, row.capability) for row in result]

    async def resource_state(
        self, resource_type: str, resource_id: uuid.UUID
    ) -> EditorialResourceState | None:
        statement = select(EditorialResourceState).where(
            EditorialResourceState.resource_type == resource_type,
            EditorialResourceState.resource_id == resource_id,
        )
        return cast(EditorialResourceState | None, await self.db.scalar(statement))

    async def revoke_membership(
        self,
        membership: EditorialMembership,
        *,
        revoked_by: uuid.UUID,
        reason: str,
    ) -> None:
        membership.revoked_by = revoked_by
        membership.revoked_at = datetime.now(UTC)
        membership.revoke_reason = reason

    def add_membership(self, membership: EditorialMembership) -> None:
        self.db.add(membership)

    def add_invitation(self, invitation: EditorialInvitation) -> None:
        self.db.add(invitation)

    def append_audit(
        self,
        *,
        actor_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        changes: dict[str, Any],
        reason: str | None = None,
        request_id: uuid.UUID | None = None,
    ) -> AuditLog:
        record = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            reason=reason,
            request_id=request_id,
        )
        self.db.add(record)
        return record

    async def commit(self) -> None:
        await self.db.commit()
