-- ECO-1702: validate ready metadata according to stored vs Google proxy media kind.

ALTER TABLE app_private.media_assets
    DROP CONSTRAINT media_assets_processing_result_check,
    DROP CONSTRAINT media_assets_storage_mode_check;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_processing_result_check CHECK (
        (processing_status = 'ready'
            AND processed_at IS NOT NULL
            AND license_code IS NOT NULL
            AND alt_text IS NOT NULL AND length(trim(alt_text)) > 0
            AND credit IS NOT NULL AND length(trim(credit)) > 0
            AND (
                (media_kind = 'stored'
                    AND checksum_sha256 IS NOT NULL
                    AND width_px IS NOT NULL AND height_px IS NOT NULL
                    AND derivatives ?& ARRAY['thumb', 'card', 'hero']
                    AND jsonb_typeof(derivatives -> 'thumb') = 'object'
                    AND jsonb_typeof(derivatives -> 'card') = 'object'
                    AND jsonb_typeof(derivatives -> 'hero') = 'object'
                    AND length(trim(derivatives -> 'thumb' ->> 'storage_key')) > 0
                    AND length(trim(derivatives -> 'card' ->> 'storage_key')) > 0
                    AND length(trim(derivatives -> 'hero' ->> 'storage_key')) > 0
                    AND (derivatives -> 'thumb' ->> 'checksum_sha256') ~ '^[0-9a-f]{64}$'
                    AND (derivatives -> 'card' ->> 'checksum_sha256') ~ '^[0-9a-f]{64}$'
                    AND (derivatives -> 'hero' ->> 'checksum_sha256') ~ '^[0-9a-f]{64}$')
                OR (media_kind = 'google_proxy'
                    AND external_cache_expires_at > created_at)
            ))
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
            AND width_px IS NULL AND height_px IS NULL
            AND derivatives = '{}'::jsonb
            AND license_code = 'GOOGLE_PLACES_PROXY'
            AND external_photo_reference IS NOT NULL
            AND length(trim(external_photo_reference)) > 0
            AND external_attributions IS NOT NULL
            AND jsonb_typeof(external_attributions) = 'array'
            AND jsonb_array_length(external_attributions) > 0
            AND external_cache_expires_at IS NOT NULL
            AND external_cache_expires_at > created_at
            AND external_cache_expires_at <= created_at + interval '30 days')
    );
