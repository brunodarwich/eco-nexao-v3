"""Build the deterministic, metadata-only ECO-1505 promotion package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.ingestion.manifest import MANIFEST_ENTRIES
from app.ingestion.pindobal_repository import IMPORTER_VERSION, RULES_VERSION

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "docs" / "finalization" / "artifacts" / "pindobal-v1"
MANIFEST_PATH = ARTIFACT_DIR / "promotion_manifest.json"
CHECKSUM_PATH = ARTIFACT_DIR / "promotion_manifest.sha256"


def sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def relative_file(path: Path) -> dict[str, Any]:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def build_manifest() -> dict[str, Any]:
    migrations = sorted((ROOT / "supabase" / "migrations").glob("*.sql"))
    implementation = [
        ROOT / "backend" / "app" / "ingestion" / "manifest.py",
        ROOT / "backend" / "app" / "ingestion" / "seed_pindobal.py",
        ROOT / "backend" / "app" / "ingestion" / "pindobal_repository.py",
        ROOT / "backend" / "app" / "ingestion" / "osrm_importer.py",
        ROOT / "backend" / "scripts" / "apply_pindobal_spatial.py",
        ROOT / "backend" / "scripts" / "verify_pindobal_gate.py",
        ROOT / "docs" / "data" / "pindobal_data_contract.md",
    ]
    support_files = [
        ARTIFACT_DIR / "README.md",
        ARTIFACT_DIR / "APPROVAL.md",
        ARTIFACT_DIR / "smoke.sql",
    ]
    return {
        "package": {
            "id": "econexao-pindobal-v1",
            "schema_version": 1,
            "snapshot_version": "pindobal-v1",
            "importer_version": IMPORTER_VERSION,
            "rules_version": RULES_VERSION,
            "promotion_status": "blocked_pending_editorial_acceptance",
        },
        "source_revision": {
            "kind": "unavailable",
            "reason": "no_git_metadata",
            "integrity_fallback": "individual_file_sha256",
        },
        "source_snapshot": [
            {"name": name, "bytes": size, "sha256": digest}
            for name, (size, digest) in MANIFEST_ENTRIES.items()
        ],
        "migrations": [relative_file(path) for path in migrations],
        "implementation": [relative_file(path) for path in implementation],
        "support_files": [relative_file(path) for path in support_files],
        "verified_test_state": {
            "regions": 1,
            "routes": 1,
            "origins": 3,
            "geometries": 3,
            "actors": 674,
            "route_actors": 313,
            "fuzzy_candidates_pending": 53,
            "completed_ingestion_runs": 3,
            "raw_records_from_authorized_double_load": 3428,
            "field_provenance": 8088,
            "second_load_created": 0,
            "second_load_updated": 0,
            "second_load_unchanged": 1661,
            "second_load_candidates": 53,
            "google_records_without_place_id_per_run": 737,
        },
        "geometry_contract": {
            "porto": {"points": 884, "distance_m": 45229},
            "aeroporto": {"points": 777, "distance_m": 41452},
            "rodoviaria": {"points": 866, "distance_m": 42319},
            "srid": 4326,
        },
        "promotion_blockers": [
            "owner/editorial review of the 53 fuzzy candidates is pending",
            "legacy Google records have no trusted Place ID and cannot be auto-merged",
            "SEMTUR retention terms do not constitute a reviewed public-content license",
            "route cover and editorial media with alt text, credit and license are pending",
            "Publish Guard and administrative publication workflow are not yet complete",
            "staging and production promotion require separate explicit authorization",
        ],
        "approved_actions": [
            "offline verification",
            "dry-run against an isolated environment",
            "review of candidates and licensing metadata",
        ],
        "prohibited_actions": [
            "automatic fuzzy merge",
            "inventing Google Place IDs",
            "copying Google photo binaries to Supabase Storage",
            "promotion to staging or production without explicit approval",
        ],
        "rollback": {
            "strategy": "logical_unpublish",
            "required_state": "draft_or_unpublished",
            "data_deletion": "not_part_of_automatic_rollback",
            "procedure": (
                "Stop promotion, keep content non-public, preserve audit/provenance, "
                "and supersede this package with a newly reviewed immutable version."
            ),
        },
        "publication_classification": {
            "route": "draft_candidate_only",
            "actors": "draft_candidates_only",
            "google_legacy": "raw_evidence_only",
            "media": "excluded_pending_license_credit_alt_and_processing",
            "fuzzy_candidates": "pending_human_review",
        },
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    MANIFEST_PATH.write_bytes(encoded)
    checksum = hashlib.sha256(encoded).hexdigest()
    CHECKSUM_PATH.write_text(
        f"{checksum}  {MANIFEST_PATH.name}\n", encoding="ascii", newline="\n"
    )
    print("PINDOBAL_PACKAGE_BUILD=OK")
    print(f"- package checksum: {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
