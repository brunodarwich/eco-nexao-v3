"""Staging migration gate and advisors verification script for ECO-2002.

Executes safe migration list/drift verification and Supabase Advisors inspection
against the authorized staging project exclusively. Fails closed if secrets are missing,
never prints credentials, and applies migrations only when explicitly authorized.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")
_URL_PASSWORD_REGEX = re.compile(r"://([^:@\s]+):([^@\s]+)@")
_TOKEN_REGEX = re.compile(
    r"(sb_secret_[a-zA-Z0-9_-]+|eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)"
)


def sanitize_log(text: str, secrets: list[str] | None = None) -> str:
    """Redact passwords, DSNs, tokens and explicit secret values from command output."""
    if not text:
        return ""
    redacted = _URL_PASSWORD_REGEX.sub(r"://\1:[REDACTED]@", text)
    redacted = _TOKEN_REGEX.sub("[REDACTED_TOKEN]", redacted)
    if secrets:
        for secret in secrets:
            if secret and len(secret) >= 4:
                redacted = redacted.replace(secret, "[REDACTED_SECRET]")
    return redacted


def extract_project_ref_from_url(url: str | None) -> str:
    """Extract 20-char project ref from a Supabase project URL."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    if not parsed.hostname:
        return ""
    parts = parsed.hostname.split(".")
    if len(parts) == 3 and parts[1:] == ["supabase", "co"]:
        return parts[0]
    return ""


def validate_staging_project_ref(
    project_ref: str,
    dev_ref: str | None = None,
    test_ref: str | None = None,
) -> str:
    """Validate that the project ref is well-formed and distinct from dev/test/production."""
    ref = (project_ref or "").strip().lower()
    if not ref:
        raise ValueError("SUPABASE_PROJECT_REF is empty.")

    if not PROJECT_REF_PATTERN.fullmatch(ref):
        raise ValueError(
            "SUPABASE_PROJECT_REF must be exactly 20 lowercase alphanumeric characters."
        )

    if any(marker in ref for marker in ("replace", "your", "project", "prod")):
        raise ValueError("SUPABASE_PROJECT_REF contains placeholder or production marker.")

    if dev_ref and ref == dev_ref.strip().lower():
        raise ValueError("Staging SUPABASE_PROJECT_REF collides with development project ref.")

    if test_ref and ref == test_ref.strip().lower():
        raise ValueError("Staging SUPABASE_PROJECT_REF collides with test project ref.")

    return ref


def run_cli_command(
    args: list[str],
    env_vars: dict[str, str],
    secrets_to_redact: list[str],
    timeout_seconds: float = 60.0,
    cwd: Path | None = None,
) -> tuple[int, str]:
    """Execute a CLI command safely with sanitized output."""
    root_dir = BACKEND_DIR.parent
    cmd_cwd = cwd or root_dir

    # Find npx or supabase executable
    is_win = sys.platform == "win32"
    cmd_name = f"{args[0]}.cmd" if is_win and not args[0].endswith(".cmd") else args[0]
    executable = shutil.which(cmd_name) or shutil.which(args[0])
    if not executable:
        return 1, f"Executable '{args[0]}' not found in PATH."

    full_cmd = [executable] + args[1:]
    full_env = {**os.environ, **env_vars}

    try:
        proc = subprocess.run(
            full_cmd,
            cwd=cmd_cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=full_env,
            check=False,
        )
        combined_output = f"{proc.stdout}\n{proc.stderr}".strip()
        sanitized = sanitize_log(combined_output, secrets_to_redact)
        return proc.returncode, sanitized
    except Exception as exc:
        return 1, sanitize_log(f"Error executing command: {exc}", secrets_to_redact)


def check_migration_drift(
    project_ref: str,
    db_password: str,
    access_token: str,
) -> tuple[bool, str, list[str]]:
    """Run `supabase migration list` to inspect remote vs local migration drift."""
    secrets = [db_password, access_token]
    env_vars = {"SUPABASE_ACCESS_TOKEN": access_token}
    args = [
        "npx",
        "--yes",
        "supabase",
        "migration",
        "list",
        "--project-ref",
        project_ref,
        "--password",
        db_password,
    ]

    code, output = run_cli_command(args, env_vars=env_vars, secrets_to_redact=secrets)
    if code != 0:
        return False, f"supabase migration list failed (exit {code}):\n{output}", []

    # Parse output to detect pending/unapplied migrations
    unapplied: list[str] = []
    for line in output.splitlines():
        # Typical table output has LOCAL | REMOTE or timestamp indicators
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                local_ver = parts[0]
                remote_ver = parts[1]
                if local_ver and not remote_ver:
                    unapplied.append(local_ver)

    return True, output, unapplied


def check_supabase_advisors(
    project_ref: str,
    db_password: str,
    access_token: str,
) -> tuple[bool, str]:
    """Run `supabase db advisors` to detect security and performance issues."""
    secrets = [db_password, access_token]
    env_vars = {"SUPABASE_ACCESS_TOKEN": access_token}
    args = [
        "npx",
        "--yes",
        "supabase",
        "db",
        "advisors",
        "--project-ref",
        project_ref,
        "--type",
        "all",
        "--fail-on",
        "error",
    ]

    code, output = run_cli_command(args, env_vars=env_vars, secrets_to_redact=secrets)
    if code != 0:
        return False, f"supabase db advisors reported errors (exit {code}):\n{output}"

    return True, output


def apply_staging_migrations(
    project_ref: str,
    db_password: str,
    access_token: str,
) -> tuple[bool, str]:
    """Apply pending migrations to the authorized staging database."""
    secrets = [db_password, access_token]
    env_vars = {"SUPABASE_ACCESS_TOKEN": access_token}
    args = [
        "npx",
        "--yes",
        "supabase",
        "db",
        "push",
        "--project-ref",
        project_ref,
        "--password",
        db_password,
    ]

    code, output = run_cli_command(args, env_vars=env_vars, secrets_to_redact=secrets)
    if code != 0:
        return False, f"supabase db push failed (exit {code}):\n{output}"

    return True, output


def run_gate(
    project_ref: str,
    db_password: str,
    access_token: str,
    apply_migrations: bool = False,
) -> int:
    """Orchestrate staging migration gate verification."""
    print("==================================================")
    print("ECOnexão — Staging Migration & Advisors Gate (ECO-2002)")
    print("==================================================")

    # 1. Validate Secret Presence (Fail Closed)
    missing: list[str] = []
    if not access_token or not access_token.strip():
        missing.append("SUPABASE_ACCESS_TOKEN")
    if not project_ref or not project_ref.strip():
        missing.append("SUPABASE_PROJECT_REF")
    if not db_password or not db_password.strip():
        missing.append("SUPABASE_DB_PASSWORD")

    if missing:
        print(f"[GATE][ERROR] Missing mandatory staging secret(s): {', '.join(missing)}")
        print(
            "[GATE][ERROR] Failing closed. Staging secrets must be configured in "
            "GitHub Environment 'staging'."
        )
        return 1

    # 2. Validate Project Ref Isolation
    dev_env = dotenv_values(BACKEND_DIR / ".env")
    test_env = dotenv_values(BACKEND_DIR / ".env.test")
    dev_ref = extract_project_ref_from_url(dev_env.get("SUPABASE_URL"))
    test_ref = extract_project_ref_from_url(test_env.get("SUPABASE_URL"))

    try:
        valid_ref = validate_staging_project_ref(project_ref, dev_ref=dev_ref, test_ref=test_ref)
        print(f"[GATE] Staging project ref validated: {valid_ref[:6]}...{valid_ref[-4:]}")
    except ValueError as err:
        print(f"[GATE][ERROR] Project ref validation failed: {err}")
        return 1

    # 3. Migration Drift Inspection
    print("[GATE] Checking remote migration list and drift status...")
    ok, list_output, unapplied = check_migration_drift(
        project_ref=valid_ref,
        db_password=db_password,
        access_token=access_token,
    )
    if not ok:
        print(f"[GATE][ERROR] Migration list inspection failed:\n{list_output}")
        return 1

    if unapplied:
        print(f"[GATE][WARN] Detected {len(unapplied)} unapplied migration(s) on staging.")
        if not apply_migrations:
            print("[GATE][ERROR] Migration apply is not authorized for this run.")
            print("[GATE][ERROR] Re-run with explicit authorization to promote migrations.")
            return 1

        print("[GATE] Applying migrations to staging (authorized)...")
        apply_ok, apply_output = apply_staging_migrations(
            project_ref=valid_ref,
            db_password=db_password,
            access_token=access_token,
        )
        if not apply_ok:
            print(f"[GATE][ERROR] Staging migration apply failed:\n{apply_output}")
            return 1
        print("[GATE] Migrations successfully applied to staging.")
    else:
        print("[GATE] Staging database schema is in sync (zero unapplied migrations).")

    # 4. Supabase Advisors Inspection
    print("[GATE] Running Supabase Database Security and Performance Advisors...")
    adv_ok, adv_output = check_supabase_advisors(
        project_ref=valid_ref,
        db_password=db_password,
        access_token=access_token,
    )
    if not adv_ok:
        print(
            f"[GATE][ERROR] Supabase Advisors reported security/performance violations:\n"
            f"{adv_output}"
        )
        return 1

    print("[GATE] Supabase Advisors check PASSED (zero blocking security/performance issues).")
    print("[GATE] All staging migration gate checks PASSED successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Staging Migration Gate for ECO-2002.")
    parser.add_argument(
        "--project-ref",
        default=os.environ.get("SUPABASE_PROJECT_REF", ""),
        help="Supabase staging project ref (20 lowercase alphanumeric characters)",
    )
    parser.add_argument(
        "--db-password",
        default=os.environ.get("SUPABASE_DB_PASSWORD", ""),
        help="Supabase staging database password",
    )
    parser.add_argument(
        "--access-token",
        default=os.environ.get("SUPABASE_ACCESS_TOKEN", ""),
        help="Supabase management access token",
    )
    parser.add_argument(
        "--apply-migrations",
        action="store_true",
        default=os.environ.get("APPLY_STAGING_MIGRATIONS", "").lower() in ("true", "1", "yes"),
        help="Explicitly authorize applying pending migrations to staging",
    )

    args = parser.parse_args()
    exit_code = run_gate(
        project_ref=args.project_ref,
        db_password=args.db_password,
        access_token=args.access_token,
        apply_migrations=args.apply_migrations,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
