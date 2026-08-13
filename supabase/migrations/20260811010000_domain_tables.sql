-- Migration: 20260811010000_domain_tables.sql
-- Description: Domain model tables for ECOnexão (ECO-0201 to ECO-0206)

-- 1. Helper function for updated_at timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = clock_timestamp();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

REVOKE ALL ON FUNCTION public.update_updated_at_column() FROM PUBLIC, anon, authenticated;

-- -----------------------------------------------------------------------------
-- ECO-0201: Regiões, Rotas, Origens e Geometrias
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    center extensions.geography(Point, 4326),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_regions_updated_at
    BEFORE UPDATE ON public.regions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_regions_center ON public.regions USING GIST (center);
CREATE INDEX IF NOT EXISTS idx_regions_active ON public.regions (is_active) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS public.routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID NOT NULL REFERENCES public.regions(id) ON DELETE RESTRICT,
    slug VARCHAR(150) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    city VARCHAR(100) NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    is_verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    best_season VARCHAR(100),
    connectivity VARCHAR(100),
    road_access VARCHAR(100),
    payment_info TEXT,
    cover_media_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    deleted_at TIMESTAMPTZ
);

CREATE TRIGGER update_routes_updated_at
    BEFORE UPDATE ON public.routes
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_routes_region_id ON public.routes (region_id);
CREATE INDEX IF NOT EXISTS idx_routes_status ON public.routes (status) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS public.route_origins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES public.routes(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location extensions.geography(Point, 4326) NOT NULL,
    distance_m INTEGER CHECK (distance_m >= 0),
    duration_s INTEGER CHECK (duration_s >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_route_origins_route_code UNIQUE (route_id, code)
);

CREATE TRIGGER update_route_origins_updated_at
    BEFORE UPDATE ON public.route_origins
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_route_origins_location ON public.route_origins USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_route_origins_route_id ON public.route_origins (route_id);

CREATE TABLE IF NOT EXISTS public.route_geometries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_origin_id UUID NOT NULL REFERENCES public.route_origins(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'osrm',
    geometry extensions.geography(LineString, 4326) NOT NULL,
    encoded_polyline TEXT,
    distance_m INTEGER CHECK (distance_m >= 0),
    duration_s INTEGER CHECK (duration_s >= 0),
    source_collected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_route_geometries_updated_at
    BEFORE UPDATE ON public.route_geometries
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_route_geometries_geometry ON public.route_geometries USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_route_geometries_origin ON public.route_geometries (route_origin_id);

-- -----------------------------------------------------------------------------
-- ECO-0202: Atores, Categorias e Acessibilidade
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.actor_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    icon VARCHAR(100),
    color VARCHAR(50),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_actor_categories_updated_at
    BEFORE UPDATE ON public.actor_categories
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(150) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID NOT NULL REFERENCES public.actor_categories(id) ON DELETE RESTRICT,
    sub_category VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state_code VARCHAR(2),
    phone VARCHAR(50),
    email VARCHAR(255),
    instagram VARCHAR(100),
    website VARCHAR(255),
    opening_hours JSONB DEFAULT '{}'::jsonb,
    payment_methods JSONB DEFAULT '[]'::jsonb,
    location extensions.geography(Point, 4326),
    green_badge_status VARCHAR(50) DEFAULT 'none',
    verification_status VARCHAR(50) DEFAULT 'unverified',
    google_rating NUMERIC(3, 2) CHECK (google_rating IS NULL OR (google_rating >= 0 AND google_rating <= 5.0)),
    google_review_count INTEGER CHECK (google_review_count IS NULL OR google_review_count >= 0),
    google_data_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    deleted_at TIMESTAMPTZ
);

CREATE TRIGGER update_actors_updated_at
    BEFORE UPDATE ON public.actors
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_actors_location ON public.actors USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_actors_category_id ON public.actors (category_id);
CREATE INDEX IF NOT EXISTS idx_actors_city ON public.actors (city);

CREATE TABLE IF NOT EXISTS public.route_actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES public.routes(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    distance_to_route_m DOUBLE PRECISION CHECK (distance_to_route_m IS NULL OR distance_to_route_m >= 0),
    route_segment_index INTEGER,
    origin_flags JSONB DEFAULT '{}'::jsonb,
    is_featured BOOLEAN NOT NULL DEFAULT false,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_route_actors_route_actor UNIQUE (route_id, actor_id)
);

CREATE TRIGGER update_route_actors_updated_at
    BEFORE UPDATE ON public.route_actors
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_route_actors_route_id ON public.route_actors (route_id);
CREATE INDEX IF NOT EXISTS idx_route_actors_actor_id ON public.route_actors (actor_id);

CREATE TABLE IF NOT EXISTS public.accessibility_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_accessibility_features_updated_at
    BEFORE UPDATE ON public.accessibility_features
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.actor_accessibility_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    feature_id UUID NOT NULL REFERENCES public.accessibility_features(id) ON DELETE CASCADE,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'self_declared',
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_actor_accessibility_actor_feature UNIQUE (actor_id, feature_id)
);

CREATE TRIGGER update_actor_accessibility_features_updated_at
    BEFORE UPDATE ON public.actor_accessibility_features
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- -----------------------------------------------------------------------------
-- ECO-0203: Alertas e Mídia
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.route_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES public.routes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    source VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_route_alerts_updated_at
    BEFORE UPDATE ON public.route_alerts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_route_alerts_lookup ON public.route_alerts (route_id, is_active, starts_at, ends_at);

CREATE TABLE IF NOT EXISTS public.media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_type VARCHAR(50) NOT NULL,
    owner_id UUID NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    alt_text TEXT,
    credit TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_media_assets_updated_at
    BEFORE UPDATE ON public.media_assets
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_media_assets_owner ON public.media_assets (owner_type, owner_id);

-- -----------------------------------------------------------------------------
-- ECO-0204: Proveniência e Ingestão
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.external_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_external_sources_updated_at
    BEFORE UPDATE ON public.external_sources
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.actor_external_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES public.external_sources(id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL,
    source_url TEXT,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_actor_external_refs_source_extid UNIQUE (source_id, external_id)
);

CREATE TRIGGER update_actor_external_refs_updated_at
    BEFORE UPDATE ON public.actor_external_refs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES public.external_sources(id) ON DELETE RESTRICT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    parameters JSONB DEFAULT '{}'::jsonb,
    stats JSONB DEFAULT '{}'::jsonb,
    error_log TEXT,
    estimated_cost NUMERIC(10, 4) DEFAULT 0,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_ingestion_runs_updated_at
    BEFORE UPDATE ON public.ingestion_runs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.raw_source_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID NOT NULL REFERENCES public.ingestion_runs(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    payload JSONB NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    license_terms TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_raw_source_records_updated_at
    BEFORE UPDATE ON public.raw_source_records
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.reconciliation_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id_a UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    actor_id_b UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    score NUMERIC(5, 4) NOT NULL CHECK (score >= 0 AND score <= 1),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    decision_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_reconciliation_candidates_updated_at
    BEFORE UPDATE ON public.reconciliation_candidates
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.field_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_table VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL REFERENCES public.external_sources(id) ON DELETE CASCADE,
    confidence NUMERIC(5, 4) DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    collected_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_field_provenance_updated_at
    BEFORE UPDATE ON public.field_provenance
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- -----------------------------------------------------------------------------
-- ECO-0205: Usuário, Preferências e Favoritos
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    location VARCHAR(255),
    avatar_media_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    active_region_id UUID REFERENCES public.regions(id) ON DELETE SET NULL,
    screen_reader_mode BOOLEAN NOT NULL DEFAULT false,
    high_contrast BOOLEAN NOT NULL DEFAULT false,
    text_scale NUMERIC(3, 2) NOT NULL DEFAULT 1.0 CHECK (text_scale >= 0.5 AND text_scale <= 3.0),
    locale VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.favorite_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES public.routes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_favorite_routes_user_route UNIQUE (user_id, route_id)
);

CREATE TRIGGER update_favorite_routes_updated_at
    BEFORE UPDATE ON public.favorite_routes
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.favorite_actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_favorite_actors_user_actor UNIQUE (user_id, actor_id)
);

CREATE TRIGGER update_favorite_actors_updated_at
    BEFORE UPDATE ON public.favorite_actors
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- -----------------------------------------------------------------------------
-- ECO-0206: Viagens, Visitas e Selos
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES public.routes(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_trips_updated_at
    BEFORE UPDATE ON public.trips
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.trip_actor_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES public.actors(id) ON DELETE CASCADE,
    visited_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    confirmation_method VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_trip_actor_visits_trip_actor UNIQUE (trip_id, actor_id)
);

CREATE TRIGGER update_trip_actor_visits_updated_at
    BEFORE UPDATE ON public.trip_actor_visits
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    badge_code VARCHAR(100) NOT NULL,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_user_badges_user_badge UNIQUE (user_id, badge_code)
);

CREATE TRIGGER update_user_badges_updated_at
    BEFORE UPDATE ON public.user_badges
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- The FastAPI domain is intentionally outside the Data API exposed schemas.
ALTER TABLE public.regions SET SCHEMA app_private;
ALTER TABLE public.routes SET SCHEMA app_private;
ALTER TABLE public.route_origins SET SCHEMA app_private;
ALTER TABLE public.route_geometries SET SCHEMA app_private;
ALTER TABLE public.actor_categories SET SCHEMA app_private;
ALTER TABLE public.actors SET SCHEMA app_private;
ALTER TABLE public.route_actors SET SCHEMA app_private;
ALTER TABLE public.accessibility_features SET SCHEMA app_private;
ALTER TABLE public.actor_accessibility_features SET SCHEMA app_private;
ALTER TABLE public.route_alerts SET SCHEMA app_private;
ALTER TABLE public.media_assets SET SCHEMA app_private;
ALTER TABLE public.external_sources SET SCHEMA app_private;
ALTER TABLE public.actor_external_refs SET SCHEMA app_private;
ALTER TABLE public.ingestion_runs SET SCHEMA app_private;
ALTER TABLE public.raw_source_records SET SCHEMA app_private;
ALTER TABLE public.reconciliation_candidates SET SCHEMA app_private;
ALTER TABLE public.field_provenance SET SCHEMA app_private;
ALTER TABLE public.profiles SET SCHEMA app_private;
ALTER TABLE public.user_preferences SET SCHEMA app_private;
ALTER TABLE public.favorite_routes SET SCHEMA app_private;
ALTER TABLE public.favorite_actors SET SCHEMA app_private;
ALTER TABLE public.trips SET SCHEMA app_private;
ALTER TABLE public.trip_actor_visits SET SCHEMA app_private;
ALTER TABLE public.user_badges SET SCHEMA app_private;

ALTER FUNCTION public.update_updated_at_column() SET SCHEMA app_private;
REVOKE ALL ON FUNCTION app_private.update_updated_at_column()
    FROM PUBLIC, anon, authenticated;

ALTER TABLE app_private.routes
    ADD CONSTRAINT fk_routes_cover_media
    FOREIGN KEY (cover_media_id) REFERENCES app_private.media_assets(id) ON DELETE SET NULL;

ALTER TABLE app_private.profiles
    ADD CONSTRAINT fk_profiles_avatar_media
    FOREIGN KEY (avatar_media_id) REFERENCES app_private.media_assets(id) ON DELETE SET NULL;
