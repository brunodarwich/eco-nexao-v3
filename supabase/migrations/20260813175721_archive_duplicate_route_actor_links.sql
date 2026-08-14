-- ECO-1604: preserve duplicate route links during an editorial actor merge.
-- A duplicated relationship is archived in place instead of being deleted.

ALTER TABLE app_private.route_actors
    ADD COLUMN archived_at TIMESTAMPTZ,
    ADD COLUMN archived_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    ADD COLUMN archive_reason TEXT;

ALTER TABLE app_private.route_actors
    ADD CONSTRAINT chk_route_actors_archive_metadata
    CHECK (
        (archived_at IS NULL AND archived_by IS NULL AND archive_reason IS NULL)
        OR
        (archived_at IS NOT NULL AND archived_by IS NOT NULL AND btrim(archive_reason) <> '')
    );

CREATE INDEX idx_route_actors_active_route_actor
    ON app_private.route_actors (route_id, actor_id)
    WHERE archived_at IS NULL;

COMMENT ON COLUMN app_private.route_actors.archived_at IS
    'Soft archive timestamp used by audited editorial reconciliation.';
COMMENT ON COLUMN app_private.route_actors.archived_by IS
    'Supabase identity that archived the relationship.';
COMMENT ON COLUMN app_private.route_actors.archive_reason IS
    'Mandatory human-readable reason for the reversible archive.';
