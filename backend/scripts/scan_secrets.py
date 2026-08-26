"""High-confidence repository secret scanner used by the staging gate."""

import argparse
import base64
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".git-history-backup",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".test-cache",
    ".test-tmp",
    ".uv-cache",
    ".uv-python",
    ".venv",
    "node_modules",
}

TOKEN_PATTERNS = {
    "Supabase secret key": re.compile(r"\bsb_secret_[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
JWT_PATTERN = re.compile(
    r"\b(?P<header>[A-Za-z0-9_-]{10,})\."
    r"(?P<payload>[A-Za-z0-9_-]{10,})\."
    r"(?P<signature>[A-Za-z0-9_-]{10,})\b"
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str


def _decode_jwt_payload(encoded_payload: str) -> dict[str, object] | None:
    padding = "=" * (-len(encoded_payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(encoded_payload + padding)
        payload = json.loads(decoded)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def scan_text(text: str, path: Path) -> list[Finding]:
    """Return redacted metadata for high-confidence secrets found in text."""
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in TOKEN_PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(path=path, line=line_number, kind=kind))

        for match in JWT_PATTERN.finditer(line):
            payload = _decode_jwt_payload(match.group("payload"))
            if payload and payload.get("role") == "service_role":
                findings.append(
                    Finding(path=path, line=line_number, kind="Supabase service_role JWT")
                )
    return findings


def scan_repository(root: Path) -> list[Finding]:
    """Scan repository text files without following excluded dependency/cache trees."""
    paths: list[Path] = []
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            paths = [root / item.decode() for item in result.stdout.split(b"\x00") if item]

    if not paths:
        paths = _walk_repository_files(root)

    findings: list[Finding] = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            with path.open("rb") as source:
                if b"\x00" in source.read(8192):
                    continue
            raw = path.read_bytes()
        except OSError:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(text, path.relative_to(root)))
    return findings


def _walk_repository_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory, subdirectories, filenames in os.walk(root, topdown=True):
        subdirectories[:] = [
            name for name in subdirectories if name not in EXCLUDED_DIRECTORIES
        ]
        for filename in filenames:
            paths.append(Path(directory) / filename)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repository for committed secrets")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    findings = scan_repository(args.root.resolve())
    if findings:
        print("SECRET_SCAN=ERROR")
        for finding in findings:
            print(f"- {finding.path}:{finding.line}: {finding.kind}")
        return 1

    print("SECRET_SCAN=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
