-- Migration: 20260824040000_actor_region_layers_adr0011.sql
-- Description: Add region_id to actors and backfill from routes/route_actors (ADR 0011 / ECO-2306)

-- 1. Add region_id column to app_private.actors
ALTER TABLE app_private.actors
ADD COLUMN IF NOT EXISTS region_id UUID REFERENCES app_private.regions(id) ON DELETE SET NULL;

-- 2. Create index on actors.region_id
CREATE INDEX IF NOT EXISTS idx_actors_region_id ON app_private.actors (region_id);

-- 3. Idempotent backfill relating actors.region_id from route_actors and routes
UPDATE app_private.actors a
SET region_id = sub.region_id,
    updated_at = clock_timestamp()
FROM (
    SELECT ra.actor_id, r.region_id
    FROM app_private.route_actors ra
    JOIN app_private.routes r ON r.id = ra.route_id
    WHERE ra.archived_at IS NULL
    ORDER BY ra.created_at ASC
) sub
WHERE a.id = sub.actor_id
  AND a.region_id IS NULL;
