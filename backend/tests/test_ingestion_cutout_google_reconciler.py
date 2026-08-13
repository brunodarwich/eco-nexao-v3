"""Unit tests for Pindobal Cutout, Google Snapshot, Reconciler and Seed Runner (ECO-0304..0308)."""

from app.ingestion.google_snapshot_importer import process_google_snapshot
from app.ingestion.pindobal_cutout_importer import process_pindobal_cutout
from app.ingestion.reconciler import reconcile_semtur_and_google
from app.ingestion.seed_pindobal import DEFAULT_SNAPSHOT_DIR, run_seed_pindobal
from app.ingestion.semtur_importer import process_semtur_inventory


def test_pindobal_cutout_real_snapshot() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    records, stats = process_pindobal_cutout(DEFAULT_SNAPSHOT_DIR)
    assert stats["total_read"] == 303
    assert stats["valid_records"] == 303
    assert stats["coord_status_ok_count"] == 303


def test_google_snapshot_real_snapshot() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    records, stats = process_google_snapshot(DEFAULT_SNAPSHOT_DIR)
    assert stats["total_records"] == 737
    assert stats["support_poi_count"] == 593
    assert stats["emergency_poi_count"] == 144
    assert stats["external_id_missing_count"] == 737

    # Check contract rule: place_id MUST NOT be invented
    for rec in records:
        assert rec.google_place_id is None
        assert rec.external_id_missing is True


def test_reconciler_logic() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    semtur_recs, _ = process_semtur_inventory(DEFAULT_SNAPSHOT_DIR)
    google_recs, _ = process_google_snapshot(DEFAULT_SNAPSHOT_DIR)

    matches = reconcile_semtur_and_google(semtur_recs, google_recs)
    assert isinstance(matches, list)
    # Check that fuzzy matches are never auto-merged
    for m in matches:
        if m.match_type == "fuzzy_candidate":
            assert m.is_auto_merged is False


def test_run_seed_pindobal_dry_run() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    report = run_seed_pindobal(DEFAULT_SNAPSHOT_DIR, dry_run=True)
    assert report["status"] == "success"
    assert report["dry_run"] is True
    assert report["manifest"]["is_valid"] is True
    assert report["semtur_inventory"]["total_read"] == 674
    assert report["pindobal_cutout"]["total_read"] == 303
    assert report["google_snapshot"]["total_records"] == 737
    counts = report["counts"]
    assert counts["reconciled"] is True
    assert counts["read"] == sum(
        counts[key] for key in ("created", "updated", "unchanged", "rejected", "candidates")
    )
    reconciliation = report["reconciliation"]
    assert reconciliation["candidate_google_record_count"] == counts["candidates"]
    assert reconciliation["candidate_counting_rule"] == "unique_google_snapshot_record"
    assert reconciliation["fuzzy_candidate_count"] >= counts["candidates"]
    assert len(report["manifest"]["files"]) == 9
