-- ECO-1902: deny residual JWTs after an Auth user is permanently deleted.
-- This table deliberately has no auth.users foreign key so the marker survives
-- the managed Auth cascade. It is private and never exposed through Data API.
CREATE TABLE app_private.deleted_user_tombstones (
    user_id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT deleted_user_tombstones_status_check
        CHECK (status IN ('processing', 'completed')),
    CONSTRAINT deleted_user_tombstones_completion_check CHECK (
        (status = 'processing' AND completed_at IS NULL)
        OR (status = 'completed' AND completed_at IS NOT NULL)
    )
);

ALTER TABLE app_private.deleted_user_tombstones ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_private.deleted_user_tombstones FROM PUBLIC, anon, authenticated;

COMMENT ON TABLE app_private.deleted_user_tombstones IS
    'Minimal deletion marker used to reject still-unexpired Supabase access tokens.';
