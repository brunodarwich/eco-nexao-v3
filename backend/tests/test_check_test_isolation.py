"""Regression tests for the sanitized Supabase test-environment gate."""

from scripts.check_test_isolation import validate_isolation

TEST_REF = "abcdefghijklmnopqrst"
DEV_REF = "zyxwvutsrqponmlkjihg"


def environment(project_ref: str, *, database_ref: str | None = None) -> dict[str, str]:
    """Build synthetic, non-secret configuration for validation tests."""
    db_ref = database_ref or project_ref
    return {
        "APP_ENV": "test",
        "DATABASE_URL": (
            f"postgresql://postgres.{db_ref}:synthetic-password@"
            "aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
        ),
        "SUPABASE_URL": f"https://{project_ref}.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_synthetic",
    }


def test_accepts_isolated_managed_project_with_matching_pooler_tenant() -> None:
    development = environment(DEV_REF)
    test = environment(TEST_REF)

    assert validate_isolation(development, test) == []


def test_rejects_human_slug_that_is_not_a_supabase_project_ref() -> None:
    development = environment(DEV_REF)
    test = environment("econexao-teste")

    assert "SUPABASE_PROJECT_REF_INVALID" in validate_isolation(development, test)


def test_rejects_database_tenant_from_another_project() -> None:
    development = environment(DEV_REF)
    test = environment(TEST_REF, database_ref=DEV_REF)

    assert "DATABASE_PROJECT_REF_MISMATCH" in validate_isolation(development, test)


def test_accepts_matching_direct_database_host() -> None:
    development = environment(DEV_REF)
    test = environment(TEST_REF)
    test["DATABASE_URL"] = (
        f"postgresql://postgres:synthetic-password@db.{TEST_REF}.supabase.co:5432/postgres"
    )

    assert validate_isolation(development, test) == []
