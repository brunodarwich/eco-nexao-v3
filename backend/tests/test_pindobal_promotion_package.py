"""Offline integrity tests for the ECO-1505 promotion package."""

import hashlib
import json

from scripts.build_pindobal_promotion_package import (
    CHECKSUM_PATH,
    MANIFEST_PATH,
    build_manifest,
)


def test_manifest_is_no_go_and_contains_no_environment_identity() -> None:
    manifest = build_manifest()
    encoded = json.dumps(manifest)

    assert manifest["package"]["promotion_status"] == "blocked_pending_editorial_acceptance"
    assert manifest["verified_test_state"]["fuzzy_candidates_pending"] == 53
    assert manifest["publication_classification"]["google_legacy"] == "raw_evidence_only"
    assert manifest["publication_classification"]["media"].startswith("excluded_")
    assert manifest["source_revision"]["kind"] == "unavailable"
    for forbidden in ("DATABASE_URL", "SUPABASE_SECRET_KEY", "access_token", "postgresql://"):
        assert forbidden not in encoded


def test_committed_manifest_checksum_matches() -> None:
    expected, filename = CHECKSUM_PATH.read_text(encoding="ascii").strip().split("  ", 1)

    assert filename == MANIFEST_PATH.name
    content = MANIFEST_PATH.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(content).hexdigest() == expected
