"""Run allowlisted Supabase CLI test operations with redacted output."""

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEST_ENV = REPOSITORY_ROOT / "backend" / ".env.test"
CLI = ("npx.cmd" if sys.platform == "win32" else "npx", "--yes", "supabase@2.113.0")


def redact(output: str, secrets: tuple[str, ...]) -> str:
    """Remove configured values if a CLI error unexpectedly echoes them."""
    safe = output
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[REDACTED]")
    return safe


def main() -> int:
    """Execute only explicitly supported read/dry-run/apply/advisor operations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("dry-run", "apply", "list", "advisors"))
    args = parser.parse_args()
    values = {key: value or "" for key, value in dotenv_values(TEST_ENV).items()}
    database_url = values.get("DATABASE_URL", "")
    if not database_url:
        print("SUPABASE_CLI=ERROR")
        print("- categoria: TEST_DATABASE_URL_MISSING")
        return 1

    commands = {
        "dry-run": (
            *CLI,
            "db",
            "push",
            "--dry-run",
            "--include-all",
            "--db-url",
            database_url,
            "--workdir",
            str(REPOSITORY_ROOT),
        ),
        "apply": (
            *CLI,
            "db",
            "push",
            "--include-all",
            "--db-url",
            database_url,
            "--workdir",
            str(REPOSITORY_ROOT),
            "--yes",
        ),
        "list": (
            *CLI,
            "migration",
            "list",
            "--db-url",
            database_url,
            "--workdir",
            str(REPOSITORY_ROOT),
        ),
        "advisors": (
            *CLI,
            "db",
            "advisors",
            "--db-url",
            database_url,
            "--type",
            "all",
            "--level",
            "warn",
            "--fail-on",
            "error",
            "--workdir",
            str(REPOSITORY_ROOT),
        ),
    }
    completed = subprocess.run(
        commands[args.operation], capture_output=True, text=True, check=False
    )
    secrets = tuple(
        values.get(name, "")
        for name in ("DATABASE_URL", "SUPABASE_SECRET_KEY", "GOOGLE_PLACES_API_KEY", "SENTRY_DSN")
        if values.get(name)
    )
    print(redact(completed.stdout, secrets), end="")
    print(redact(completed.stderr, secrets), end="")
    print(f"SUPABASE_CLI_EXIT={completed.returncode}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
