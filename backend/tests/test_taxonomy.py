"""Focused ECO-2302 contract tests for the canonical visual taxonomy."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.core.taxonomy import (
    CANONICAL_CATEGORIES,
    CANONICAL_CATEGORY_SLUGS,
    normalize_category_slug,
)
from app.models.domain import ActorCategory
from app.repositories.territorial import TerritorialRepository
from app.schemas.admin_actors import AdminCategoryCreateSchema
from app.services.territorial import _CATEGORIES_CACHE, TerritorialService

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FORWARD_MIGRATION = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260824194405_remediate_canonical_taxonomy_adr0010.sql"
)
CLASSIFICATION_REMEDIATION = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260824211947_remediate_emergency_taxonomy_classification_adr0010.sql"
)


def test_canonical_taxonomy_matches_accepted_metadata_and_spatial_scope() -> None:
    assert list(CANONICAL_CATEGORIES) == [
        "alimentacao",
        "atrativos",
        "hospedagem",
        "artesanato",
        "transporte",
        "saude",
        "seguranca",
        "outros",
    ]
    assert {item["sort_order"] for item in CANONICAL_CATEGORIES.values()} == {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        99,
    }
    assert all(item["label"] for item in CANONICAL_CATEGORIES.values())
    assert all(item["color"].startswith("#") for item in CANONICAL_CATEGORIES.values())
    assert all(item["icon"] for item in CANONICAL_CATEGORIES.values())
    assert all(item["is_public"] is True for item in CANONICAL_CATEGORIES.values())
    assert CANONICAL_CATEGORIES["outros"] == {
        "slug": "outros",
        "label": "Outros",
        "color": "#6B7280",
        "icon": "help-circle",
        "sort_order": 99,
        "is_public": True,
        "spatial_scope": "route_corridor",
    }


@pytest.mark.parametrize(
    ("source_value", "expected_slug"),
    [
        ("Barraca de Praia", "alimentacao"),
        ("Ponto Turístico", "atrativos"),
        ("Igreja Histórica", "atrativos"),
        ("Casas de temporada", "hospedagem"),
        ("Comunidade Tradicional (Vendas)", "artesanato"),
        ("Porto / Catraia", "transporte"),
        ("Ponto de Ônibus", "transporte"),
        ("Farmácias", "saude"),
        ("Delegacia de Polícia", "seguranca"),
        ("categoria completamente desconhecida", "outros"),
        (None, "outros"),
    ],
)
def test_source_aliases_normalize_to_canonical_slug(
    source_value: str | None, expected_slug: str
) -> None:
    assert normalize_category_slug(source_value) == expected_slug
    assert expected_slug in CANONICAL_CATEGORY_SLUGS


def test_admin_schema_rejects_invalid_slug_and_missing_visual_metadata() -> None:
    with pytest.raises(ValidationError):
        AdminCategoryCreateSchema(
            slug="categoria-invalida",
            label="Inválida",
            icon="circle",
            color="#000000",
        )

    with pytest.raises(ValidationError):
        AdminCategoryCreateSchema(slug="outros", label="Outros")


def test_forward_migration_enforces_slug_metadata_publication_and_private_access() -> None:
    sql = FORWARD_MIGRATION.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS is_public BOOLEAN" in sql
    assert "ADD COLUMN IF NOT EXISTS spatial_scope VARCHAR(32)" in sql
    assert "chk_actor_categories_canonical_metadata" in sql
    assert "slug NOT IN" in sql
    assert "ALTER COLUMN icon SET NOT NULL" in sql
    assert "ALTER COLUMN color SET NOT NULL" in sql
    assert "'outros', 'Outros', '#6B7280', 'help-circle', 99, true" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON app_private.actor_categories FROM PUBLIC, anon, authenticated" in sql


def test_classification_remediation_uses_exclusive_specific_accent_safe_terms() -> None:
    sql = CLASSIFICATION_REMEDIATION.read_text(encoding="utf-8")
    normalized = sql.casefold()

    assert "begin;" in normalized
    assert "commit;" in normalized
    assert "translate(" in normalized
    assert "unaccent" not in normalized
    assert "posto[[:space:]]+de[[:space:]]+saude" in normalized
    assert "pronto[[:space:]]+atendimento" in normalized
    assert "|posto|" not in normalized
    assert "|pronto|" not in normalized
    assert "health_match and not candidates.security_match" in normalized
    assert "security_match and not candidates.health_match" in normalized
    assert "where actor.category_id = v_outros_id" in normalized
    assert "app_private.eco_2302_taxonomy_remediation_events" in normalized
    assert "unique (migration_version, actor_id)" in normalized
    assert "matched_rule in ('health_only', 'security_only')" in normalized
    assert "on conflict (migration_version, actor_id) do nothing" in normalized
    assert "actor.category_id = event.from_category_id" in normalized
    assert "current category_id still" in normalized
    assert "equals event.to_category_id" in normalized
    assert "enable row level security" in normalized
    assert "from public, anon, authenticated" in normalized
    assert "references app_private.actors(id) on delete restrict" in normalized
    assert normalized.count("references app_private.actor_categories(id) on delete restrict") == 2


def test_seed_is_idempotent_when_canonical_metadata_is_unchanged() -> None:
    sql = (REPOSITORY_ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    assert "ON CONFLICT (slug) DO UPDATE" in sql
    assert "IS DISTINCT FROM" in sql
    assert "actor_categories.is_public" in sql
    assert "actor_categories.spatial_scope" in sql


@pytest.mark.asyncio
async def test_public_category_query_filters_public_and_returns_outros() -> None:
    db = AsyncMock()
    outros = ActorCategory(
        id=uuid.uuid4(),
        slug="outros",
        label="Outros",
        icon="help-circle",
        color="#6B7280",
        sort_order=99,
        is_public=True,
        spatial_scope="route_corridor",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [outros]
    db.scalars.return_value = scalars_result

    repo = TerritorialRepository(db)
    assert await repo.list_actor_categories() == [outros]
    statement = db.scalars.await_args.args[0]
    assert "actor_categories.is_public IS true" in str(statement)

    _CATEGORIES_CACHE["data"] = None
    _CATEGORIES_CACHE["expires_at"] = 0.0
    service = TerritorialService(AsyncMock())
    service.repo.list_actor_categories = AsyncMock(return_value=[outros])
    response = await service.list_actor_categories()
    assert [category.slug for category in response.data] == ["outros"]


def test_canonical_actor_types_count_and_invariants() -> None:
    from app.core.taxonomy import (
        CANONICAL_ACTOR_TYPES,
        CANONICAL_TYPE_SLUGS,
        get_canonical_actor_type,
        is_canonical_actor_type,
    )

    # 32 specialized subtypes defined in ADR 0015
    assert len(CANONICAL_ACTOR_TYPES) == 32
    assert len(CANONICAL_TYPE_SLUGS) == 32

    for slug, type_def in CANONICAL_ACTOR_TYPES.items():
        assert is_canonical_actor_type(slug) is True
        assert type_def["slug"] == slug
        assert type_def["category_slug"] in CANONICAL_CATEGORY_SLUGS
        assert type_def["label"]
        assert type_def["icon"]
        assert type_def["spatial_scope"] in ("route_corridor", "citywide_essential", "both")
        assert len(type_def["aliases"]) > 0

    assert get_canonical_actor_type("invalid_type_slug")["slug"] == "nao_classificado"


@pytest.mark.parametrize(
    ("raw_text", "expected_type_slug"),
    [
        ("Restaurante e Bar Regional", "restaurante"),
        ("Peixaria da Orla", "restaurante"),
        ("Botequim & Choperia", "bar_vida_noturna"),
        ("Barraca de praia Pindobal", "barraca_praia"),
        ("Cafeteria e Sorveteria", "cafe_lanchonete"),
        ("Supermercado e Mercearia", "mercado_conveniencia"),
        ("Feira Agroecológica Municipal", "feira_livre"),
        ("Trilha do Macaco e Igarapé", "atrativo_natural"),
        ("Praia de Ponta de Pedras", "praia_fluvial"),
        ("Bancada de Areia e Arquipélago", "ilha"),
        ("Mirante da Serra da Piroca", "serra_mirante"),
        ("Área de Proteção Ambiental Flona", "unidade_conservacao"),
        ("Centro Cultural e Museu", "patrimonio_cultural"),
        ("Catedral e Igreja Matriz", "templo_religioso"),
        ("Balneário e Parque Aquático", "lazer_balneario"),
        ("Pousada e Ecopousada", "pousada_hotel"),
        ("Aluguel de Casa de Praia e Camping", "casa_temporada"),
        ("Associação de Artesãos Tapajônicos", "artesanato_local"),
        ("Aeroporto de Santarém", "terminal_aeroporto"),
        ("Terminal Hidroviário e Balsa", "terminal_porto"),
        ("Rodoviária e Vans", "terminal_rodoviario"),
        ("Catraias e Barqueiro em Alter do Chão", "catraia_travessia"),
        ("Posto de Gasolina 24h", "posto_combustivel"),
        ("Locadora de Veículos e Rent a Car", "locadora_mobilidade"),
        ("Agência de Receptivo e Passeios", "agencia_turismo"),
        ("Hospital Municipal e UPA", "hospital_upa"),
        ("UBS e Centro de Saúde da Família", "posto_saude_ubs"),
        ("Farmácia e Drogaria 24 Horas", "farmacia"),
        ("Delegacia da Polícia Civil e Bombeiros", "seguranca_publica"),
        ("Conselho Tutelar e CRAS", "conselho_tutelar_protecao"),
        ("Cartório e Prefeitura", "servicos_publicos_cartorios"),
        ("Shopping e Decoração de Eventos", "comercio_eventos"),
        ("Totalmente desconhecido", "nao_classificado"),
        (None, "nao_classificado"),
    ],
)
def test_normalize_actor_type_slug(raw_text: str | None, expected_type_slug: str) -> None:
    from app.core.taxonomy import normalize_actor_type_slug

    assert normalize_actor_type_slug(raw_text) == expected_type_slug
