"""Unit tests for the staging migration gate script (ECO-2002)."""

from unittest.mock import patch

import pytest

from scripts.staging_migration_gate import (
    run_gate,
    sanitize_log,
    validate_staging_project_ref,
)


def test_validate_staging_project_ref_accepts_valid_ref() -> None:
    valid_ref = "abcdefghijklmnopqrst"
    assert validate_staging_project_ref(valid_ref) == valid_ref


@pytest.mark.parametrize(
    "invalid_ref",
    [
        "",
        "short",
        "UPPERCASEPROJECTREF12",
        "invalid_chars_here!!",
        "your-project-ref-here",
        "prod-database-project",
    ],
)
def test_validate_staging_project_ref_rejects_invalid_or_placeholder_refs(
    invalid_ref: str,
) -> None:
    with pytest.raises(ValueError):
        validate_staging_project_ref(invalid_ref)


def test_validate_staging_project_ref_rejects_dev_and_test_collisions() -> None:
    ref = "abcdefghijklmnopqrst"
    with pytest.raises(ValueError, match="development"):
        validate_staging_project_ref(ref, dev_ref=ref)

    with pytest.raises(ValueError, match="test"):
        validate_staging_project_ref(ref, test_ref=ref)


def test_sanitize_log_redacts_passwords_and_tokens() -> None:
    secret_pass = "super_secret_db_pass_123"
    token = "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz123456"
    raw_text = (
        f"Connecting to postgres://postgres:{secret_pass}@"
        f"db.abcdefghijklmnopqrst.supabase.co:5432/postgres with token {token}"
    )


    sanitized = sanitize_log(raw_text, secrets=[secret_pass, token])
    assert secret_pass not in sanitized
    assert token not in sanitized
    assert any(
        marker in sanitized
        for marker in ("[REDACTED]", "[REDACTED_SECRET]", "[REDACTED_TOKEN]")
    )



def test_run_gate_fails_closed_when_secrets_missing() -> None:
    # Missing all secrets
    assert run_gate(project_ref="", db_password="", access_token="") == 1
    # Missing token
    assert run_gate(project_ref="abcdefghijklmnopqrst", db_password="pass", access_token="") == 1
    # Missing password
    assert run_gate(project_ref="abcdefghijklmnopqrst", db_password="", access_token="token") == 1


def test_run_gate_happy_path_zero_drift() -> None:
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "All migrations in sync", []),
        ),
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors",
            return_value=(True, "No issues found"),
        ),
    ):
        code = run_gate(
            project_ref="abcdefghijklmnopqrst",
            db_password="db_secret_password",
            access_token="supabase_mgmt_token",
            apply_migrations=False,
        )
        assert code == 0


def test_run_gate_blocks_when_drift_detected_without_apply_authorization() -> None:
    with patch(
        "scripts.staging_migration_gate.check_migration_drift",
        return_value=(True, "Table of migrations", ["20260826000000_new_feature.sql"]),
    ):
        code = run_gate(
            project_ref="abcdefghijklmnopqrst",
            db_password="db_secret_password",
            access_token="supabase_mgmt_token",
            apply_migrations=False,
        )
        assert code == 1


def test_run_gate_applies_migrations_when_authorized() -> None:
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "Table of migrations", ["20260826000000_new_feature.sql"]),
        ),
        patch(
            "scripts.staging_migration_gate.apply_staging_migrations",
            return_value=(True, "Applied 1 migration"),
        ),
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors",
            return_value=(True, "No issues found"),
        ),
    ):
        code = run_gate(
            project_ref="abcdefghijklmnopqrst",
            db_password="db_secret_password",
            access_token="supabase_mgmt_token",
            apply_migrations=True,
        )
        assert code == 0


def test_run_gate_fails_when_advisors_report_issues() -> None:
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "All in sync", []),
        ),
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors",
            return_value=(False, "ERROR: RLS disabled on public table"),
        ),
    ):
        code = run_gate(
            project_ref="abcdefghijklmnopqrst",
            db_password="db_secret_password",
            access_token="supabase_mgmt_token",
            apply_migrations=False,
        )
        assert code == 1
