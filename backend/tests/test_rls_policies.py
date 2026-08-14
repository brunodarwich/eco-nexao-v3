"""Static migration security gates; database RLS tests run only against Supabase test."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPOSITORY_ROOT / "supabase" / "migrations"
DOMAIN_TABLES = (
    "regions",
    "routes",
    "route_origins",
    "route_geometries",
    "route_alerts",
    "actor_categories",
    "actors",
    "route_actors",
    "accessibility_features",
    "actor_accessibility_features",
    "media_assets",
    "external_sources",
    "actor_external_refs",
    "ingestion_runs",
    "raw_source_records",
    "reconciliation_candidates",
    "field_provenance",
    "profiles",
    "user_preferences",
    "favorite_routes",
    "favorite_actors",
    "trips",
    "trip_actor_visits",
    "user_badges",
)


def test_migration_files_and_seed_exist() -> None:
    """The ordered migration chain and configured seed hook must exist."""
    filenames = {path.name for path in MIGRATIONS_DIR.glob("*.sql")}
    required_filenames = {
        "20260811000000_init_postgis_and_base_schemas.sql",
        "20260811010000_domain_tables.sql",
        "20260811020000_rls_and_permissions.sql",
        "20260812095417_fix_updated_at_function_search_path.sql",
        "20260812095647_reset_database_search_path.sql",
        "20260812120000_storage_buckets_and_policies.sql",
        "20260813084440_harden_storage_buckets_and_policies.sql",
        "20260813091542_editorial_rbac_and_audit_trail.sql",
        "20260813102503_pindobal_spatial_integrity.sql",
        "20260813141416_add_editorial_media_lifecycle.sql",
        "20260813142059_harden_editorial_media_lifecycle.sql",
        "20260813142447_finalize_media_kind_invariants.sql",
        "20260813142802_close_derivative_metadata_null_gap.sql",
        "20260813152038_allow_media_processing_without_storage_key.sql",
        "20260813175721_archive_duplicate_route_actor_links.sql",
    }
    assert required_filenames <= filenames
    assert (REPOSITORY_ROOT / "supabase" / "seed.sql").is_file()


def test_domain_tables_are_moved_out_of_the_exposed_schema() -> None:
    """Every domain table must finish in app_private and use qualified geography."""
    domain_sql = (MIGRATIONS_DIR / "20260811010000_domain_tables.sql").read_text(encoding="utf-8")
    for table in DOMAIN_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS public.{table}" in domain_sql
        assert f"ALTER TABLE public.{table} SET SCHEMA app_private;" in domain_sql
    assert domain_sql.count("extensions.geography(") == 4
    assert "REFERENCES app_private.media_assets(id)" in domain_sql


def test_auto_rls_trigger_uses_exact_schema_allowlist_and_relation_name() -> None:
    """The event trigger must not quote an already-qualified object identity."""
    base_sql = (MIGRATIONS_DIR / "20260811000000_init_postgis_and_base_schemas.sql").read_text(
        encoding="utf-8"
    )
    assert "cmd.schema_name IN ('public', 'app_private')" in base_sql
    assert "SELECT relname INTO table_name FROM pg_class WHERE oid = cmd.objid" in base_sql
    assert "cmd.object_identity" not in base_sql
    assert "REVOKE ALL ON FUNCTION extensions.auto_enable_rls() FROM PUBLIC" in base_sql


def test_private_domain_is_deny_by_default() -> None:
    """No Data API role receives direct domain privileges or badge mutations."""
    rls_sql = (MIGRATIONS_DIR / "20260811020000_rls_and_permissions.sql").read_text(
        encoding="utf-8"
    )
    for table in DOMAIN_TABLES:
        assert f"ALTER TABLE app_private.{table} ENABLE ROW LEVEL SECURITY;" in rls_sql
    assert "GRANT " not in rls_sql
    assert "CREATE POLICY" not in rls_sql
    assert "auth.role()" not in rls_sql
    assert "REVOKE ALL ON SCHEMA app_private FROM PUBLIC, anon, authenticated;" in rls_sql
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA app_private" in rls_sql


def test_storage_policy_hardening_is_forward_only_and_owner_scoped() -> None:
    """The corrective migration must close BOLA without rewriting history."""
    original_sql = (
        MIGRATIONS_DIR / "20260812120000_storage_buckets_and_policies.sql"
    ).read_text(encoding="utf-8")
    hardening_sql = (
        MIGRATIONS_DIR / "20260813084440_harden_storage_buckets_and_policies.sql"
    ).read_text(encoding="utf-8")

    # The historical migration remains untouched; the forward migration removes
    # its broad policies before recreating the final secure policy set.
    assert "OR auth.uid() IS NOT NULL" in original_sql
    assert "ALTER TABLE storage.objects" not in original_sql
    assert "OR auth.uid() IS NOT NULL" not in hardening_sql
    assert 'DROP POLICY IF EXISTS "Public Read Avatars"' in hardening_sql
    assert 'DROP POLICY IF EXISTS "Public Read Editorial Media"' in hardening_sql

    ownership = "(storage.foldername(name))[1] = (SELECT auth.uid())::text"
    assert hardening_sql.count(ownership) == 5
    assert 'CREATE POLICY "Authenticated User Select Own Avatar"' in hardening_sql
    assert "FOR INSERT\nTO authenticated\nWITH CHECK" in hardening_sql
    assert "FOR UPDATE\nTO authenticated\nUSING" in hardening_sql
    assert "WITH CHECK (" in hardening_sql
    assert "FOR DELETE\nTO authenticated\nUSING" in hardening_sql
    assert "auth.role()" not in hardening_sql
    assert "SECURITY DEFINER" not in hardening_sql


def test_storage_buckets_match_accepted_media_policy() -> None:
    """ADR 0008 requires two public derivative buckets and one private raw bucket."""
    sql = (MIGRATIONS_DIR / "20260813084440_harden_storage_buckets_and_policies.sql").read_text(
        encoding="utf-8"
    )

    assert "('avatars', 'avatars', true, 5242880, ARRAY['image/webp'])" in sql
    assert "('editorial-media', 'editorial-media', true, 10485760, ARRAY['image/webp'])" in sql
    assert "'raw-ingestion',\n        'raw-ingestion',\n        false" in sql
    assert "image/gif" not in sql
    assert "cardinality(storage.foldername(name)) = 1" in sql
    assert "lower(storage.extension(name)) = 'webp'" in sql


def test_editorial_rbac_is_private_deny_by_default_and_audit_is_immutable() -> None:
    sql = (MIGRATIONS_DIR / "20260813091542_editorial_rbac_and_audit_trail.sql").read_text(
        encoding="utf-8"
    )
    for table in (
        "editorial_role_capabilities",
        "editorial_memberships",
        "editorial_invitations",
        "editorial_resource_states",
        "audit_logs",
    ):
        assert f"CREATE TABLE app_private.{table}" in sql
        assert f"ALTER TABLE app_private.{table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"REVOKE ALL ON app_private.{table} FROM PUBLIC, anon, authenticated" in sql
    assert "BEFORE UPDATE OR DELETE ON app_private.audit_logs" in sql
    assert "audit_logs is append-only" in sql
    assert "SECURITY DEFINER" not in sql
    assert "auth.role()" not in sql
    assert "user_metadata" not in sql


def test_reconciliation_archives_duplicate_route_links_reversibly() -> None:
    sql = (
        MIGRATIONS_DIR / "20260813175721_archive_duplicate_route_actor_links.sql"
    ).read_text(encoding="utf-8")
    assert "ADD COLUMN archived_at TIMESTAMPTZ" in sql
    assert "ADD COLUMN archived_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT" in sql
    assert "chk_route_actors_archive_metadata" in sql
    assert "btrim(archive_reason) <> ''" in sql
    assert "WHERE archived_at IS NULL" in sql
    assert "DELETE FROM" not in sql.upper()
    assert "SECURITY DEFINER" not in sql.upper()


def test_editorial_rbac_contains_adr_roles_capabilities_and_state_machine() -> None:
    sql = (MIGRATIONS_DIR / "20260813091542_editorial_rbac_and_audit_trail.sql").read_text(
        encoding="utf-8"
    )
    for role in ("admin", "editor", "reviewer", "publisher"):
        assert f"'{role}'" in sql
    for state in ("draft", "review", "published", "archived"):
        assert f"'{state}'" in sql
    assert "editorial_memberships_active_unique" in sql
    assert "revoked_at IS NULL" in sql
    assert "REFERENCES auth.users(id)" in sql
