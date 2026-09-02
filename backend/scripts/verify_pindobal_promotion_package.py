"""Verify ECO-1505 promotion package integrity without network or secrets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_pindobal_promotion_package import CHECKSUM_PATH, MANIFEST_PATH, ROOT


def read_normalized(path: Path) -> tuple[int, str]:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return len(content), hashlib.sha256(content).hexdigest()


def sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    expected, filename = CHECKSUM_PATH.read_text(encoding="ascii").strip().split("  ", 1)
    if filename != MANIFEST_PATH.name or sha256(MANIFEST_PATH) != expected:
        print("PINDOBAL_PACKAGE_VERIFY=ERROR")
        print("- category: PACKAGE_CHECKSUM_MISMATCH")
        return 1
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = manifest["migrations"] + manifest["implementation"] + manifest["support_files"]
    invalid = []
    for item in files:
        file_path = ROOT / item["path"]
        if not file_path.is_file():
            invalid.append(item["path"])
            continue
        size, digest = read_normalized(file_path)
        if digest != item["sha256"] or size != item["bytes"]:
            invalid.append(item["path"])

    snapshot = manifest["source_snapshot"]
    state = manifest["verified_test_state"]
    semantic_ok = (
        len(snapshot) == 9
        and len(manifest["migrations"]) == 25
        and state["second_load_created"] == 0
        and state["second_load_updated"] == 0
        and state["route_actors"] == 313
        and state["fuzzy_candidates_pending"] == 53
        and manifest["package"]["promotion_status"]
        == "blocked_pending_editorial_acceptance"
        and bool(manifest["promotion_blockers"])
        and manifest["publication_classification"]["media"].startswith("excluded_")
        and manifest["source_revision"]["kind"] == "unavailable"
    )
    if invalid or not semantic_ok:
        print("PINDOBAL_PACKAGE_VERIFY=ERROR")
        print("- category: PACKAGE_CONTENT_MISMATCH")
        return 1
    print("PINDOBAL_PACKAGE_VERIFY=OK")
    print(f"- package checksum: {expected}")
    print("- snapshot files: 9; migrations: 25; route actors: 313")
    print("- promotion remains blocked pending editorial acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
