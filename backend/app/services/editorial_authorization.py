"""Deny-by-default editorial authorization rules from ADR 0006."""

import uuid
from collections.abc import AsyncIterator
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.models.domain import (
    EditorialInvitation,
    EditorialMembership,
    EditorialResourceState,
)
from app.repositories.editorial_authorization import EditorialAuthorizationRepository

TRANSITIONS: dict[tuple[str, str], str] = {
    ("draft", "review"): "content.review.submit",
    ("review", "draft"): "content.review.reject",
    ("review", "published"): "content.publish",
    ("published", "draft"): "content.unpublish",
    ("draft", "archived"): "content.archive.draft",
    ("review", "archived"): "content.archive",
    ("published", "archived"): "content.archive",
}
REASON_REQUIRED = {("review", "draft"), ("published", "draft")}

editorial_region_scope_ctx: ContextVar[uuid.UUID | None] = ContextVar(
    "editorial_region_scope", default=None
)


async def bind_editorial_region_scope(
    x_region_id: Annotated[
        uuid.UUID | None,
        Header(alias="X-Region-ID", description="Escopo regional explícito da operação editorial."),
    ] = None,
) -> AsyncIterator[None]:
    """Bind the optional regional scope for one administrative request."""
    token = editorial_region_scope_ctx.set(x_region_id)
    try:
        yield
    finally:
        editorial_region_scope_ctx.reset(token)


@dataclass(frozen=True)
class AuthorizationContext:
    actor_id: uuid.UUID
    scope_type: str = "global"
    scope_id: uuid.UUID | None = None


def authorization_context_for(actor_id: uuid.UUID) -> AuthorizationContext:
    """Build an authorization context from the request-bound regional scope."""
    region_id = editorial_region_scope_ctx.get()
    if region_id is None:
        return AuthorizationContext(actor_id=actor_id)
    return AuthorizationContext(actor_id=actor_id, scope_type="region", scope_id=region_id)


@dataclass(frozen=True, slots=True)
class ScopedEditorialAccess:
    scope_type: str
    scope_id: uuid.UUID | None
    roles: frozenset[str]
    capabilities: frozenset[str]


class EditorialAuthorizationService:
    def __init__(self, repository: EditorialAuthorizationRepository) -> None:
        self.repository = repository

    async def require_capability(self, context: AuthorizationContext, capability: str) -> None:
        capabilities = await self.repository.capabilities_for(
            context.actor_id,
            scope_type=context.scope_type,
            scope_id=context.scope_id,
        )
        if capability not in capabilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A identidade não possui a capability editorial necessária.",
            )

    @staticmethod
    def require_global_scope(context: AuthorizationContext) -> None:
        """Reject region-scoped access to platform-wide resources."""
        if context.scope_type != "global" or context.scope_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A operação exige escopo editorial global.",
            )

    @staticmethod
    def require_region_scope(context: AuthorizationContext, resource_region_id: uuid.UUID) -> None:
        """Prevent a selected regional scope from crossing into another region."""
        if context.scope_type == "global":
            return
        if context.scope_type != "region" or context.scope_id != resource_region_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O recurso não pertence ao escopo regional autorizado.",
            )

    async def access_summary(self, context: AuthorizationContext) -> list[ScopedEditorialAccess]:
        """Return current database-backed editorial access, denying non-members."""
        rows = await self.repository.scoped_access_for(context.actor_id)
        grouped: dict[tuple[str, uuid.UUID | None], tuple[set[str], set[str]]] = {}
        for scope_type, scope_id, role, capability in rows:
            roles, capabilities = grouped.setdefault((scope_type, scope_id), (set(), set()))
            roles.add(role)
            capabilities.add(capability)
        if not grouped:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A identidade não possui acesso editorial.",
            )
        return [
            ScopedEditorialAccess(
                scope_type=scope_type,
                scope_id=scope_id,
                roles=frozenset(roles),
                capabilities=frozenset(capabilities),
            )
            for (scope_type, scope_id), (roles, capabilities) in sorted(
                grouped.items(), key=lambda item: (item[0][0], str(item[0][1] or ""))
            )
        ]

    async def authorize_transition(
        self,
        context: AuthorizationContext,
        resource: EditorialResourceState,
        target_status: str,
        *,
        reason: str | None = None,
    ) -> str:
        transition = (resource.status, target_status)
        capability = TRANSITIONS.get(transition)
        if capability is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transição editorial inválida.",
            )
        if transition in REASON_REQUIRED and not (reason and reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A transição exige justificativa.",
            )
        await self.require_capability(context, capability)
        if target_status == "published" and resource.author_id == context.actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O autor não pode publicar o próprio conteúdo.",
            )
        return capability

    async def revoke_membership(
        self,
        context: AuthorizationContext,
        membership: EditorialMembership,
        *,
        reason: str,
    ) -> None:
        await self.require_capability(context, "memberships.manage")
        if not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A revogação exige justificativa.",
            )
        before = {"role": membership.role, "revoked_at": None}
        await self.repository.revoke_membership(
            membership, revoked_by=context.actor_id, reason=reason.strip()
        )
        self.repository.append_audit(
            actor_id=context.actor_id,
            action="MEMBERSHIP_REVOKE",
            resource_type="editorial_membership",
            resource_id=membership.id,
            changes={"before": before, "after": {"role": membership.role, "revoked": True}},
            reason=reason.strip(),
        )
        await self.repository.commit()

    async def grant_membership(
        self,
        context: AuthorizationContext,
        *,
        user_id: uuid.UUID,
        role: str,
        scope_type: str = "global",
        scope_id: uuid.UUID | None = None,
    ) -> EditorialMembership:
        await self.require_capability(context, "memberships.manage")
        membership = EditorialMembership(
            id=uuid.uuid4(),
            user_id=user_id,
            role=role,
            scope_type=scope_type,
            scope_id=scope_id,
            granted_by=context.actor_id,
        )
        self.repository.add_membership(membership)
        self.repository.append_audit(
            actor_id=context.actor_id,
            action="MEMBERSHIP_GRANT",
            resource_type="editorial_membership",
            resource_id=membership.id,
            changes={"before": None, "after": {"role": role, "scope_type": scope_type}},
        )
        await self.repository.commit()
        return membership

    async def create_invitation(
        self,
        context: AuthorizationContext,
        *,
        email: str,
        role: str,
        expires_in: timedelta = timedelta(days=7),
    ) -> tuple[EditorialInvitation, str]:
        await self.require_capability(context, "invitations.manage")
        normalized_email = email.strip().casefold()
        if "@" not in normalized_email or expires_in <= timedelta(0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Convite editorial inválido.",
            )
        raw_token = token_urlsafe(32)
        invitation = EditorialInvitation(
            id=uuid.uuid4(),
            email_hash=sha256(normalized_email.encode()).hexdigest(),
            token_hash=sha256(raw_token.encode()).hexdigest(),
            role=role,
            invited_by=context.actor_id,
            expires_at=datetime.now(UTC) + expires_in,
        )
        self.repository.add_invitation(invitation)
        self.repository.append_audit(
            actor_id=context.actor_id,
            action="INVITATION_CREATE",
            resource_type="editorial_invitation",
            resource_id=invitation.id,
            changes={"before": None, "after": {"role": role, "expires": True}},
        )
        await self.repository.commit()
        return invitation, raw_token
