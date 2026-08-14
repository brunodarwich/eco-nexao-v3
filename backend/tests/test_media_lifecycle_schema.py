"""Structural contract tests for ECO-1702 media lifecycle schema."""

from pathlib import Path

from app.models.domain import MediaAsset
from app.schemas.domain import MediaAssetRead

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260813141416_add_editorial_media_lifecycle.sql"
)
HARDENING_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260813142059_harden_editorial_media_lifecycle.sql"
)
FINAL_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260813142447_finalize_media_kind_invariants.sql"
)
NULL_GAP_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260813142802_close_derivative_metadata_null_gap.sql"
)
PROCESSING_KEY_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260813152038_allow_media_processing_without_storage_key.sql"
)


def test_media_lifecycle_migration_is_private_and_fail_closed() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "ALTER TABLE app_private.media_assets" in sql
    assert "processing_status VARCHAR(20) NOT NULL DEFAULT 'pending'" in sql
    assert "license_code VARCHAR(40)" in sql
    assert "checksum_sha256 VARCHAR(64)" in sql
    assert "derivatives JSONB NOT NULL DEFAULT '{}'::jsonb" in sql
    assert "location extensions.geography(Point, 4326)" in sql
    assert "deleted_at TIMESTAMPTZ" in sql
    assert "processing_status = 'ready'" in sql
    assert "checksum_sha256 IS NOT NULL" in sql
    assert "license_code IS NOT NULL" in sql
    assert "length(trim(alt_text)) > 0" in sql
    assert "length(trim(credit)) > 0" in sql
    assert "GRANT" not in sql.upper()
    assert "SECURITY DEFINER" not in sql.upper()


def test_media_lifecycle_model_and_read_schema_are_synchronized() -> None:
    columns = MediaAsset.__table__.columns
    expected = {
        "license_code",
        "processing_status",
        "checksum_sha256",
        "width_px",
        "height_px",
        "derivatives",
        "location",
        "processed_at",
        "rejected_reason",
        "deleted_at",
        "media_kind",
        "external_photo_reference",
        "external_attributions",
        "external_cache_expires_at",
    }

    assert expected <= set(columns.keys())
    assert expected <= set(MediaAssetRead.model_fields)


def test_media_lifecycle_hardening_closes_null_and_google_storage_gaps() -> None:
    sql = HARDENING_MIGRATION.read_text(encoding="utf-8")

    assert "alt_text IS NOT NULL" in sql
    assert "credit IS NOT NULL" in sql
    assert "rejected_reason IS NOT NULL" in sql
    assert "width_px IS NOT NULL AND height_px IS NOT NULL" in sql
    assert "derivatives ?& ARRAY['thumb', 'card', 'hero']" in sql
    assert "media_kind IN ('stored', 'google_proxy')" in sql
    assert "license_code IS DISTINCT FROM 'GOOGLE_PLACES_PROXY'" in sql
    assert "media_kind = 'google_proxy'" in sql
    assert "storage_key IS NULL" in sql
    assert "external_cache_expires_at <= created_at + interval '30 days'" in sql


def test_media_kind_invariants_require_usable_derivatives_or_valid_google_proxy() -> None:
    sql = FINAL_MIGRATION.read_text(encoding="utf-8")

    assert "derivatives -> 'thumb' ->> 'storage_key'" in sql
    assert "derivatives -> 'card' ->> 'checksum_sha256'" in sql
    assert "derivatives -> 'hero' ->> 'checksum_sha256'" in sql
    assert "media_kind = 'google_proxy'" in sql
    assert "external_cache_expires_at > created_at" in sql
    assert "storage_key IS NULL" in sql


def test_derivative_metadata_nulls_are_forced_to_false() -> None:
    sql = NULL_GAP_MIGRATION.read_text(encoding="utf-8")

    assert "coalesce(length(trim(derivatives -> 'thumb' ->> 'storage_key')), 0) > 0" in sql
    assert "coalesce(derivatives -> 'hero' ->> 'checksum_sha256', '')" in sql


def test_stored_media_requires_storage_key_only_when_ready() -> None:
    sql = PROCESSING_KEY_MIGRATION.read_text(encoding="utf-8")

    assert "DROP CONSTRAINT media_assets_storage_mode_check" in sql
    assert "ADD CONSTRAINT media_assets_storage_mode_check" in sql
    assert "processing_status = 'ready' AND storage_key IS NOT NULL" in sql
    assert "processing_status <> 'ready' AND storage_key IS NULL" in sql
    assert "media_kind = 'google_proxy'" in sql
