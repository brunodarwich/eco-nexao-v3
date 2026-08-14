-- ECO-1702: PostgreSQL CHECK treats NULL as passing; force missing derivative metadata false.

ALTER TABLE app_private.media_assets
    DROP CONSTRAINT media_assets_processing_result_check;

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
                    AND coalesce(length(trim(derivatives -> 'thumb' ->> 'storage_key')), 0) > 0
                    AND coalesce(length(trim(derivatives -> 'card' ->> 'storage_key')), 0) > 0
                    AND coalesce(length(trim(derivatives -> 'hero' ->> 'storage_key')), 0) > 0
                    AND coalesce(derivatives -> 'thumb' ->> 'checksum_sha256', '')
                        ~ '^[0-9a-f]{64}$'
                    AND coalesce(derivatives -> 'card' ->> 'checksum_sha256', '')
                        ~ '^[0-9a-f]{64}$'
                    AND coalesce(derivatives -> 'hero' ->> 'checksum_sha256', '')
                        ~ '^[0-9a-f]{64}$')
                OR (media_kind = 'google_proxy'
                    AND external_cache_expires_at > created_at)
            ))
        OR (processing_status = 'rejected'
            AND processed_at IS NOT NULL
            AND rejected_reason IS NOT NULL
            AND length(trim(rejected_reason)) > 0)
        OR processing_status IN ('pending', 'processing', 'quarantined')
    );
