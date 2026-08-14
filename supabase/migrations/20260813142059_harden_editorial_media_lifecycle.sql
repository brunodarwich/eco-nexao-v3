-- ECO-1702: close nullable CHECK gaps and distinguish stored media from Google proxy refs.

ALTER TABLE app_private.media_assets
    ADD COLUMN media_kind VARCHAR(20) NOT NULL DEFAULT 'stored',
    ADD COLUMN external_photo_reference TEXT,
    ADD COLUMN external_attributions JSONB,
    ADD COLUMN external_cache_expires_at TIMESTAMPTZ,
    ALTER COLUMN storage_key DROP NOT NULL,
    DROP CONSTRAINT media_assets_dimensions_check,
    DROP CONSTRAINT media_assets_processing_result_check;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_media_kind_check CHECK (
        media_kind IN ('stored', 'google_proxy')
    ),
    ADD CONSTRAINT media_assets_dimensions_check CHECK (
        (width_px IS NULL AND height_px IS NULL)
        OR (width_px IS NOT NULL AND height_px IS NOT NULL AND width_px > 0 AND height_px > 0)
    ),
    ADD CONSTRAINT media_assets_processing_result_check CHECK (
        (processing_status = 'ready'
            AND processed_at IS NOT NULL
            AND checksum_sha256 IS NOT NULL
            AND license_code IS NOT NULL
            AND alt_text IS NOT NULL AND length(trim(alt_text)) > 0
            AND credit IS NOT NULL AND length(trim(credit)) > 0
            AND width_px IS NOT NULL AND height_px IS NOT NULL
            AND derivatives ?& ARRAY['thumb', 'card', 'hero'])
        OR (processing_status = 'rejected'
            AND processed_at IS NOT NULL
            AND rejected_reason IS NOT NULL
            AND length(trim(rejected_reason)) > 0)
        OR processing_status IN ('pending', 'processing', 'quarantined')
    ),
    ADD CONSTRAINT media_assets_storage_mode_check CHECK (
        (media_kind = 'stored'
            AND storage_key IS NOT NULL
            AND license_code IS DISTINCT FROM 'GOOGLE_PLACES_PROXY'
            AND external_photo_reference IS NULL
            AND external_attributions IS NULL
            AND external_cache_expires_at IS NULL)
        OR (media_kind = 'google_proxy'
            AND storage_key IS NULL
            AND checksum_sha256 IS NULL
            AND derivatives = '{}'::jsonb
            AND license_code = 'GOOGLE_PLACES_PROXY'
            AND external_photo_reference IS NOT NULL
            AND length(trim(external_photo_reference)) > 0
            AND external_attributions IS NOT NULL
            AND jsonb_typeof(external_attributions) = 'array'
            AND jsonb_array_length(external_attributions) > 0
            AND external_cache_expires_at IS NOT NULL
            AND external_cache_expires_at <= created_at + interval '30 days')
    );

COMMENT ON COLUMN app_private.media_assets.processing_status IS
    'Existing records remain pending until an explicit audited media-processing backfill.';
