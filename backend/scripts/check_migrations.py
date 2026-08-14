"""Fail closed on malformed or silently unordered Supabase migrations."""

import re
from pathlib import Path

MIGRATION_NAME = re.compile(r"^(?P<version>\d{14})_(?P<name>[a-z0-9_]+)\.sql$")
FORBIDDEN_SQL = {
    "auth.role(": "auth.role() is forbidden; policies must use TO plus ownership predicates",
}


def validate_migrations(migrations_dir: Path) -> list[str]:
    """Return deterministic validation errors without connecting to a database."""
    errors: list[str] = []
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        return [f"No SQL migrations found in {migrations_dir}"]

    seen_versions: set[str] = set()
    for path in files:
        match = MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            errors.append(f"Invalid migration filename: {path.name}")
            continue
        version = match.group("version")
        if version in seen_versions:
            errors.append(f"Duplicate migration version: {version}")
        seen_versions.add(version)

        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            errors.append(f"Empty migration: {path.name}")
        normalized = "\n".join(
            line for line in sql.casefold().splitlines() if not line.lstrip().startswith("--")
        )
        for forbidden, reason in FORBIDDEN_SQL.items():
            if forbidden in normalized:
                errors.append(f"{path.name}: {reason}")
        if "alembic" in normalized:
            errors.append(f"{path.name}: Alembic metadata is not allowed")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = validate_migrations(root / "supabase" / "migrations")
    if errors:
        for error in errors:
            print(f"MIGRATION_ERROR: {error}")
        return 1
    print("MIGRATIONS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
