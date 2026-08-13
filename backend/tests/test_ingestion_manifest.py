"""Unit tests for Manifest Inventory and Checksum Verification (ECO-0301)."""

from pathlib import Path

from app.ingestion.manifest import DEFAULT_SNAPSHOT_DIR, verify_manifest


def test_verify_manifest_real_snapshot() -> None:
    """Verify manifest against real snapshot in C:\\Users\\Bruno\\Downloads\\teste-rota."""
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return  # Skip if environment does not have snapshot directory

    report = verify_manifest(DEFAULT_SNAPSHOT_DIR)
    assert report.is_valid is True
    assert report.total_files == 9
    assert report.valid_files == 9
    assert len(report.invalid_files) == 0


def test_verify_manifest_invalid_dir(tmp_path: Path) -> None:
    """Verify manifest report returns invalid status when files are missing."""
    report = verify_manifest(tmp_path)
    assert report.is_valid is False
    assert report.total_files == 9
    assert report.valid_files == 0
    assert len(report.invalid_files) == 9
