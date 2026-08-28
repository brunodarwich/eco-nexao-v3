-- Migration: 20260827195436_territorial_catalog_schema_adr0014_adr0015.sql
-- Description: Territorial Catalog schema, hierarchical taxonomy (actor_types), provenance, external sources and SEMTUR badge derivation (ADR 0014 / ADR 0015 / ECO-2504)

BEGIN;

-- 1. Create app_private.actor_types table for Level-2 specialized taxonomy (ADR 0015)
CREATE TABLE IF NOT EXISTS app_private.actor_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES app_private.actor_categories(id) ON DELETE RESTRICT,
    slug VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    icon VARCHAR(100) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    aliases TEXT[] NOT NULL DEFAULT '{}'::text[],
    spatial_scope VARCHAR(32) NOT NULL CHECK (spatial_scope IN ('route_corridor', 'citywide_essential', 'both')),
    publication_rule TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER update_actor_types_updated_at
    BEFORE UPDATE ON app_private.actor_types
    FOR EACH ROW EXECUTE FUNCTION app_private.update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_actor_types_category_id ON app_private.actor_types (category_id);
CREATE INDEX IF NOT EXISTS idx_actor_types_spatial_scope ON app_private.actor_types (spatial_scope);

-- 2. Populate canonical actor_types with full taxonomy from ADR 0015
DO $$
DECLARE
    v_alimentacao_id UUID;
    v_atrativos_id UUID;
    v_hospedagem_id UUID;
    v_artesanato_id UUID;
    v_transporte_id UUID;
    v_saude_id UUID;
    v_seguranca_id UUID;
    v_outros_id UUID;
BEGIN
    SELECT id INTO v_alimentacao_id FROM app_private.actor_categories WHERE slug = 'alimentacao';
    SELECT id INTO v_atrativos_id FROM app_private.actor_categories WHERE slug = 'atrativos';
    SELECT id INTO v_hospedagem_id FROM app_private.actor_categories WHERE slug = 'hospedagem';
    SELECT id INTO v_artesanato_id FROM app_private.actor_categories WHERE slug = 'artesanato';
    SELECT id INTO v_transporte_id FROM app_private.actor_categories WHERE slug = 'transporte';
    SELECT id INTO v_saude_id FROM app_private.actor_categories WHERE slug = 'saude';
    SELECT id INTO v_seguranca_id FROM app_private.actor_categories WHERE slug = 'seguranca';
    SELECT id INTO v_outros_id FROM app_private.actor_categories WHERE slug = 'outros';

    -- alimentacao (10-15)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_alimentacao_id, 'restaurante', 'Restaurante & Gastronomia', 'utensils', 10,
         ARRAY['restaurante', 'restaurantes e bares', 'alimentacao', 'culinaria', 'gastronomia', 'comida regional', 'peixaria', 'self-service', 'churrascaria', 'pizzaria', 'bistrô', 'buffet'],
         'route_corridor', 'Público se published. Selo SEMTUR se originário do inventário oficial.'),
        (v_alimentacao_id, 'bar_vida_noturna', 'Bar & Vida Noturna', 'beer', 11,
         ARRAY['bar', 'bares', 'botequim', 'pub', 'vida noturna', 'casa de shows', 'musica ao vivo', 'boate', 'cervejaria', 'lounge'],
         'route_corridor', 'Público se published. Selo SEMTUR se originário do inventário.'),
        (v_alimentacao_id, 'barraca_praia', 'Barraca de Praia & Quiosque', 'umbrella', 12,
         ARRAY['barraca de praia', 'quiosque', 'cabana de praia', 'restaurante de praia', 'apoio de praia', 'barraca'],
         'route_corridor', 'Público se published. Relevância máxima no corredor de praias (Pindobal / Alter).'),
        (v_alimentacao_id, 'cafe_lanchonete', 'Café & Lanchonete', 'coffee', 13,
         ARRAY['lanchonete', 'café', 'cafeteria', 'padaria', 'lanches', 'salgaderia', 'doceria', 'sorveteria', 'sucos'],
         'route_corridor', 'Público se published.'),
        (v_alimentacao_id, 'mercado_conveniencia', 'Mercado & Conveniência', 'shopping-cart', 14,
         ARRAY['mercado', 'mercadinho', 'conveniencia', 'mercearia', 'supermercado', 'empório', 'armazém', 'quitanda', 'minimercado'],
         'both', 'Público se published. Apoio essencial ao turista no corredor e na cidade.'),
        (v_alimentacao_id, 'feira_livre', 'Feira & Mercado Produtor', 'store', 15,
         ARRAY['feira', 'feiras', 'feira livre', 'mercado municipal', 'feira do produtor', 'mercado de peixe', 'feira agroecológica'],
         'both', 'Público se published. Patrimônio gastronômico e abastecimento.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- atrativos (20-27)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_atrativos_id, 'atrativo_natural', 'Atrativo Natural & Trilha', 'trees', 20,
         ARRAY['atrativos naturais', 'atrativo natural', 'natureza', 'ponto turistico', 'trilha', 'floresta', 'igarapé', 'lago', 'encontro das águas'],
         'route_corridor', 'Público institucional (published). Soberania SEMTUR para patrimônio natural.'),
        (v_atrativos_id, 'praia_fluvial', 'Praia Fluvial', 'sun', 21,
         ARRAY['praias fluviais', 'praia fluvial', 'praia', 'ponta de pedras', 'pindobal', 'maracanã', 'carapanari', 'ilha do amor', 'cururu'],
         'route_corridor', 'Público institucional (published). Soberania SEMTUR. Selo SEMTUR.'),
        (v_atrativos_id, 'ilha', 'Ilha & Bancada de Areia', 'waves', 22,
         ARRAY['ilhas', 'ilha', 'arquipélago', 'bancada de areia', 'banco de areia'],
         'route_corridor', 'Público institucional (published).'),
        (v_atrativos_id, 'serra_mirante', 'Serra & Mirante Panorâmico', 'mountain', 23,
         ARRAY['serras', 'serra', 'mirante', 'morro', 'vista panoramica', 'serra da piroca', 'serra do saubal'],
         'route_corridor', 'Público institucional (published).'),
        (v_atrativos_id, 'unidade_conservacao', 'Unidade de Conservação & APA', 'shield-check', 24,
         ARRAY['unidade de conservação', 'área de proteção ambiental', 'apa', 'flona tapajós', 'parna', 'resex tapajós-arapiuns', 'parque ambiental', 'uc'],
         'both', 'Público institucional (published). Máxima relevância socioambiental.'),
        (v_atrativos_id, 'patrimonio_cultural', 'Patrimônio Cultural & Histórico', 'landmark', 25,
         ARRAY['edificações e arquiteturas', 'obras de arte', 'instituições culturais', 'bibliotecas', 'patrimonio', 'centro cultural', 'museu', 'monumento', 'teatro'],
         'both', 'Público institucional (published). Selo SEMTUR.'),
        (v_atrativos_id, 'templo_religioso', 'Igreja & Templo Histórico', 'church', 26,
         ARRAY['igrejas e templos', 'igreja', 'templo', 'religioso', 'catedral', 'capela', 'santuário', 'paróquia', 'matriz'],
         'both', 'Público se published. Atração histórico-cultural e referência de comunidade.'),
        (v_atrativos_id, 'lazer_balneario', 'Balneário & Clube de Lazer', 'umbrella', 27,
         ARRAY['balneários/chácaras', 'balneário', 'chácara', 'clubes sociais, desportivos e de lazer', 'serviços/equipamentos de lazer', 'parque aquático', 'clube'],
         'route_corridor', 'Público se published.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- hospedagem (30-31)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_hospedagem_id, 'pousada_hotel', 'Hotel & Pousada', 'bed', 30,
         ARRAY['hospedagem', 'hotel', 'pousada', 'hostel', 'albergue', 'resort', 'dormitório', 'suítes', 'ecopousada'],
         'route_corridor', 'Público se published. Selo SEMTUR se cadastrado na prefeitura.'),
        (v_hospedagem_id, 'casa_temporada', 'Casa de Temporada & Camping', 'home', 31,
         ARRAY['casas de temporada', 'casa de temporada', 'aluguel temporada', 'chalé', 'bangalô', 'flat', 'camping', 'area de camping', 'casa de praia'],
         'route_corridor', 'Público se published. Modalidade essencial em Alter do Chão e Pindobal.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- artesanato (40)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_artesanato_id, 'artesanato_local', 'Artesanato & Produção Comunitária', 'palette', 40,
         ARRAY['artesanato', 'artesao', 'trançado', 'cerâmica tapajônica', 'cuia', 'souvenir', 'lembranças', 'associação de artesãos', 'arte indígena', 'biojoias'],
         'route_corridor', 'Público se published. Foco em economia solidária e fomento comunitário; selo SEMTUR.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- transporte (50-56)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_transporte_id, 'terminal_aeroporto', 'Aeroporto & Pistas de Pouso', 'plane', 50,
         ARRAY['aeroporto', 'aeroporto de santarem', 'maestro wilson fonseca', 'pista de pouso', 'taxi aereo', 'táxi aéreo em santarem e regioes', 'aerodromo'],
         'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'terminal_porto', 'Porto & Terminal Hidroviário', 'anchor', 51,
         ARRAY['porto', 'terminal hidroviario', 'hidroviaria', 'balsa', 'transporte fluvial em Santarém', 'transporte fluvial', 'cais', 'embarcadouro', 'porto de santarém'],
         'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'terminal_rodoviario', 'Rodoviária & Transporte Coletivo', 'bus', 52,
         ARRAY['rodoviaria', 'terminal rodoviario', 'ponto de onibus', 'vans', 'vans e micro-ônibus', 'transporte intermunicipal', 'transfer', 'coletivo'],
         'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'catraia_travessia', 'Catraia & Travessia Fluvial', 'ship', 53,
         ARRAY['catraias em alter do chão', 'catraias', 'catraia', 'catraieiro', 'travessia ilha do amor', 'canoa', 'voadeira', 'barqueiro'],
         'route_corridor', 'Público se published. Patrimônio cultural imaterial e transporte local.'),
        (v_transporte_id, 'posto_combustivel', 'Posto de Combustível', 'fuel', 54,
         ARRAY['posto de gasolina', 'combustível', 'gasolina', 'etanol', 'diesel', 'posto', 'abastecimento', 'posto 24h'],
         'both', 'Público se published. Infraestrutura viária vital no corredor da rodovia e na cidade.'),
        (v_transporte_id, 'locadora_mobilidade', 'Locadora de Veículos & Táxi', 'car', 55,
         ARRAY['locadoras de veículos', 'locadora veículos', 'aluguel de carro', 'rent a car', 'taxi', 'mototaxi', 'ponto de taxi'],
         'both', 'Público se published.'),
        (v_transporte_id, 'agencia_turismo', 'Agência de Turismo & Receptivo', 'briefcase', 56,
         ARRAY['agências', 'agência turismo', 'agências de passagens aéreas', 'receptivo', 'operadora de turismo', 'guias', 'passeios de barco'],
         'both', 'Público se published.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- saude (60-62)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_saude_id, 'hospital_upa', 'Hospital & Pronto Socorro', 'heart-pulse', 60,
         ARRAY['hospital/UPA', 'hospital', 'upa', 'pronto socorro', 'unidade de pronto atendimento', 'emergencia medica', 'samu', 'hospital municipal', 'hospital regional'],
         'citywide_essential', 'Serviço Essencial Vital: Visível na cidade e sob demanda na rota.'),
        (v_saude_id, 'posto_saude_ubs', 'UBS & Posto de Saúde', 'cross', 61,
         ARRAY['posto de saúde', 'posto de saude', 'ubs', 'unidade basica de saude', 'centro de saude', 'posto medico', 'saude da familia', 'ambulatorio'],
         'citywide_essential', 'Serviço Essencial: Atenção primária municipal.'),
        (v_saude_id, 'farmacia', 'Farmácia & Drogaria', 'pill', 62,
         ARRAY['farmácia', 'farmacia', 'drogaria', 'medicamentos', 'remédios', 'plantão farmácia', 'drogaria 24h'],
         'both', 'Serviço de Saúde & Apoio: Visível na cidade e no corredor em deslocamentos.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- seguranca (70-71)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_seguranca_id, 'seguranca_publica', 'Polícia, Delegacia & Bombeiros', 'shield', 70,
         ARRAY['delegacia', 'bombeiros', 'seguranca', 'segurança', 'polícia militar', 'polícia civil', 'corpo de bombeiros', 'guarda municipal', 'defesa civil', 'resgate', '4 gbm'],
         'citywide_essential', 'Serviço Essencial de Proteção: Visível na cidade e sob demanda na rota. Selo SEMTUR se oficial.'),
        (v_seguranca_id, 'conselho_tutelar_protecao', 'Conselho Tutelar & Proteção Social', 'scale', 71,
         ARRAY['conselho tutelar', 'proteção social', 'cidadania', 'direitos humanos', 'vara da infância', 'assistência social', 'cras', 'creas'],
         'citywide_essential', 'Proteção Social & Cidadania: Serviço público essencial.')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();

    -- outros (90-99)
    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_outros_id, 'servicos_publicos_cartorios', 'Serviços Públicos & Cartórios', 'landmark', 90,
         ARRAY['cartórios', 'cartório', 'cartorios', 'serviço público', 'repartição pública', 'prefeitura', 'fórum', 'tabelionato', 'registro civil'],
         'citywide_essential', 'Público institucional (published).'),
        (v_outros_id, 'comercio_eventos', 'Comércio & Serviços para Eventos', 'store', 91,
         ARRAY['para eventos', 'serviços para eventos', 'serviços/equipamentos para eventos', 'shopping/lojas de departamento', 'shopping/lojas', 'loja', 'decoração', 'som e iluminação'],
         'both', 'Curadoria Editorial (review / published se auditado).'),
        (v_outros_id, 'nao_classificado', 'Não Classificado / Triagem', 'help-circle', 99,
         ARRAY['indefinido', 'desconhecido', 'outros', 'nao classificado', 'a classificar', 'sem categoria'],
         'route_corridor', 'Retenção na Fila de Triagem Editorial (draft / review).')
    ON CONFLICT (slug) DO UPDATE SET
        category_id = EXCLUDED.category_id,
        label = EXCLUDED.label,
        icon = EXCLUDED.icon,
        sort_order = EXCLUDED.sort_order,
        aliases = EXCLUDED.aliases,
        spatial_scope = EXCLUDED.spatial_scope,
        publication_rule = EXCLUDED.publication_rule,
        updated_at = clock_timestamp();
END $$;

-- 3. Add type_id to app_private.actors
ALTER TABLE app_private.actors
    ADD COLUMN IF NOT EXISTS type_id UUID REFERENCES app_private.actor_types(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_actors_type_id ON app_private.actors (type_id);

-- 4. Ensure canonical external sources exist in app_private.external_sources (ADR 0014)
INSERT INTO app_private.external_sources (id, slug, name, description)
VALUES
    (gen_random_uuid(), 'semtur_inventory', 'Inventário Turístico SEMTUR Santarém', 'Inventário oficial da Secretaria Municipal de Turismo de Santarém.'),
    (gen_random_uuid(), 'google_places', 'Google Places API', 'Dados comerciais e de descoberta geográfica da plataforma Google Maps / Places.'),
    (gen_random_uuid(), 'editorial_curation', 'Curadoria Editorial ECOnexão', 'Dados verificados e cadastrados pela equipe editorial ECOnexão.')
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = clock_timestamp();

-- 5. Enrich actor_external_refs with status_ref and indexing (ADR 0014 §2.3)
ALTER TABLE app_private.actor_external_refs
    ADD COLUMN IF NOT EXISTS status_ref VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status_ref IN ('active', 'stale', 'unlinked'));

CREATE INDEX IF NOT EXISTS idx_actor_external_refs_actor_status ON app_private.actor_external_refs (actor_id, status_ref);
CREATE INDEX IF NOT EXISTS idx_actor_external_refs_source_status ON app_private.actor_external_refs (source_id, status_ref);

-- 6. Enrich raw_source_records with payload_hash_sha256 and ingestion metadata (ADR 0014 §2.2)
ALTER TABLE app_private.raw_source_records
    ADD COLUMN IF NOT EXISTS payload_hash_sha256 VARCHAR(64);

-- 7. Create view with security_invoker = true to safely derive SEMTUR inventory badge (ADR 0014 §2.6 / DoD)
CREATE OR REPLACE VIEW app_private.v_actor_semtur_inventory
WITH (security_invoker = true) AS
SELECT
    a.id AS actor_id,
    EXISTS (
        SELECT 1
        FROM app_private.actor_external_refs aer
        JOIN app_private.external_sources es ON es.id = aer.source_id
        WHERE aer.actor_id = a.id
          AND es.slug = 'semtur_inventory'
          AND aer.status_ref = 'active'
    ) AS is_semtur_inventory,
    (
        SELECT aer.external_id
        FROM app_private.actor_external_refs aer
        JOIN app_private.external_sources es ON es.id = aer.source_id
        WHERE aer.actor_id = a.id
          AND es.slug = 'semtur_inventory'
          AND aer.status_ref = 'active'
        ORDER BY aer.last_seen_at DESC
        LIMIT 1
    ) AS semtur_external_id
FROM app_private.actors a;

-- 8. Apply strict RLS and grants (Deny-by-default for Data API roles)
ALTER TABLE app_private.actor_types ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_private.actor_types FROM PUBLIC, anon, authenticated;

REVOKE ALL ON app_private.v_actor_semtur_inventory FROM PUBLIC, anon, authenticated;

COMMIT;