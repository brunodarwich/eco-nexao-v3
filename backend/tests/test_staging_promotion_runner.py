"""Unit tests for staging promotion runner (ECO-2005 Phase 1)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.staging_promotion_runner import (
    ADVISORY_LOCK_ID,
    CANONICAL_PINDOBAL_METRICS,
    CANONICAL_STAGING_PROJECT_REF,
    AdvisoryLockBusyError,
    ConfirmationError,
    PreflightVerificationError,
    TargetValidationError,
    execute_phase1_preflight,
    extract_ref_from_database_url,
    extract_ref_from_supabase_url,
    request_human_double_confirmation,
    sanitize_message,
    staging_advisory_lock,
    validate_environment_config,
    validate_target_project_ref,
    verify_canonical_counts,
    verify_migrations_alignment,
)


def test_validate_target_project_ref_accepts_canonical_staging():
    """Canonical staging ref must be accepted."""
    assert (
        validate_target_project_ref(CANONICAL_STAGING_PROJECT_REF) == CANONICAL_STAGING_PROJECT_REF
    )


@pytest.mark.parametrize(
    "invalid_ref",
    [
        "",
        "   ",
        "rgfuqmwxjuceqpxcraxm",  # Obsolete staging ref
        "hjtkcmbfndbgyurfhsuo",  # Production ref
        "short_ref",
        "this_ref_is_far_too_long_to_be_a_supabase_ref",
        "invalid!ref!characters",
        "12345678901234567890",
        "kchzucvrnzwzehfdwzwX",  # Capital letters
    ],
)
def test_validate_target_project_ref_rejects_non_canonical(invalid_ref: str):
    """Any ref other than kchzucvrnzwzehfdwzwi must fail closed."""
    with pytest.raises(TargetValidationError):
        validate_target_project_ref(invalid_ref)


def test_extract_ref_from_supabase_url_success():
    """Valid staging HTTPS URL should extract the canonical ref."""
    url = f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co"
    assert extract_ref_from_supabase_url(url) == CANONICAL_STAGING_PROJECT_REF
    assert extract_ref_from_supabase_url(f"{url}/auth/v1") == CANONICAL_STAGING_PROJECT_REF


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://kchzucvrnzwzehfdwzwi.supabase.co",
        "https://rgfuqmwxjuceqpxcraxm.supabase.co",
        "https://hjtkcmbfndbgyurfhsuo.supabase.co",
        "https://otherdomain.com",
        "not_a_url",
    ],
)
def test_extract_ref_from_supabase_url_failures(bad_url: str):
    """Invalid schemes, other domains or non-staging refs must fail."""
    with pytest.raises(TargetValidationError):
        extract_ref_from_supabase_url(bad_url)


def test_extract_ref_from_database_url_direct_host():
    """Direct host connection string should resolve and validate the ref."""
    dsn = f"postgresql://postgres:secret_pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres"
    assert extract_ref_from_database_url(dsn) == CANONICAL_STAGING_PROJECT_REF


def test_extract_ref_from_database_url_pooler_host():
    """Supavisor connection string with tenant username should resolve the ref."""
    dsn = (
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:secret_pass"
        "@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
    )
    assert extract_ref_from_database_url(dsn) == CANONICAL_STAGING_PROJECT_REF


@pytest.mark.parametrize(
    "bad_dsn",
    [
        "postgresql://postgres:pass@db.rgfuqmwxjuceqpxcraxm.supabase.co:5432/postgres",
        "postgresql://postgres:pass@db.hjtkcmbfndbgyurfhsuo.supabase.co:5432/postgres",
        "postgresql://postgres:pass@localhost:5432/postgres",
        "mysql://root:pass@db.kchzucvrnzwzehfdwzwi.supabase.co:3306/db",
        "invalid_dsn",
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:pass@pooler.supabase.com.exemplo-invalido:6543/postgres",
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:pass@evil-pooler.supabase.com.attacker.org:6543/postgres",
        f"postgresql+psycopg://postgres.{CANONICAL_STAGING_PROJECT_REF}:pass@pooler.supabase.com:6543/postgres",
    ],
)
def test_extract_ref_from_database_url_failures(bad_dsn: str):
    """Non-staging or invalid database URLs must fail closed."""
    with pytest.raises(TargetValidationError):
        extract_ref_from_database_url(bad_dsn)


def test_validate_environment_config_success():
    """Environment with staging APP_ENV and matching canonical URLs passes."""
    env = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    }
    assert validate_environment_config(env) == CANONICAL_STAGING_PROJECT_REF


def test_validate_environment_config_app_env_not_staging():
    """APP_ENV other than staging must be rejected."""
    for env_name in ("development", "test", "production"):
        env = {
            "APP_ENV": env_name,
            "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
            "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
        }
        with pytest.raises(TargetValidationError, match="APP_ENV inválido"):
            validate_environment_config(env)


def test_validate_environment_config_mismatched_refs():
    """Different refs in Supabase URL and Database URL must fail closed."""
    env = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": "postgresql://postgres:pass@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
    }
    with pytest.raises(TargetValidationError):
        validate_environment_config(env)


def test_sanitize_message_masks_secrets():
    """Sanitization removes credentials from URLs, tokens, and keys."""
    dummy_secret = f"{'sb_secret_'}{'dummy_secret_for_sanitization_test_123'}"
    dummy_sbp = f"{'sbp_'}{'dummy_sbp_token_for_sanitization_test_123456789'}"
    raw = (
        "Error in postgresql://postgres:MySuperSecret123@"
        f"db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres. "
        f"Key: {dummy_secret} and token {dummy_sbp}"
    )
    sanitized = sanitize_message(raw)
    assert "MySuperSecret123" not in sanitized
    assert "[REDACTED]@" in sanitized
    assert "sb_secret_" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
    assert "[REDACTED_SBP]" in sanitized


def test_human_double_confirmation_success():
    """Both correct ref and explicit yes grant confirmation."""
    inputs = [CANONICAL_STAGING_PROJECT_REF, "y"]
    assert (
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )
        is True
    )


def test_human_double_confirmation_ref_mismatch():
    """Mismatched ref on confirmation 1 fails closed."""
    inputs = ["wrong_ref", "y"]
    with pytest.raises(ConfirmationError, match="Confirmação 1 falhou"):
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )


def test_human_double_confirmation_second_factor_rejected():
    """Refusal on confirmation 2 fails closed."""
    inputs = [CANONICAL_STAGING_PROJECT_REF, "n"]
    with pytest.raises(ConfirmationError, match="Confirmação 2 falhou"):
        request_human_double_confirmation(
            CANONICAL_STAGING_PROJECT_REF, prompt_input=lambda _: inputs.pop(0)
        )


@pytest.mark.asyncio
async def test_staging_advisory_lock_success():
    """When lock is available, context manager yields and releases in finally."""
    session = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    async with staging_advisory_lock(session, lock_id=ADVISORY_LOCK_ID) as acquired:
        assert acquired is True

    # 2 calls: 1 to acquire pg_try_advisory_lock, 1 to release pg_advisory_unlock
    assert session.execute.call_count == 2


@pytest.mark.asyncio
async def test_staging_advisory_lock_busy():
    """When lock is held by another process, raises AdvisoryLockBusyError without blocking."""
    session = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 0
    session.execute.return_value = execute_result

    with pytest.raises(AdvisoryLockBusyError, match="ocupado por outro processo"):
        async with staging_advisory_lock(session, lock_id=ADVISORY_LOCK_ID):
            pass

    # Only 1 call was made (try acquire); unlock must NOT be called if not acquired
    assert session.execute.call_count == 1


@pytest.mark.asyncio
async def test_staging_advisory_lock_releases_on_exception():
    """If an exception occurs inside the lock block, unlock must be called in finally."""
    session = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = 1
    session.execute.return_value = execute_result

    with pytest.raises(RuntimeError, match="simulated failure"):
        async with staging_advisory_lock(session, lock_id=ADVISORY_LOCK_ID):
            raise RuntimeError("simulated failure")

    # Lock must still have been unlocked
    assert session.execute.call_count == 2


def test_verify_canonical_counts_valid():
    """Mocked seed_pindobal report matching canonical metrics passes."""
    mock_report = {
        "status": "success",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 53, "fuzzy_candidate_count": 53},
    }
    with patch(
        "app.ingestion.staging_promotion_runner.run_seed_pindobal", return_value=mock_report
    ):
        result = verify_canonical_counts(Path("dummy"))
        assert result["status"] == "verified"
        assert result["counts"]["read"] == 1714
        assert result["counts"]["created"] == 1661


def test_verify_canonical_counts_divergence_fails():
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


def test_verify_migrations_alignment():
    """Migrations directory with 25 migrations is aligned."""
    migrations_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    info = verify_migrations_alignment(migrations_dir)
    assert info["status"] == "aligned_locally"
    assert info["scope"] == "local_directory_only"
    assert info["count"] == 25


def test_execute_phase1_preflight_end_to_end():
    """End-to-end Phase 1 execution succeeds offline with zero remote writes."""
    mock_dry_run = {
        "status": "success",
        "counts": dict(CANONICAL_PINDOBAL_METRICS),
        "google_snapshot": {"external_id_missing_count": 737},
        "reconciliation": {"matches_count": 53, "fuzzy_candidate_count": 53},
    }
    mock_manifest = MagicMock()
    mock_manifest.is_valid = True
    mock_manifest.total_files = 9
    mock_manifest.valid_files = 9
    mock_manifest.invalid_files = []

    inputs = [CANONICAL_STAGING_PROJECT_REF, "y"]
    env_config = {
        "APP_ENV": "staging",
        "SUPABASE_URL": f"https://{CANONICAL_STAGING_PROJECT_REF}.supabase.co",
        "DATABASE_URL": f"postgresql://postgres:pass@db.{CANONICAL_STAGING_PROJECT_REF}.supabase.co:5432/postgres",
    }

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
    assert report["remote_write_performed"] is False
    assert report["phase"] == 1
    assert report["target_project_ref"] == CANONICAL_STAGING_PROJECT_REF
    assert report["migrations"]["status"] == "aligned_locally"
    assert report["canonical_counts"]["reconciliation"]["matches_count"] == 53
    assert report["governance"]["phase2_remote_write"] == "BLOCKED_PENDING_EXPLICIT_OWNER_GO"
    assert report["governance"]["schema_rollback"] == "PITR_snapshot_only"
    assert report["governance"]["data_rollback"] == "logical_unpublish_draft_only"
