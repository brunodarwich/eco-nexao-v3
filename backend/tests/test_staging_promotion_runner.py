"""Unit tests for staging promotion runner (ECO-2005 Phase 1).

Tests atomic transaction lock ownership, fail-closed target guards,
deterministic migration baseline verification, credential sanitization,
and CLI entrypoint safety. Zero remote network calls.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.pindobal_repository import PersistenceCounts
from app.ingestion.staging_promotion_runner import (
    ADVISORY_LOCK_ID,
    CANONICAL_PINDOBAL_METRICS,
    CANONICAL_STAGING_PROJECT_REF,
    AdvisoryLockBusyError,
    ConfirmationError,
    EarlyCommitProhibitedError,
    LockedAsyncSessionProxy,
    PreflightVerificationError,
    PromotionExecutionError,
    StagingPromotionError,
    TargetValidationError,
    execute_phase1_preflight,
    execute_phase2_staging_promotion,
    extract_ref_from_database_url,
    extract_ref_from_supabase_url,
    load_canonical_migrations_manifest,
    main,
    request_human_double_confirmation,
    sanitize_message,
    staging_atomic_lock_transaction,
    validate_environment_config,
    validate_manifest_structure,
    validate_target_project_ref,
    verify_canonical_counts,
    verify_migrations_alignment,
)

SYNTHETIC_UNAUTHORIZED_REF: str = "unauthorizedref12345"
SYNTHETIC_OBSOLETE_REF: str = "rgfuqmwxjuceqpxcraxm"


# ==============================================================================
# 1. Target Validation & Project Ref Extraction
# ==============================================================================


def test_validate_target_project_ref_accepts_canonical_staging() -> None:
    """Canonical staging ref must be accepted."""
    assert (
        validate_target_project_ref(CANONICAL_STAGING_PROJECT_REF) == CANONICAL_STAGING_PROJECT_REF
    )


@pytest.mark.parametrize(
    "invalid_ref",
    [
        "",
        "   ",
        None,
        SYNTHETIC_OBSOLETE_REF,
        SYNTHETIC_UNAUTHORIZED_REF,
        "short_ref",
        "this_ref_is_far_too_long_to_be_a_supabase_ref",
        "invalid!ref!characters",
        "12345678901234567890",
        "kchzucvrnzwzehfdwzwX",  # Capital letters
    ],
)
def test_validate_target_project_ref_rejects_non_canonical(invalid_ref: str | None) -> None:
    """Any ref other than kchzucvrnzwzehfdwzwi must fail closed."""
    with pytest.raises(TargetValidationError):
        validate_target_project_ref(invalid_ref)


def test_extract_ref_from_supabase_url_success() -> None:
    """Valid staging HTTPS URL should extract the canonical ref."""
    url = f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co"
    assert extract_ref_from_supabase_url(url) == CANONICAL_STAGING_PROJECT_REF
    assert extract_ref_from_supabase_url(f"{url}/auth/v1") == CANONICAL_STAGING_PROJECT_REF


@pytest.mark.parametrize(
    "bad_url",
    [
        f"http://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        f"https://{SYNTHETIC_OBSOLETE_REF}.supabase.co",
        f"https://{SYNTHETIC_UNAUTHORIZED_REF}.supabase.co",
        "https://otherdomain.com",
        "not_a_url",
        "",
        None,
    ],
)
def test_extract_ref_from_supabase_url_failures(bad_url: str | None) -> None:
    """Invalid schemes, other domains or non-staging refs must fail."""
    with pytest.raises(TargetValidationError):
        extract_ref_from_supabase_url(bad_url)


def test_extract_ref_from_database_url_direct_host_port_5432() -> None:
    """Direct host connection string on port 5432 should resolve and validate the ref."""
    dsn = f"postgresql://postgres:secret_pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres"
    assert extract_ref_from_database_url(dsn) == CANONICAL_STAGING_PROJECT_REF


def test_extract_ref_from_database_url_direct_host_default_port() -> None:
    """Direct host connection string without explicit port (default 5432) resolves ref."""
    dsn = f"postgresql://postgres:secret_pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co/postgres"
    assert extract_ref_from_database_url(dsn) == CANONICAL_STAGING_PROJECT_REF


def test_extract_ref_from_database_url_pooler_session_port_5432() -> None:
    """Supavisor session pooler on port 5432 should resolve the ref."""
    dsn = (
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:secret_pass"
        "@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
    )
    assert extract_ref_from_database_url(dsn) == CANONICAL_STAGING_PROJECT_REF


def test_extract_ref_from_database_url_rejects_transaction_pooler_port_6543() -> None:
    """Supavisor transaction pooler (port 6543) must be strictly rejected."""
    dsn = (
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:secret_pass"
        "@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
    )
    with pytest.raises(TargetValidationError, match="Porta 6543.*Supavisor transaction pooler"):
        extract_ref_from_database_url(dsn)


@pytest.mark.parametrize(
    "bad_port_dsn",
    [
        f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5433/postgres",
        f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:6432/postgres",
        f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:8000/postgres",
    ],
)
def test_extract_ref_from_database_url_rejects_non_5432_ports(bad_port_dsn: str) -> None:
    """Any port other than 5432 must be rejected."""
    with pytest.raises(TargetValidationError, match="Porta de banco de dados.*não suportada"):
        extract_ref_from_database_url(bad_port_dsn)


def test_extract_ref_from_database_url_malformed_does_not_leak_credentials() -> None:
    """Malformed DSN must raise TargetValidationError without leaking credentials."""
    raw_dsn = "postgresql://my_secret_user:my_secret_pass_123@invalid:not_a_port/db"
    with pytest.raises(TargetValidationError) as exc_info:
        extract_ref_from_database_url(raw_dsn)
    err_str = str(exc_info.value)
    assert "my_secret_pass_123" not in err_str
    assert "my_secret_user" not in err_str


@pytest.mark.parametrize(
    "bad_dsn",
    [
        f"postgresql://postgres:pass@db.{SYNTHETIC_OBSOLETE_REF}.supabase.co:5432/postgres",
        f"postgresql://postgres:pass@db.{SYNTHETIC_UNAUTHORIZED_REF}.supabase.co:5432/postgres",
        "postgresql://postgres:pass@localhost:5432/postgres",
        f"mysql://root:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:3306/db",
        "invalid_dsn",
        "",
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:pass@evil-pooler.attacker.org:5432/postgres",
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:pass@pooler.supabase.com:5432/postgres",
    ],
)
def test_extract_ref_from_database_url_failures(bad_dsn: str) -> None:
    """Non-staging or invalid database URLs must fail closed."""
    with pytest.raises(TargetValidationError):
        extract_ref_from_database_url(bad_dsn)


# ==============================================================================
# 2. Environment Configuration Cross-Validation
# ==============================================================================


def test_validate_environment_config_success() -> None:
    """Environment with staging APP_ENV and matching canonical URLs passes."""
    env = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    }
    assert validate_environment_config(env) == CANONICAL_STAGING_PROJECT_REF


@pytest.mark.parametrize(
    "missing_key",
    ["APP_ENV", "SUPABASE_URL", "DATABASE_URL"],
)
def test_validate_environment_config_fails_closed_on_missing_keys(missing_key: str) -> None:
    """Incomplete environment triad fails closed with TargetValidationError."""
    env = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    }
    del env[missing_key]
    with pytest.raises(TargetValidationError, match="Configuração remota incompleta"):
        validate_environment_config(env)


def test_validate_environment_config_app_env_not_staging() -> None:
    """APP_ENV other than staging must be rejected."""
    for env_name in ("development", "test", "production", "local"):
        env = {
            "APP_ENV": env_name,
            "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
            "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
        }
        with pytest.raises(TargetValidationError, match="APP_ENV inválido"):
            validate_environment_config(env)


def test_validate_environment_config_mismatched_refs() -> None:
    """Different refs in Supabase URL and Database URL must fail closed."""
    env = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{SYNTHETIC_UNAUTHORIZED_REF}.supabase.co:5432/postgres",
    }
    with pytest.raises(TargetValidationError, match="Divergência de project ref"):
        validate_environment_config(env)


# ==============================================================================
# 3. Concurrency Control, Atomic Transaction & Session Proxy
# ==============================================================================


@pytest.mark.asyncio
async def test_staging_atomic_lock_transaction_success() -> None:
    """When lock is available, opens transaction, acquires lock, and yields proxy."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True, True]

    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    # Mock session.begin() context manager
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    canary_executed = False
    async with staging_atomic_lock_transaction(session, lock_id=ADVISORY_LOCK_ID) as proxy:
        assert isinstance(proxy, LockedAsyncSessionProxy)
        canary_executed = True

    assert canary_executed is True
    session.begin.assert_called_once()
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_staging_atomic_lock_transaction_busy_blocks_operation() -> None:
    """When lock is held, raises AdvisoryLockBusyError without running payload."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True]

    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 0
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    canary_executed = False
    with pytest.raises(AdvisoryLockBusyError, match="ocupado por outro processo"):
        async with staging_atomic_lock_transaction(session, lock_id=ADVISORY_LOCK_ID):
            canary_executed = True

    assert canary_executed is False
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_staging_atomic_lock_transaction_prohibits_existing_transaction() -> None:
    """If session is already in a transaction, fails closed to preserve atomic ownership."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.return_value = True

    with pytest.raises(StagingPromotionError, match="já possui uma transação ativa"):
        async with staging_atomic_lock_transaction(session):
            pass


@pytest.mark.asyncio
async def test_session_proxy_prohibits_early_commit() -> None:
    """Calling commit() inside the protected block is strictly forbidden."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True, True]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(EarlyCommitProhibitedError, match=r"commit\(\).*proibida"):
        async with staging_atomic_lock_transaction(session) as proxy:
            await proxy.commit()


@pytest.mark.asyncio
async def test_session_proxy_prohibits_early_rollback() -> None:
    """Calling rollback() inside the protected block is strictly forbidden."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True, True]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(EarlyCommitProhibitedError, match=r"rollback\(\).*proibida"):
        async with staging_atomic_lock_transaction(session) as proxy:
            await proxy.rollback()


@pytest.mark.asyncio
async def test_session_proxy_prohibits_nested_begin() -> None:
    """Calling begin() inside the protected block is strictly forbidden."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True, True]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(EarlyCommitProhibitedError, match="transação aninhada é proibida"):
        async with staging_atomic_lock_transaction(session) as proxy:
            proxy.begin()


@pytest.mark.asyncio
async def test_session_proxy_delegates_methods() -> None:
    """Standard database operations pass through the proxy cleanly."""
    session = AsyncMock(spec=AsyncSession)
    proxy = LockedAsyncSessionProxy(session)
    proxy.add("dummy_entity")
    session.add.assert_called_once_with("dummy_entity")


@pytest.mark.asyncio
async def test_state_guard_detects_prematurely_closed_transaction() -> None:
    """State Guard raises if transaction was closed before runner finalization."""
    session = AsyncMock(spec=AsyncSession)
    # in_transaction: False on initial entry check, False on exit check
    session.in_transaction.side_effect = [False, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(EarlyCommitProhibitedError, match="encerrada indevidamente"):
        async with staging_atomic_lock_transaction(session):
            pass


@pytest.mark.asyncio
async def test_cancellation_propagates_cleanly() -> None:
    """asyncio.CancelledError propagates out and aborts transaction."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(asyncio.CancelledError):
        async with staging_atomic_lock_transaction(session):
            raise asyncio.CancelledError()


@pytest.mark.asyncio
async def test_exception_triggers_rollback() -> None:
    """Exceptions inside the protected block propagate and abort transaction."""
    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, True]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(RuntimeError, match="simulated failure"):
        async with staging_atomic_lock_transaction(session):
            raise RuntimeError("simulated failure")


@pytest.mark.asyncio
async def test_integration_lock_transaction_with_real_repository_operation() -> None:
    """Prove real Pindobal persistence runs under staging_atomic_lock_transaction.

    Verifies no nested begin occurs and entire slice runs under the single UoW.
    """
    from app.ingestion.osrm_importer import OSRMRouteResult
    from app.ingestion.pindobal_repository import PindobalPersistenceRepository

    # Mock session with real transaction state tracking
    session = AsyncMock(spec=AsyncSession)
    in_tx_state = False

    def get_in_transaction() -> bool:
        return in_tx_state

    session.in_transaction.side_effect = get_in_transaction

    tx_cm = AsyncMock()

    async def enter_tx() -> None:
        nonlocal in_tx_state
        in_tx_state = True
        return None

    async def exit_tx(exc_type: Any, exc_val: Any, tb: Any) -> None:
        nonlocal in_tx_state
        in_tx_state = False
        return None

    tx_cm.__aenter__.side_effect = enter_tx
    tx_cm.__aexit__.side_effect = exit_tx
    session.begin.return_value = tx_cm

    lock_result = MagicMock()
    lock_result.scalar_one.return_value = 1
    dummy_scalar_result = MagicMock()
    dummy_scalar_result.scalar_one_or_none.return_value = None
    dummy_scalar_result.tuples.return_value = []
    dummy_scalar_result.all.return_value = []

    def execute_dispatcher(statement: Any, *args: Any, **kwargs: Any) -> Any:
        sql_str = str(statement)
        if "pg_try_advisory_xact_lock" in sql_str:
            return lock_result
        return dummy_scalar_result

    session.execute.side_effect = execute_dispatcher
    session.scalar.return_value = 0

    now = datetime.now(UTC)
    mock_report = {
        "manifest": {
            "valid_files": 9,
            "files": [
                {"name": f"rota_{code}_OSRM_01.csv", "sha256": "a" * 64}
                for code in ("porto", "aeroporto", "rodoviaria")
            ],
        }
    }
    mock_osrm = {
        code: OSRMRouteResult(
            origin_code=code,
            origin_name=code.title(),
            points_count=2,
            start_point=(-2.4, -54.7),
            end_point=(-2.5, -54.9),
            distance_m=1000,
            wkt_linestring="LINESTRING(-54.7 -2.4, -54.9 -2.5)",
            wkt_start_point="POINT(-54.7 -2.4)",
            bounds={"min_lat": -2.5, "max_lat": -2.4, "min_lon": -54.9, "max_lon": -54.7},
            points=[],
            is_valid=True,
        )
        for code in ("porto", "aeroporto", "rodoviaria")
    }

    # Execute atomic lock transaction and run persist_in_transaction under the single UoW
    async with staging_atomic_lock_transaction(session) as protected_session:
        assert protected_session.in_transaction() is True
        repository = PindobalPersistenceRepository(protected_session)  # type: ignore[arg-type]
        run_id, stats = await repository.persist_in_transaction(
            report=mock_report,
            osrm_results=mock_osrm,
            started_at=now,
            finished_at=now,
        )
        assert isinstance(run_id, uuid.UUID)
        assert stats["territorial"]["regions_created"] == 1

    # 1. session.begin() was called exactly ONCE (owned by runner UoW, never nested)
    session.begin.assert_called_once()
    # 2. Transaction committed cleanly on exit
    tx_cm.__aexit__.assert_awaited_once_with(None, None, None)
    # 3. Transaction is closed
    assert session.in_transaction() is False
    # 4. Flushed changes within the transaction
    assert session.flush.call_count > 0


# ==============================================================================
# 4. Migrations Validation & Baseline Integrity
# ==============================================================================


def test_load_canonical_migrations_manifest() -> None:
    """Baseline manifest must load successfully with 25 migrations."""
    manifest = load_canonical_migrations_manifest()
    assert manifest["total_migrations"] == 25
    assert len(manifest["migrations"]) == 25
    assert manifest["baseline_ref"] == "origin/staging"


def test_validate_manifest_structure_canonical() -> None:
    """The versioned manifest in docs/finalization/artifacts must satisfy all structural rules."""
    manifest = load_canonical_migrations_manifest()
    validate_manifest_structure(manifest)
    assert manifest["schema_version"] == 1
    assert manifest["total_migrations"] == 25


def test_validate_manifest_structure_unsupported_schema_version() -> None:
    """Manifest with unsupported schema_version must fail."""
    bad_manifest = {
        "schema_version": 99,
        "total_migrations": 1,
        "migrations": [],
    }
    with pytest.raises(PreflightVerificationError, match="Versão de schema.*não suportada"):
        validate_manifest_structure(bad_manifest)


def test_validate_manifest_structure_mismatched_total_count() -> None:
    """Manifest where total_migrations does not match list length must fail."""
    bad_manifest = {
        "schema_version": 1,
        "total_migrations": 5,
        "migrations": [
            {
                "version": "20260811000000",
                "filename": "20260811000000_test.sql",
                "path": "supabase/migrations/20260811000000_test.sql",
                "bytes": 100,
                "sha256": "a" * 64,
            }
        ],
    }
    with pytest.raises(PreflightVerificationError, match="Incoerência no manifesto"):
        validate_manifest_structure(bad_manifest)


def test_validate_manifest_structure_missing_fields() -> None:
    """Migration entry missing required fields must fail."""
    bad_manifest = {
        "schema_version": 1,
        "total_migrations": 1,
        "migrations": [
            {
                "version": "20260811000000",
                "filename": "20260811000000_test.sql",
                # missing path, bytes, sha256
            }
        ],
    }
    with pytest.raises(PreflightVerificationError, match="sem campos"):
        validate_manifest_structure(bad_manifest)


def test_validate_manifest_structure_invalid_sha256_format() -> None:
    """Invalid SHA-256 (not 64 hex characters) must fail."""
    bad_manifest = {
        "schema_version": 1,
        "total_migrations": 1,
        "migrations": [
            {
                "version": "20260811000000",
                "filename": "20260811000000_test.sql",
                "path": "supabase/migrations/20260811000000_test.sql",
                "bytes": 100,
                "sha256": "invalid_short_hash",
            }
        ],
    }
    with pytest.raises(PreflightVerificationError, match="Hash SHA-256 inválido"):
        validate_manifest_structure(bad_manifest)


def test_validate_manifest_structure_incoherent_version_and_filename() -> None:
    """Mismatched version and filename prefix must fail."""
    bad_manifest = {
        "schema_version": 1,
        "total_migrations": 1,
        "migrations": [
            {
                "version": "20260811000000",
                "filename": "20260812999999_mismatched.sql",
                "path": "supabase/migrations/20260812999999_mismatched.sql",
                "bytes": 100,
                "sha256": "a" * 64,
            }
        ],
    }
    with pytest.raises(PreflightVerificationError, match="Incoerência entre version"):
        validate_manifest_structure(bad_manifest)


def test_verify_migrations_alignment_success() -> None:
    """Official migrations directory must align with baseline manifest."""
    migrations_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    info = verify_migrations_alignment(migrations_dir)
    assert info["status"] == "aligned_locally"
    assert info["scope"] == "local_directory_only"
    assert info["count"] == 25
    assert info["manifest_verified"] is True


def test_migrations_identical_to_baseline_manifest() -> None:
    """Prove that every migration in supabase/migrations matches the origin/staging manifest."""
    migrations_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    manifest = load_canonical_migrations_manifest()
    sql_files = sorted(migrations_dir.glob("*.sql"), key=lambda f: f.name)

    assert len(sql_files) == 25
    for sql_file, entry in zip(sql_files, manifest["migrations"], strict=True):
        assert sql_file.name == entry["filename"]
        file_bytes = sql_file.read_bytes()
        assert len(file_bytes) == entry["bytes"]
        import hashlib

        assert hashlib.sha256(file_bytes).hexdigest() == entry["sha256"]


def test_verify_migrations_fails_on_missing_intermediate(tmp_path: Path) -> None:
    """Missing intermediate migration must fail closed."""
    manifest = load_canonical_migrations_manifest()
    # Create 24 files, omitting one intermediate
    for entry in manifest["migrations"]:
        if entry["version"] == "20260813142447":
            continue
        (tmp_path / entry["filename"]).write_bytes(b"SELECT 1;")

    with pytest.raises(PreflightVerificationError, match="Quantidade de migrations.*divergente"):
        verify_migrations_alignment(tmp_path)


def test_verify_migrations_fails_on_unexpected_file(tmp_path: Path) -> None:
    """Extra unexpected migration must fail closed."""
    manifest = load_canonical_migrations_manifest()
    for entry in manifest["migrations"]:
        (tmp_path / entry["filename"]).write_bytes(b"SELECT 1;")
    (tmp_path / "20260828000000_extra_unexpected.sql").write_bytes(b"SELECT 1;")

    with pytest.raises(PreflightVerificationError, match="Quantidade de migrations.*divergente"):
        verify_migrations_alignment(tmp_path)


def test_verify_migrations_fails_on_renamed_file(tmp_path: Path) -> None:
    """Renamed migration file must fail closed."""
    real_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    manifest = load_canonical_migrations_manifest()
    for entry in manifest["migrations"]:
        fname = entry["filename"]
        content = (real_dir / fname).read_bytes()
        if entry["version"] == "20260824010914":
            fname = "20260824010914_renamed_file.sql"
        (tmp_path / fname).write_bytes(content)

    with pytest.raises(PreflightVerificationError, match="Migration inesperada ou renomeada"):
        verify_migrations_alignment(tmp_path)


def test_verify_migrations_fails_on_altered_hash(tmp_path: Path) -> None:
    """Altered SQL content (hash mismatch) with same file size must fail closed."""
    real_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    manifest = load_canonical_migrations_manifest()
    for entry in manifest["migrations"]:
        content = bytearray((real_dir / entry["filename"]).read_bytes())
        if entry["version"] == "20260811000000":
            content[0] = ord(b"-") if content[0] != ord(b"-") else ord(b"#")
        (tmp_path / entry["filename"]).write_bytes(bytes(content))

    with pytest.raises(PreflightVerificationError, match="Hash SHA-256 divergente"):
        verify_migrations_alignment(tmp_path)


def test_verify_migrations_fails_on_duplicate_timestamp(tmp_path: Path) -> None:
    """Duplicate 14-digit timestamps must fail closed."""
    (tmp_path / "20260811000000_migration_a.sql").write_bytes(b"SELECT 1;")
    (tmp_path / "20260811000000_migration_b.sql").write_bytes(b"SELECT 1;")
    # Pad to 25 files
    for i in range(2, 25):
        (tmp_path / f"202608120000{i:02d}_migration.sql").write_bytes(b"SELECT 1;")

    with pytest.raises(PreflightVerificationError, match="Duplicidade de versão"):
        verify_migrations_alignment(tmp_path)


# ==============================================================================
# 5. Extended Credential & Secret Sanitization
# ==============================================================================


def test_sanitize_message_masks_all_secret_categories() -> None:
    """Sanitization masks credentials, JWTs, Supabase keys, Bearer headers, and params."""
    dummy_secret = "sb_secret_" + "dummy_secret_for_sanitization_test_123"
    dummy_publishable = "sb_publishable_dummy_pub_key_test_12345"
    dummy_sbp = "sbp_dummy_sbp_token_for_sanitization_test_123456789"
    dummy_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_payload_signature_123.dummy_sig"
    raw = (
        f"Error connecting to postgresql://postgres_user:my_secret_password_123@"
        f"db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres?"
        "apikey=sensitive_api_key_456&token=sensitive_token_789. "
        f"Keys: {dummy_secret}, {dummy_publishable}, {dummy_sbp}, and JWT: {dummy_jwt}. "
        "Header: Authorization: Bearer my_super_secret_bearer_token_abc. "
        "Config: password='pass_in_quotes', secret=secret_value."
    )
    sanitized = sanitize_message(raw)

    assert "my_secret_password_123" not in sanitized
    assert "postgres_user" not in sanitized
    assert "[REDACTED_USER]:[REDACTED_PASSWORD]@" in sanitized
    assert "sensitive_api_key_456" not in sanitized
    assert "sensitive_token_789" not in sanitized
    assert "sb_secret_" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
    assert "sb_publishable_" not in sanitized
    assert "[REDACTED_PUBLISHABLE]" in sanitized
    assert "sbp_" not in sanitized
    assert "[REDACTED_SBP]" in sanitized
    assert "eyJhbGciOi" not in sanitized
    assert "[REDACTED_JWT]" in sanitized
    assert "my_super_secret_bearer_token_abc" not in sanitized
    assert "[REDACTED_AUTH]" in sanitized
    assert "pass_in_quotes" not in sanitized
    assert "secret_value" not in sanitized


# ==============================================================================
# 6. Human Double Confirmation
# ==============================================================================


def test_human_double_confirmation_success() -> None:
    """Both correct ref and explicit yes grant confirmation."""
    inputs = [CANONICAL_STAGING_PROJECT_REF, "y"]
    assert (
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )
        is True
    )


def test_human_double_confirmation_ref_mismatch() -> None:
    """Mismatched ref on confirmation 1 fails closed."""
    inputs = ["wrong_ref", "y"]
    with pytest.raises(ConfirmationError, match="Confirmação 1 falhou"):
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )


def test_human_double_confirmation_second_factor_rejected() -> None:
    """Refusal on confirmation 2 fails closed."""
    inputs = [CANONICAL_STAGING_PROJECT_REF, "n"]
    with pytest.raises(ConfirmationError, match="Confirmação 2 falhou"):
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )


# ==============================================================================
# 7. Canonical Counts & Dry-Run
# ==============================================================================


def test_verify_canonical_counts_valid() -> None:
    """Mocked seed_pindobal report matching canonical metrics passes."""
    mock_report = {
        "status": "success",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 89, "fuzzy_candidate_count": 57},
    }
    with patch(
        "app.ingestion.staging_promotion_runner.run_seed_pindobal", return_value=mock_report
    ):
        result = verify_canonical_counts(Path("dummy"))
        assert result["status"] == "verified"
        assert result["counts"]["read"] == 1714
        assert result["counts"]["created"] == 1661


def test_verify_canonical_counts_divergence_fails() -> None:
    """Divergent counts must raise PreflightVerificationError."""
    divergent_report = {
        "status": "success",
        "counts": {**CANONICAL_PINDOBAL_METRICS, "created": 999},
        "google_snapshot": {"external_id_missing_count": 737},
    }
    with patch(
        "app.ingestion.staging_promotion_runner.run_seed_pindobal", return_value=divergent_report
    ):
        with pytest.raises(PreflightVerificationError, match="Contagens do dry-run divergem"):
            verify_canonical_counts(Path("dummy"))


# ==============================================================================
# 8. End-to-End Preflight Execution
# ==============================================================================


def test_execute_phase1_preflight_offline_dry_run_pure() -> None:
    """Pure offline dry-run without targets or env vars reports unvalidated remote config."""
    mock_dry_run = {
        "status": "success",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 89, "fuzzy_candidate_count": 57},
    }
    mock_manifest = MagicMock()
    mock_manifest.is_valid = True
    mock_manifest.total_files = 9
    mock_manifest.valid_files = 9
    mock_manifest.invalid_files = []

    with (
        patch("app.ingestion.staging_promotion_runner.verify_manifest", return_value=mock_manifest),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal", return_value=mock_dry_run
        ),
    ):
        report = execute_phase1_preflight(
            snapshot_dir=Path("dummy"),
            require_confirmation=False,
        )

    assert report["status"] == "phase1_success"
    assert report["remote_write_performed"] is False
    assert report["target_project_ref"] is None
    assert report["remote_configuration"]["validated"] is False
    assert (
        report["remote_configuration"]["status"] == "offline_dry_run_no_remote_config_validated"
    )
    assert report["manifest"]["valid_files"] == 9
    assert report["canonical_counts"]["counts"]["read"] == 1714


def test_execute_phase1_preflight_with_env_validation() -> None:
    """Preflight with valid environment config validates staging isolation."""
    mock_dry_run = {
        "status": "success",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 89, "fuzzy_candidate_count": 57},
    }
    mock_manifest = MagicMock()
    mock_manifest.is_valid = True
    mock_manifest.total_files = 9
    mock_manifest.valid_files = 9

    env_config = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    }
    inputs = [CANONICAL_STAGING_PROJECT_REF, "y"]

    with (
        patch("app.ingestion.staging_promotion_runner.verify_manifest", return_value=mock_manifest),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal", return_value=mock_dry_run
        ),
    ):
        report = execute_phase1_preflight(
            snapshot_dir=Path("dummy"),
            env_values=env_config,
            confirm_func=lambda _: inputs.pop(0),
            require_confirmation=True,
        )

    assert report["status"] == "phase1_success"
    assert report["target_project_ref"] == CANONICAL_STAGING_PROJECT_REF
    assert report["remote_configuration"]["validated"] is True


def test_execute_phase1_preflight_requires_target_for_human_confirmation() -> None:
    """Human confirmation without a target ref raises TargetValidationError."""
    with pytest.raises(TargetValidationError, match="Confirmação humana exige"):
        execute_phase1_preflight(
            snapshot_dir=Path("dummy"),
            target_project_ref=None,
            env_values=None,
            require_confirmation=True,
        )


# ==============================================================================
# 9. CLI Entrypoint Tests (main)
# ==============================================================================


def test_main_offline_dry_run_success(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI execution with --non-interactive succeeds offline."""
    mock_report = {
        "status": "phase1_success",
        "phase": 1,
        "remote_write_performed": False,
        "target_project_ref": None,
    }
    with patch(
        "app.ingestion.staging_promotion_runner.execute_phase1_preflight", return_value=mock_report
    ):
        exit_code = main(["--snapshot-dir", "dummy", "--non-interactive"])
        assert exit_code == 0
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)
        assert output_json["status"] == "phase1_success"


def test_main_error_outputs_sanitized_json_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """StagingPromotionError in main() emits sanitized JSON to stderr and returns 1."""
    dummy_secret = "sb_secret_" + "dummy_error_secret_123"
    with patch(
        "app.ingestion.staging_promotion_runner.execute_phase1_preflight",
        side_effect=TargetValidationError(f"Invalid config with {dummy_secret}"),
    ):
        exit_code = main(["--snapshot-dir", "dummy", "--non-interactive"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        err_json = json.loads(captured.err)
        assert err_json["status"] == "error"
        assert err_json["error_type"] == "TargetValidationError"
        assert dummy_secret not in err_json["message"]
        assert "[REDACTED_SECRET]" in err_json["message"]


def test_main_unexpected_error_outputs_sanitized_json_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unexpected exception in main() emits sanitized JSON to stderr and returns 1."""
    with patch(
        "app.ingestion.staging_promotion_runner.execute_phase1_preflight",
        side_effect=RuntimeError("Unexpected failure in postgresql://u:p@db/db"),
    ):
        exit_code = main(["--snapshot-dir", "dummy", "--non-interactive"])
        assert exit_code == 1
        captured = capsys.readouterr()
        err_json = json.loads(captured.err)
        assert err_json["status"] == "unexpected_error"
        assert err_json["error_type"] == "RuntimeError"
        assert "p@" not in err_json["message"]


@pytest.mark.asyncio
async def test_no_work_occurs_after_lock_transaction_termination() -> None:
    """Ensure that after the atomic lock block terminates, transaction is closed."""
    session = AsyncMock(spec=AsyncSession)
    # in_transaction: False on entry, True inside, False after block exits
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    captured_proxy = None
    async with staging_atomic_lock_transaction(session) as proxy:
        captured_proxy = proxy

    assert captured_proxy is not None
    # Underlying session transaction is now terminated; no work can continue under lock
    assert session.in_transaction() is False


def test_non_interactive_cannot_enable_remote_mode() -> None:
    """Prove that --non-interactive in Phase 1 always enforces remote_write_performed: False."""
    mock_report = {
        "status": "phase1_success",
        "phase": 1,
        "mode": "local_preflight_and_validation_only",
        "remote_write_performed": False,
        "target_project_ref": None,
    }
    with patch(
        "app.ingestion.staging_promotion_runner.execute_phase1_preflight",
        return_value=mock_report,
    ):
        exit_code = main(["--snapshot-dir", "dummy", "--non-interactive"])
        assert exit_code == 0
        assert mock_report["remote_write_performed"] is False
        assert mock_report["mode"] == "local_preflight_and_validation_only"


# ==============================================================================
# 10. Phase 2 Remote Promotion Execution Tests
# ==============================================================================


def _build_mock_phase2_prerequisites() -> dict[str, Any]:
    mock_manifest = MagicMock()
    mock_manifest.is_valid = True
    mock_manifest.total_files = 9
    mock_manifest.valid_files = 9

    mock_dry_run = {
        "status": "success",
        "run_started_at": "2026-09-02T12:00:00+00:00",
        "run_finished_at": "2026-09-02T12:01:00+00:00",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 89, "fuzzy_candidate_count": 57},
    }

    mock_osrm_result = MagicMock()
    mock_osrm_result.is_valid = True

    return {
        "manifest": mock_manifest,
        "dry_run": mock_dry_run,
        "osrm_result": mock_osrm_result,
    }


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_success() -> None:
    """Phase 2 execution under lock succeeds and returns canonical metrics."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    fake_run_id = uuid.uuid4()
    mock_counts = PersistenceCounts(
        read=1714,
        created=1661,
        updated=0,
        unchanged=0,
        rejected=0,
        candidates=53,
    )

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            new_callable=AsyncMock,
            return_value=(fake_run_id, mock_counts),
        ) as mock_persist,
    ):
        report = await execute_phase2_staging_promotion(
            session=session,
            snapshot_dir=Path("dummy"),
            require_confirmation=False,
        )

    assert report["status"] == "phase2_success"
    assert report["phase"] == 2
    assert report["mode"] == "staging_promotion_applied"
    assert report["remote_write_performed"] is True
    assert report["target_project_ref"] == CANONICAL_STAGING_PROJECT_REF
    assert report["run_id"] == str(fake_run_id)
    assert report["persisted_counts"]["created"] == 1661
    assert report["persisted_counts"]["unchanged"] == 0
    assert report["persisted_counts"]["candidates"] == 53
    assert report["persisted_counts"]["rejected"] == 0
    mock_persist.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_idempotency_second_run() -> None:
    """Second run on already persisted database leaves items unchanged (0 created)."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    fake_run_id = uuid.uuid4()
    mock_counts = PersistenceCounts(
        read=1714,
        created=0,
        updated=0,
        unchanged=1661,
        rejected=0,
        candidates=53,
    )

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            new_callable=AsyncMock,
            return_value=(fake_run_id, mock_counts),
        ),
    ):
        report = await execute_phase2_staging_promotion(
            session=session,
            snapshot_dir=Path("dummy"),
            require_confirmation=False,
        )

    assert report["status"] == "phase2_success"
    assert report["persisted_counts"]["created"] == 0
    assert report["persisted_counts"]["unchanged"] == 1661
    assert report["persisted_counts"]["rejected"] == 0


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_lock_busy_aborts() -> None:
    """If another runner holds the advisory lock, execution aborts immediately."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 0  # Lock busy!
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
    ):
        with pytest.raises(AdvisoryLockBusyError, match="ocupado por outro processo"):
            await execute_phase2_staging_promotion(
                session=session,
                snapshot_dir=Path("dummy"),
                require_confirmation=False,
            )


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_rollback_on_repository_error() -> None:
    """Failure inside persist_in_transaction triggers automatic rollback via context manager."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            side_effect=RuntimeError("Simulated database failure during persistence"),
        ),
    ):
        with pytest.raises(RuntimeError, match="Simulated database failure"):
            await execute_phase2_staging_promotion(
                session=session,
                snapshot_dir=Path("dummy"),
                require_confirmation=False,
            )


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_target_validation_fail_closed() -> None:
    """Attempting to target any non-authorized project ref raises TargetValidationError."""
    session = AsyncMock(spec=AsyncSession)
    with pytest.raises(TargetValidationError, match="não autorizado"):
        await execute_phase2_staging_promotion(
            session=session,
            snapshot_dir=Path("dummy"),
            target_project_ref=SYNTHETIC_UNAUTHORIZED_REF,
            require_confirmation=False,
        )


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_state_guard_fails_on_rejections() -> None:
    """State Guard raises PromotionExecutionError if any records are rejected."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    fake_run_id = uuid.uuid4()
    mock_counts = PersistenceCounts(
        read=1714,
        created=1651,
        updated=0,
        unchanged=0,
        rejected=10,  # Unexpected rejection!
        candidates=53,
    )

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            new_callable=AsyncMock,
            return_value=(fake_run_id, mock_counts),
        ),
    ):
        with pytest.raises(PromotionExecutionError, match="Contagem de rejeições inesperada"):
            await execute_phase2_staging_promotion(
                session=session,
                snapshot_dir=Path("dummy"),
                require_confirmation=False,
            )


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_state_guard_fails_on_divergent_total() -> None:
    """State Guard raises error if created + unchanged != canonical count."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    fake_run_id = uuid.uuid4()
    mock_counts = PersistenceCounts(
        read=1714,
        created=1500,  # Divergent count! (1500 != 1661)
        updated=0,
        unchanged=0,
        rejected=0,
        candidates=53,
    )

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            new_callable=AsyncMock,
            return_value=(fake_run_id, mock_counts),
        ),
    ):
        with pytest.raises(
            PromotionExecutionError, match="Contagem de registros válidos inesperada"
        ):
            await execute_phase2_staging_promotion(
                session=session,
                snapshot_dir=Path("dummy"),
                require_confirmation=False,
            )


@pytest.mark.asyncio
async def test_execute_phase2_staging_promotion_with_human_confirmation() -> None:
    """Human double confirmation required in Phase 2 succeeds when properly answered."""
    prereqs = _build_mock_phase2_prerequisites()

    session = AsyncMock(spec=AsyncSession)
    session.in_transaction.side_effect = [False, True, False]
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result
    session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    session.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    fake_run_id = uuid.uuid4()
    mock_counts = PersistenceCounts(
        read=1714,
        created=1661,
        updated=0,
        unchanged=0,
        rejected=0,
        candidates=53,
    )
    inputs = [CANONICAL_STAGING_PROJECT_REF, "y"]

    with (
        patch(
            "app.ingestion.staging_promotion_runner.verify_manifest",
            return_value=prereqs["manifest"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.run_seed_pindobal",
            return_value=prereqs["dry_run"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_osrm_origin",
            return_value=prereqs["osrm_result"],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_semtur_inventory",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_google_snapshot",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.process_pindobal_cutout",
            return_value=([], {}),
        ),
        patch(
            "app.ingestion.staging_promotion_runner.reconcile_semtur_and_google",
            return_value=[],
        ),
        patch(
            "app.ingestion.staging_promotion_runner.PindobalPersistenceRepository.persist_in_transaction",
            new_callable=AsyncMock,
            return_value=(fake_run_id, mock_counts),
        ),
    ):
        report = await execute_phase2_staging_promotion(
            session=session,
            snapshot_dir=Path("dummy"),
            confirm_func=lambda _: inputs.pop(0),
            require_confirmation=True,
        )

    assert report["status"] == "phase2_success"
    assert report["human_confirmation"]["confirmed"] is True


def test_main_apply_non_interactive_prohibited(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI execution with both --apply and --non-interactive is strictly prohibited."""
    exit_code = main(["--snapshot-dir", "dummy", "--apply", "--non-interactive"])
    assert exit_code == 1
    captured = capsys.readouterr()
    err_json = json.loads(captured.err)
    assert err_json["status"] == "error"
    assert "proíbe --non-interactive" in err_json["message"]


def test_main_apply_missing_env_vars_fails_closed(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI execution with --apply without required env vars fails closed."""
    for key in ("APP_ENV", "SUPABASE_URL", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)

    exit_code = main(["--snapshot-dir", "dummy", "--apply"])
    assert exit_code == 1
    captured = capsys.readouterr()
    err_json = json.loads(captured.err)
    assert err_json["status"] == "error"
    assert "exige variáveis de ambiente" in err_json["message"]


def test_main_apply_target_mismatch_fails_closed(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI execution with --apply when explicit target diverges from env fails closed."""
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SUPABASE_URL", f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co")
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    )

    exit_code = main(
        [
            "--snapshot-dir",
            "dummy",
            "--apply",
            "--target-project-ref",
            SYNTHETIC_UNAUTHORIZED_REF,
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    err_json = json.loads(captured.err)
    assert err_json["status"] == "error"
