"""Tests for the high-confidence staging secret scanner."""

import base64
import json
from pathlib import Path

from scripts.scan_secrets import scan_repository, scan_text


def _jwt(payload: dict[str, object]) -> str:
    def encode(value: dict[str, object]) -> str:
        raw = json.dumps(value, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{encode({'alg': 'HS256', 'typ': 'JWT'})}.{encode(payload)}.{'x' * 32}"


def test_documentation_prefixes_and_non_privileged_jwts_are_allowed() -> None:
    text = "\n".join(
        (
            "Use sb_secret_... only on the backend.",
            r"Detection regex: sb_secret_[A-Za-z0-9_-]+",
            f"Publishable fixture: {_jwt({'role': 'anon'})}",
        )
    )

    assert scan_text(text, Path("docs/example.md")) == []


def test_complete_supabase_secret_is_reported_without_its_value() -> None:
    secret = "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz123456"

    findings = scan_text(f"SUPABASE_SECRET_KEY={secret}", Path("config.env"))

    assert [(finding.line, finding.kind) for finding in findings] == [
        (1, "Supabase secret key")
    ]
    assert secret not in repr(findings)


def test_service_role_jwt_is_reported_but_anon_jwt_is_not() -> None:
    service_jwt = _jwt({"role": "service_role", "sub": "server"})
    anon_jwt = _jwt({"role": "anon", "sub": "public"})

    findings = scan_text(f"{anon_jwt}\n{service_jwt}", Path("fixture.txt"))

    assert [(finding.line, finding.kind) for finding in findings] == [
        (2, "Supabase service_role JWT")
    ]


def test_repository_scan_ignores_dependency_directories(tmp_path: Path) -> None:
    dependency_dir = tmp_path / "node_modules" / "package"
    dependency_dir.mkdir(parents=True)
    (dependency_dir / "config.txt").write_text(
        "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz123456",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("sb_secret_...", encoding="utf-8")

    assert scan_repository(tmp_path) == []
