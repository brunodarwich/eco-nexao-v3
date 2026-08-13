"""Manifest inventory and hash verification for Pindobal data snapshot (ECO-0301)."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")

# Normative manifesto from docs/data/pindobal_data_contract.md
MANIFEST_ENTRIES: dict[str, tuple[int, str]] = {
    "inventario_semtur.csv": (
        310926,
        "9b4bdf682a83facbbfdb76176810f0ebcc3efba7efbe848fcfafa4d156e7eabb",
    ),
    "data_semtur.json": (
        358434,
        "0a384b8bcda64744cf3db9bd07a62826d2617bc66b80b9ae6671d051c7ff18d1",
    ),
    "santarem-pindobal.csv.csv": (
        221156,
        "75e0552320409447771134566e93657487bcd7d74fe192a2a496a9a42a2a6999",
    ),
    "data.json": (
        172947,
        "b597eb1ed56caf4f7e655976d878d5baaf4c90fab4cd62ee365f5b3d5343e018",
    ),
    "empresas_infraestrutura_rotas.csv": (
        311479,
        "23c7a8c0998e0d6b2036640959c92e0ebf36f7822e4623c5fc906c7c51ad874b",
    ),
    "pois_data.json": (
        490219,
        "8875a1eaa2e6bc8bdd0d2a8cce9a10ae4ba742042c41effebbd0725c9a5fecea",
    ),
    "rota_porto_OSRM_01.csv": (
        133946,
        "15c557a406bc6ebd87d4f8706d15c80127fc98b416d535ae57b4454fc991b6cb",
    ),
    "rota_aeroporto_OSRM_01.csv": (
        117739,
        "8cae67ad9d00d6056733787ed41c940d1ba68490dc5bd5e60c6cb1c1f1d15776",
    ),
    "rota_rodoviaria_OSRM_01.csv": (
        131265,
        "fd21e0df95368553aa81aaff22d630e9cffd00c1ef3d0feef6fb5573fc08c70b",
    ),
}


@dataclass
class FileCheckResult:
    filename: str
    expected_bytes: int
    actual_bytes: int
    expected_hash: str
    actual_hash: str
    valid_bytes: bool
    valid_hash: bool


@dataclass
class ManifestReport:
    base_dir: str
    total_files: int
    valid_files: int
    invalid_files: list[FileCheckResult]
    is_valid: bool


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_manifest(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    manifest: dict[str, tuple[int, str]] = MANIFEST_ENTRIES,
) -> ManifestReport:
    """Verify that all snapshot files exist, have correct size and SHA-256 hash."""
    results: list[FileCheckResult] = []
    invalid_results: list[FileCheckResult] = []

    for filename, (expected_bytes, expected_hash) in manifest.items():
        file_path = snapshot_dir / filename
        if not file_path.exists():
            res = FileCheckResult(
                filename=filename,
                expected_bytes=expected_bytes,
                actual_bytes=0,
                expected_hash=expected_hash,
                actual_hash="FILE_NOT_FOUND",
                valid_bytes=False,
                valid_hash=False,
            )
            results.append(res)
            invalid_results.append(res)
            continue

        actual_bytes = file_path.stat().st_size
        actual_hash = calculate_sha256(file_path)

        valid_bytes = actual_bytes == expected_bytes
        valid_hash = actual_hash.lower() == expected_hash.lower()

        res = FileCheckResult(
            filename=filename,
            expected_bytes=expected_bytes,
            actual_bytes=actual_bytes,
            expected_hash=expected_hash,
            actual_hash=actual_hash,
            valid_bytes=valid_bytes,
            valid_hash=valid_hash,
        )
        results.append(res)
        if not (valid_bytes and valid_hash):
            invalid_results.append(res)

    is_valid = len(invalid_results) == 0
    return ManifestReport(
        base_dir=str(snapshot_dir),
        total_files=len(manifest),
        valid_files=len(results) - len(invalid_results),
        invalid_files=invalid_results,
        is_valid=is_valid,
    )
