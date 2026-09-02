"""Staging promotion runner for Pindobal territorial slice (ECO-2005).

Ensures fail-closed target isolation (staging ref kchzucvrnzwzehfdwzwi only),
offline preflight validation, double human confirmation, non-blocking
pg_try_advisory_xact_lock concurrency control with atomic transaction ownership,
and logical rollback governance.
Remote write execution is strictly prohibited during Phase 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import AsyncGenerator, Callable, Sequence
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
PROJECT_REF_PATTERN = re.compile(r"^[a-z0-9]{20}$")
DIRECT_HOST_PATTERN = re.compile(r"^db\.([a-z0-9]{20})\.supabase\.co$")
POOLER_USER_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+\.([a-z0-9]{20})$")
POOLER_HOST_PATTERN = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)*\.pooler\.supabase\.com$")
MIGRATION_FILENAME_PATTERN = re.compile(r"^(\d{14})_[a-z0-9_]+\.sql$")

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


class EarlyCommitProhibitedError(StagingPromotionError):
    """Prohibited early commit or transaction tampering within protected lock context."""


def sanitize_message(text_content: str) -> str:
    """Mask credentials, passwords, tokens, and sensitive headers from messages and logs."""
    if not text_content:
        return ""
    # 1. Mask DSN credentials: ://user:pass@ -> ://[REDACTED_USER]:[REDACTED_PASSWORD]@
    sanitized = re.sub(
        r"://([^:@\s]+):([^@\s]+)@",
        r"://[REDACTED_USER]:[REDACTED_PASSWORD]@",
        text_content,
    )
    # 2. Mask query parameters: ?key=value or &key=value for sensitive keys
    sanitized = re.sub(
        r"(?i)([?&](?:apikey|token|password|secret|key)=)[^&\s'\",]+",
        r"\1[REDACTED]",
        sanitized,
    )
    # 3. Mask Supabase Secret Keys: sb_secret_...
    sanitized = re.sub(r"\bsb_secret_[a-zA-Z0-9_-]+\b", "[REDACTED_SECRET]", sanitized)
    # 4. Mask Supabase Publishable Keys: sb_publishable_...
    sanitized = re.sub(
        r"\bsb_publishable_[a-zA-Z0-9_-]+\b", "[REDACTED_PUBLISHABLE]", sanitized
    )
    # 5. Mask Supabase Management / Personal Tokens: sbp_...
    sanitized = re.sub(r"\bsbp_[a-zA-Z0-9_-]+\b", "[REDACTED_SBP]", sanitized)
    # 6. Mask JWTs (RFC 7519 3-part base64url)
    sanitized = re.sub(
        r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b",
        "[REDACTED_JWT]",
        sanitized,
    )
    # 7. Mask Authorization / Bearer headers entirely
    sanitized = re.sub(
        r"(?i)\b(?:Authorization:\s*Bearer|Bearer)\s+[^\s'\",]+",
        "[REDACTED_AUTH]",
        sanitized,
    )
    # 8. Mask key-value pairs (e.g. password=xyz, secret: "abc")
    sanitized = re.sub(
        r"(?i)\b(password|passwd|secret|token|api_key|apikey)\b\s*[:=]\s*['\"]?([^\s,'\"]+)['\"]?",
        r"\1=[REDACTED]",
        sanitized,
    )
    return sanitized


def validate_target_project_ref(project_ref: str | None) -> str:
    """Ensure project ref matches canonical staging ref and fail closed otherwise."""
    cleaned = (project_ref or "").strip().lower()
    if not cleaned:
        raise TargetValidationError("Project ref não pode ser vazio.")
    if not PROJECT_REF_PATTERN.fullmatch(cleaned):
        raise TargetValidationError(
            "Formato de project ref inválido. Deve conter 20 caracteres alfanuméricos minúsculos."
        )
    if cleaned != CANONICAL_STAGING_PROJECT_REF:
        raise TargetValidationError(
            f"Target '{cleaned}' não autorizado para promoção staging. "
            f"Target obrigatório: '{CANONICAL_STAGING_PROJECT_REF}'."
        )
    return cleaned


def _extract_raw_ref_from_supabase_url(url: str | None) -> str:
    """Extract raw project ref from Supabase REST URL without validating against allowlist."""
    cleaned = (url or "").strip()
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.hostname:
        raise TargetValidationError("SUPABASE_URL inválida. Deve utilizar o esquema https://.")
    parts = parsed.hostname.split(".")
    if len(parts) != 3 or parts[1:] != ["supabase", "co"]:
        raise TargetValidationError(
            "SUPABASE_URL não corresponde a um projeto gerenciado (*.supabase.co)."
        )
    ref = parts[0].lower()
    if not PROJECT_REF_PATTERN.fullmatch(ref):
        raise TargetValidationError(
            "Formato de project ref na SUPABASE_URL inválido."
        )
    return ref


def extract_ref_from_supabase_url(url: str | None) -> str:
    """Extract and validate project ref from Supabase REST URL."""
    raw_ref = _extract_raw_ref_from_supabase_url(url)
    return validate_target_project_ref(raw_ref)


def _extract_raw_ref_from_database_url(url: str | None) -> str:
    """Extract raw project ref from DATABASE_URL without validating against allowlist."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise TargetValidationError("DATABASE_URL não informada ou vazia.")
    try:
        db_url = make_url(cleaned)
    except Exception as exc:
        raise TargetValidationError(
            "DATABASE_URL inválida ou malformada (falha ao analisar DSN)."
        ) from exc

    if db_url.drivername not in {
        "postgres",
        "postgresql",
        "postgresql+psycopg",
        "postgresql+asyncpg",
    }:
        raise TargetValidationError(
            "Driver não suportado. Utilize postgresql, postgresql+psycopg ou postgresql+asyncpg."
        )

    # Validate port: strictly reject 6543 (transaction pooler)
    port = db_url.port
    if port == 6543:
        raise TargetValidationError(
            "Porta 6543 (Supavisor transaction pooler) não é permitida para promoção staging. "
            "Utilize a porta 5432 (conexão direta ou session pooler)."
        )
    if port is not None and port != 5432:
        raise TargetValidationError(
            f"Porta de banco de dados {port} não suportada. A promoção exige a porta 5432."
        )

    host = (db_url.host or "").lower()
    username = db_url.username or ""

    # Direct connection: db.<ref>.supabase.co:5432
    direct_match = DIRECT_HOST_PATTERN.fullmatch(host)
    if direct_match:
        return direct_match.group(1).lower()

    # Pooler session mode connection: user.<ref>@*.pooler.supabase.com:5432
    pooler_match = POOLER_USER_PATTERN.fullmatch(username)
    if (
        pooler_match
        and host.endswith(".pooler.supabase.com")
        and POOLER_HOST_PATTERN.fullmatch(host)
    ):
        return pooler_match.group(1).lower()

    raise TargetValidationError(
        "DATABASE_URL não corresponde ao padrão Supabase direto (db.<ref>.supabase.co:5432) "
        "nem ao session pooler (<user>.<ref>@*.pooler.supabase.com:5432)."
    )


def extract_ref_from_database_url(url: str | None) -> str:
    """Extract and validate project ref from DB host or Supavisor pooler string."""
    raw_ref = _extract_raw_ref_from_database_url(url)
    return validate_target_project_ref(raw_ref)


def validate_environment_config(env_values: dict[str, str]) -> str:
    """Cross-validate APP_ENV, SUPABASE_URL, and DATABASE_URL for staging isolation."""
    raw_app_env = env_values.get("APP_ENV")
    raw_supabase_url = env_values.get("SUPABASE_URL")
    raw_database_url = env_values.get("DATABASE_URL")

    if not raw_app_env or not raw_supabase_url or not raw_database_url:
        raise TargetValidationError(
            "Configuração remota incompleta: APP_ENV, SUPABASE_URL e DATABASE_URL são obrigatórios "
            "para validação de ambiente."
        )

    app_env = raw_app_env.strip().lower()
    if app_env != "staging":
        raise TargetValidationError(
            f"APP_ENV inválido: '{app_env}'. O runner exige estritamente 'staging'."
        )

    raw_supabase_ref = _extract_raw_ref_from_supabase_url(raw_supabase_url)
    raw_database_ref = _extract_raw_ref_from_database_url(raw_database_url)

    if raw_supabase_ref != raw_database_ref:
        raise TargetValidationError(
            "Divergência de project ref entre SUPABASE_URL e DATABASE_URL."
        )

    return validate_target_project_ref(raw_supabase_ref)


class LockedAsyncSessionProxy:
    """Helper guard to reduce accidental transaction mismanagement within the locked context.

    Note: In Python, this proxy is an accidental-misuse guard, not a security boundary
    or guarantee of isolation. Atomicity is achieved by the architectural boundary
    of a single Unit of Work owning the transaction lifecycle (begin, advisory lock,
    operations, commit/rollback).
    """

    def __init__(self, session: AsyncSession) -> None:
        object.__setattr__(self, "_session", session)

    async def commit(self) -> None:
        raise EarlyCommitProhibitedError(
            "Chamada a commit() dentro do bloco sob advisory lock é proibida. "
            "A transação é controlada pela Unit of Work proprietária."
        )

    async def rollback(self) -> None:
        raise EarlyCommitProhibitedError(
            "Chamada a rollback() dentro do bloco sob advisory lock é proibida. "
            "Lance uma exceção para que a Unit of Work proprietária aborte a transação."
        )

    def begin(self, *args: Any, **kwargs: Any) -> Any:
        raise EarlyCommitProhibitedError(
            "Abertura de transação aninhada é proibida dentro do bloco sob advisory lock. "
            "A persistência deve operar sob a transação já ativa da Unit of Work."
        )

    def in_transaction(self) -> bool:
        return bool(self._session.in_transaction())

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._session, name, value)


@asynccontextmanager
async def staging_atomic_lock_transaction(
    session: AsyncSession,
    lock_id: int = PINDOBAL_STAGING_ADVISORY_LOCK_ID,
) -> AsyncGenerator[LockedAsyncSessionProxy]:
    """Single Unit of Work context manager owning the transaction and advisory lock.

    Architecture:
    - Exactly one transaction owner: opens transaction via session.begin()
    - Acquires pg_try_advisory_xact_lock as first query
    - Yields session proxy (accidental-misuse helper)
    - Automatically releases lock on transaction commit/rollback or disconnect via PostgreSQL
      ResourceOwner
    - Post-execution State Guard asserts session was not prematurely closed
    - Single commit upon clean exit, rollback upon exception
    """
    if session.in_transaction():
        raise StagingPromotionError(
            "A sessão já possui uma transação ativa. "
            "staging_atomic_lock_transaction exige ser a proprietária exclusiva da transação."
        )

    async with session.begin():
        # First query in transaction: non-blocking acquisition of transaction-level lock
        lock_query = select(func.pg_try_advisory_xact_lock(lock_id))
        result = await session.execute(lock_query)
        acquired = bool(result.scalar_one())

        if not acquired:
            raise AdvisoryLockBusyError(
                f"Advisory xact lock {lock_id} está ocupado por outro processo em staging. "
                "A promoção foi abortada sem bloqueio indefinido."
            )

        proxy = LockedAsyncSessionProxy(session)
        yield proxy

        # State Guard: verify transaction was not prematurely closed
        if not session.in_transaction():
            raise EarlyCommitProhibitedError(
                "A transação foi encerrada indevidamente antes da conclusão pelo runner."
            )


# Compatibility alias for existing callers
staging_advisory_lock = staging_atomic_lock_transaction


CANONICAL_MANIFEST_PATH: Path = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "finalization"
    / "artifacts"
    / "staging_migrations_manifest.json"
)


def validate_manifest_structure(manifest_data: dict[str, Any]) -> None:
    """Validate schema and structural integrity of the migrations manifest."""
    if not isinstance(manifest_data, dict):
        raise PreflightVerificationError("Manifesto de migrations deve ser um objeto JSON.")

    schema_version = manifest_data.get("schema_version")
    if schema_version != 1:
        raise PreflightVerificationError(
            f"Versão de schema de manifesto não suportada: {schema_version}. Suportada: 1."
        )

    total_migrations = manifest_data.get("total_migrations")
    if not isinstance(total_migrations, int) or total_migrations <= 0:
        raise PreflightVerificationError(
            f"Campo total_migrations inválido no manifesto: {total_migrations}."
        )

    migrations = manifest_data.get("migrations")
    if not isinstance(migrations, list):
        raise PreflightVerificationError(
            "Campo migrations inválido no manifesto: deve ser uma lista."
        )

    if len(migrations) != total_migrations:
        raise PreflightVerificationError(
            f"Incoerência no manifesto: total_migrations={total_migrations}, "
            f"mas a lista migrations contém {len(migrations)} itens."
        )

    required_fields = {"version", "filename", "path", "bytes", "sha256"}
    seen_versions: set[str] = set()

    for idx, entry in enumerate(migrations):
        if not isinstance(entry, dict):
            raise PreflightVerificationError(
                f"Item {idx + 1} de migrations no manifesto deve ser um objeto."
            )

        missing = required_fields - entry.keys()
        if missing:
            raise PreflightVerificationError(
                f"Item {idx + 1} ({entry.get('filename', '?')}) no manifesto sem campos: "
                f"{sorted(missing)}."
            )

        version = str(entry["version"])
        if not re.fullmatch(r"^\d{14}$", version):
            raise PreflightVerificationError(
                f"Versão inválida no manifesto (item {idx + 1}): '{version}'. Deve ter 14 dígitos."
            )
        if version in seen_versions:
            raise PreflightVerificationError(
                f"Versão duplicada no manifesto: '{version}'."
            )
        seen_versions.add(version)

        filename = str(entry["filename"])
        if not filename.startswith(f"{version}_") or not filename.endswith(".sql"):
            raise PreflightVerificationError(
                f"Incoerência entre version '{version}' e filename '{filename}' no manifesto."
            )

        expected_path = f"supabase/migrations/{filename}"
        if entry["path"] != expected_path:
            raise PreflightVerificationError(
                f"Incoerência de path no manifesto para '{filename}': "
                f"esperava '{expected_path}', obteve '{entry['path']}'."
            )

        file_bytes = entry["bytes"]
        if not isinstance(file_bytes, int) or file_bytes <= 0:
            raise PreflightVerificationError(
                f"Tamanho em bytes inválido no manifesto para '{filename}': {file_bytes}."
            )

        sha256 = str(entry["sha256"]).lower()
        if not re.fullmatch(r"^[0-9a-f]{64}$", sha256):
            raise PreflightVerificationError(
                f"Hash SHA-256 inválido no manifesto para '{filename}': '{entry['sha256']}'. "
                "Deve conter exatamente 64 caracteres hexadecimais minúsculos."
            )


def load_canonical_migrations_manifest(
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Load and validate the single normative migrations manifest."""
    target_path = manifest_path or CANONICAL_MANIFEST_PATH
    if not target_path.is_file():
        raise PreflightVerificationError(
            f"Manifesto canônico de migrations não encontrado na fonte normativa: {target_path}."
        )

    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreflightVerificationError(
            f"Falha ao ler JSON do manifesto canônico de migrations: {exc}"
        ) from exc

    validate_manifest_structure(data)
    return data  # type: ignore[no-any-return]


def verify_migrations_alignment(migrations_dir: Path) -> dict[str, Any]:
    """Inspect local migrations directory to verify strict alignment against baseline manifest."""
    if not migrations_dir.is_dir():
        raise PreflightVerificationError(
            f"Diretório de migrations não encontrado: {migrations_dir}"
        )

    manifest_data = load_canonical_migrations_manifest()
    expected_entries = manifest_data.get("migrations", [])
    expected_count = manifest_data.get("total_migrations", CANONICAL_MIGRATIONS_COUNT)

    sql_files = sorted(migrations_dir.glob("*.sql"), key=lambda f: f.name)

    if len(sql_files) != expected_count:
        raise PreflightVerificationError(
            f"Quantidade de migrations local divergente: esperado {expected_count}, "
            f"encontrado {len(sql_files)}."
        )

    # 1. Validate timestamp formats, uniqueness, and monotonic ordering
    versions: list[str] = []
    for f in sql_files:
        match = MIGRATION_FILENAME_PATTERN.fullmatch(f.name)
        if not match:
            raise PreflightVerificationError(
                f"Nome de migration fora do padrão YYYYMMDDHHMMSS_<name>.sql: '{f.name}'."
            )
        version = match.group(1)
        if version in versions:
            raise PreflightVerificationError(
                f"Duplicidade de versão detectada: '{version}' em '{f.name}'."
            )
        if versions and version < versions[-1]:
            raise PreflightVerificationError(
                f"Migrations fora de ordem cronológica: '{f.name}' sucede '{versions[-1]}'."
            )
        versions.append(version)

    # 2. Validate 1-to-1 match against baseline manifest
    for idx, (sql_file, expected) in enumerate(zip(sql_files, expected_entries, strict=True)):
        expected_name = expected["filename"]
        if sql_file.name != expected_name:
            raise PreflightVerificationError(
                f"Migration inesperada ou renomeada na posição {idx + 1}: "
                f"esperava '{expected_name}', encontrou '{sql_file.name}'."
            )

        file_bytes = sql_file.read_bytes()
        actual_size = len(file_bytes)
        expected_size = expected["bytes"]
        if actual_size != expected_size:
            raise PreflightVerificationError(
                f"Tamanho divergente na migration '{sql_file.name}': "
                f"esperado {expected_size} bytes, obtido {actual_size} bytes."
            )

        actual_hash = hashlib.sha256(file_bytes).hexdigest()
        expected_hash = expected["sha256"]
        if actual_hash != expected_hash:
            raise PreflightVerificationError(
                f"Hash SHA-256 divergente na migration '{sql_file.name}': "
                f"esperado {expected_hash}, obtido {actual_hash}."
            )

    return {
        "status": "aligned_locally",
        "scope": "local_directory_only",
        "count": len(sql_files),
        "first_migration": sql_files[0].name,
        "latest_migration": sql_files[-1].name,
        "baseline_ref": manifest_data.get("baseline_ref", "origin/staging"),
        "manifest_verified": True,
        "remote_drift_and_advisors_check": "deferred_to_phase2_preflight",
    }


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


def execute_phase1_preflight(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    migrations_dir: Path | None = None,
    target_project_ref: str | None = None,
    env_values: dict[str, str] | None = None,
    confirm_func: Callable[[str], str] | None = None,
    require_confirmation: bool = True,
) -> dict[str, Any]:
    """Execute Phase 1: offline and read-only preflight verification without remote writes."""
    start_time = datetime.now(UTC).isoformat()

    # Step 1: Environment and target validation
    validated_target: str | None = None
    remote_config_status: dict[str, Any]

    has_env_vars = env_values and any(
        k in env_values for k in ("APP_ENV", "SUPABASE_URL", "DATABASE_URL")
    )

    if has_env_vars:
        assert env_values is not None
        ref_from_env = validate_environment_config(env_values)
        if target_project_ref is not None:
            explicit_ref = validate_target_project_ref(target_project_ref)
            if explicit_ref != ref_from_env:
                raise TargetValidationError(
                    f"Divergência entre --target-project-ref ('{explicit_ref}') "
                    f"e configuração de ambiente ('{ref_from_env}')."
                )
        validated_target = ref_from_env
        remote_config_status = {
            "validated": True,
            "status": "validated_staging",
            "project_ref": validated_target,
        }
    elif target_project_ref is not None:
        validated_target = validate_target_project_ref(target_project_ref)
        remote_config_status = {
            "validated": False,
            "status": "offline_dry_run_explicit_target_only",
            "details": (
                "Target project ref fornecido explicitamente, mas URLs remotas não foram validadas."
            ),
            "project_ref": validated_target,
        }
    else:
        validated_target = None
        remote_config_status = {
            "validated": False,
            "status": "offline_dry_run_no_remote_config_validated",
            "details": (
                "Nenhuma configuração remota foi fornecida ou validada no modo dry-run offline."
            ),
        }

    # Fail fast if human confirmation was requested but no target ref was provided
    if require_confirmation and validated_target is None:
        raise TargetValidationError(
            "Confirmação humana exige um target_project_ref explícito ou ambiente válido."
        )

    # Step 2: Manifest hash validation
    manifest_info = verify_pindobal_offline_manifest(snapshot_dir)

    # Step 3: Local dry-run and canonical count validation
    counts_info = verify_canonical_counts(snapshot_dir)

    # Step 4: Migrations alignment verification against origin/staging baseline
    if migrations_dir is None:
        migrations_dir = Path(__file__).resolve().parents[3] / "supabase" / "migrations"
    migrations_info = verify_migrations_alignment(migrations_dir)

    # Step 5: Double human confirmation (if requested)
    confirmed = False
    if require_confirmation:
        assert validated_target is not None
        confirm_fn = confirm_func or input
        confirmed = request_human_double_confirmation(validated_target, prompt_input=confirm_fn)

    end_time = datetime.now(UTC).isoformat()

    return {
        "status": "phase1_success",
        "phase": 1,
        "mode": "local_preflight_and_validation_only",
        "remote_write_performed": False,
        "target_project_ref": validated_target,
        "remote_configuration": remote_config_status,
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
            "lock_mechanism": "pg_try_advisory_xact_lock",
            "transaction_ownership": "single_unit_of_work_transaction",
            "lock_release_guarantee": (
                "postgresql_server_resource_owner_on_disconnect_or_termination"
            ),
            "schema_rollback": "PITR_snapshot_only",
            "data_rollback": "logical_unpublish_draft_only",
            "phase2_remote_write": "BLOCKED_PENDING_EXPLICIT_OWNER_GO",
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for the staging promotion runner."""
    # Ensure stdout/stderr emit valid UTF-8 across Windows consoles
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

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
        "--target-project-ref",
        type=str,
        default=None,
        help="Target Supabase project ref (staging allowlist: kchzucvrnzwzehfdwzwi)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Phase 1 offline preflight only: skip prompts (prohibited for write)",
    )
    args = parser.parse_args(argv)

    try:
        # Check environment variables without loading arbitrary .env files
        import os

        env_keys = ("APP_ENV", "SUPABASE_URL", "DATABASE_URL")
        env_values: dict[str, str] | None = None
        if any(k in os.environ for k in env_keys):
            env_values = {k: os.environ.get(k, "") for k in env_keys}

        report = execute_phase1_preflight(
            snapshot_dir=args.snapshot_dir,
            migrations_dir=args.migrations_dir,
            target_project_ref=args.target_project_ref,
            env_values=env_values,
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
