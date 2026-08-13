-- Migration: 20260811020000_rls_and_permissions.sql
-- Description: Defense-in-depth RLS and deny-by-default grants for ECOnexão domain.
-- Domain access is exclusively FastAPI -> PostgreSQL. Expo accesses Supabase Auth
-- and explicitly approved Storage flows only.

REVOKE ALL ON SCHEMA app_private FROM PUBLIC, anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA app_private
    REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_private
    REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_private
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;

ALTER TABLE app_private.regions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.route_origins ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.route_geometries ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.route_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.actor_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.route_actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.accessibility_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.actor_accessibility_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.external_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.actor_external_refs ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.ingestion_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.raw_source_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.reconciliation_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.field_provenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.favorite_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.favorite_actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.trip_actor_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.user_badges ENABLE ROW LEVEL SECURITY;

-- No policies are intentionally created here. Without schema USAGE, table grants,
-- and policies, anon/authenticated cannot use the Data API to bypass FastAPI.
-- A future direct Data API use requires its own accepted decision, migration,
-- per-operation grants, ownership policies, and positive/negative tests.

REVOKE ALL ON ALL TABLES IN SCHEMA app_private FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA app_private FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA app_private FROM PUBLIC, anon, authenticated;
