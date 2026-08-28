"""Comprehensive Unit and Edge-Case Tests for Staging Migration Gate (ECO-2002).

Covers all negative scenarios, environment boundary checks, CLI execution failures,
drift authorization lifecycles, advisors failures, secret redaction, and gate short-circuiting.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.staging_migration_gate import (
    apply_staging_migrations,
    check_migration_drift,
    check_supabase_advisors,
    extract_project_ref_from_url,
    main,
    run_cli_command,
    run_gate,
    sanitize_log,
    validate_staging_project_ref,
)

VALID_REF = "abcdefghijklmnopqrst"
VALID_PASS = "staging_db_secret_pass_123"
VALID_TOKEN = "sb_" + "secret_" + "staging_mgmt_token_xyz"


# ==============================================================================
# 1. SECRETS AUSENTES & FALHAS DE CONFIGURAÇÃO (FAIL-CLOSED)
# ==============================================================================


@pytest.mark.parametrize(
    ("project_ref", "db_password", "access_token", "missing_label"),
    [
        ("", VALID_PASS, VALID_TOKEN, "SUPABASE_PROJECT_REF"),
        ("   ", VALID_PASS, VALID_TOKEN, "SUPABASE_PROJECT_REF"),
        (VALID_REF, "", VALID_TOKEN, "SUPABASE_DB_PASSWORD"),
        (VALID_REF, "   ", VALID_TOKEN, "SUPABASE_DB_PASSWORD"),
        (VALID_REF, VALID_PASS, "", "SUPABASE_ACCESS_TOKEN"),
        (VALID_REF, VALID_PASS, "   ", "SUPABASE_ACCESS_TOKEN"),
        ("", "", "", "SUPABASE_ACCESS_TOKEN, SUPABASE_PROJECT_REF, SUPABASE_DB_PASSWORD"),
    ],
)
def test_run_gate_fails_closed_on_missing_or_whitespace_secrets(
    capsys: pytest.CaptureFixture[str],
    project_ref: str,
    db_password: str,
    access_token: str,
    missing_label: str,
) -> None:
    """Ensure run_gate fails immediately with code 1 if any mandatory secret is blank."""
    code = run_gate(
        project_ref=project_ref,
        db_password=db_password,
        access_token=access_token,
    )
    assert code == 1
    captured = capsys.readouterr().out
    assert "[GATE][ERROR] Missing mandatory staging secret(s)" in captured
    for label in missing_label.split(", "):
        assert label in captured


# ==============================================================================
# 2. VALIDAÇÃO DE PROJECT REF E ISOLAMENTO DE AMBIENTES
# ==============================================================================


def test_extract_project_ref_from_url() -> None:
    """Test extracting project ref from standard and irregular Supabase URLs."""
    assert (
        extract_project_ref_from_url("https://abcdefghijklmnopqrst.supabase.co")
        == "abcdefghijklmnopqrst"
    )
    assert (
        extract_project_ref_from_url("https://abcdefghijklmnopqrst.supabase.co:5432/postgres")
        == "abcdefghijklmnopqrst"
    )
    assert extract_project_ref_from_url("") == ""
    assert extract_project_ref_from_url(None) == ""
    assert extract_project_ref_from_url("https://customdomain.com") == ""
    assert extract_project_ref_from_url("invalid-url-format") == ""


def test_validate_staging_project_ref_valid() -> None:
    """Valid 20-character alphanumeric ref is accepted and lowercased."""
    assert validate_staging_project_ref("abcdefghijklmnopqrst") == "abcdefghijklmnopqrst"
    assert validate_staging_project_ref("  abcdefghijklmnopqrst  ") == "abcdefghijklmnopqrst"


def test_validate_staging_project_ref_expected_match() -> None:
    """Ref matches expected staging ref successfully."""
    assert (
        validate_staging_project_ref(
            "abcdefghijklmnopqrst", expected_staging_ref="abcdefghijklmnopqrst"
        )
        == "abcdefghijklmnopqrst"
    )


def test_validate_staging_project_ref_expected_mismatch_raises() -> None:
    """Ref mismatching expected staging ref raises ValueError."""
    with pytest.raises(ValueError, match="does not match EXPECTED_STAGING_PROJECT_REF"):
        validate_staging_project_ref(
            "abcdefghijklmnopqrst", expected_staging_ref="zyxwvutsrqponmlkjihg"
        )


@pytest.mark.parametrize(
    ("invalid_ref", "error_match"),
    [
        ("", "empty"),
        ("   ", "empty"),
        ("short", "20 lowercase alphanumeric"),
        ("abcdefghijklmnopqrs", "20 lowercase alphanumeric"),  # 19 chars
        ("abcdefghijklmnopqrstu", "20 lowercase alphanumeric"),  # 21 chars
        ("UPPERCASEPROJECTREF12", "placeholder or production marker"),  # contains 'project'
        ("invalid_chars_here!!", "20 lowercase alphanumeric"),
        ("invalid-with-hyphens", "20 lowercase alphanumeric"),
        ("your-project-ref-here", "placeholder or production marker"),
        ("replace-this-token-now", "placeholder or production marker"),
        ("prod-database-project", "placeholder or production marker"),
    ],
)
def test_validate_staging_project_ref_invalid_formats_and_markers(
    invalid_ref: str, error_match: str
) -> None:
    """Validate that invalid lengths, formats, and placeholder markers are rejected."""
    with pytest.raises(ValueError, match=error_match):
        validate_staging_project_ref(invalid_ref)


def test_validate_staging_project_ref_prevents_collisions() -> None:
    """Ensure staging ref cannot collide with development, test or production project refs."""
    dev_ref = "abcdefghijklmnopqrst"
    test_ref = "zyxwvutsrqponmlkjihg"
    prod_ref = "0123456789abcdefghij"

    # Dev collision
    with pytest.raises(ValueError, match="development"):
        validate_staging_project_ref("abcdefghijklmnopqrst", dev_ref=dev_ref, test_ref=test_ref)

    # Test collision
    with pytest.raises(ValueError, match="test"):
        validate_staging_project_ref("zyxwvutsrqponmlkjihg", dev_ref=dev_ref, test_ref=test_ref)

    # Prod collision
    with pytest.raises(ValueError, match="production"):
        validate_staging_project_ref("0123456789abcdefghij", prod_ref=prod_ref)


# ==============================================================================
# 3. FALHAS NA EXECUÇÃO DA CLI DO SUPABASE
# ==============================================================================


def test_run_cli_command_missing_executable() -> None:
    """CLI execution fails gracefully when executable (e.g. npx) is not in PATH."""
    with patch("shutil.which", return_value=None):
        code, output = run_cli_command(
            args=["npx", "supabase", "migration", "list"],
            env_vars={},
            secrets_to_redact=[],
        )
        assert code == 1
        assert "Executable 'npx' not found in PATH" in output


def test_run_cli_command_nonzero_exit_code() -> None:
    """CLI execution captures and sanitizes nonzero exit codes and stderr."""
    mock_proc = MagicMock(returncode=127, stdout="", stderr="command not found: supabase")
    with (
        patch("shutil.which", return_value="/usr/bin/npx"),
        patch("subprocess.run", return_value=mock_proc),
    ):
        code, output = run_cli_command(
            args=["npx", "supabase", "migration", "list"],
            env_vars={},
            secrets_to_redact=[],
        )
        assert code == 127
        assert "command not found: supabase" in output


def test_run_cli_command_timeout_handling() -> None:
    """CLI command timeout is handled safely without crashing."""
    with (
        patch("shutil.which", return_value="/usr/bin/npx"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["npx"], timeout=120)),
    ):
        code, output = run_cli_command(
            args=["npx", "supabase", "migration", "list"],
            env_vars={},
            secrets_to_redact=[],
        )
        assert code == 1
        assert "Error executing command" in output


def test_run_cli_command_generic_exception() -> None:
    """CLI command OS exceptions (e.g. PermissionError) are caught and sanitized."""
    with (
        patch("shutil.which", return_value="/usr/bin/npx"),
        patch("subprocess.run", side_effect=PermissionError("Permission denied")),
    ):
        code, output = run_cli_command(
            args=["npx", "supabase", "migration", "list"],
            env_vars={},
            secrets_to_redact=[],
        )
        assert code == 1
        assert "Permission denied" in output


# ==============================================================================
# 4. DRIFT DE MIGRATIONS E AUTORIZAÇÃO DE APPLY
# ==============================================================================


def test_check_migration_drift_parses_unapplied_migrations_table() -> None:
    """Verify that unapplied local migrations are parsed from supabase migration list output."""
    mock_table_output = (
        "┌────────────────┬────────────────┬────────┐\n"
        "│ LOCAL          │ REMOTE         │ TIME   │\n"
        "├────────────────┼────────────────┼────────┤\n"
        "│ 20260826000001 │ 20260826000001 │ 10:00  │\n"
        "│ 20260826000002 │                │        │\n"
        "│ 20260826000003 │ -              │        │\n"
        "└────────────────┴────────────────┴────────┘\n"
    )
    with patch(
        "scripts.staging_migration_gate.run_cli_command", return_value=(0, mock_table_output)
    ):
        ok, output, unapplied = check_migration_drift(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is True
        assert unapplied == ["20260826000002", "20260826000003"]


def test_check_migration_drift_handles_cli_error() -> None:
    """check_migration_drift returns ok=False when CLI execution fails."""
    with patch(
        "scripts.staging_migration_gate.run_cli_command",
        return_value=(1, "Error: Unauthorized token"),
    ):
        ok, output, unapplied = check_migration_drift(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is False
        assert "failed" in output
        assert unapplied == []


def test_run_gate_drift_detected_without_apply_authorization_fails() -> None:
    """If unapplied migrations exist and apply_migrations=False, gate fails closed."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "drift", ["20260826000001"]),
        ),
        patch("scripts.staging_migration_gate.apply_staging_migrations") as mock_apply,
        patch("scripts.staging_migration_gate.check_supabase_advisors") as mock_advisors,
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN, apply_migrations=False)
        assert code == 1
        mock_apply.assert_not_called()
        mock_advisors.assert_not_called()


def test_run_gate_drift_detected_with_apply_authorization_apply_fails() -> None:
    """If apply_migrations=True but apply command fails, gate fails and stops."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "drift", ["20260826000001"]),
        ),
        patch(
            "scripts.staging_migration_gate.apply_staging_migrations",
            return_value=(False, "Failed to apply migration"),
        ),
        patch("scripts.staging_migration_gate.check_supabase_advisors") as mock_advisors,
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN, apply_migrations=True)
        assert code == 1
        mock_advisors.assert_not_called()


def test_run_gate_drift_detected_with_apply_authorization_success() -> None:
    """If apply_migrations=True and apply succeeds, proceeds to advisors and succeeds."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "drift", ["20260826000001"]),
        ),
        patch(
            "scripts.staging_migration_gate.apply_staging_migrations",
            return_value=(True, "All applied"),
        ),
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors",
            return_value=(True, "No issues"),
        ),
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN, apply_migrations=True)
        assert code == 0


def test_apply_staging_migrations_cli_success() -> None:
    """apply_staging_migrations returns ok=True when db push succeeds."""
    with patch(
        "scripts.staging_migration_gate.run_cli_command", return_value=(0, "Pushed 1 migration")
    ):
        ok, output = apply_staging_migrations(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is True
        assert "Pushed 1 migration" in output


def test_apply_staging_migrations_cli_failure() -> None:
    """apply_staging_migrations returns ok=False when db push fails."""
    with patch(
        "scripts.staging_migration_gate.run_cli_command",
        return_value=(1, "Error: Migration syntax error"),
    ):
        ok, output = apply_staging_migrations(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is False
        assert "db push failed" in output


# ==============================================================================
# 5. FALHAS NOS ADVISORS (SEGURANÇA E PERFORMANCE)
# ==============================================================================


def test_check_supabase_advisors_cli_success() -> None:
    """check_supabase_advisors returns ok=True when CLI exits with code 0."""
    with patch(
        "scripts.staging_migration_gate.run_cli_command",
        return_value=(0, "No advisor issues detected."),
    ):
        ok, output = check_supabase_advisors(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is True
        assert "No advisor issues" in output


@pytest.mark.parametrize(
    "advisor_error_output",
    [
        "ERROR: Security Advisor: RLS is disabled on table public.pois",
        "ERROR: Performance Advisor: Missing index on foreign key user_id",
        "ERROR: Network timeout connecting to Supabase Management API",
    ],
)
def test_check_supabase_advisors_cli_failure(advisor_error_output: str) -> None:
    """check_supabase_advisors returns ok=False when advisor errors or violations occur."""
    with patch(
        "scripts.staging_migration_gate.run_cli_command", return_value=(1, advisor_error_output)
    ):
        ok, output = check_supabase_advisors(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert ok is False
        assert "reported errors" in output
        assert advisor_error_output in output


def test_run_gate_fails_when_advisors_fail() -> None:
    """Gate fails with code 1 when advisors check fails, even with zero drift."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "in sync", []),
        ),
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors",
            return_value=(False, "RLS violation"),
        ),
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN, apply_migrations=False)
        assert code == 1


# ==============================================================================
# 6. SANITIZAÇÃO RIGOROSA DE LOGS E CREDENCIAIS
# ==============================================================================


@pytest.mark.parametrize(
    ("raw_text", "expected_not_in"),
    [
        (
            "Connecting to postgres://postgres:super_secret_db_pass_123@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
            "super_secret_db_pass_123",
        ),
        (
            "Connecting with Bearer " + "sb_" + "secret_" + "production_admin_key_998877665544",
            "sb_" + "secret_" + "production_admin_key_998877665544",
        ),
        (
            (
                "Auth header eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSignature"
            ),
            "doNotLeakThisSignature",
        ),
    ],
)
def test_sanitize_log_masks_tokens_and_connection_strings(
    raw_text: str, expected_not_in: str
) -> None:
    """Verify that credentials matching regexes are redacted even without explicit secrets list."""
    sanitized = sanitize_log(raw_text)
    assert expected_not_in not in sanitized
    assert any(tag in sanitized for tag in ("[REDACTED]", "[REDACTED_TOKEN]"))


def test_sanitize_log_explicit_secrets_list() -> None:
    """Verify that custom secrets in secrets list are redacted."""
    secret_key = "my_custom_high_entropy_api_secret_key"
    log = f"An error occurred while calling API with key {secret_key}"
    sanitized = sanitize_log(log, secrets=[secret_key])
    assert secret_key not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_sanitize_log_handles_empty_and_short_secrets() -> None:
    """Verify edge cases: empty strings, short secrets (ignored to avoid corrupting text)."""
    assert sanitize_log("") == ""
    assert sanitize_log("Normal log message", secrets=["", "abc"]) == "Normal log message"


# ==============================================================================
# 7. PROVA DE SUCESSO ESTRITO & SHORT-CIRCUITING
# ==============================================================================


def test_run_gate_short_circuit_on_invalid_project_ref() -> None:
    """Ensure invalid project ref immediately fails and does not execute drift or advisors."""
    with (
        patch("scripts.staging_migration_gate.check_migration_drift") as mock_drift,
        patch("scripts.staging_migration_gate.check_supabase_advisors") as mock_advisors,
    ):
        code = run_gate("invalid-short-ref", VALID_PASS, VALID_TOKEN)
        assert code == 1
        mock_drift.assert_not_called()
        mock_advisors.assert_not_called()


def test_run_gate_short_circuit_on_drift_check_failure() -> None:
    """Ensure drift check failure immediately fails and does not execute advisors."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(False, "CLI crashed", []),
        ),
        patch("scripts.staging_migration_gate.check_supabase_advisors") as mock_advisors,
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN)
        assert code == 1
        mock_advisors.assert_not_called()


def test_run_gate_returns_zero_only_when_all_steps_succeed() -> None:
    """Proof of total success: code 0 is returned only when all 4 pipeline stages succeed."""
    with (
        patch(
            "scripts.staging_migration_gate.check_migration_drift",
            return_value=(True, "in sync", []),
        ) as mock_drift,
        patch(
            "scripts.staging_migration_gate.check_supabase_advisors", return_value=(True, "clean")
        ) as mock_advisors,
    ):
        code = run_gate(VALID_REF, VALID_PASS, VALID_TOKEN, apply_migrations=False)
        assert code == 0
        mock_drift.assert_called_once()
        mock_advisors.assert_called_once()


def test_main_cli_entrypoint_orchestration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CLI main() argument parsing and exit code propagation."""
    test_args = [
        "staging_migration_gate.py",
        "--project-ref",
        VALID_REF,
        "--expected-staging-ref",
        VALID_REF,
        "--db-password",
        VALID_PASS,
        "--access-token",
        VALID_TOKEN,
        "--apply-migrations",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with (
        patch("scripts.staging_migration_gate.run_gate", return_value=0) as mock_run_gate,
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 0
    mock_run_gate.assert_called_once_with(
        project_ref=VALID_REF,
        expected_staging_ref=VALID_REF,
        db_password=VALID_PASS,
        access_token=VALID_TOKEN,
        apply_migrations=True,
    )
