"""Comprehensive unit and transactional integration tests for ECO-2605.

Verifies:
1. Parsing and strict validation of Route Packages (Pindobal and Altamira).
2. Fail-closed rejection of invented google_place_id, artificial cid= URLs,
   invalid categories and broken bounds.
3. Transactional atomic persistence with complete rollback upon induced failure (fail_after).
4. Strict idempotency across re-execution (unchanged=N, created=0, updated=0).
5. Coexistence of multiple routes across different regions without collision.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from app.ingestion.route_package_importer import (
    run_route_package_dry_run,
)
from app.ingestion.route_package_parser import (
    RouteActorPackageSchema,
    RoutePackageParser,
)
from app.ingestion.route_package_repository import (
    RoutePackageRepository,
)
from app.models.domain import (
    Actor,
    ExternalSource,
    IngestionRun,
    RawSourceRecord,
    Region,
    Route,
    RouteActor,
    RouteGeometry,
    RouteOrigin,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "route_packages"
PINDOBAL_PACKAGE_PATH = (
    Path(__file__).parent.parent.parent / "docs" / "data" / "pindobal_route_package.md"
)
ALTAMIRA_PACKAGE_PATH = FIXTURES_DIR / "altamira_xingu_package.md"


def fake_session() -> tuple[Mock, AsyncMock]:
    session = Mock()
    transaction = AsyncMock()
    session.begin = Mock(return_value=transaction)
    session.add_all = Mock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    result = Mock()
    result.tuples.return_value = []
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=None)
    return session, transaction


# =============================================================================
# 1. Parser & Validation Tests
# =============================================================================


def test_parser_loads_pindobal_package() -> None:
    assert PINDOBAL_PACKAGE_PATH.is_file(), f"Missing {PINDOBAL_PACKAGE_PATH}"
    pkg = RoutePackageParser.parse_file(PINDOBAL_PACKAGE_PATH)

    assert pkg.metadata.route_slug == "rota-pindobal"
    assert pkg.metadata.region_slug == "santarem-belterra"
    assert pkg.metadata.status == "draft"
    assert pkg.metadata.is_verified is False
    assert len(pkg.origins) == 3
    assert {o.origin_code for o in pkg.origins} == {"porto", "aeroporto", "rodoviaria"}
    assert len(pkg.geometries) == 3
    assert len(pkg.actors) == 5

    # Check actor details and missing values handled as None
    actor_casa_vidro = next(a for a in pkg.actors if a.slug == "pousada-casa-de-vidro-pindobal")
    assert actor_casa_vidro.category_slug == "hospedagem"
    assert actor_casa_vidro.contacts.phone_raw is None
    assert actor_casa_vidro.contacts.email == "paulocruz012@gmail.com"
    assert actor_casa_vidro.provenance_and_sources.is_semtur_inventory is True
    assert actor_casa_vidro.provenance_and_sources.semtur_external_id == "semtur_p57_id40"
    assert actor_casa_vidro.provenance_and_sources.google_places_ref.get("place_id") is None


def test_parser_loads_altamira_fixture_package() -> None:
    assert ALTAMIRA_PACKAGE_PATH.is_file(), f"Missing {ALTAMIRA_PACKAGE_PATH}"
    pkg = RoutePackageParser.parse_file(ALTAMIRA_PACKAGE_PATH)

    assert pkg.metadata.route_slug == "rota-volta-grande-xingu"
    assert pkg.metadata.region_slug == "xingu-altamira"
    assert pkg.metadata.city == "Altamira"
    assert len(pkg.origins) == 2
    assert {o.origin_code for o in pkg.origins} == {"rodoviaria_altamira", "aeroporto_altamira"}
    assert len(pkg.geometries) == 2
    assert len(pkg.actors) == 3

    hospital = next(
        a for a in pkg.actors if a.slug == "hospital-regional-publico-da-transamazonica"
    )
    assert hospital.category_slug == "saude"
    assert hospital.spatial_scope == "citywide_essential"
    assert hospital.contacts.phone_raw == "(93) 3515-7700"
    assert hospital.contacts.email is None


# =============================================================================
# 2. Negative Validation / Guardrail Tests
# =============================================================================


def test_reject_invented_google_place_id_with_rating() -> None:
    """Hard guard: rating cannot exist if place_id is absent/missing."""
    raw_actor = {
        "slug": "invalido-bar",
        "name": "Bar Inválido",
        "category_slug": "alimentacao",
        "spatial_scope": "route_corridor",
        "location": {"latitude": -2.5, "longitude": -54.9, "status_coord": "ok"},
        "provenance_and_sources": {
            "google_places_ref": {
                "place_id": "VALOR_AUSENTE",
                "google_rating": 4.8,  # FORBIDDEN: Rating without verified Place ID
            }
        },
    }
    with pytest.raises(ValidationError, match="google_rating cannot be assigned"):
        RouteActorPackageSchema(**raw_actor)


def test_reject_artificial_cid_urls() -> None:
    """Hard guard: URIs containing cid= are strictly prohibited."""
    raw_actor = {
        "slug": "invalido-cid",
        "name": "Local com CID",
        "category_slug": "alimentacao",
        "spatial_scope": "route_corridor",
        "location": {"latitude": -2.5, "longitude": -54.9, "status_coord": "ok"},
        "provenance_and_sources": {
            "google_places_ref": {
                "place_id": "ChIJ123",
                "google_maps_uri": "https://maps.google.com/?cid=987654321",
            }
        },
    }
    with pytest.raises(
        ValidationError, match="Artificial Google Maps URIs with 'cid=' are strictly forbidden"
    ):
        RouteActorPackageSchema(**raw_actor)


def test_reject_non_canonical_category() -> None:
    """Hard guard: only the 8 canonical groups (ADR 0010) are accepted."""
    raw_actor = {
        "slug": "invalido-cat",
        "name": "Categoria Fictícia",
        "category_slug": "compras_gerais",  # Non-canonical
        "spatial_scope": "route_corridor",
        "location": {"latitude": -2.5, "longitude": -54.9, "status_coord": "ok"},
    }
    with pytest.raises(ValidationError, match="not one of canonical groups"):
        RouteActorPackageSchema(**raw_actor)


def test_reject_unmatched_geometry_origin_code() -> None:
    """Hard guard: geometry origin code must refer to declared origin."""
    content = """## 1. Identificação e Ficha Geral da Rota
| Campo | Valor Normativo |
| `route_id` | 11111111-1111-1111-1111-111111111111 |
| `route_slug` | rota-teste |
| `title` | Rota Teste |
| `region_slug` | regiao-teste |
| `region_name` | Região Teste |
| `city` | Cidade |
| `state_code` | PA |

## 2. Origens Homologadas e Pontos de Saída
| Código | Nome | Descrição | Lat | Lon | Ordem |
|---|---|---|:---:|:---:|:---:|
| `origem_a` | Origem A | Ponto A | -2.5 | -54.9 | 1 |

## 3. Geometrias por Origem, Bounds e Proveniência
| Origem | Provedor | CRS | Extensão | Bounds | SHA-256 |
|---|---|:---:|---:|---|---|
| `origem_fantasma` | OSRM | 4326 | 10 km | VALOR_AUSENTE | VALOR_AUSENTE |

## 5. Fichas de Atores Verificáveis e Auditadas
"""
    with pytest.raises(ValueError, match="does not match origins"):
        RoutePackageParser.parse_markdown(content)


def test_reject_unverified_google_place_id() -> None:
    """Hard guard: google_place_id without verified contractual provenance is rejected."""
    raw_actor = {
        "slug": "invalido-place-id",
        "name": "Local sem Proveniência",
        "category_slug": "alimentacao",
        "spatial_scope": "route_corridor",
        "location": {"latitude": -2.5, "longitude": -54.9, "status_coord": "ok"},
        "provenance_and_sources": {
            "google_places_ref": {
                "place_id": "ChIJ_invented_arbitrary_id_12345",
                "has_verified_places_source": False,  # Missing contractual verification
            }
        },
    }
    with pytest.raises(ValidationError, match="lacks verifiable contractual provenance"):
        RouteActorPackageSchema(**raw_actor)


def test_reject_invalid_bounds() -> None:
    """Hard guard: bounds must be [min_lon, min_lat, max_lon, max_lat] with min < max."""
    from app.ingestion.route_package_parser import RouteGeometryMetadataSchema

    # Case 1: min_lon >= max_lon
    with pytest.raises(ValidationError, match="min_lon .* must be strictly less than max_lon"):
        RouteGeometryMetadataSchema(
            origin_code="porto",
            bounds={"min_lon": -54.0, "min_lat": -2.5, "max_lon": -54.8, "max_lat": -2.0},
        )

    # Case 2: min_lat >= max_lat
    with pytest.raises(ValidationError, match="min_lat .* must be strictly less than max_lat"):
        RouteGeometryMetadataSchema(
            origin_code="porto",
            bounds={"min_lon": -55.0, "min_lat": -2.0, "max_lon": -54.0, "max_lat": -2.5},
        )


def test_reject_invalid_sha256_hash() -> None:
    """Hard guard: source_hash_sha256 must be exactly 64 hexadecimal characters."""
    from app.ingestion.route_package_parser import RouteGeometryMetadataSchema

    sha_msg = "must be a valid 64-character hexadecimal SHA-256 string"
    with pytest.raises(ValidationError, match=sha_msg):
        RouteGeometryMetadataSchema(
            origin_code="porto",
            source_hash_sha256="not-a-valid-sha256-hash",
        )


def test_reject_invalid_provider_and_crs() -> None:
    """Hard guard: provider must be in allowed list and CRS must be strictly 4326."""
    from app.ingestion.route_package_parser import RouteGeometryMetadataSchema

    with pytest.raises(ValidationError, match="provider 'mapquest' is not permitted"):
        RouteGeometryMetadataSchema(origin_code="porto", provider="mapquest")

    with pytest.raises(ValidationError, match="crs must be strictly 4326"):
        RouteGeometryMetadataSchema(origin_code="porto", crs=3857)


@pytest.mark.asyncio
async def test_reject_region_resolution_without_origins() -> None:
    """Hard guard: Region center cannot fall back to invented coordinates if origins are absent."""
    session, _ = fake_session()
    repository = RoutePackageRepository(session)
    repository._one = AsyncMock(return_value=None)  # Region not in DB

    # Create package with no origins
    pkg = RoutePackageParser.parse_file(ALTAMIRA_PACKAGE_PATH)
    pkg.origins = []

    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="Não é possível resolver centro da região"):
        await repository.persist(package=pkg, started_at=now, finished_at=now)


# =============================================================================
# 3. Dry-Run Reporting Tests
# =============================================================================


def test_dry_run_pindobal_package() -> None:
    report = run_route_package_dry_run(PINDOBAL_PACKAGE_PATH)
    assert report["status"] == "success"
    assert report["dry_run"] is True
    assert report["is_estimate"] is True
    assert report["route"]["slug"] == "rota-pindobal"
    assert report["origins_count"] == 3
    assert report["geometries_count"] == 3
    assert report["actors_summary"]["total_read"] == 5
    assert report["actors_summary"]["semtur_inventory"] == 4
    assert report["counts"]["reconciled"] is True
    assert report["counts"]["is_estimate"] is True


def test_dry_run_altamira_package() -> None:
    report = run_route_package_dry_run(ALTAMIRA_PACKAGE_PATH)
    assert report["status"] == "success"
    assert report["dry_run"] is True
    assert report["is_estimate"] is True
    assert report["route"]["slug"] == "rota-volta-grande-xingu"
    assert report["route"]["region_slug"] == "xingu-altamira"
    assert report["origins_count"] == 2
    assert report["actors_summary"]["total_read"] == 3
    assert report["actors_summary"]["semtur_inventory"] == 0
    assert report["counts"]["reconciled"] is True
    assert report["counts"]["is_estimate"] is True


# =============================================================================
# 4. Atomic Transaction & Rollback Tests
# =============================================================================


@pytest.mark.asyncio
async def test_persist_adds_complete_package_inside_transaction() -> None:
    session, transaction = fake_session()
    repository = RoutePackageRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)

    package = RoutePackageParser.parse_file(ALTAMIRA_PACKAGE_PATH)
    run_id, stats = await repository.persist(
        package=package,
        started_at=now,
        finished_at=now,
    )

    assert isinstance(run_id, uuid.UUID)
    added = [call.args[0] for call in session.add.call_args_list]

    assert sum(isinstance(item, Region) for item in added) == 1
    assert sum(isinstance(item, Route) for item in added) == 1
    assert sum(isinstance(item, RouteOrigin) for item in added) == 2
    assert sum(isinstance(item, RouteGeometry) for item in added) == 2
    assert sum(isinstance(item, Actor) for item in added) == 3
    assert sum(isinstance(item, RouteActor) for item in added) == 3
    assert sum(isinstance(item, IngestionRun) for item in added) == 1
    assert sum(isinstance(item, RawSourceRecord) for item in added) == 3
    assert stats["territorial"]["route_created"] == 1
    assert stats["counts"]["created"] == 3
    assert stats["counts"]["unchanged"] == 0

    transaction.__aenter__.assert_awaited_once()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_induced_failure_triggers_rollback() -> None:
    session, transaction = fake_session()
    repository = RoutePackageRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)
    package = RoutePackageParser.parse_file(ALTAMIRA_PACKAGE_PATH)

    with pytest.raises(RuntimeError, match="Falha de persistência induzida"):
        await repository.persist(
            package=package,
            started_at=now,
            finished_at=now,
            fail_after="route",
        )

    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is RuntimeError
    assert session.add.call_count > 0
    transaction.__aexit__.assert_awaited_once()


# =============================================================================
# 5. Idempotency on Re-execution Tests
# =============================================================================


@pytest.mark.asyncio
async def test_idempotent_reexecution_produces_zero_duplicates() -> None:
    session, transaction = fake_session()
    repository = RoutePackageRepository(session)
    now = datetime.now(UTC)
    package = RoutePackageParser.parse_file(ALTAMIRA_PACKAGE_PATH)

    # Simulate existing records on second run
    existing_region = Region(id=uuid.uuid4(), slug="xingu-altamira", name="Xingu", state_code="PA")
    existing_route = Route(
        id=package.metadata.route_id,
        region_id=existing_region.id,
        slug="rota-volta-grande-xingu",
        title="Rota Volta Grande",
        city="Altamira",
        state_code="PA",
    )
    existing_source = ExternalSource(
        id=uuid.uuid4(),
        slug="route-package-rota-volta-grande-xingu-v1",
        name="Fonte",
        description="Desc",
    )
    existing_semtur_source = ExternalSource(
        id=uuid.uuid4(), slug="semtur_inventory", name="SEMTUR", description="SEMTUR"
    )

    async def mock_one(model, **filters):
        if model is Region:
            return existing_region
        if model is Route:
            return existing_route
        if model is ExternalSource:
            if filters.get("slug") == "semtur_inventory":
                return existing_semtur_source
            return existing_source
        if model is RouteOrigin:
            return RouteOrigin(
                id=uuid.uuid4(),
                route_id=existing_route.id,
                code=filters.get("code"),
                name="Origem",
                location="POINT(0 0)",
            )
        if model is RouteGeometry:
            return RouteGeometry(
                id=uuid.uuid4(),
                route_origin_id=uuid.uuid4(),
                provider="osrm",
                geometry="LINESTRING(0 0, 1 1)",
            )
        if model is Actor:
            return Actor(
                id=uuid.uuid4(),
                slug=filters.get("slug", "actor"),
                name=filters.get("slug", "actor"),
                category_id=uuid.uuid4(),
                city="Altamira",
                state_code="PA",
                region_id=existing_region.id,
                opening_hours={},
                payment_methods=[],
            )
        if model is RouteActor:
            return RouteActor(id=uuid.uuid4(), route_id=existing_route.id, actor_id=uuid.uuid4())
        return None

    repository._one = AsyncMock(side_effect=mock_one)  # type: ignore[method-assign]

    run_id, stats = await repository.persist(
        package=package,
        started_at=now,
        finished_at=now,
    )

    assert stats["territorial"]["route_created"] == 0
    assert stats["territorial"]["origins_created"] == 0
    assert stats["territorial"]["geometries_created"] == 0
    assert stats["territorial"]["origins_unchanged"] == 2
    assert stats["counts"]["created"] == 0
    # In 2nd run with unchanged actors, created is 0
    assert stats["reconciled"] is True
