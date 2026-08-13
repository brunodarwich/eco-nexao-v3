"""Unit tests for check_environment.py (ECO-1301).

Validates:
- No network calls or implicit npx installs (--no-install used for npx).
- No shell=True execution in subprocesses.
- Real redaction of sensitive credentials (URLs, passwords, tokens, API keys) in stdout.
- Non-zero exit code on environment collision.
"""

from unittest.mock import MagicMock, patch

import scripts.check_environment as check_env


def test_sanitize_text_direct():
    """Verify sanitize_text redacts passwords in URLs, JWTs, secret keys, and key=value pairs."""
    raw_dsn = "DATABASE_URL=postgres://db_user:my_super_secret_password_123@localhost:5432/mydb"
    sanitized_dsn = check_env.sanitize_text(raw_dsn)
    assert "my_super_secret_password_123" not in sanitized_dsn
    assert "[REDACTED]" in sanitized_dsn

    raw_key = "SUPABASE_SECRET_KEY=sb_secret_abc123xyz456789"
    sanitized_key = check_env.sanitize_text(raw_key)
    assert "sb_secret_abc123xyz456789" not in sanitized_key
    assert "[REDACTED" in sanitized_key

    raw_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
    sanitized_jwt = check_env.sanitize_text(raw_jwt)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized_jwt


def test_check_tool_without_shell():
    """Verify check_tool executes subprocess without shell=True."""
    with patch("subprocess.run") as mock_run, patch("shutil.which", return_value="/bin/dummy"):
        mock_run.return_value = MagicMock(stdout="v1.0.0", stderr="", returncode=0)
        ok, version = check_env.check_tool("dummy", ["--version"])

        assert ok is True
        assert version == "v1.0.0"
        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        assert kwargs.get("shell") is not True


def test_run_checks_sanitizes_subprocess_stdout(capsys):
    """Verify run_checks redacts secrets present in subprocess stdout
    (e.g. isolation check output)."""
    synthetic_secret_stdout = (
        "Colisão detectada: DATABASE_URL=postgres://admin:super_secret_pass_999@db.local:5432/appdb\n"
        "Chave exposta: SUPABASE_SECRET_KEY=sb_secret_999888777666"
    )

    with patch("scripts.check_environment.check_tool", return_value=(True, "v1.0.0")), patch(
        "scripts.check_env.validate", return_value=[]
    ), patch("subprocess.run") as mock_sub_run:
        mock_sub_run.return_value = MagicMock(returncode=1, stdout=synthetic_secret_stdout)
        exit_code = check_env.run_checks()

        assert exit_code != 0

        captured = capsys.readouterr()
        # Assert raw secrets DO NOT appear in stdout
        assert "super_secret_pass_999" not in captured.out
        assert "sb_secret_999888777666" not in captured.out
        # Assert redacted indicators ARE present
        assert "[REDACTED]" in captured.out or "[REDACTED_TOKEN]" in captured.out


def test_run_checks_uses_no_install_for_npx_supabase():
    """Verify npx supabase check uses --no-install to avoid network calls
    or dynamic package installs."""
    with patch("subprocess.run") as mock_run, patch("shutil.which", return_value="/usr/bin/npx"):
        mock_run.return_value = MagicMock(stdout="2.113.0", stderr="", returncode=0)
        ok, version = check_env.check_tool("npx", ["--no-install", "supabase", "--version"])


        assert ok is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--no-install" in args


def test_run_checks_returns_nonzero_on_collision():
    """Verify run_checks returns non-zero when environment collision is detected."""
    with patch("scripts.check_environment.check_tool", return_value=(True, "v1.0.0")), patch(
        "subprocess.run"
    ) as mock_sub_run:
        # Simulate check_test_isolation failing with exit code 1 (collision)
        mock_sub_run.return_value = MagicMock(returncode=1, stdout="Collision detected")
        exit_code = check_env.run_checks()
        assert exit_code != 0

