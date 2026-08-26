-- ECO-2306 forward remediation. The registered 20260824040000 migration is
-- immutable; every domain reference below is explicitly app_private.
BEGIN;

ALTER TABLE app_private.actors
    ADD COLUMN IF NOT EXISTS region_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'actors_region_id_fkey'
          AND conrelid = 'app_private.actors'::regclass
    ) THEN
        ALTER TABLE app_private.actors
            ADD CONSTRAINT actors_region_id_fkey
            FOREIGN KEY (region_id)
            REFERENCES app_private.regions(id)
            ON DELETE SET NULL
            NOT VALID;
    END IF;
END
$$;

ALTER TABLE app_private.actors
    VALIDATE CONSTRAINT actors_region_id_fkey;

-- Only unambiguous route ownership may repair/backfill a territorial link.
WITH actor_regions AS (
    SELECT
        ra.actor_id,
        (array_agg(DISTINCT r.region_id))[1] AS region_id
    FROM app_private.route_actors AS ra
    JOIN app_private.routes AS r ON r.id = ra.route_id
    WHERE ra.archived_at IS NULL
      AND r.deleted_at IS NULL
    GROUP BY ra.actor_id
    HAVING count(DISTINCT r.region_id) = 1
)
UPDATE app_private.actors AS a
SET region_id = ar.region_id,
    updated_at = clock_timestamp()
FROM actor_regions AS ar
WHERE a.id = ar.actor_id
  AND a.region_id IS DISTINCT FROM ar.region_id;

CREATE INDEX IF NOT EXISTS idx_actors_region_id
    ON app_private.actors (region_id);

CREATE INDEX IF NOT EXISTS idx_actors_region_category_active
    ON app_private.actors (region_id, category_id)
    WHERE deleted_at IS NULL AND location IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_route_actors_map_priority
    ON app_private.route_actors (
        route_id,
        is_featured DESC,
        sort_order ASC,
        actor_id
    )
    WHERE archived_at IS NULL;

COMMIT;
