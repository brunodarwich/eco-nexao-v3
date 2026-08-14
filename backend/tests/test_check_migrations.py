"""Tests for the offline migration gate used by CI."""

from pathlib import Path

from scripts.check_migrations import validate_migrations


def test_repository_migrations_pass_offline_gate() -> None:
    migrations = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    assert validate_migrations(migrations) == []


def test_gate_rejects_bad_names_duplicates_empty_and_forbidden_sql(tmp_path: Path) -> None:
    (tmp_path / "bad.sql").write_text("select 1;", encoding="utf-8")
    (tmp_path / "20260813000000_first.sql").write_text("", encoding="utf-8")
    (tmp_path / "20260813000000_second.sql").write_text(
        "create policy p using (auth.role() = 'authenticated');", encoding="utf-8"
    )

    errors = validate_migrations(tmp_path)

    assert any("Invalid migration filename" in error for error in errors)
    assert any("Duplicate migration version" in error for error in errors)
    assert any("Empty migration" in error for error in errors)
    assert any("auth.role() is forbidden" in error for error in errors)
