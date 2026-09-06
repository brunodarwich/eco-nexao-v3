-- Migration: 20260906125246_eco_2605_widen_route_metadata_columns.sql
-- Description: Widen route contextual fields (best_season, connectivity, road_access) to TEXT
-- to accommodate detailed regional contextual descriptions from standardized route data packages (ECO-2604/ECO-2605).

BEGIN;

ALTER TABLE app_private.routes
    ALTER COLUMN best_season TYPE TEXT,
    ALTER COLUMN connectivity TYPE TEXT,
    ALTER COLUMN road_access TYPE TEXT;

COMMIT;
