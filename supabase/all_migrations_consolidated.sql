-- Migration: 20260811000000_init_postgis_and_base_schemas.sql
-- Description: Scaffolding base do Supabase - Ativação do PostGIS, schemas base, revogação de privilégios padrão e RLS-on por padrão.
-- Specification references: docs/backend_integration_spec.md §4, §6, §8.6; AGENTS.md; ADR 0002

-- 1. Garante a existência do schema 'extensions' e ativa a extensão PostGIS
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA extensions;

-- 2. Define o search_path padrão para incluir public e extensions
ALTER DATABASE postgres SET search_path TO public, extensions;
SET search_path TO public, extensions;

-- 3. Configuração de Schemas Base (públicos e privados de domínio)
-- app_private guarda objetos internos do backend FastAPI que não devem ser expostos pela Data API (PostgREST)
CREATE SCHEMA IF NOT EXISTS app_private;

-- 4. Garantir revogação de permissões padrão automáticas nos schemas (Data API explicitly exposed)
-- Por padrão, nenhuma tabela nova criada em public ou app_private será exposta para 'anon' ou 'authenticated' sem GRANT explícito.
REVOKE ALL ON SCHEMA public FROM anon, authenticated;
GRANT USAGE ON SCHEMA public TO anon, authenticated;

REVOKE ALL ON SCHEMA app_private FROM anon, authenticated;

-- Revoga permissões automáticas para tabelas, funções e sequências futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA app_private REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_private REVOKE ALL ON FUNCTIONS FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_private REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_private REVOKE ALL ON SEQUENCES FROM anon, authenticated;

-- 5. Trigger de Evento DDL para Habilitar RLS em qualquer nova tabela criada no banco (RLS-on por padrão)
-- Regra de segurança: toda tabela de aplicação deve obrigatoriamente possuir Row Level Security habilitado.
CREATE OR REPLACE FUNCTION extensions.auto_enable_rls()
RETURNS event_trigger
LANGUAGE plpgsql
AS $$
DECLARE
  cmd record;
  table_name name;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS')
  LOOP
    IF cmd.schema_name IN ('public', 'app_private') AND cmd.object_type = 'table' THEN
      SELECT relname INTO table_name FROM pg_class WHERE oid = cmd.objid;
      IF table_name IS NOT NULL THEN
        EXECUTE format(
          'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY;',
          cmd.schema_name,
          table_name
        );
      END IF;
    END IF;
  END LOOP;
END;
$$;

REVOKE ALL ON FUNCTION extensions.auto_enable_rls() FROM PUBLIC, anon, authenticated;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_event_trigger WHERE evtname = 'ensure_rls_enabled_on_create') THEN
    CREATE EVENT TRIGGER ensure_rls_enabled_on_create ON ddl_command_end
    WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS')
    EXECUTE FUNCTION extensions.auto_enable_rls();
  END IF;
END $$;

-- 6. Documentação das Regras de RLS e Segurança Supabase (Normativa AGENTS.md e spec §8.6):
-- - Proibido criar objetos customizados nos schemas gerenciados: auth, storage ou realtime.
-- - Ownership de usuário DEVE usar: (select auth.uid()) = user_id
-- - NUNCA utilizar auth.role() para autorização (usuários anônimos também assumem o papel 'authenticated').
-- - Políticas de UPDATE exigem obrigatoriamente as cláusulas USING e WITH CHECK.
-- - Views expostas DEVEM ser criadas com WITH (security_invoker = true).
-- - Proibido o uso de SECURITY DEFINER para contornar políticas de RLS.
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
-- Pin the trigger function lookup path to remove role-dependent resolution.
ALTER FUNCTION app_private.update_updated_at_column()
    SET search_path = pg_catalog, app_private;
-- Domain objects and extension types are explicitly schema-qualified.
-- Avoid changing name resolution globally for unrelated applications.
ALTER DATABASE postgres RESET search_path;
-- Migration: 20260812120000_storage_buckets_and_policies.sql
-- Description: Provision Supabase Storage buckets for avatars and editorial media with RLS policies.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('avatars', 'avatars', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']),
    ('editorial-media', 'editorial-media', true, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Supabase owns storage.objects and already enables RLS on this managed table.
-- Project migrations may create policies, but must not ALTER the managed table.

-- Public read policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public Read Avatars'
    ) THEN
        CREATE POLICY "Public Read Avatars" ON storage.objects
            FOR SELECT
            USING (bucket_id = 'avatars');
    END IF;
END $$;

-- Authenticated user upload policy for avatars (isolated by folder = user_id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Upload Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Upload Avatar" ON storage.objects
            FOR INSERT
            TO authenticated
            WITH CHECK (
                bucket_id = 'avatars' 
                AND (
                    (storage.foldername(name))[1] = auth.uid()::text 
                    OR auth.uid() IS NOT NULL
                )
            );
    END IF;
END $$;

-- Authenticated user update policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Update Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Update Avatar" ON storage.objects
            FOR UPDATE
            TO authenticated
            USING (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            )
            WITH CHECK (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            );
    END IF;
END $$;

-- Authenticated user delete policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Delete Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Delete Avatar" ON storage.objects
            FOR DELETE
            TO authenticated
            USING (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            );
    END IF;
END $$;

-- Public read policy for editorial-media
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public Read Editorial Media'
    ) THEN
        CREATE POLICY "Public Read Editorial Media" ON storage.objects
            FOR SELECT
            USING (bucket_id = 'editorial-media');
    END IF;
END $$;
-- Migration: harden_storage_buckets_and_policies
-- Description: Enforce avatar ownership, prevent public object listing, and
--              align bucket visibility and MIME constraints with ADR 0008.

-- Bucket rows are Supabase-managed configuration data. This migration does not
-- create custom objects in the managed storage schema.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
    ('avatars', 'avatars', true, 5242880, ARRAY['image/webp']),
    ('editorial-media', 'editorial-media', true, 10485760, ARRAY['image/webp']),
    (
        'raw-ingestion',
        'raw-ingestion',
        false,
        20971520,
        ARRAY['image/jpeg', 'image/png', 'image/webp']
    )
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Public buckets are downloaded through /object/public without an RLS SELECT
-- policy. Removing broad SELECT policies prevents anon/authenticated clients
-- from listing every object in those buckets through the Storage API.
DROP POLICY IF EXISTS "Public Read Avatars" ON storage.objects;
DROP POLICY IF EXISTS "Public Read Editorial Media" ON storage.objects;

-- Recreate every avatar policy so projects that already applied the vulnerable
-- migration converge to the same secure state. Signed-in anonymous users also
-- use the authenticated database role, therefore folder ownership is mandatory.
DROP POLICY IF EXISTS "Authenticated User Select Own Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Upload Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Update Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Delete Avatar" ON storage.objects;

CREATE POLICY "Authenticated User Select Own Avatar"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
);

CREATE POLICY "Authenticated User Upload Avatar"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'avatars'
    AND cardinality(storage.foldername(name)) = 1
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
    AND lower(storage.extension(name)) = 'webp'
);

CREATE POLICY "Authenticated User Update Avatar"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
)
WITH CHECK (
    bucket_id = 'avatars'
    AND cardinality(storage.foldername(name)) = 1
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
    AND lower(storage.extension(name)) = 'webp'
);

CREATE POLICY "Authenticated User Delete Avatar"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
);

-- editorial-media and raw-ingestion deliberately have no client mutation
-- policies. The trusted FastAPI backend is the only writer and uses its secret
-- server-side credential after domain authorization.
-- ECO-1403: private editorial RBAC, workflow state and immutable audit trail.

CREATE TABLE app_private.editorial_role_capabilities (
    role VARCHAR(20) NOT NULL,
    capability VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT editorial_role_capabilities_pk PRIMARY KEY (role, capability),
    CONSTRAINT editorial_role_capabilities_role_check
        CHECK (role IN ('admin', 'editor', 'reviewer', 'publisher'))
);

INSERT INTO app_private.editorial_role_capabilities (role, capability)
VALUES
    ('admin', 'memberships.manage'),
    ('admin', 'invitations.manage'),
    ('admin', 'categories.manage'),
    ('admin', 'audit.read'),
    ('admin', 'content.archive'),
    ('editor', 'content.draft.create'),
    ('editor', 'content.draft.update'),
    ('editor', 'content.review.submit'),
    ('editor', 'content.archive.draft'),
    ('reviewer', 'content.review.read'),
    ('reviewer', 'content.review.reject'),
    ('publisher', 'content.review.read'),
    ('publisher', 'content.review.reject'),
    ('publisher', 'content.publish'),
    ('publisher', 'content.unpublish'),
    ('publisher', 'content.archive')
ON CONFLICT DO NOTHING;

CREATE TABLE app_private.editorial_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    scope_type VARCHAR(20) NOT NULL DEFAULT 'global',
    scope_id UUID,
    granted_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    revoked_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    revoked_at TIMESTAMPTZ,
    revoke_reason TEXT,
    CONSTRAINT editorial_memberships_role_check
        CHECK (role IN ('admin', 'editor', 'reviewer', 'publisher')),
    CONSTRAINT editorial_memberships_scope_check CHECK (
        (scope_type = 'global' AND scope_id IS NULL)
        OR (scope_type = 'region' AND scope_id IS NOT NULL)
    ),
    CONSTRAINT editorial_memberships_revocation_check CHECK (
        (revoked_at IS NULL AND revoked_by IS NULL AND revoke_reason IS NULL)
        OR (revoked_at IS NOT NULL AND revoked_by IS NOT NULL AND length(trim(revoke_reason)) > 0)
    )
);

CREATE UNIQUE INDEX editorial_memberships_active_unique
ON app_private.editorial_memberships (
    user_id, role, scope_type, COALESCE(scope_id, '00000000-0000-0000-0000-000000000000'::uuid)
)
WHERE revoked_at IS NULL;
CREATE INDEX editorial_memberships_active_lookup
ON app_private.editorial_memberships (user_id, scope_type, scope_id)
WHERE revoked_at IS NULL;

CREATE TABLE app_private.editorial_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_hash VARCHAR(64) NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL,
    scope_type VARCHAR(20) NOT NULL DEFAULT 'global',
    scope_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    invited_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    accepted_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT editorial_invitations_hash_check CHECK (
        email_hash ~ '^[0-9a-f]{64}$' AND token_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT editorial_invitations_role_check
        CHECK (role IN ('admin', 'editor', 'reviewer', 'publisher')),
    CONSTRAINT editorial_invitations_scope_check CHECK (
        (scope_type = 'global' AND scope_id IS NULL)
        OR (scope_type = 'region' AND scope_id IS NOT NULL)
    ),
    CONSTRAINT editorial_invitations_status_check
        CHECK (status IN ('pending', 'accepted', 'expired', 'revoked'))
);

CREATE TABLE app_private.editorial_resource_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(20) NOT NULL,
    resource_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    reviewed_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    published_by UUID REFERENCES auth.users(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT editorial_resource_states_resource_check
        CHECK (resource_type IN ('region', 'route', 'origin', 'actor', 'media')),
    CONSTRAINT editorial_resource_states_status_check
        CHECK (status IN ('draft', 'review', 'published', 'archived')),
    CONSTRAINT editorial_resource_states_resource_unique UNIQUE (resource_type, resource_id)
);

CREATE TRIGGER update_editorial_resource_states_updated_at
BEFORE UPDATE ON app_private.editorial_resource_states
FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at_column();

CREATE TABLE app_private.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    actor_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    action VARCHAR(40) NOT NULL,
    resource_type VARCHAR(40) NOT NULL,
    resource_id UUID NOT NULL,
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason TEXT,
    request_id UUID,
    CONSTRAINT audit_logs_action_check CHECK (
        action IN (
            'CREATE', 'UPDATE', 'TRANSITION_STATUS', 'DELETE', 'RECONCILE',
            'MEMBERSHIP_GRANT', 'MEMBERSHIP_REVOKE', 'INVITATION_CREATE',
            'INVITATION_REVOKE'
        )
    ),
    CONSTRAINT audit_logs_changes_check CHECK (jsonb_typeof(changes) = 'object')
);

CREATE INDEX audit_logs_resource_lookup
ON app_private.audit_logs (resource_type, resource_id, "timestamp" DESC);
CREATE INDEX audit_logs_actor_lookup
ON app_private.audit_logs (actor_id, "timestamp" DESC);

CREATE FUNCTION app_private.prevent_audit_log_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, app_private
AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only' USING ERRCODE = '42501';
END;
$$;

REVOKE ALL ON FUNCTION app_private.prevent_audit_log_mutation() FROM PUBLIC;

CREATE TRIGGER audit_logs_append_only
BEFORE UPDATE OR DELETE ON app_private.audit_logs
FOR EACH ROW EXECUTE FUNCTION app_private.prevent_audit_log_mutation();

ALTER TABLE app_private.editorial_role_capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.editorial_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.editorial_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.editorial_resource_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.audit_logs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON app_private.editorial_role_capabilities FROM PUBLIC, anon, authenticated;
REVOKE ALL ON app_private.editorial_memberships FROM PUBLIC, anon, authenticated;
REVOKE ALL ON app_private.editorial_invitations FROM PUBLIC, anon, authenticated;
REVOKE ALL ON app_private.editorial_resource_states FROM PUBLIC, anon, authenticated;
REVOKE ALL ON app_private.audit_logs FROM PUBLIC, anon, authenticated;
-- ECO-1503: make imported route geometry auditable and spatial relations safe.
ALTER TABLE app_private.route_geometries
    ADD COLUMN bounds JSONB,
    ADD COLUMN source_hash VARCHAR(64);

ALTER TABLE app_private.route_geometries
    ADD CONSTRAINT uq_route_geometries_origin_provider
        UNIQUE (route_origin_id, provider),
    ADD CONSTRAINT ck_route_geometries_source_hash
        CHECK (source_hash IS NULL OR source_hash ~ '^[0-9a-f]{64}$'),
    ADD CONSTRAINT ck_route_geometries_bounds
        CHECK (
            bounds IS NULL OR (
                bounds ?& ARRAY['min_lat', 'max_lat', 'min_lon', 'max_lon']
                AND jsonb_typeof(bounds->'min_lat') = 'number'
                AND jsonb_typeof(bounds->'max_lat') = 'number'
                AND jsonb_typeof(bounds->'min_lon') = 'number'
                AND jsonb_typeof(bounds->'max_lon') = 'number'
                AND (bounds->>'min_lat')::double precision
                    <= (bounds->>'max_lat')::double precision
                AND (bounds->>'min_lon')::double precision
                    <= (bounds->>'max_lon')::double precision
            )
        ),
    ADD CONSTRAINT ck_route_geometries_valid_linestring
        CHECK (
            NOT extensions.ST_IsEmpty(geometry::extensions.geometry)
            AND extensions.ST_IsValid(geometry::extensions.geometry)
            AND extensions.ST_NPoints(geometry::extensions.geometry) >= 2
            AND extensions.ST_SRID(geometry::extensions.geometry) = 4326
        );

ALTER TABLE app_private.route_actors
    ALTER COLUMN origin_flags SET NOT NULL,
    ADD CONSTRAINT ck_route_actors_segment_nonnegative
        CHECK (route_segment_index IS NULL OR route_segment_index >= 0);
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
-- ECO-1702: close nullable CHECK gaps and distinguish stored media from Google proxy refs.

ALTER TABLE app_private.media_assets
    ADD COLUMN media_kind VARCHAR(20) NOT NULL DEFAULT 'stored',
    ADD COLUMN external_photo_reference TEXT,
    ADD COLUMN external_attributions JSONB,
    ADD COLUMN external_cache_expires_at TIMESTAMPTZ,
    ALTER COLUMN storage_key DROP NOT NULL,
    DROP CONSTRAINT media_assets_dimensions_check,
    DROP CONSTRAINT media_assets_processing_result_check;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_media_kind_check CHECK (
        media_kind IN ('stored', 'google_proxy')
    ),
    ADD CONSTRAINT media_assets_dimensions_check CHECK (
        (width_px IS NULL AND height_px IS NULL)
        OR (width_px IS NOT NULL AND height_px IS NOT NULL AND width_px > 0 AND height_px > 0)
    ),
    ADD CONSTRAINT media_assets_processing_result_check CHECK (
        (processing_status = 'ready'
            AND processed_at IS NOT NULL
            AND checksum_sha256 IS NOT NULL
            AND license_code IS NOT NULL
            AND alt_text IS NOT NULL AND length(trim(alt_text)) > 0
            AND credit IS NOT NULL AND length(trim(credit)) > 0
            AND width_px IS NOT NULL AND height_px IS NOT NULL
            AND derivatives ?& ARRAY['thumb', 'card', 'hero'])
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
            AND derivatives = '{}'::jsonb
            AND license_code = 'GOOGLE_PLACES_PROXY'
            AND external_photo_reference IS NOT NULL
            AND length(trim(external_photo_reference)) > 0
            AND external_attributions IS NOT NULL
            AND jsonb_typeof(external_attributions) = 'array'
            AND jsonb_array_length(external_attributions) > 0
            AND external_cache_expires_at IS NOT NULL
            AND external_cache_expires_at <= created_at + interval '30 days')
    );

COMMENT ON COLUMN app_private.media_assets.processing_status IS
    'Existing records remain pending until an explicit audited media-processing backfill.';
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
-- ECO-1702: stored binaries exist only after processing succeeds. Pending,
-- processing and rejected rows intentionally have no Storage object.
ALTER TABLE app_private.media_assets
    DROP CONSTRAINT media_assets_storage_mode_check;

ALTER TABLE app_private.media_assets
    ADD CONSTRAINT media_assets_storage_mode_check CHECK (
        (media_kind = 'stored'
            AND external_photo_reference IS NULL
            AND external_attributions IS NULL
            AND external_cache_expires_at IS NULL
            AND (
                (processing_status = 'ready' AND storage_key IS NOT NULL)
                OR (processing_status <> 'ready' AND storage_key IS NULL)
            ))
        OR
        (media_kind = 'google_proxy'
            AND license_code = 'GOOGLE_PLACES_PROXY'
            AND storage_key IS NULL
            AND checksum_sha256 IS NULL
            AND width_px IS NULL
            AND height_px IS NULL
            AND derivatives = '{}'::jsonb
            AND external_photo_reference IS NOT NULL
            AND length(trim(external_photo_reference)) > 0
            AND external_attributions IS NOT NULL
            AND jsonb_typeof(external_attributions) = 'array'
            AND jsonb_array_length(external_attributions) > 0
            AND external_cache_expires_at IS NOT NULL
            AND external_cache_expires_at > created_at
            AND external_cache_expires_at <= created_at + interval '30 days')
    );
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
