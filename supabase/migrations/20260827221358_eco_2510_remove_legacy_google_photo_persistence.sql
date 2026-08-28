-- ECO-2510: Google Place Photo resource names, URLs and attribution metadata
-- are request-scoped credentials.  They must never be persisted in PostgreSQL
-- or represented as a media asset.  Editorial media remains unchanged.
--
-- Forward-only: legacy proxy rows are intentionally removed because converting
-- them into editorial media would falsely imply Storage ownership/licensing.

DELETE FROM app_private.media_assets
WHERE media_kind = 'google_proxy'
   OR license_code = 'GOOGLE_PLACES_PROXY';

ALTER TABLE app_private.media_assets
    DROP CONSTRAINT IF EXISTS media_assets_storage_mode_check,
    DROP CONSTRAINT IF EXISTS media_assets_processing_result_check,
    DROP CONSTRAINT IF EXISTS media_assets_media_kind_check,
    DROP CONSTRAINT IF EXISTS media_assets_license_code_check;

ALTER TABLE app_private.media_assets
    DROP COLUMN IF EXISTS external_photo_reference,
    DROP COLUMN IF EXISTS external_attributions,
    DROP COLUMN IF EXISTS external_cache_expires_at,
    DROP COLUMN IF EXISTS media_kind;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_license_code_check CHECK (
        license_code IS NULL OR license_code IN (
            'CC-BY-4.0',
            'SEMTUR_INSTITUTIONAL',
            'PROPRIETARY'
        )
    ),
    ADD CONSTRAINT media_assets_processing_result_check CHECK (
        (processing_status = 'ready'
            AND processed_at IS NOT NULL
            AND checksum_sha256 IS NOT NULL
            AND width_px IS NOT NULL AND height_px IS NOT NULL
            AND alt_text IS NOT NULL AND length(trim(alt_text)) > 0
            AND credit IS NOT NULL AND length(trim(credit)) > 0
            AND license_code IS NOT NULL
            AND derivatives ?& ARRAY['thumb', 'card', 'hero']
            AND coalesce(length(trim(derivatives -> 'thumb' ->> 'storage_key')), 0) > 0
            AND coalesce(length(trim(derivatives -> 'card' ->> 'storage_key')), 0) > 0
            AND coalesce(length(trim(derivatives -> 'hero' ->> 'storage_key')), 0) > 0
            AND coalesce(derivatives -> 'thumb' ->> 'checksum_sha256', '') ~ '^[0-9a-f]{64}$'
            AND coalesce(derivatives -> 'card' ->> 'checksum_sha256', '') ~ '^[0-9a-f]{64}$'
            AND coalesce(derivatives -> 'hero' ->> 'checksum_sha256', '') ~ '^[0-9a-f]{64}$')
        OR (processing_status = 'rejected'
            AND processed_at IS NOT NULL
            AND rejected_reason IS NOT NULL
            AND length(trim(rejected_reason)) > 0)
        OR processing_status IN ('pending', 'processing', 'quarantined')
    ),
    ADD CONSTRAINT media_assets_storage_mode_check CHECK (
        (processing_status = 'ready' AND storage_key IS NOT NULL)
        OR (processing_status <> 'ready' AND storage_key IS NULL)
    );

COMMENT ON TABLE app_private.media_assets IS
    'Editorial media only. Google Place Photos are proxied in-memory and are never persisted.';
