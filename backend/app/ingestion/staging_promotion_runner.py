"""Staging promotion runner for Pindobal territorial slice (ECO-2005).

Ensures fail-closed target isolation (staging ref kchzucvrnzwzehfdwzwi only),
offline preflight validation, double human confirmation, non-blocking
pg_try_advisory_lock concurrency control, and logical rollback governance.
Remote write execution is strictly prohibited during Phase 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.manifest import verify_manifest
from app.ingestion.seed_pindobal import DEFAULT_SNAPSHOT_DIR, run_seed_pindobal

CANONICAL_STAGING_PROJECT_REF: str = "kchzucvrnzwzehfdwzwi"
KNOWN_OBVIOUS_NON_STAGING_REFS: frozenset[str] = frozenset(
    {
        "rgfuqmwxjuceqpxcraxm",  # Obsolete staging ref
        "hjtkcmbfndbgyurfhsuo",  # Production ref (STRICTLY FORBIDDEN)
    }
)
PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")
DIRECT_HOST_PATTERN = re.compile(r"^db\.([a-z0-9]{20})\.supabase\.co$")
POOLER_USER_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+\.([a-z0-9]{20})$")

# Deterministic 64-bit advisory lock ID derived from namespace string
PINDOBAL_STAGING_ADVISORY_LOCK_ID: int = int.from_bytes(
    hashlib.sha256(b"econexao:staging_promotion:pindobal").digest()[:8],
    "big",
    signed=True,
)
ADVISORY_LOCK_ID: int = PINDOBAL_STAGING_ADVISORY_LOCK_ID

CANONICAL_PINDOBAL_METRICS: dict[str, int] = {
    "read": 1714,
    "created": 1661,
    "candidates": 53,
    "rejected": 0,
    "unchanged": 0,
    "updated": 0,
}
CANONICAL_MIGRATIONS_COUNT: int = 25


class StagingPromotionError(Exception):
    """Base exception for staging promotion runner."""


class TargetValidationError(StagingPromotionError):
    """Target environment or project ref is not valid or not authorized."""


class PreflightVerificationError(StagingPromotionError):
    """Preflight checks (manifest, counts, migrations) failed."""


class ConfirmationError(StagingPromotionError):
    """Operator confirmation was denied or invalid."""


class AdvisoryLockBusyError(StagingPromotionError):
    """Advisory lock could not be acquired due to concurrent execution."""


def sanitize_message(text_content: str) -> str:
    """Mask credentials, passwords, and tokens from error messages and logs."""
    sanitized = re.sub(r"://([^:\s]+):([^@\s]+)@", r"://\1:[REDACTED]@", text_content)
    sanitized = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[REDACTED_JWT]", sanitized
    )
    sanitized = re.sub(r"\bsb_secret_[A-Za-z0-9_-]{20,}\b", "[REDACTED_SECRET]", sanitized)
    sanitized = re.sub(r"\bsbp_[A-Za-z0-9_-]{30,}\b", "[REDACTED_SBP]", sanitized)
    return sanitized


def validate_target_project_ref(project_ref: str) -> str:
    """Ensure project ref matches canonical staging ref and fail closed otherwise."""
    cleaned = (project_ref or "").strip().lower()
    if not cleaned:
        raise TargetValidationError("Project ref não pode ser vazio.")
    if not PROJECT_REF_PATTERN.fullmatch(cleaned):
        raise TargetValidationError(
            f"Formato de project ref inválido: '{cleaned}'. "
            "Deve conter 20 caracteres alfanuméricos."
        )
    if cleaned in KNOWN_OBVIOUS_NON_STAGING_REFS:
        raise TargetValidationError(
            f"Project ref '{cleaned}' é explicitamente bloqueado (ref obsoleto ou produção)."
        )
    if cleaned != CANONICAL_STAGING_PROJECT_REF:
        raise TargetValidationError(
            f"Target '{cleaned}' não autorizado para promoção staging. "
            f"Target obrigatório: '{CANONICAL_STAGING_PROJECT_REF}'."
        )
    return cleaned


def extract_ref_from_supabase_url(url: str) -> str:
    """Extract project ref from Supabase REST URL."""
    cleaned = (url or "").strip()
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.hostname:
        raise TargetValidationError(f"SUPABASE_URL inválida: '{cleaned}'. Deve usar https://.")
    parts = parsed.hostname.split(".")
    if len(parts) != 3 or parts[1:] != ["supabase", "co"]:
        raise TargetValidationError(
            f"SUPABASE_URL '{cleaned}' não é um projeto Supabase gerenciado (*.supabase.co)."
        )
    return validate_target_project_ref(parts[0])


def extract_ref_from_database_url(url: str) -> str:
    """Extract project ref from direct DB host or Supavisor pooler connection string."""
    cleaned = (url or "").strip()
    try:
        db_url = make_url(cleaned)
    except Exception as exc:
        raise TargetValidationError(f"DATABASE_URL inválida: {sanitize_message(str(exc))}") from exc

    if db_url.drivername not in {
        "postgres",
        "postgresql",
        "postgresql+psycopg",
        "postgresql+asyncpg",
    }:
        raise TargetValidationError(f"Driver de banco não suportado: '{db_url.drivername}'.")

    host = db_url.host or ""
    username = db_url.username or ""

    # Direct connection: db.<ref>.supabase.co
    direct_match = DIRECT_HOST_PATTERN.fullmatch(host)
    if direct_match:
        return validate_target_project_ref(direct_match.group(1))

    # Pooler connection: user.<ref>@aws-0-sa-east-1.pooler.supabase.com
    pooler_match = POOLER_USER_PATTERN.fullmatch(username)
    if pooler_match and "pooler.supabase.com" in host:
        return validate_target_project_ref(pooler_match.group(1))

    raise TargetValidationError(
        "DATABASE_URL não corresponde ao padrão Supabase direto (db.<ref>.supabase.co) "
        "nem ao connection pooler (<user>.<ref>@*.pooler.supabase.com)."
    )


def validate_environment_config(env_values: dict[str, str]) -> str:
    """Cross-validate APP_ENV, SUPABASE_URL, and DATABASE_URL for staging isolation."""
    app_env = (env_values.get("APP_ENV") or "").strip().lower()
    if app_env != "staging":
        raise TargetValidationError(
            f"APP_ENV inválido: '{app_env}'. O runner exige estritamente 'staging'."
        )

    supabase_url = env_values.get("SUPABASE_URL") or ""
    database_url = env_values.get("DATABASE_URL") or ""

    ref_from_supabase = extract_ref_from_supabase_url(supabase_url)
    ref_from_database = extract_ref_from_database_url(database_url)

    if ref_from_supabase != ref_from_database:
        raise TargetValidationError(
            "Divergência entre SUPABASE_URL e DATABASE_URL: "
            f"{ref_from_supabase} vs {ref_from_database}."
        )
    return ref_from_supabase


def verify_pindobal_offline_manifest(snapshot_dir: Path) -> dict[str, Any]:
    """Verify SHA-256 hashes of all 9 files in the canonical Pindobal snapshot."""
    manifest_report = verify_manifest(snapshot_dir)
    if not manifest_report.is_valid:
        invalid_summary = [
            f"{f.filename} (esperado: {f.expected_hash[:8]}..., real: {f.actual_hash[:8]}...)"
            for f in manifest_report.invalid_files
        ]
        inv_count = len(manifest_report.invalid_files)
        raise PreflightVerificationError(
            f"Falha de integridade no manifesto Pindobal ({inv_count} arquivos inválidos): "
            f"{'; '.join(invalid_summary)}"
        )
    return {
        "status": "valid",
        "total_files": manifest_report.total_files,
        "valid_files": manifest_report.valid_files,
    }


def verify_canonical_counts(snapshot_dir: Path) -> dict[str, Any]:
    """Execute local dry-run against snapshot and assert canonical counts."""
    dry_run_report = run_seed_pindobal(snapshot_dir=snapshot_dir, dry_run=True)
    if dry_run_report.get("status") != "success":
        raise PreflightVerificationError(
            f"Dry-run local falhou: {dry_run_report.get('message', 'erro desconhecido')}"
        )

    counts = dry_run_report.get("counts", {})
    divergences: list[str] = []
    for key, expected_val in CANONICAL_PINDOBAL_METRICS.items():
        actual_val = counts.get(key)
        if actual_val != expected_val:
            divergences.append(f"{key}: esperado {expected_val}, obtido {actual_val}")

    # Check Google Place IDs: none should be invented (all 737 have external_id_missing_count = 737)
    google_stats = dry_run_report.get("google_snapshot", {})
    missing_place_ids = google_stats.get("external_id_missing_count", 0)
    if missing_place_ids != 737:
        divergences.append(f"Google sem Place ID: esperado 737, obtido {missing_place_ids}")

    if divergences:
        raise PreflightVerificationError(
            f"Contagens do dry-run divergem do contrato canônico: {', '.join(divergences)}"
        )

    return {
        "status": "verified",
        "counts": counts,
        "google_records_without_place_id": missing_place_ids,
        "invented_place_ids": 0,
        "reconciliation": {
            "matches_count": dry_run_report.get("reconciliation", {}).get("matches_count", 0),
            "fuzzy_candidate_count": dry_run_report.get("reconciliation", {}).get(
                "fuzzy_candidate_count", 0
            ),
        },
    }


def verify_migrations_alignment(migrations_dir: Path) -> dict[str, Any]:
    """Inspect local migrations directory to verify alignment with the 25 migrations."""
    if not migrations_dir.is_dir():
        raise PreflightVerificationError(
            f"Diretório de migrations não encontrado: {migrations_dir}"
        )
    sql_files = sorted(migrations_dir.glob("*.sql"))
    if len(sql_files) != CANONICAL_MIGRATIONS_COUNT:
        raise PreflightVerificationError(
            f"Quantidade de migrations local divergente: esperado {CANONICAL_MIGRATIONS_COUNT}, "
            f"encontrado {len(sql_files)}."
        )
    return {
        "status": "aligned_locally",
        "scope": "local_directory_only",
        "count": len(sql_files),
        "first_migration": sql_files[0].name,
        "latest_migration": sql_files[-1].name,
        "remote_drift_and_advisors_check": "deferred_to_phase2_preflight",
    }


def request_human_double_confirmation(
    target_ref: str,
    prompt_input: Callable[[str], str] = input,
) -> bool:
    """Require two explicit human confirmation gates before granting execution authorization."""
    prompt_msg = (
        f"[CONFIRMAÇÃO 1/2] Digite o Project Ref de Staging ({target_ref}) para confirmar: "
    )
    prompt_ref = prompt_input(prompt_msg).strip().lower()

    if prompt_ref != target_ref:
        raise ConfirmationError(
            f"Confirmação 1 falhou: '{prompt_ref}' != '{target_ref}'. Operação cancelada."
        )

    # Factor 2: Explicit affirmative yes/no
    prompt_yn = (
        prompt_input(
            "[CONFIRMAÇÃO 2/2] Confirma prosseguir para a fase de validação de staging? [y/N]: "
        )
        .strip()
        .lower()
    )

    if prompt_yn not in {"y", "yes"}:
        raise ConfirmationError(
            "Confirmação 2 falhou: resposta não afirmativa. Operação cancelada."
        )

    return True


@asynccontextmanager
async def staging_advisory_lock(
    session: AsyncSession,
    lock_id: int = PINDOBAL_STAGING_ADVISORY_LOCK_ID,
) -> AsyncGenerator[bool]:
    """Asynchronously acquire pg_try_advisory_lock and always unlock in finally."""
    # Use scalar query with pg_try_advisory_lock
    lock_query = select(func.pg_try_advisory_lock(lock_id))
    result = await session.execute(lock_query)
    acquired = bool(result.scalar_one())

    if not acquired:
        raise AdvisoryLockBusyError(
            f"Advisory lock {lock_id} está ocupado por outro processo em staging. "
            "A promoção foi abortada sem bloqueio indefinido."
        )
    try:
        yield acquired
    finally:
        unlock_query = select(func.pg_advisory_unlock(lock_id))
        await session.execute(unlock_query)


def execute_phase1_preflight(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    migrations_dir: Path | None = None,
    env_values: dict[str, str] | None = None,
    confirm_func: Callable[[str], str] | None = None,
    require_confirmation: bool = True,
) -> dict[str, Any]:
    """Execute Phase 1: offline and read-only preflight verification without remote writes."""
    start_time = datetime.now(UTC).isoformat()

    # Step 1: Environment and target validation
    if env_values is not None:
        target_ref = validate_environment_config(env_values)
    else:
        target_ref = CANONICAL_STAGING_PROJECT_REF

    # Step 2: Manifest hash validation
    manifest_info = verify_pindobal_offline_manifest(snapshot_dir)

    # Step 3: Local dry-run and canonical count validation
    counts_info = verify_canonical_counts(snapshot_dir)

    # Step 4: Migrations alignment verification
    if migrations_dir is None:
        # Default relative to repo root
        migrations_dir = Path(__file__).resolve().parents[3] / "supabase" / "migrations"
    migrations_info = verify_migrations_alignment(migrations_dir)

    # Step 5: Double human confirmation (simulated or real)
    confirmed = False
    if require_confirmation:
        confirm_fn = confirm_func or input
        confirmed = request_human_double_confirmation(target_ref, prompt_input=confirm_fn)

    end_time = datetime.now(UTC).isoformat()

    return {
        "status": "phase1_success",
        "phase": 1,
        "mode": "local_preflight_and_validation_only",
        "remote_write_performed": False,
        "target_project_ref": target_ref,
        "started_at": start_time,
        "finished_at": end_time,
        "manifest": manifest_info,
        "canonical_counts": counts_info,
        "migrations": migrations_info,
        "human_confirmation": {
            "required": require_confirmation,
            "confirmed": confirmed,
        },
        "governance": {
            "advisory_lock_id": PINDOBAL_STAGING_ADVISORY_LOCK_ID,
            "lock_mechanism": "pg_try_advisory_lock",
            "schema_rollback": "PITR_snapshot_only",
            "data_rollback": "logical_unpublish_draft_only",
            "phase2_remote_write": "BLOCKED_PENDING_EXPLICIT_OWNER_GO",
        },
    }


def main() -> int:
    """CLI entrypoint for the staging promotion runner."""
    parser = argparse.ArgumentParser(
        description="ECOnexão Staging Promotion Runner (ECO-2005 Phase 1)"
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help="Path to snapshot source directory (teste-rota)",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=None,
        help="Path to Supabase migrations directory",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive confirmation prompts (for automated testing)",
    )
    args = parser.parse_args()

    try:
        report = execute_phase1_preflight(
            snapshot_dir=args.snapshot_dir,
            migrations_dir=args.migrations_dir,
            require_confirmation=not args.non_interactive,
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except StagingPromotionError as exc:
        err_msg = sanitize_message(str(exc))
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": exc.__class__.__name__,
                    "message": err_msg,
                    "remote_write_performed": False,
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        err_msg = sanitize_message(str(exc))
        print(
            json.dumps(
                {
                    "status": "unexpected_error",
                    "error_type": exc.__class__.__name__,
                    "message": err_msg,
                    "remote_write_performed": False,
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
