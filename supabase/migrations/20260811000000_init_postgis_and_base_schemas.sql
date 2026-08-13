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
