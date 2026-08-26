"""Credential configuration and repository secret-scanning tests (ECO-0106)."""

import re
from os import walk
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".uv-cache",
    ".uv-python",
    ".venv",
    "node_modules",
}



def test_sensitive_settings_are_masked_in_representations() -> None:
    """Sensitive values must not appear when settings are logged or inspected."""
    marker = "credential-that-must-stay-masked"
    configured = Settings(
        _env_file=None,  # type: ignore[call-arg]
        DATABASE_URL=SecretStr(f"postgresql+psycopg://user:{marker}@db.example/postgres"),
        SUPABASE_SECRET_KEY=SecretStr(marker),
        GOOGLE_PLACES_API_KEY=SecretStr(marker),
        GOOGLE_ROUTES_API_KEY=SecretStr(marker),
        SENTRY_DSN=SecretStr(marker),
    )

    assert marker not in repr(configured)
    assert configured.SUPABASE_SECRET_KEY.get_secret_value() == marker


def test_deployed_environment_rejects_placeholders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Staging and production must fail closed when required values are placeholders."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="Configuração obrigatória"):
        Settings(_env_file=None, APP_ENV="production", DATABASE_URL=SecretStr(""))  # type: ignore[call-arg]


def test_deployed_environment_rejects_fake_and_production_activation() -> None:
    common = {
        "_env_file": None,
        "APP_ENV": "staging",
        "DATABASE_URL": SecretStr("postgresql://user:password@db.example/postgres"),
        "SUPABASE_URL": "https://project-ref.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    }
    with pytest.raises(ValidationError, match="Google Routes"):
        Settings(**common, ROUTING_PROVIDER="fake_deterministic")  # type: ignore[arg-type]
    configured = Settings(**common, ROUTING_PROVIDER="google_routes")  # type: ignore[arg-type]
    assert configured.ENABLE_DYNAMIC_ROUTING is False
    production = {**common, "APP_ENV": "production"}
    with pytest.raises(ValidationError, match="não está autorizado em production"):
        Settings(
            **production,
            ROUTING_PROVIDER="google_routes",
            ENABLE_DYNAMIC_ROUTING=True,
            GOOGLE_ROUTES_API_KEY=SecretStr("test-only"),
        )  # type: ignore[arg-type]


def test_provider_database_url_and_jwks_are_normalized() -> None:
    """Provider connection strings should load without duplicating derived configuration."""
    configured = Settings(
        _env_file=None,  # type: ignore[call-arg]
        DATABASE_URL=SecretStr("postgresql://user:password@db.example/postgres"),
        SUPABASE_URL="https://project-ref.supabase.co",
        SUPABASE_JWKS_URL="",
    )

    assert configured.DATABASE_URL.get_secret_value().startswith("postgresql+psycopg://")
    assert configured.SUPABASE_JWKS_URL.endswith("/auth/v1/.well-known/jwks.json")


def test_frontend_example_contains_only_public_configuration() -> None:
    """The Expo example must never advertise server-only credential names."""
    example = (REPOSITORY_ROOT / "econexao-app" / ".env.example").read_text(encoding="utf-8")
    assigned_names = {
        line.split("=", 1)[0]
        for line in example.splitlines()
        if line and not line.startswith("#") and "=" in line
    }

    assert assigned_names
    assert all(name.startswith("EXPO_PUBLIC_") for name in assigned_names)
    assert not any("SECRET" in name or "SERVICE_ROLE" in name for name in assigned_names)


def test_repository_does_not_contain_recognizable_live_api_keys() -> None:
    """Fail the normal pytest gate if a recognizable provider key is committed."""
    patterns = (
        re.compile("sb_" + "secret_" + r"[A-Za-z0-9_-]{20,}"),
        re.compile("AI" + "za" + r"[A-Za-z0-9_-]{30,}"),
        re.compile("sk-" + r"[A-Za-z0-9_-]{20,}"),
    )
    findings: list[str] = []

    for directory, child_dirs, filenames in walk(REPOSITORY_ROOT):
        child_dirs[:] = [name for name in child_dirs if name not in IGNORED_PARTS]
        for filename in filenames:
            path = Path(directory, filename)
            if path.name != ".env.example" and path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(pattern.search(content) for pattern in patterns):
                findings.append(str(path.relative_to(REPOSITORY_ROOT)))

    assert findings == [], f"Possíveis credenciais reais encontradas: {findings}"
