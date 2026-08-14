-- ECO-1702: stored binaries exist only after processing succeeds. Pending,
-- processing and rejected rows intentionally have no Storage object.
ALTER TABLE app_private.media_assets
    DROP CONSTRAINT media_assets_storage_mode_check;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_storage_mode_check CHECK (
        (media_kind = 'stored'
            AND external_photo_reference IS NULL
            AND external_attributions IS NULL
            AND external_cache_expires_at IS NULL
            AND (
                (processing_status = 'ready' AND storage_key IS NOT NULL)
                OR (processing_status <> 'ready' AND storage_key IS NULL)
            ))
        OR
        (media_kind = 'google_proxy'
            AND license_code = 'GOOGLE_PLACES_PROXY'
            AND storage_key IS NULL
            AND checksum_sha256 IS NULL
            AND width_px IS NULL
            AND height_px IS NULL
            AND derivatives = '{}'::jsonb
            AND external_photo_reference IS NOT NULL
            AND length(trim(external_photo_reference)) > 0
            AND external_attributions IS NOT NULL
            AND jsonb_typeof(external_attributions) = 'array'
            AND jsonb_array_length(external_attributions) > 0
            AND external_cache_expires_at IS NOT NULL
            AND external_cache_expires_at > created_at
            AND external_cache_expires_at <= created_at + interval '30 days')
    );
