"""Test suite for administrative actor CRUD operations (ECO-1603)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.models.domain import (
    AccessibilityFeature,
    Actor,
    ActorCategory,
    RouteActor,
)
from app.repositories.actor_admin import ActorAdminRepository
from app.schemas.admin_actors import (
    AdminAccessibilityFeatureCreateSchema,
    AdminAccessibilityFeatureEnvelope,
    AdminAccessibilityFeatureListEnvelope,
    AdminAccessibilityFeatureSchema,
    AdminAccessibilityFeatureUpdateSchema,
    AdminActorCreateSchema,
    AdminActorEnvelope,
    AdminActorListEnvelope,
    AdminActorSchema,
    AdminActorUpdateSchema,
    AdminCategoryEnvelope,
    AdminCategoryListEnvelope,
    AdminCategorySchema,
    AdminCategoryUpdateSchema,
    AdminRouteActorCreateSchema,
    AdminRouteActorEnvelope,
    AdminRouteActorListEnvelope,
    AdminRouteActorSchema,
    AdminRouteActorUpdateSchema,
)
from app.services.actor_admin import ActorAdminService
from app.services.dependencies import get_actor_admin_service
from app.services.editorial_authorization import AuthorizationContext


def authenticated_user(*, anonymous: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid.uuid4(),
        email="admin@econexao.org",
        is_anonymous=anonymous,
        role="authenticated",
        claims={},
    )


# -----------------------------------------------------------------------------
# Repository Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repo_categories_crud() -> None:
    db = AsyncMock()
    repo = ActorAdminRepository(db)
    cat_id = uuid.uuid4()
    cat = ActorCategory(
        id=cat_id,
        slug="hospedagem",
        label="Hospedagem",
        icon="bed",
        color="#000",
        sort_order=1,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = cat
    exec_mock.scalars.return_value.all.return_value = [cat]
    db.execute.return_value = exec_mock

    res_id = await repo.get_category_by_id(cat_id)
    assert res_id is cat

    res_slug = await repo.get_category_by_slug("hospedagem")
    assert res_slug is cat

    res_list = await repo.list_categories()
    assert len(res_list) == 1

    new_cat = await repo.create_category("alimentacao", "Alimentação")
    assert new_cat.slug == "alimentacao"

    updated = await repo.update_category(cat_id, label="Novo Label")
    assert updated is not None and updated.label == "Novo Label"

    exec_mock.scalar_one_or_none.return_value = None
    none_updated = await repo.update_category(uuid.uuid4(), label="Outro Label")
    assert none_updated is None


@pytest.mark.asyncio
async def test_repo_accessibility_features_crud() -> None:
    db = AsyncMock()
    repo = ActorAdminRepository(db)
    feat_id = uuid.uuid4()
    feat = AccessibilityFeature(
        id=feat_id,
        slug="rampa",
        label="Rampa",
        description="Rampa de acesso",
        icon="ramp",
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = feat
    exec_mock.scalars.return_value.all.return_value = [feat]
    db.execute.return_value = exec_mock

    assert await repo.get_accessibility_feature_by_id(feat_id) is feat
    assert await repo.get_accessibility_feature_by_slug("rampa") is feat
    assert len(await repo.list_accessibility_features()) == 1

    created = await repo.create_accessibility_feature("libras", "Libras")
    assert created.slug == "libras"

    updated = await repo.update_accessibility_feature(feat_id, label="Rampa Editada")
    assert updated is not None and updated.label == "Rampa Editada"

    exec_mock.scalar_one_or_none.return_value = None
    assert await repo.update_accessibility_feature(uuid.uuid4(), label="Outro Label") is None


@pytest.mark.asyncio
async def test_repo_actors_crud() -> None:
    db = AsyncMock()
    repo = ActorAdminRepository(db)
    actor_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    now = datetime.now(UTC)

    actor = Actor(
        id=actor_id,
        category_id=cat_id,
        slug="pousada-eco",
        name="Pousada Ecológica",
        location=None,
        green_badge_status="bronze",
        verification_status="verified",
        created_at=now,
        updated_at=now,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = actor
    exec_mock.scalar_one.return_value = 1
    exec_mock.scalars.return_value.all.return_value = [actor]
    exec_mock.one_or_none.return_value = MagicMock(lat=-2.44, lon=-54.7)
    db.execute.return_value = exec_mock

    assert await repo.get_actor_by_id(actor_id) is actor
    assert await repo.get_actor_by_slug("pousada-eco") is actor

    actors, total = await repo.list_actors(category_id=cat_id, q="pousada", limit=10, offset=0)
    assert len(actors) == 1 and total == 1

    created = await repo.create_actor(
        category_id=cat_id,
        slug="novo-actor",
        name="Novo Ator",
        latitude=-2.44,
        longitude=-54.7,
    )
    assert created.slug == "novo-actor"

    updated = await repo.update_actor(
        actor_id, name="Nome Atualizado", latitude=-2.45, longitude=-54.71
    )
    assert updated is not None and updated.name == "Nome Atualizado"

    exec_mock.scalar_one_or_none.return_value = None
    assert await repo.update_actor(uuid.uuid4(), name="Novo Nome") is None
    assert await repo.soft_delete_actor(uuid.uuid4()) is None

    exec_mock.scalar_one_or_none.return_value = actor
    deleted = await repo.soft_delete_actor(actor_id)
    assert deleted is not None and deleted.deleted_at is not None

    lat, lon = await repo.get_actor_coordinates(actor)
    assert lat == -2.44 and lon == -54.7

    no_loc_actor = Actor(id=uuid.uuid4(), category_id=cat_id, slug="s", name="n", location=None)
    assert await repo.get_actor_coordinates(no_loc_actor) == (None, None)

    # test set_actor_accessibility_features
    link_mock = MagicMock()
    del_mock = MagicMock()
    del_mock.scalars.return_value.all.return_value = [link_mock]
    db.execute.return_value = del_mock
    await repo.set_actor_accessibility_features(actor_id, [uuid.uuid4()])


@pytest.mark.asyncio
async def test_repo_route_actors_crud() -> None:
    db = AsyncMock()
    repo = ActorAdminRepository(db)
    link_id = uuid.uuid4()
    route_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    link = RouteActor(
        id=link_id,
        route_id=route_id,
        actor_id=actor_id,
        distance_to_route_m=100.0,
        sort_order=1,
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = link
    exec_mock.scalars.return_value.all.return_value = [link]
    db.execute.return_value = exec_mock

    assert await repo.get_route_actor_by_id(link_id) is link
    assert await repo.get_route_actor_by_route_and_actor(route_id, actor_id) is link
    assert len(await repo.list_route_actors_by_actor(actor_id)) == 1
    assert len(await repo.list_route_actors_by_route(route_id)) == 1

    created = await repo.create_route_actor(route_id, actor_id, distance_to_route_m=50.0)
    assert created.distance_to_route_m == 50.0

    updated = await repo.update_route_actor(link_id, is_featured=True)
    assert updated is not None and updated.is_featured is True

    exec_mock.scalar_one_or_none.return_value = None
    assert await repo.update_route_actor(uuid.uuid4(), is_featured=True) is None

    exec_mock.scalar_one_or_none.return_value = link
    assert await repo.delete_route_actor(link_id) is True

    exec_mock.scalar_one_or_none.return_value = None
    assert await repo.delete_route_actor(uuid.uuid4()) is False


# -----------------------------------------------------------------------------
# Service Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_categories_edge_cases() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.repo = AsyncMock()
    service.auth_repo = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    cat_id = uuid.uuid4()

    # 404 get_category
    service.repo.get_category_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.get_category(ctx, cat_id)
    assert exc.value.status_code == 404

    # 404 update_category
    service.repo.get_category_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_category(ctx, cat_id, AdminCategoryUpdateSchema(label="Novo Label"))
    assert exc.value.status_code == 404

    # 422 before persistence when canonical metadata would drift
    service.repo.get_category_by_id.return_value = ActorCategory(
        id=cat_id,
        slug="hospedagem",
        label="Hospedagem",
        icon="bed",
        color="#2563EB",
        sort_order=3,
        is_public=True,
        spatial_scope="route_corridor",
    )
    with pytest.raises(HTTPException) as exc:
        await service.update_category(
            ctx, cat_id, AdminCategoryUpdateSchema(label="Label divergente")
        )
    assert exc.value.status_code == 422
    service.repo.update_category.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_accessibility_features_edge_cases() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.repo = AsyncMock()
    service.auth_repo = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    feat_id = uuid.uuid4()

    # 404 get_accessibility_feature
    service.repo.get_accessibility_feature_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.get_accessibility_feature(ctx, feat_id)
    assert exc.value.status_code == 404

    # 409 create_accessibility_feature
    service.repo.get_accessibility_feature_by_slug.return_value = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await service.create_accessibility_feature(
            ctx,
            AdminAccessibilityFeatureCreateSchema(slug="rampa", label="Rampa"),
        )
    assert exc.value.status_code == 409

    # 404 update_accessibility_feature
    service.repo.get_accessibility_feature_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_accessibility_feature(
            ctx, feat_id, AdminAccessibilityFeatureUpdateSchema(label="Novo Label")
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_service_actor_edge_cases() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.repo = AsyncMock()
    service.auth_repo = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    actor_id = uuid.uuid4()

    # 404 get_actor
    service.repo.get_actor_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.get_actor(ctx, actor_id)
    assert exc.value.status_code == 404

    # 404 create_actor category missing
    service.repo.get_category_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.create_actor(
            ctx,
            AdminActorCreateSchema(category_id=uuid.uuid4(), slug="pousada", name="Pousada"),
        )
    assert exc.value.status_code == 404

    # 409 create_actor duplicate slug
    service.repo.get_category_by_id.return_value = MagicMock()
    service.repo.get_actor_by_slug.return_value = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await service.create_actor(
            ctx,
            AdminActorCreateSchema(category_id=uuid.uuid4(), slug="pousada", name="Pousada"),
        )
    assert exc.value.status_code == 409

    # 404 create_actor feature missing
    service.repo.get_category_by_id.return_value = MagicMock()
    service.repo.get_actor_by_slug.return_value = None
    service.repo.get_accessibility_feature_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.create_actor(
            ctx,
            AdminActorCreateSchema(
                category_id=uuid.uuid4(),
                slug="pousada",
                name="Pousada",
                accessibility_feature_ids=[uuid.uuid4()],
            ),
        )
    assert exc.value.status_code == 404

    # 404 update_actor missing category
    service.repo.get_actor_by_id.return_value = MagicMock()
    service.repo.get_category_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_actor(ctx, actor_id, AdminActorUpdateSchema(category_id=uuid.uuid4()))
    assert exc.value.status_code == 404

    # 404 update_actor missing feature
    service.repo.get_actor_by_id.return_value = MagicMock()
    service.repo.get_category_by_id.return_value = MagicMock()
    service.repo.get_accessibility_feature_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_actor(
            ctx,
            actor_id,
            AdminActorUpdateSchema(accessibility_feature_ids=[uuid.uuid4()]),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_service_route_actor_edge_cases() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.repo = AsyncMock()
    service.auth_repo = MagicMock()

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    actor_id = uuid.uuid4()
    link_id = uuid.uuid4()

    # 404 list_route_links_by_actor missing actor
    service.repo.get_actor_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.list_route_links_by_actor(ctx, actor_id)
    assert exc.value.status_code == 404

    # 404 create_route_link missing actor
    service.repo.get_actor_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.create_route_link(
            ctx,
            actor_id,
            AdminRouteActorCreateSchema(route_id=uuid.uuid4(), actor_id=actor_id),
        )
    assert exc.value.status_code == 404

    # 409 create_route_link duplicate link
    service.repo.get_actor_by_id.return_value = MagicMock()
    service.repo.get_route_actor_by_route_and_actor.return_value = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await service.create_route_link(
            ctx,
            actor_id,
            AdminRouteActorCreateSchema(route_id=uuid.uuid4(), actor_id=actor_id),
        )
    assert exc.value.status_code == 409

    # 404 update_route_link missing link
    service.repo.get_route_actor_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_route_link(ctx, link_id, AdminRouteActorUpdateSchema(is_featured=True))
    assert exc.value.status_code == 404

    # 404 delete_route_link missing link
    service.repo.get_route_actor_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.delete_route_link(ctx, link_id)
    assert exc.value.status_code == 404


# -----------------------------------------------------------------------------
# Admin Categories API Tests
# -----------------------------------------------------------------------------


def test_admin_list_categories_success() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    admin_service.list_categories.return_value = AdminCategoryListEnvelope(
        data=[
            AdminCategorySchema(
                id=uuid.uuid4(),
                slug="hospedagem",
                label="Hospedagem Ecológica",
                icon="bed",
                color="#2E7D32",
                sort_order=1,
                created_at=now,
                updated_at=now,
            )
        ]
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).get(
            "/api/v1/admin/categories",
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()["data"]
    assert len(res_data) == 1
    assert res_data[0]["slug"] == "hospedagem"


def test_admin_get_category_endpoints() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    cat_id = uuid.uuid4()

    admin_service.get_category.return_value = AdminCategoryEnvelope(
        data=AdminCategorySchema(
            id=cat_id,
            slug="hospedagem",
            label="Hospedagem",
            icon="bed",
            color="#000",
            sort_order=1,
            created_at=now,
            updated_at=now,
        )
    )
    admin_service.update_category.return_value = AdminCategoryEnvelope(
        data=AdminCategorySchema(
            id=cat_id,
            slug="hospedagem",
            label="Novo Label",
            icon="bed",
            color="#000",
            sort_order=1,
            created_at=now,
            updated_at=now,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_get = client.get(
            f"/api/v1/admin/categories/{cat_id}",
            headers={"Authorization": "Bearer token"},
        )
        assert res_get.status_code == 200

        res_patch = client.patch(
            f"/api/v1/admin/categories/{cat_id}",
            json={"label": "Novo Label"},
            headers={"Authorization": "Bearer token"},
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["data"]["label"] == "Novo Label"
    finally:
        app.dependency_overrides.clear()


def test_admin_create_category_duplicate_slug_conflict() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    admin_service.create_category.side_effect = HTTPException(
        status_code=409, detail="Já existe uma categoria com o slug 'hospedagem'."
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            "/api/v1/admin/categories",
            json={
                "slug": "hospedagem",
                "label": "Hospedagem",
                "icon": "bed",
                "color": "#2563EB",
                "sort_order": 3,
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


# -----------------------------------------------------------------------------
# Admin Accessibility Features API Tests
# -----------------------------------------------------------------------------


def test_admin_accessibility_feature_endpoints() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    feat_id = uuid.uuid4()

    feat_schema = AdminAccessibilityFeatureSchema(
        id=feat_id,
        slug="rampa",
        label="Rampa",
        description="Rampa de acesso",
        icon="ramp",
        created_at=now,
        updated_at=now,
    )

    admin_service.list_accessibility_features.return_value = AdminAccessibilityFeatureListEnvelope(
        data=[feat_schema]
    )
    admin_service.get_accessibility_feature.return_value = AdminAccessibilityFeatureEnvelope(
        data=feat_schema
    )
    admin_service.update_accessibility_feature.return_value = AdminAccessibilityFeatureEnvelope(
        data=feat_schema
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_list = client.get(
            "/api/v1/admin/accessibility-features",
            headers={"Authorization": "Bearer token"},
        )
        assert res_list.status_code == 200

        res_get = client.get(
            f"/api/v1/admin/accessibility-features/{feat_id}",
            headers={"Authorization": "Bearer token"},
        )
        assert res_get.status_code == 200

        res_patch = client.patch(
            f"/api/v1/admin/accessibility-features/{feat_id}",
            json={"label": "Rampa Editada"},
            headers={"Authorization": "Bearer token"},
        )
        assert res_patch.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_admin_create_accessibility_feature_success() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    feature_id = uuid.uuid4()
    admin_service.create_accessibility_feature.return_value = AdminAccessibilityFeatureEnvelope(
        data=AdminAccessibilityFeatureSchema(
            id=feature_id,
            slug="rampa-acesso",
            label="Rampa de Acesso",
            description="Rampa para cadeirantes",
            icon="ramp",
            created_at=now,
            updated_at=now,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            "/api/v1/admin/accessibility-features",
            json={
                "slug": "rampa-acesso",
                "label": "Rampa de Acesso",
                "description": "Rampa para cadeirantes",
                "icon": "ramp",
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["id"] == str(feature_id)


# -----------------------------------------------------------------------------
# Admin Actors API Tests
# -----------------------------------------------------------------------------


def test_admin_list_and_get_actors_endpoints() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    actor_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    actor_schema = AdminActorSchema(
        id=actor_id,
        category_id=cat_id,
        slug="pousada-eco",
        name="Pousada Ecológica",
        opening_hours={},
        payment_methods=[],
        green_badge_status="none",
        verification_status="unverified",
        created_at=now,
        updated_at=now,
    )

    admin_service.list_actors.return_value = AdminActorListEnvelope(
        data=[actor_schema],
        meta=MagicMock(total=1, limit=50, next_cursor=None),
    )
    admin_service.get_actor.return_value = AdminActorEnvelope(data=actor_schema)
    admin_service.update_actor.return_value = AdminActorEnvelope(data=actor_schema)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_list = client.get(
            "/api/v1/admin/actors?q=pousada&include_deleted=true",
            headers={"Authorization": "Bearer token"},
        )
        assert res_list.status_code == 200

        res_get = client.get(
            f"/api/v1/admin/actors/{actor_id}",
            headers={"Authorization": "Bearer token"},
        )
        assert res_get.status_code == 200

        res_patch = client.patch(
            f"/api/v1/admin/actors/{actor_id}",
            json={"name": "Novo Nome"},
            headers={"Authorization": "Bearer token"},
        )
        assert res_patch.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_admin_create_actor_success() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    actor_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    admin_service.create_actor.return_value = AdminActorEnvelope(
        data=AdminActorSchema(
            id=actor_id,
            category_id=cat_id,
            category=AdminCategorySchema(
                id=cat_id,
                slug="restaurante",
                label="Restaurante",
                icon=None,
                color=None,
                sort_order=0,
                created_at=now,
                updated_at=now,
            ),
            slug="pousada-eco",
            name="Pousada Ecológica",
            description="Pousada sustentável",
            opening_hours={},
            payment_methods=[],
            latitude=-2.44,
            longitude=-54.7,
            green_badge_status="bronze",
            verification_status="verified",
            created_at=now,
            updated_at=now,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).post(
            "/api/v1/admin/actors",
            json={
                "category_id": str(cat_id),
                "slug": "pousada-eco",
                "name": "Pousada Ecológica",
                "description": "Pousada sustentável",
                "latitude": -2.44,
                "longitude": -54.7,
                "green_badge_status": "bronze",
                "verification_status": "verified",
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Pousada Ecológica"


def test_admin_update_actor_optimistic_concurrency_409() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    admin_service.update_actor.side_effect = HTTPException(
        status_code=409,
        detail="O ator foi alterado por outro usuário. Por favor recarregue antes de salvar.",
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    actor_id = uuid.uuid4()
    try:
        response = TestClient(app).patch(
            f"/api/v1/admin/actors/{actor_id}",
            json={
                "name": "Novo Nome",
                "expected_version": "2026-08-13T00:00:00+00:00",
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "outro usuário" in response.json()["error"]["message"]


def test_admin_delete_actor_soft_delete_success() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    actor_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    admin_service.delete_actor.return_value = AdminActorEnvelope(
        data=AdminActorSchema(
            id=actor_id,
            category_id=cat_id,
            slug="pousada-eco",
            name="Pousada Ecológica",
            opening_hours={},
            payment_methods=[],
            green_badge_status="none",
            verification_status="unverified",
            created_at=now,
            updated_at=now,
            deleted_at=now,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        response = TestClient(app).delete(
            f"/api/v1/admin/actors/{actor_id}",
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["deleted_at"] is not None


# -----------------------------------------------------------------------------
# Admin Route Links API Tests
# -----------------------------------------------------------------------------


def test_admin_route_links_endpoints() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    now = datetime.now(UTC)
    actor_id = uuid.uuid4()
    route_id = uuid.uuid4()
    link_id = uuid.uuid4()

    link_schema = AdminRouteActorSchema(
        id=link_id,
        route_id=route_id,
        actor_id=actor_id,
        distance_to_route_m=100.0,
        origin_flags={},
        is_featured=False,
        sort_order=1,
        created_at=now,
        updated_at=now,
    )

    admin_service.list_route_links_by_actor.return_value = AdminRouteActorListEnvelope(
        data=[link_schema]
    )
    admin_service.update_route_link.return_value = AdminRouteActorEnvelope(data=link_schema)
    admin_service.delete_route_link.return_value = True

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    try:
        client = TestClient(app)
        res_list = client.get(
            f"/api/v1/admin/actors/{actor_id}/route-links",
            headers={"Authorization": "Bearer token"},
        )
        assert res_list.status_code == 200

        res_patch = client.patch(
            f"/api/v1/admin/actors/route-links/{link_id}",
            json={"is_featured": True},
            headers={"Authorization": "Bearer token"},
        )
        assert res_patch.status_code == 200

        res_del = client.delete(
            f"/api/v1/admin/actors/route-links/{link_id}",
            headers={"Authorization": "Bearer token"},
        )
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"
    finally:
        app.dependency_overrides.clear()


def test_admin_create_route_link_mismatched_actor_id_422() -> None:
    user = authenticated_user()
    admin_service = AsyncMock()
    admin_service.create_route_link.side_effect = HTTPException(
        status_code=422,
        detail="O ID do ator na URL não coincide com o corpo da requisição.",
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_actor_admin_service] = lambda: admin_service
    actor_id = uuid.uuid4()
    other_actor_id = uuid.uuid4()
    route_id = uuid.uuid4()
    try:
        response = TestClient(app).post(
            f"/api/v1/admin/actors/{actor_id}/route-links",
            json={
                "route_id": str(route_id),
                "actor_id": str(other_actor_id),
            },
            headers={"Authorization": "Bearer token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


# -----------------------------------------------------------------------------
# Unit Tests for Service Layer (Capabilities, Concurrency, Audit Logs)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_create_actor_requires_publish_capability() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.auth_service.require_capability.side_effect = [
        None,  # actor.write ok
        HTTPException(status_code=403, detail="Sem permissão de publicação"),
    ]
    service.repo = AsyncMock()
    service.repo.get_category_by_id.return_value = MagicMock()
    service.repo.get_actor_by_slug.return_value = None

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminActorCreateSchema(
        category_id=uuid.uuid4(),
        slug="pousada-test",
        name="Pousada Test",
        verification_status="verified",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_actor(ctx, body)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_service_update_actor_optimistic_concurrency_mismatch() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.repo = AsyncMock()

    now = datetime.now(UTC)
    actor_id = uuid.uuid4()
    existing_actor = MagicMock()
    existing_actor.id = actor_id
    existing_actor.updated_at = now
    existing_actor.verification_status = "unverified"
    service.repo.get_actor_by_id.return_value = existing_actor

    ctx = AuthorizationContext(actor_id=uuid.uuid4())
    body = AdminActorUpdateSchema(
        name="Novo Nome",
        expected_version="2020-01-01T00:00:00+00:00",  # mismatched timestamp
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_actor(ctx, actor_id, body)

    assert exc_info.value.status_code == 409
    assert "outro usuário" in exc_info.value.detail


@pytest.mark.asyncio
async def test_service_delete_actor_records_audit_log() -> None:
    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.auth_repo = MagicMock()
    service.repo = AsyncMock()

    actor_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    now = datetime.now(UTC)
    existing_actor = Actor(
        id=actor_id,
        category_id=cat_id,
        slug="pousada-test",
        name="Pousada Test",
        description=None,
        sub_category=None,
        address=None,
        city=None,
        state_code=None,
        phone=None,
        email=None,
        instagram=None,
        website=None,
        opening_hours={},
        payment_methods=[],
        green_badge_status="none",
        verification_status="unverified",
        google_rating=None,
        google_review_count=None,
        created_at=now,
        updated_at=now,
        deleted_at=now,
    )
    existing_actor.category = None
    existing_actor.accessibility_features = []

    service.repo.get_actor_by_id.return_value = existing_actor
    service.repo.soft_delete_actor.return_value = existing_actor
    service.repo.get_actor_coordinates.return_value = (None, None)

    actor_user_id = uuid.uuid4()
    ctx = AuthorizationContext(actor_id=actor_user_id)

    res = await service.delete_actor(ctx, actor_id)

    assert res.data.deleted_at == now
    service.auth_repo.append_audit.assert_called_once()
    call_kwargs = service.auth_repo.append_audit.call_args.kwargs
    assert call_kwargs["actor_id"] == actor_user_id
    assert call_kwargs["action"] == "delete"
    assert call_kwargs["resource_type"] == "actor"
    assert call_kwargs["resource_id"] == actor_id


@pytest.mark.asyncio
async def test_repo_actor_types_crud() -> None:
    from app.models.domain import ActorType

    db = AsyncMock()
    repo = ActorAdminRepository(db)
    type_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    t = ActorType(
        id=type_id,
        category_id=cat_id,
        slug="pousada_hotel",
        label="Hotel & Pousada",
        icon="bed",
        sort_order=30,
        aliases=["pousada", "hotel"],
        spatial_scope="route_corridor",
        publication_rule="Público se published.",
    )

    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = t
    exec_mock.scalars.return_value.all.return_value = [t]
    db.execute.return_value = exec_mock

    assert await repo.get_actor_type_by_id(type_id) is t
    assert await repo.get_actor_type_by_slug("pousada_hotel") is t
    assert len(await repo.list_actor_types(category_id=cat_id)) == 1

    created = await repo.create_actor_type(
        category_id=cat_id,
        slug="novo_tipo",
        label="Novo Tipo",
        icon="star",
        sort_order=1,
    )
    assert created.slug == "novo_tipo"

    updated = await repo.update_actor_type(type_id, label="Hotel e Pousada Atualizado")
    assert updated is not None and updated.label == "Hotel e Pousada Atualizado"

    exec_mock.scalar_one_or_none.return_value = None
    assert await repo.update_actor_type(uuid.uuid4(), label="Outro") is None


@pytest.mark.asyncio
async def test_service_actor_types_crud() -> None:
    from app.models.domain import ActorType
    from app.schemas.admin_actors import AdminActorTypeCreateSchema, AdminActorTypeUpdateSchema

    db = AsyncMock()
    service = ActorAdminService(db)
    service.auth_service = AsyncMock()
    service.auth_repo = MagicMock()
    service.repo = AsyncMock()

    cat_id = uuid.uuid4()
    type_id = uuid.uuid4()
    now = datetime.now(UTC)
    t = ActorType(
        id=type_id,
        category_id=cat_id,
        slug="pousada_hotel",
        label="Hotel & Pousada",
        icon="bed",
        sort_order=30,
        aliases=["pousada", "hotel"],
        spatial_scope="route_corridor",
        publication_rule="Público se published.",
        created_at=now,
        updated_at=now,
    )

    service.repo.list_actor_types.return_value = [t]
    service.repo.get_actor_type_by_id.return_value = t
    service.repo.get_actor_type_by_slug.return_value = None
    service.repo.get_category_by_id.return_value = MagicMock()
    service.repo.create_actor_type.return_value = t
    service.repo.update_actor_type.return_value = t

    ctx = AuthorizationContext(actor_id=uuid.uuid4())

    list_res = await service.list_actor_types(ctx, category_id=cat_id)
    assert len(list_res.data) == 1
    assert list_res.data[0].slug == "pousada_hotel"

    get_res = await service.get_actor_type(ctx, type_id)
    assert get_res.data.id == type_id

    create_res = await service.create_actor_type(
        ctx,
        AdminActorTypeCreateSchema(
            category_id=cat_id,
            slug="novo_subtipo",
            label="Novo Subtipo",
            icon="star",
            sort_order=5,
            spatial_scope="route_corridor",
        ),
    )
    assert create_res.data.slug == "pousada_hotel"

    update_res = await service.update_actor_type(
        ctx,
        type_id,
        AdminActorTypeUpdateSchema(label="Novo Nome Subtipo"),
    )
    assert update_res.data.id == type_id
