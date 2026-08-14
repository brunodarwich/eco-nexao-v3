"""Authorization matrix for ADR 0006 editorial roles and transitions."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.models.domain import EditorialMembership, EditorialResourceState
from app.services.editorial_authorization import (
    AuthorizationContext,
    EditorialAuthorizationService,
)


def service_with(*capabilities: str) -> tuple[EditorialAuthorizationService, Mock]:
    repository = Mock()
    repository.capabilities_for = AsyncMock(return_value=set(capabilities))
    repository.revoke_membership = AsyncMock()
    repository.commit = AsyncMock()
    repository.append_audit = Mock()
    repository.add_membership = Mock()
    repository.add_invitation = Mock()
    return EditorialAuthorizationService(repository), repository


def resource(*, author_id: uuid.UUID, current_status: str) -> EditorialResourceState:
    return EditorialResourceState(
        id=uuid.uuid4(),
        resource_type="route",
        resource_id=uuid.uuid4(),
        status=current_status,
        author_id=author_id,
    )


@pytest.mark.asyncio
async def test_anonymous_or_regular_user_is_denied_by_default() -> None:
    service, _ = service_with()
    with pytest.raises(HTTPException) as exc:
        await service.require_capability(
            AuthorizationContext(actor_id=uuid.uuid4()), "content.draft.create"
        )
    assert exc.value.status_code == 403


def test_region_scope_rejects_cross_region_and_global_only_operations() -> None:
    service, _ = service_with("territory.write")
    region_id = uuid.uuid4()
    context = AuthorizationContext(
        actor_id=uuid.uuid4(), scope_type="region", scope_id=region_id
    )

    service.require_region_scope(context, region_id)
    with pytest.raises(HTTPException) as cross_region:
        service.require_region_scope(context, uuid.uuid4())
    with pytest.raises(HTTPException) as global_only:
        service.require_global_scope(context)

    assert cross_region.value.status_code == 403
    assert global_only.value.status_code == 403


def test_global_scope_can_access_any_region() -> None:
    service, _ = service_with("territory.write")
    context = AuthorizationContext(actor_id=uuid.uuid4())

    service.require_region_scope(context, uuid.uuid4())
    service.require_global_scope(context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("current", "target", "capability"),
    [
        ("draft", "review", "content.review.submit"),
        ("review", "draft", "content.review.reject"),
        ("review", "published", "content.publish"),
        ("published", "draft", "content.unpublish"),
        ("published", "archived", "content.archive"),
    ],
)
async def test_authorized_role_capability_allows_valid_transition(
    current: str, target: str, capability: str
) -> None:
    actor_id = uuid.uuid4()
    service, _ = service_with(capability)
    state = resource(author_id=uuid.uuid4(), current_status=current)
    reason = "Justificativa editorial" if (current, target) in {
        ("review", "draft"),
        ("published", "draft"),
    } else None

    assert (
        await service.authorize_transition(
            AuthorizationContext(actor_id=actor_id), state, target, reason=reason
        )
        == capability
    )


@pytest.mark.asyncio
async def test_publisher_cannot_publish_own_draft_even_with_capability() -> None:
    actor_id = uuid.uuid4()
    service, _ = service_with("content.publish")
    state = resource(author_id=actor_id, current_status="review")

    with pytest.raises(HTTPException) as exc:
        await service.authorize_transition(
            AuthorizationContext(actor_id=actor_id), state, "published"
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_transition_and_missing_reason_are_rejected() -> None:
    service, _ = service_with("content.review.reject")
    state = resource(author_id=uuid.uuid4(), current_status="review")

    with pytest.raises(HTTPException) as missing_reason:
        await service.authorize_transition(
            AuthorizationContext(actor_id=uuid.uuid4()), state, "draft"
        )
    assert missing_reason.value.status_code == 422

    with pytest.raises(HTTPException) as invalid:
        await service.authorize_transition(
            AuthorizationContext(actor_id=uuid.uuid4()), state, "review"
        )
    assert invalid.value.status_code == 409


@pytest.mark.asyncio
async def test_admin_revocation_is_audited_and_committed() -> None:
    admin_id = uuid.uuid4()
    service, repository = service_with("memberships.manage")
    membership = EditorialMembership(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="editor",
        granted_by=admin_id,
    )

    await service.revoke_membership(
        AuthorizationContext(actor_id=admin_id), membership, reason="Acesso encerrado"
    )

    repository.revoke_membership.assert_awaited_once()
    repository.append_audit.assert_called_once()
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_admin_cannot_revoke_membership() -> None:
    service, repository = service_with("content.draft.update")
    membership = EditorialMembership(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="editor",
        granted_by=uuid.uuid4(),
    )

    with pytest.raises(HTTPException) as exc:
        await service.revoke_membership(
            AuthorizationContext(actor_id=uuid.uuid4()), membership, reason="Tentativa"
        )
    assert exc.value.status_code == 403
    repository.revoke_membership.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_can_grant_membership_with_audit() -> None:
    admin_id = uuid.uuid4()
    service, repository = service_with("memberships.manage")

    membership = await service.grant_membership(
        AuthorizationContext(actor_id=admin_id), user_id=uuid.uuid4(), role="reviewer"
    )

    assert membership.role == "reviewer"
    repository.add_membership.assert_called_once_with(membership)
    repository.append_audit.assert_called_once()
    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_invitation_hashes_email_and_token_and_audits() -> None:
    service, repository = service_with("invitations.manage")

    invitation, raw_token = await service.create_invitation(
        AuthorizationContext(actor_id=uuid.uuid4()),
        email=" Editor@Example.com ",
        role="editor",
    )

    assert "editor@example.com" not in invitation.email_hash
    assert raw_token not in invitation.token_hash
    assert len(invitation.email_hash) == len(invitation.token_hash) == 64
    repository.add_invitation.assert_called_once_with(invitation)
    repository.append_audit.assert_called_once()
    repository.commit.assert_awaited_once()
