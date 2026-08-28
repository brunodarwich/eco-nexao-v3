"""Exhaustive tests for SEMTUR and Google Places reconciliation (ECO-2509 / ADR 0014).

Ensures:
- Exact multi-tier matching priorities (Tier 1, Tier 2, Tier 3).
- Strict editorial queuing for fuzzy candidates (Tier 4, NEVER auto-merged).
- Homonyms with distant coordinates (>500m) and incompatible types are rejected as conflicts.
- Provenance and authority precedence (ADR 0014) are strictly preserved.
- Editorial workflow decisions (accept, reject, compensate/unmerge) are audited and reversible.
- Place ID lifecycle refresh (same ID, redirect/canonical update, 404 stale).
- Batch idempotency and reexecution safety with 0 network calls.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from app.ingestion.semtur_google_matcher import (
    GooglePlaceCandidate,
    MatchTier,
    SemturGoogleMatcher,
    are_types_compatible,
    calculate_name_similarity,
    haversine_distance_m,
    normalize_business_name,
    normalize_domain,
    normalize_phone,
)
from app.models.domain import (
    ActorExternalRef,
    AuditLog,
    ExternalSource,
    FieldProvenance,
    ReconciliationCandidate,
)
from app.services.semtur_google_reconciler import (
    SemturGoogleReconciliationService,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "reconciliation"


def load_fixture(filename: str) -> dict[str, Any]:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


class InMemoryAsyncSession:
    """Stateful in-memory mock of SQLAlchemy AsyncSession for unit testing."""

    def __init__(self) -> None:
        self.sources: dict[uuid.UUID, ExternalSource] = {}
        self.external_refs: dict[uuid.UUID, ActorExternalRef] = {}
        self.field_provenances: dict[uuid.UUID, FieldProvenance] = {}
        self.candidates: dict[uuid.UUID, ReconciliationCandidate] = {}
        self.audit_logs: dict[uuid.UUID, AuditLog] = {}

    def add(self, entity: Any) -> None:
        if isinstance(entity, ExternalSource):
            self.sources[entity.id] = entity
        elif isinstance(entity, ActorExternalRef):
            self.external_refs[entity.id] = entity
        elif isinstance(entity, FieldProvenance):
            self.field_provenances[entity.id] = entity
        elif isinstance(entity, ReconciliationCandidate):
            self.candidates[entity.id] = entity
        elif isinstance(entity, AuditLog):
            self.audit_logs[entity.id] = entity

    def add_all(self, entities: list[Any]) -> None:
        for e in entities:
            self.add(e)

    async def flush(self) -> None:
        pass

    async def refresh(self, entity: Any) -> None:
        pass

    async def execute(self, stmt: Any) -> Mock:
        result = Mock()
        sql_str = str(stmt)

        # Handle ExternalSource query
        if "external_sources" in sql_str.lower():
            matching = list(self.sources.values())
            result.scalar_one_or_none.return_value = matching[0] if matching else None
            result.scalars.return_value.all.return_value = matching
            return result

        # Handle ActorExternalRef query
        if "actor_external_refs" in sql_str.lower():
            matching_refs = list(self.external_refs.values())
            # Simple filtering simulation
            result.scalar_one_or_none.return_value = matching_refs[0] if matching_refs else None
            result.scalars.return_value.all.return_value = matching_refs
            return result

        # Handle FieldProvenance query
        if "field_provenance" in sql_str.lower():
            matching_provs = list(self.field_provenances.values())
            result.scalar_one_or_none.return_value = matching_provs[0] if matching_provs else None
            result.scalars.return_value.all.return_value = matching_provs
            return result

        # Handle ReconciliationCandidate query
        if "reconciliation_candidates" in sql_str.lower():
            matching_cands = list(self.candidates.values())
            result.scalar_one_or_none.return_value = matching_cands[0] if matching_cands else None
            result.scalars.return_value.all.return_value = matching_cands
            return result

        # Handle AuditLog query
        if "audit_logs" in sql_str.lower():
            matching_logs = list(self.audit_logs.values())
            result.scalar_one_or_none.return_value = matching_logs[-1] if matching_logs else None
            result.scalars.return_value.all.return_value = matching_logs
            return result

        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        return result


# --- Unit Tests for Matcher and Normalizers ---


def test_normalizers() -> None:
    # Phone normalizer
    assert normalize_phone("+55 (93) 99123-4567") == "93991234567"
    assert normalize_phone("93 991234567") == "93991234567"
    assert normalize_phone("123") is None

    # Domain normalizer
    assert (
        normalize_domain("https://www.restaurantedosaulo.com.br/cardapio?ref=1")
        == "restaurantedosaulo.com.br/cardapio"
    )
    assert normalize_domain("http://viladealter.com.br/") == "viladealter.com.br"
    assert normalize_domain(None) is None

    # Business name normalizer
    assert normalize_business_name("Restaurante do Saulo Alter") == "saulo alter"
    assert normalize_business_name("Pousada Borari") == "borari"


def test_name_similarity_and_distance() -> None:
    sim1 = calculate_name_similarity("Restaurante do Saulo", "Restaurante do Saulo Alter")
    assert sim1 >= 0.55

    sim_exact = calculate_name_similarity("Pousada Borari", "Pousada Borari")
    assert sim_exact == 1.0

    # Distance calculation: Alter do Chão center to Santarém center (~30km)
    dist = haversine_distance_m(-2.5042, -54.9535, -2.4410, -54.7100)
    assert 25_000 < dist < 35_000


def test_taxonomic_compatibility() -> None:
    # Compatible
    assert (
        are_types_compatible("Alimentos e Bebidas", "restaurante", ["restaurant", "food"]) is True
    )
    assert are_types_compatible("Hospedagem", "pousada", ["lodging", "hotel"]) is True
    assert (
        are_types_compatible(
            "Atrativos Turísticos", "praia", ["natural_feature", "tourist_attraction"]
        )
        is True
    )

    # Incompatible
    assert are_types_compatible("Utilidade Pública", "saude", ["restaurant", "bar"]) is False
    assert are_types_compatible("Hospedagem", "hotel", ["hospital", "doctor"]) is False


# --- Multi-Tier Matcher Evaluation Tests (Fixtures) ---


def test_matcher_tier1_exact_place_id() -> None:
    data = load_fixture("deterministic_tier1_place_id.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(**data["google_candidate"])
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_1_EXACT_EXTERNAL_ID
    assert eval_result.score == 1.0
    assert eval_result.is_auto_link_eligible is True
    assert eval_result.is_conflict is False


def test_matcher_tier2_phone_and_website() -> None:
    data = load_fixture("deterministic_tier2_phone_site.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(**data["google_candidate"])
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_2_PHONE_OR_SITE
    assert eval_result.score == 0.95
    assert eval_result.is_auto_link_eligible is True
    assert eval_result.is_conflict is False
    assert eval_result.distance_m is not None and eval_result.distance_m <= 200.0


def test_matcher_tier3_exact_canonical_name_close_geo() -> None:
    data = load_fixture("deterministic_tier3_exact_name_geo.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(**data["google_candidate"])
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_3_EXACT_NAME_CLOSE_GEO
    assert eval_result.score == 0.90
    assert eval_result.is_auto_link_eligible is True
    assert eval_result.is_conflict is False
    assert eval_result.distance_m is not None and eval_result.distance_m <= 100.0


def test_matcher_tier4_fuzzy_candidate_never_auto_merged() -> None:
    data = load_fixture("fuzzy_candidate_tier4.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(**data["google_candidate"])
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_4_FUZZY_CANDIDATE
    assert 0.50 <= eval_result.score < 0.90
    assert eval_result.is_auto_link_eligible is False  # Contract rule: FUZZY NEVER AUTO-MERGES
    assert eval_result.is_conflict is False
    assert any("editorial review" in r.lower() for r in eval_result.reasons)


def test_matcher_homonym_conflict_distant_coordinates() -> None:
    data = load_fixture("conflict_homonym_distant_geo.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(
        place_id=data["google_candidate"]["place_id"],
        name=data["google_candidate"]["name"],
        latitude=data["google_candidate"]["latitude"],
        longitude=data["google_candidate"]["longitude"],
        phone=data["google_candidate"]["phone"],
        website=data["google_candidate"]["website"],
        types=tuple(data["google_candidate"]["types"]),
    )
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_5_CONFLICT_OR_REJECTED
    assert eval_result.score == 0.0
    assert eval_result.is_auto_link_eligible is False
    assert eval_result.is_conflict is True
    assert "homonym_distant_coordinates" in eval_result.conflict_flags


def test_matcher_incompatible_taxonomic_types() -> None:
    data = load_fixture("incompatible_types.json")
    matcher = SemturGoogleMatcher()
    candidate = GooglePlaceCandidate(
        place_id=data["google_candidate"]["place_id"],
        name=data["google_candidate"]["name"],
        latitude=data["google_candidate"]["latitude"],
        longitude=data["google_candidate"]["longitude"],
        phone=data["google_candidate"]["phone"],
        website=data["google_candidate"]["website"],
        types=tuple(data["google_candidate"]["types"]),
    )
    eval_result = matcher.evaluate(data["semtur_record"], candidate)

    assert eval_result.tier == MatchTier.TIER_5_CONFLICT_OR_REJECTED
    assert eval_result.score == 0.0
    assert eval_result.is_auto_link_eligible is False
    assert eval_result.is_conflict is True
    assert "incompatible_taxonomic_types" in eval_result.conflict_flags


# --- Database Batch Reconciliation & Workflow Integration Tests ---


@pytest.mark.asyncio
async def test_reconciliation_batch_deterministic_and_fuzzy_persistence() -> None:
    db = InMemoryAsyncSession()
    service = SemturGoogleReconciliationService(db)  # type: ignore[arg-type]

    actor_t1_id = uuid.uuid4()
    actor_t4_id = uuid.uuid4()

    fixture_t1 = load_fixture("deterministic_tier1_place_id.json")
    fixture_t4 = load_fixture("fuzzy_candidate_tier4.json")

    semtur_records = [
        {**fixture_t1["semtur_record"], "actor_id": str(actor_t1_id)},
        {**fixture_t4["semtur_record"], "actor_id": str(actor_t4_id)},
    ]
    google_candidates = [
        GooglePlaceCandidate(**fixture_t1["google_candidate"]),
        GooglePlaceCandidate(**fixture_t4["google_candidate"]),
    ]

    report = await service.reconcile_batch(semtur_records, google_candidates)

    assert report.total_semtur_evaluated == 2
    assert report.deterministic_linked == 1
    assert report.fuzzy_queued_for_review == 1
    assert report.conflicts_detected == 0

    # Verify Actor 1 has external ref and field provenance (Deterministic)
    assert len(db.external_refs) == 1
    ref = list(db.external_refs.values())[0]
    assert ref.actor_id == actor_t1_id
    assert ref.external_id == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert ref.status_ref == "active"

    assert len(db.field_provenances) >= 1
    prov = list(db.field_provenances.values())[0]
    assert prov.target_id == actor_t1_id
    assert prov.confidence == 1.0

    # Verify Actor 2 has a pending candidate in reconciliation_candidates and was NEVER auto-linked
    assert len(db.candidates) == 1
    cand = list(db.candidates.values())[0]
    assert cand.actor_id_a == actor_t4_id
    assert cand.status == "pending"
    assert "ChIJ_encantos_tapajos_fuzzy_004" in cand.decision_notes


@pytest.mark.asyncio
async def test_reconciliation_batch_idempotency() -> None:
    db = InMemoryAsyncSession()
    service = SemturGoogleReconciliationService(db)  # type: ignore[arg-type]

    actor_id = uuid.uuid4()
    fixture = load_fixture("deterministic_tier2_phone_site.json")
    semtur_records = [{**fixture["semtur_record"], "actor_id": str(actor_id)}]
    google_candidates = [GooglePlaceCandidate(**fixture["google_candidate"])]

    # 1st execution
    report1 = await service.reconcile_batch(semtur_records, google_candidates)
    assert report1.deterministic_linked == 1
    assert report1.unchanged == 0
    assert len(db.external_refs) == 1

    # 2nd execution (reexecution with identical data)
    report2 = await service.reconcile_batch(semtur_records, google_candidates)
    assert report2.deterministic_linked == 0
    assert report2.unchanged == 1
    # Ensure no duplicates created
    assert len(db.external_refs) == 1


@pytest.mark.asyncio
async def test_editorial_decision_lifecycle_accept_reject_compensate() -> None:
    db = InMemoryAsyncSession()
    service = SemturGoogleReconciliationService(db)  # type: ignore[arg-type]
    editor_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    # Create a pending fuzzy candidate
    notes = json.dumps(
        {"google_place_id": "ChIJ_encantos_004", "candidate_name": "Encantos Tapajós"}
    )
    candidate = ReconciliationCandidate(
        id=uuid.uuid4(),
        actor_id_a=actor_id,
        actor_id_b=actor_id,
        score=0.75,
        status="pending",
        decision_notes=notes,
    )
    db.add(candidate)

    # Action 1: Accept Candidate
    cand_accepted, audit_accept = await service.accept_candidate(
        candidate_id=candidate.id,
        editor_id=editor_id,
        reason="Verificado em campo pela equipe editorial",
    )
    assert cand_accepted.status == "accepted"
    assert audit_accept.action == "RECONCILE_ACCEPT"
    assert len(db.external_refs) == 1
    ref = list(db.external_refs.values())[0]
    assert ref.external_id == "ChIJ_encantos_004"
    assert ref.status_ref == "active"

    # Action 2: Compensate / Reversible Unmerge
    cand_compensated, audit_comp = await service.compensate_decision(
        candidate_id=candidate.id,
        editor_id=editor_id,
        reason="Revertido após constatação de homônimo",
    )
    assert cand_compensated.status == "pending"
    assert audit_comp.action == "RECONCILE_COMPENSATE"
    assert ref.status_ref == "unlinked"

    # Action 3: Reject Candidate
    cand_rejected, audit_reject = await service.reject_candidate(
        candidate_id=candidate.id,
        editor_id=editor_id,
        reason="Confirmado como estabelecimento distinto",
    )
    assert cand_rejected.status == "rejected"
    assert audit_reject.action == "RECONCILE_REJECT"


@pytest.mark.asyncio
async def test_place_id_lifecycle_refresh_handler() -> None:
    db = InMemoryAsyncSession()
    service = SemturGoogleReconciliationService(db)  # type: ignore[arg-type]
    audit_user = uuid.uuid4()
    actor_id = uuid.uuid4()

    google_source = await service.get_or_create_source()
    ref = ActorExternalRef(
        id=uuid.uuid4(),
        actor_id=actor_id,
        source_id=google_source.id,
        external_id="ChIJ_old_id_111",
        status_ref="active",
    )
    db.add(ref)

    # Case A: Redirect to canonical place ID
    updated_ref = await service.handle_place_id_lifecycle_refresh(
        actor_id=actor_id,
        original_place_id="ChIJ_old_id_111",
        canonical_place_id="ChIJ_canonical_new_222",
        is_changed=True,
        is_stale=False,
        audit_actor_id=audit_user,
    )
    assert updated_ref is not None
    assert updated_ref.external_id == "ChIJ_canonical_new_222"
    assert updated_ref.status_ref == "active"

    # Case B: 404 NOT_FOUND marks stale
    stale_ref = await service.handle_place_id_lifecycle_refresh(
        actor_id=actor_id,
        original_place_id="ChIJ_canonical_new_222",
        canonical_place_id=None,
        is_changed=False,
        is_stale=True,
        audit_actor_id=audit_user,
    )
    assert stale_ref is not None
    assert stale_ref.status_ref == "stale"
