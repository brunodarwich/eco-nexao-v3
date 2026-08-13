"""Validate local ECOnexão environment files without printing credential values."""

from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV = REPOSITORY_ROOT / "backend" / ".env"
FRONTEND_ENV = REPOSITORY_ROOT / "econexao-app" / ".env.local"


class EnvironmentValidationError(Exception):
    """Collect validation failures without including credential values."""


def require(value: str | None, name: str, failures: list[str]) -> str:
    """Require a non-placeholder value and return a safe empty fallback."""
    if not value or any(marker in value.lower() for marker in ("replace_me", "your-project")):
        failures.append(f"{name}: ausente ou placeholder")
        return ""
    return value


def validate_url(value: str, name: str, failures: list[str], *, https_only: bool) -> None:
    """Validate URL structure without exposing the URL."""
    parsed = urlparse(value)
    allowed_schemes = {"https"} if https_only else {"http", "https"}
    if parsed.scheme not in allowed_schemes or not parsed.hostname:
        failures.append(f"{name}: URL inválida")


def validate() -> list[str]:
    """Return safe validation failures; an empty list means success."""
    failures: list[str] = []
    if not BACKEND_ENV.is_file():
        failures.append("backend/.env: arquivo ausente")
    if not FRONTEND_ENV.is_file():
        failures.append("econexao-app/.env.local: arquivo ausente")
    if failures:
        return failures

    backend = {key: value or "" for key, value in dotenv_values(BACKEND_ENV).items()}
    frontend = {key: value or "" for key, value in dotenv_values(FRONTEND_ENV).items()}

    app_env = backend.get("APP_ENV")
    if app_env not in {"development", "test"}:
        failures.append("APP_ENV: use development ou test nesta máquina")

    database_url = require(backend.get("DATABASE_URL"), "DATABASE_URL", failures)
    if database_url:
        try:
            parsed_database = make_url(database_url)
            if parsed_database.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
                failures.append("DATABASE_URL: driver PostgreSQL não reconhecido")
            if not all(
                (
                    parsed_database.username,
                    parsed_database.password,
                    parsed_database.host,
                    parsed_database.database,
                )
            ):
                failures.append("DATABASE_URL: usuário, senha, host e database são obrigatórios")
        except Exception:
            failures.append("DATABASE_URL: formato inválido")

    backend_url = require(backend.get("SUPABASE_URL"), "SUPABASE_URL", failures)
    backend_jwks = backend.get("SUPABASE_JWKS_URL", "")
    if (
        not backend_jwks
        or "your-project" in backend_jwks.lower()
        or "replace_me" in backend_jwks.lower()
    ) and backend_url:
        backend_jwks = f"{backend_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    publishable = require(
        backend.get("SUPABASE_PUBLISHABLE_KEY"),
        "SUPABASE_PUBLISHABLE_KEY",
        failures,
    )
    if backend_url:
        validate_url(backend_url, "SUPABASE_URL", failures, https_only=True)
    if backend_jwks:
        validate_url(backend_jwks, "SUPABASE_JWKS_URL", failures, https_only=True)
    if backend_url and backend_jwks:
        base = urlparse(backend_url)
        jwks = urlparse(backend_jwks)
        if base.hostname != jwks.hostname:
            failures.append("SUPABASE_JWKS_URL: projeto diferente de SUPABASE_URL")
        if jwks.path.rstrip("/") != "/auth/v1/.well-known/jwks.json":
            failures.append("SUPABASE_JWKS_URL: caminho JWKS inesperado")
    if publishable and not (
        publishable.startswith("sb_publishable_") or publishable.startswith("eyJ")
    ):
        failures.append("SUPABASE_PUBLISHABLE_KEY: formato não reconhecido")

    backend_secret = backend.get("SUPABASE_SECRET_KEY", "")
    if backend_secret and not (
        backend_secret.startswith("sb_secret_") or backend_secret.startswith("eyJ")
    ):
        failures.append("SUPABASE_SECRET_KEY: formato não reconhecido")

    public_names = [name for name in frontend if not name.startswith("EXPO_PUBLIC_")]
    if public_names:
        failures.append("econexao-app/.env.local: contém variável sem prefixo EXPO_PUBLIC_")
    if any("SECRET" in name or "SERVICE_ROLE" in name for name in frontend):
        failures.append("econexao-app/.env.local: contém nome de credencial proibida")

    frontend_api = require(frontend.get("EXPO_PUBLIC_API_URL"), "EXPO_PUBLIC_API_URL", failures)
    frontend_url = require(
        frontend.get("EXPO_PUBLIC_SUPABASE_URL"),
        "EXPO_PUBLIC_SUPABASE_URL",
        failures,
    )
    frontend_key = require(
        frontend.get("EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY"),
        "EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        failures,
    )
    if frontend_api:
        validate_url(frontend_api, "EXPO_PUBLIC_API_URL", failures, https_only=False)
    if frontend_url:
        validate_url(frontend_url, "EXPO_PUBLIC_SUPABASE_URL", failures, https_only=True)
    if frontend_url and backend_url and frontend_url.rstrip("/") != backend_url.rstrip("/"):
        failures.append("URLs Supabase do frontend e backend apontam para projetos diferentes")
    if frontend_key and publishable and frontend_key != publishable:
        failures.append("Publishable keys do frontend e backend são diferentes")

    return failures


def main() -> int:
    """Print only safe validation status and return a shell-friendly exit code."""
    failures = validate()
    if failures:
        print("ENV_CHECK=ERROR")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ENV_CHECK=OK")
    print("- arquivos locais encontrados")
    print("- variáveis obrigatórias configuradas")
    print("- formatos e separação frontend/backend válidos")
    print("- projeto Supabase coerente entre URL, JWKS e Expo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
