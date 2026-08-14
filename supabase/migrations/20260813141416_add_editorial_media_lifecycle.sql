-- ECO-1702: structured editorial media lifecycle metadata.
-- This table remains private and unavailable to Data API roles.

ALTER TABLE app_private.media_assets
    ADD COLUMN license_code VARCHAR(40),
    ADD COLUMN processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    ADD COLUMN checksum_sha256 VARCHAR(64),
    ADD COLUMN width_px INTEGER,
    ADD COLUMN height_px INTEGER,
    ADD COLUMN derivatives JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN location extensions.geography(Point, 4326),
    ADD COLUMN processed_at TIMESTAMPTZ,
    ADD COLUMN rejected_reason TEXT,
    ADD COLUMN deleted_at TIMESTAMPTZ;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_license_code_check CHECK (
        license_code IS NULL OR license_code IN (
            'CC-BY-4.0',
            'SEMTUR_INSTITUTIONAL',
            'PROPRIETARY',
            'GOOGLE_PLACES_PROXY'
        )
    ),
    ADD CONSTRAINT media_assets_processing_status_check CHECK (
        processing_status IN ('pending', 'processing', 'ready', 'rejected', 'quarantined')
    ),
    ADD CONSTRAINT media_assets_checksum_sha256_check CHECK (
        checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'
    ),
    ADD CONSTRAINT media_assets_dimensions_check CHECK (
        (width_px IS NULL AND height_px IS NULL)
        OR (width_px > 0 AND height_px > 0)
    ),
    ADD CONSTRAINT media_assets_derivatives_check CHECK (
        jsonb_typeof(derivatives) = 'object'
    ),
    ADD CONSTRAINT media_assets_processing_result_check CHECK (
        (processing_status = 'ready'
            AND processed_at IS NOT NULL
            AND checksum_sha256 IS NOT NULL
            AND license_code IS NOT NULL
            AND length(trim(alt_text)) > 0
            AND length(trim(credit)) > 0)
        OR (processing_status = 'rejected'
            AND processed_at IS NOT NULL
            AND length(trim(rejected_reason)) > 0)
        OR processing_status IN ('pending', 'processing', 'quarantined')
    ),
    ADD CONSTRAINT media_assets_quarantine_check CHECK (
        deleted_at IS NULL OR processing_status = 'quarantined'
    );

CREATE INDEX media_assets_processing_queue_idx
    ON app_private.media_assets (processing_status, created_at)
    WHERE deleted_at IS NULL;

CREATE INDEX media_assets_quarantine_idx
    ON app_private.media_assets (deleted_at)
    WHERE deleted_at IS NOT NULL;
