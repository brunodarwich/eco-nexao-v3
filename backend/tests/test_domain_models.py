"""Unit tests for domain models and Pydantic schemas (ECO-0201 to ECO-0206)."""

import uuid
from datetime import UTC, datetime

from geoalchemy2 import Geography

from app.db.base import Base
from app.models.domain import (
    Actor,
    ActorCategory,
    Profile,
    Region,
    Route,
    RouteOrigin,
    UserPreference,
)
from app.schemas.domain import (
    RegionRead,
)


def test_region_model_instantiation() -> None:
    region_id = uuid.uuid4()
    region = Region(
        id=region_id,
        slug="pindobal-region",
        name="Região de Pindobal",
        state_code="PA",
        is_active=True,
    )
    assert region.id == region_id
    assert region.slug == "pindobal-region"
    assert region.state_code == "PA"
    assert region.is_active is True


def test_domain_metadata_uses_private_schema_and_geography() -> None:
    """ORM metadata must match the private PostGIS migration contract."""
    assert Base.metadata.schema == "app_private"
    assert isinstance(Region.__table__.c.center.type, Geography)


def test_region_pydantic_schema_validation() -> None:
    now = datetime.now(UTC)
    region_id = uuid.uuid4()
    data = {
        "id": region_id,
        "slug": "santarem-pindobal",
        "name": "Santarém - Pindobal",
        "state_code": "PA",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    schema = RegionRead.model_validate(data)
    assert schema.id == region_id
    assert schema.slug == "santarem-pindobal"
    assert schema.state_code == "PA"


def test_route_and_origin_relationship() -> None:
    route_id = uuid.uuid4()
    region_id = uuid.uuid4()
    route = Route(
        id=route_id,
        region_id=region_id,
        slug="rota-pindobal",
        title="Pindobal",
        city="Belterra",
        state_code="PA",
        status="active",
    )
    origin_porto = RouteOrigin(
        id=uuid.uuid4(),
        route_id=route_id,
        code="porto",
        name="Porto de Santarém",
        distance_m=45229,
        duration_s=3600,
        sort_order=1,
    )
    route.origins.append(origin_porto)

    assert route.title == "Pindobal"
    assert len(route.origins) == 1
    assert route.origins[0].code == "porto"
    assert route.origins[0].distance_m == 45229


def test_actor_and_category_instantiation() -> None:
    cat_id = uuid.uuid4()
    category = ActorCategory(
        id=cat_id,
        slug="gastronomia",
        label="Gastronomia",
        icon="utensils",
    )
    actor = Actor(
        id=uuid.uuid4(),
        slug="restaurante-pindobal",
        name="Restaurante Pindobal",
        category_id=cat_id,
        city="Belterra",
        state_code="PA",
        google_rating=4.8,
        google_review_count=120,
    )
    actor.category = category

    assert actor.name == "Restaurante Pindobal"
    assert actor.category.label == "Gastronomia"
    assert actor.google_rating == 4.8


def test_actor_type_and_actor_relationship() -> None:
    from app.models.domain import ActorType

    cat_id = uuid.uuid4()
    type_id = uuid.uuid4()
    category = ActorCategory(
        id=cat_id,
        slug="alimentacao",
        label="Alimentação",
        icon="utensils",
    )
    actor_type = ActorType(
        id=type_id,
        category_id=cat_id,
        slug="restaurante",
        label="Restaurante & Gastronomia",
        icon="utensils",
        sort_order=10,
        aliases=["restaurante", "culinaria"],
        spatial_scope="route_corridor",
    )
    actor = Actor(
        id=uuid.uuid4(),
        slug="restaurante-tapajos",
        name="Restaurante Tapajós",
        category_id=cat_id,
        type_id=type_id,
    )
    actor_type.category = category
    actor.type = actor_type

    assert actor.type.slug == "restaurante"
    assert actor.type.category.slug == "alimentacao"
    assert actor.type.spatial_scope == "route_corridor"
    assert "restaurante" in actor.type.aliases


def test_user_profile_and_preferences() -> None:
    user_id = uuid.uuid4()
    profile = Profile(
        id=user_id,
        name="Viajante Consciente",
        location="Belém, PA",
        status="active",
    )
    prefs = UserPreference(
        id=uuid.uuid4(),
        user_id=user_id,
        screen_reader_mode=True,
        high_contrast=False,
        text_scale=1.2,
        locale="pt-BR",
    )
    profile.preferences = prefs

    assert profile.id == user_id
    assert profile.preferences.screen_reader_mode is True
    assert profile.preferences.text_scale == 1.2
