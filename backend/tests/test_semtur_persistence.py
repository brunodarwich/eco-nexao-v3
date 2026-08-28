"""Transactional persistence and idempotency tests for SEMTUR ingestion (ECO-2505)."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.ingestion.seed_semtur import run_seed_semtur
from app.ingestion.semtur_importer import (
    SEMTURRecord,
    process_semtur_inventory,
)
from app.ingestion.semtur_repository import (
    PersistenceCounts,
    SEMTURPersistenceRepository,
)
from app.models.domain import (
    Actor,
    ActorCategory,
    ActorExternalRef,
    ActorType,
    ExternalSource,
    FieldProvenance,
    IngestionRun,
    RawSourceRecord,
    Region,
)


def fake_session() -> tuple[Mock, AsyncMock]:
    session = Mock()
    transaction = AsyncMock()
    session.begin = Mock(return_value=transaction)
    session.add_all = Mock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    session.get = AsyncMock(return_value=None)
    result = Mock()
    result.tuples.return_value = []
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    return session, transaction


def sample_records() -> list[SEMTURRecord]:
    synthetic_rows = [
        {
            "pagina": "10",
            "categoria": "alimentacao",
            "titulo": "Restaurante Sabor do Tapajós",
            "coordenadas_geograficas": "-2.4300, -54.7300",
            "endereco": "Av. Tapajós, 500",
            "telefone": "(93) 99111-2233",
            "email": "contato@sabortapajos.com",
            "instagram": "instagram.com/sabortapajos",
            "site": "https://sabortapajos.com",
            "funcionamento": "11h às 23h",
            "servicos_instalacoes": "Wi-Fi, Deck panorâmico",
            "forma_pagamento": "PIX, Cartão",
            "contingente": "15",
            "projetos_sociais": "",
            "observacoes_criticas": "",
            "observacoes": "Comida regional",
            "texto_bruto": "Restaurante Sabor do Tapajós...",
        },
        {
            "pagina": "11",
            "categoria": "hospedagem",
            "titulo": "Pousada Morada do Sol",
            "coordenadas_geograficas": "",  # Valid without coords
            "endereco": "Alter do Chão",
            "telefone": "(93) 99222-3344",
            "email": "sol@pousada.com",
            "instagram": "",
            "site": "",
            "funcionamento": "24h",
            "servicos_instalacoes": "Café da manhã, Piscina",
            "forma_pagamento": "PIX",
            "contingente": "5",
            "projetos_sociais": "",
            "observacoes_criticas": "",
            "observacoes": "",
            "texto_bruto": "Pousada Morada do Sol...",
        },
        {
            "pagina": "12",
            "categoria": "outros",
            "titulo": "",  # Invalid: missing title
            "coordenadas_geograficas": "-2.4400, -54.7400",
            "endereco": "Sem identificação",
            "telefone": "",
            "email": "",
            "instagram": "",
            "site": "",
            "funcionamento": "",
            "servicos_instalacoes": "",
            "forma_pagamento": "",
            "contingente": "",
            "projetos_sociais": "",
            "observacoes_criticas": "",
            "observacoes": "",
            "texto_bruto": "",
        },
    ]
    records, _ = process_semtur_inventory(raw_rows=synthetic_rows)
    return records


@pytest.mark.asyncio
async def test_persist_adds_complete_semtur_slice_in_one_transaction() -> None:
    session, transaction = fake_session()
    repository = SEMTURPersistenceRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)

    records = sample_records()
    assert len(records) == 3

    run_id, stats = await repository.persist(
        report={"rules": {"importer_version": "eco-2505-v1"}},
        started_at=now,
        finished_at=now,
        semtur_records=records,
    )

    assert isinstance(run_id, uuid.UUID)
    added = [call.args[0] for call in session.add.call_args_list]

    assert sum(isinstance(item, ExternalSource) for item in added) == 1
    assert sum(isinstance(item, IngestionRun) for item in added) == 1
    assert sum(isinstance(item, Region) for item in added) == 1
    assert sum(isinstance(item, RawSourceRecord) for item in added) == 3
    assert sum(isinstance(item, Actor) for item in added) == 2
    assert sum(isinstance(item, ActorExternalRef) for item in added) == 2
    assert sum(isinstance(item, FieldProvenance) for item in added) > 0

    reconciliation = stats["reconciliation"]
    assert reconciliation["read"] == 3
    assert reconciliation["created"] == 2
    assert reconciliation["rejected"] == 1
    assert reconciliation["unchanged"] == 0
    assert reconciliation["updated"] == 0
    assert reconciliation["reconciled"] is True

    transaction.__aenter__.assert_awaited_once()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_persist_induced_failure_rolls_back_atomically() -> None:
    session, transaction = fake_session()
    repository = SEMTURPersistenceRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)

    records = sample_records()

    with pytest.raises(RuntimeError, match="induzida"):
        await repository.persist(
            report={"rules": {"importer_version": "eco-2505-v1"}},
            started_at=now,
            finished_at=now,
            semtur_records=records,
            fail_after="actors",
        )

    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is RuntimeError
    assert session.add.call_count > 0
    transaction.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_idempotency_second_execution_unchanged() -> None:
    session, transaction = fake_session()
    repository = SEMTURPersistenceRepository(session)
    now = datetime.now(UTC)
    records = sample_records()

    # Mock pre-existing external source, region and categories
    source = ExternalSource(
        id=uuid.uuid4(),
        slug="semtur_inventory",
        name="SEMTUR",
        description="SEMTUR Inventory",
    )
    region = Region(
        id=uuid.uuid4(),
        slug="santarem-belterra",
        name="Santarém e Belterra",
        state_code="PA",
    )
    cat_alimentacao = ActorCategory(
        id=uuid.uuid4(),
        slug="alimentacao",
        label="Alimentação",
        spatial_scope="route_corridor",
    )
    type_restaurante = ActorType(
        id=uuid.uuid4(),
        category_id=cat_alimentacao.id,
        slug="restaurante",
        label="Restaurante",
        icon="utensils",
        spatial_scope="route_corridor",
    )

    cat_hospedagem = ActorCategory(
        id=uuid.uuid4(),
        slug="hospedagem",
        label="Hospedagem",
        spatial_scope="route_corridor",
    )
    type_pousada = ActorType(
        id=uuid.uuid4(),
        category_id=cat_hospedagem.id,
        slug="pousada_hotel",
        label="Hotel & Pousada",
        icon="bed",
        spatial_scope="route_corridor",
    )

    actor1 = Actor(
        id=uuid.uuid4(),
        slug="semtur-semtur-p10-1",
        name="Restaurante Sabor do Tapajós",
        category_id=cat_alimentacao.id,
        type_id=type_restaurante.id,
        sub_category="alimentacao",
        address="Av. Tapajós, 500",
        city="Santarém",
        state_code="PA",
        region_id=region.id,
        phone="(93) 99111-2233",
        email="contato@sabortapajos.com",
        instagram="https://instagram.com/sabortapajos",
        website="https://sabortapajos.com",
        opening_hours={"raw": "11h às 23h"},
        payment_methods=["PIX, Cartão"],
    )
    ref1 = ActorExternalRef(
        id=uuid.uuid4(),
        actor_id=actor1.id,
        source_id=source.id,
        external_id="semtur_p10_1",
        status_ref="active",
    )

    actor2 = Actor(
        id=uuid.uuid4(),
        slug="semtur-semtur-p11-2",
        name="Pousada Morada do Sol",
        category_id=cat_hospedagem.id,
        type_id=type_pousada.id,
        sub_category="hospedagem",
        address="Alter do Chão",
        city="Santarém",
        state_code="PA",
        region_id=region.id,
        phone="(93) 99222-3344",
        email="sol@pousada.com",
        instagram=None,
        website=None,
        opening_hours={"raw": "24h"},
        payment_methods=["PIX"],
    )
    ref2 = ActorExternalRef(
        id=uuid.uuid4(),
        actor_id=actor2.id,
        source_id=source.id,
        external_id="semtur_p11_2",
        status_ref="active",
    )

    async def mock_one(model: type, **filters: dict) -> object | None:
        if model is ExternalSource:
            return source
        if model is Region:
            return region
        if model is ActorCategory:
            slug = filters.get("slug")
            if slug == "alimentacao":
                return cat_alimentacao
            if slug == "hospedagem":
                return cat_hospedagem
        if model is ActorType:
            slug = filters.get("slug")
            if slug == "restaurante":
                return type_restaurante
            if slug == "pousada_hotel":
                return type_pousada
        if model is ActorExternalRef:
            ext_id = filters.get("external_id")
            if ext_id == "semtur_p10_1":
                return ref1
            if ext_id == "semtur_p11_2":
                return ref2
        return None

    repository._one = AsyncMock(side_effect=mock_one)  # type: ignore[method-assign]

    async def mock_get(model: type, obj_id: uuid.UUID) -> object | None:
        if obj_id == actor1.id:
            return actor1
        if obj_id == actor2.id:
            return actor2
        return None

    session.get = AsyncMock(side_effect=mock_get)

    run_id, stats = await repository.persist(
        report={"rules": {"importer_version": "eco-2505-v1"}},
        started_at=now,
        finished_at=now,
        semtur_records=records,
    )

    reconciliation = stats["reconciliation"]
    assert reconciliation["read"] == 3
    assert reconciliation["created"] == 0
    assert reconciliation["updated"] == 0
    assert reconciliation["unchanged"] == 2
    assert reconciliation["rejected"] == 1
    assert reconciliation["reconciled"] is True


def test_persistence_counts_equation() -> None:
    counts = PersistenceCounts(
        read=674,
        created=674,
        updated=0,
        unchanged=0,
        rejected=0,
        candidates=0,
    )
    assert counts.reconciles() is True

    counts2 = PersistenceCounts(
        read=674,
        created=0,
        updated=0,
        unchanged=674,
        rejected=0,
        candidates=0,
    )
    assert counts2.reconciles() is True

    counts_bad = PersistenceCounts(
        read=674,
        created=500,
        updated=0,
        unchanged=100,
        rejected=0,
        candidates=0,
    )
    assert counts_bad.reconciles() is False


def test_run_seed_semtur_dry_run() -> None:
    report = run_seed_semtur(raw_rows=[], dry_run=True)
    assert report["status"] == "success"
    assert report["dry_run"] is True
    assert report["counts"]["read"] == 0
    assert report["counts"]["reconciled"] is True

    with pytest.raises(RuntimeError, match="sessão DB explícita"):
        run_seed_semtur(dry_run=False)


@pytest.mark.asyncio
async def test_persist_updates_modified_fields_on_existing_actor() -> None:
    session, transaction = fake_session()
    repository = SEMTURPersistenceRepository(session)
    now = datetime.now(UTC)
    records = sample_records()

    source = ExternalSource(
        id=uuid.uuid4(),
        slug="semtur_inventory",
        name="SEMTUR",
        description="SEMTUR Inventory",
    )
    region = Region(
        id=uuid.uuid4(),
        slug="santarem-belterra",
        name="Santarém e Belterra",
        state_code="PA",
    )
    cat_alimentacao = ActorCategory(
        id=uuid.uuid4(),
        slug="alimentacao",
        label="Alimentação",
        spatial_scope="route_corridor",
    )
    type_restaurante = ActorType(
        id=uuid.uuid4(),
        category_id=cat_alimentacao.id,
        slug="restaurante",
        label="Restaurante",
        icon="utensils",
        spatial_scope="route_corridor",
    )

    # Actor has old outdated phone
    actor1 = Actor(
        id=uuid.uuid4(),
        slug="semtur-semtur-p10-1",
        name="Restaurante Sabor do Tapajós",
        category_id=cat_alimentacao.id,
        type_id=type_restaurante.id,
        sub_category="alimentacao",
        address="Av. Tapajós, 500",
        city="Santarém",
        state_code="PA",
        region_id=region.id,
        phone="(93) 90000-0000",  # Different old phone
        email="contato@sabortapajos.com",
        instagram="https://instagram.com/sabortapajos",
        website="https://sabortapajos.com",
        opening_hours={"raw": "11h às 23h"},
        payment_methods=["PIX, Cartão"],
    )
    ref1 = ActorExternalRef(
        id=uuid.uuid4(),
        actor_id=actor1.id,
        source_id=source.id,
        external_id="semtur_p10_1",
        status_ref="active",
    )

    async def mock_one(model: type, **filters: dict) -> object | None:
        if model is ExternalSource:
            return source
        if model is Region:
            return region
        if model is ActorCategory:
            return cat_alimentacao
        if model is ActorType:
            return type_restaurante
        if model is ActorExternalRef:
            if filters.get("external_id") == "semtur_p10_1":
                return ref1
        return None

    repository._one = AsyncMock(side_effect=mock_one)  # type: ignore[method-assign]
    session.get = AsyncMock(return_value=actor1)

    # Only process record 0
    run_id, stats = await repository.persist(
        report={"rules": {"importer_version": "eco-2505-v1"}},
        started_at=now,
        finished_at=now,
        semtur_records=[records[0]],
    )

    reconciliation = stats["reconciliation"]
    assert reconciliation["read"] == 1
    assert reconciliation["created"] == 0
    assert reconciliation["updated"] == 1
    assert reconciliation["unchanged"] == 0
    assert reconciliation["reconciled"] is True
    assert actor1.phone == "(93) 99111-2233"


@pytest.mark.asyncio
async def test_actors_created_with_institutional_status_never_published() -> None:
    session, transaction = fake_session()
    repository = SEMTURPersistenceRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)
    records = sample_records()

    await repository.persist(
        report={"rules": {"importer_version": "eco-2505-v1"}},
        started_at=now,
        finished_at=now,
        semtur_records=records,
    )

    added_actors = [
        call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], Actor)
    ]
    for actor in added_actors:
        assert actor.verification_status == "institutional"
        assert actor.verification_status != "published"


@pytest.mark.asyncio
async def test_run_seed_semtur_apply_pipeline() -> None:
    from app.ingestion.seed_semtur import run_seed_semtur_apply

    session, transaction = fake_session()
    records = sample_records()

    report = await run_seed_semtur_apply(
        snapshot_dir=Path("fake_dir"),
        session=session,
        raw_rows=[r.raw_payload for r in records],
    )

    assert report["status"] == "success"
    assert report["dry_run"] is False
    assert "ingestion_run_id" in report
    assert report["persistence"]["reconciliation"]["reconciled"] is True


def test_apply_environment_rejects_noncanonical_test_file() -> None:
    from app.ingestion.seed_semtur import apply_from_test_environment

    backend_dir = Path(__file__).resolve().parents[1]
    noncanonical_env = backend_dir / ".env"

    with pytest.raises(RuntimeError, match="canônico"):
        import asyncio

        asyncio.run(
            apply_from_test_environment(
                snapshot_dir=backend_dir,
                env_file=noncanonical_env,
            )
        )
