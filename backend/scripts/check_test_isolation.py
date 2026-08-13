"""Validate test credentials are complete and isolated without printing values."""

import re
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")


def configured(path: Path) -> dict[str, str]:
    """Load a local dotenv file into memory without logging it."""
    return {key: value or "" for key, value in dotenv_values(path).items()}


def validate_isolation(development: dict[str, str], test: dict[str, str]) -> list[str]:
    """Return safe category codes for invalid or colliding test configuration."""
    failures: list[str] = []
    if test.get("APP_ENV") != "test":
        failures.append("APP_ENV_NOT_TEST")

    required = ("DATABASE_URL", "SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY")
    for name in required:
        value = test.get(name, "")
        if not value or any(marker in value.lower() for marker in ("replace_me", "your-test")):
            failures.append(f"{name}_MISSING_OR_PLACEHOLDER")

    if test.get("SUPABASE_URL", "").rstrip("/") == development.get(
        "SUPABASE_URL", ""
    ).rstrip("/"):
        failures.append("SUPABASE_PROJECT_MATCHES_DEVELOPMENT")
    if test.get("DATABASE_URL") == development.get("DATABASE_URL"):
        failures.append("DATABASE_URL_MATCHES_DEVELOPMENT")

    project_ref = ""
    parsed_url = urlparse(test.get("SUPABASE_URL", ""))
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        failures.append("SUPABASE_URL_INVALID")
    else:
        hostname_parts = parsed_url.hostname.split(".")
        if len(hostname_parts) != 3 or hostname_parts[1:] != ["supabase", "co"]:
            failures.append("SUPABASE_URL_NOT_MANAGED_PROJECT")
        else:
            project_ref = hostname_parts[0]
            if not PROJECT_REF_PATTERN.fullmatch(project_ref):
                failures.append("SUPABASE_PROJECT_REF_INVALID")

    try:
        database = make_url(test.get("DATABASE_URL", ""))
        if database.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
            failures.append("DATABASE_DRIVER_INVALID")
        if not all((database.username, database.password, database.host, database.database)):
            failures.append("DATABASE_URL_INCOMPLETE")
        elif project_ref:
            username = database.username or ""
            username_ref = (
                username.removeprefix("postgres.")
                if username.startswith("postgres.")
                else ""
            )
            direct_host = f"db.{project_ref}.supabase.co"
            pooler_matches = bool(username_ref) and username_ref == project_ref
            direct_matches = username == "postgres" and database.host == direct_host
            if not (pooler_matches or direct_matches):
                failures.append("DATABASE_PROJECT_REF_MISMATCH")
    except Exception:
        failures.append("DATABASE_URL_INVALID")

    return failures


def require_test_isolation(
    development_path: Path | None = None, test_path: Path | None = None
) -> None:
    """Fail closed unless test is a distinct, internally consistent managed project."""
    development_path = development_path or BACKEND_DIR / ".env"
    test_path = test_path or BACKEND_DIR / ".env.test"
    if not development_path.is_file() or not test_path.is_file():
        raise RuntimeError("Arquivos de ambiente development/test obrigatórios ausentes.")
    failures = validate_isolation(configured(development_path), configured(test_path))
    if failures:
        raise RuntimeError(f"Target test não passou no gate de isolamento: {','.join(failures)}")


def main() -> int:
    """Return a safe pass/fail result for development/test isolation."""
    development_path = BACKEND_DIR / ".env"
    test_path = BACKEND_DIR / ".env.test"
    try:
        require_test_isolation(development_path, test_path)
    except RuntimeError as exc:
        print("TEST_ISOLATION=ERROR")
        print(f"- categoria: {exc}")
        return 1

    print("TEST_ISOLATION=OK")
    print("- ambiente identificado como test")
    print("- projeto e banco diferentes de development")
    print("- formatos obrigatórios válidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
