-- Migration: 20260826074500_routing_monthly_usage.sql
-- Description: Tabela privada para controle atômico e compartilhado de quota mensal do Google Routes (ADR 0013 / ECO-2314).
-- Specification references: ADR 0013; docs/deployment_google_routes.md; AGENTS.md

CREATE TABLE IF NOT EXISTS app_private.routing_monthly_usage (
    year_month VARCHAR(7) PRIMARY KEY,
    call_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE app_private.routing_monthly_usage ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_private.routing_monthly_usage FROM PUBLIC, anon, authenticated;

COMMENT ON TABLE app_private.routing_monthly_usage IS
    'Shared atomic monthly usage counter for routing providers across workers/instances (ADR 0013).';
