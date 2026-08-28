-- Minimal local/test fixture hook.
-- Pindobal is imported by the reproducible Python command from backend/app/ingestion;
-- production APIs never read the source CSV/JSON files at runtime.

-- 1. Canonical taxonomy categories (ADR 0010 / ECO-2302)
INSERT INTO app_private.actor_categories (
    id, slug, label, color, icon, sort_order, is_public, spatial_scope
)
VALUES
    (gen_random_uuid(), 'alimentacao', 'Alimentação', '#D97706', 'utensils', 1, true, 'route_corridor'),
    (gen_random_uuid(), 'atrativos', 'Atrativos', '#059669', 'compass', 2, true, 'route_corridor'),
    (gen_random_uuid(), 'hospedagem', 'Hospedagem', '#2563EB', 'bed', 3, true, 'route_corridor'),
    (gen_random_uuid(), 'artesanato', 'Artesanato', '#7C3AED', 'palette', 4, true, 'route_corridor'),
    (gen_random_uuid(), 'transporte', 'Transporte', '#0891B2', 'bus', 5, true, 'both'),
    (gen_random_uuid(), 'saude', 'Saúde', '#DC2626', 'heart-pulse', 6, true, 'citywide_essential'),
    (gen_random_uuid(), 'seguranca', 'Segurança', '#1E3A8A', 'shield', 7, true, 'citywide_essential'),
    (gen_random_uuid(), 'outros', 'Outros', '#6B7280', 'help-circle', 99, true, 'route_corridor')
ON CONFLICT (slug) DO UPDATE SET
    label = EXCLUDED.label,
    color = EXCLUDED.color,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_public = EXCLUDED.is_public,
    spatial_scope = EXCLUDED.spatial_scope,
    updated_at = clock_timestamp()
WHERE (
    actor_categories.label,
    actor_categories.color,
    actor_categories.icon,
    actor_categories.sort_order,
    actor_categories.is_public,
    actor_categories.spatial_scope
) IS DISTINCT FROM (
    EXCLUDED.label,
    EXCLUDED.color,
    EXCLUDED.icon,
    EXCLUDED.sort_order,
    EXCLUDED.is_public,
    EXCLUDED.spatial_scope
);

-- 2. Canonical external sources (ADR 0014)
INSERT INTO app_private.external_sources (id, slug, name, description)
VALUES
    (gen_random_uuid(), 'semtur_inventory', 'Inventário Turístico SEMTUR Santarém', 'Inventário oficial da Secretaria Municipal de Turismo de Santarém.'),
    (gen_random_uuid(), 'google_places', 'Google Places API', 'Dados comerciais e de descoberta geográfica da plataforma Google Maps / Places.'),
    (gen_random_uuid(), 'editorial_curation', 'Curadoria Editorial ECOnexão', 'Dados verificados e cadastrados pela equipe editorial ECOnexão.')
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = clock_timestamp();

-- 3. Canonical actor types (ADR 0015 / ECO-2503)
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

    INSERT INTO app_private.actor_types (category_id, slug, label, icon, sort_order, aliases, spatial_scope, publication_rule)
    VALUES
        (v_alimentacao_id, 'restaurante', 'Restaurante & Gastronomia', 'utensils', 10, ARRAY['restaurante', 'restaurantes e bares', 'alimentacao', 'culinaria', 'gastronomia', 'comida regional', 'peixaria', 'self-service', 'churrascaria', 'pizzaria', 'bistrô', 'buffet'], 'route_corridor', 'Público se published. Selo SEMTUR se originário do inventário oficial.'),
        (v_alimentacao_id, 'bar_vida_noturna', 'Bar & Vida Noturna', 'beer', 11, ARRAY['bar', 'bares', 'botequim', 'pub', 'vida noturna', 'casa de shows', 'musica ao vivo', 'boate', 'cervejaria', 'lounge'], 'route_corridor', 'Público se published. Selo SEMTUR se originário do inventário.'),
        (v_alimentacao_id, 'barraca_praia', 'Barraca de Praia & Quiosque', 'umbrella', 12, ARRAY['barraca de praia', 'quiosque', 'cabana de praia', 'restaurante de praia', 'apoio de praia', 'barraca'], 'route_corridor', 'Público se published. Relevância máxima no corredor de praias (Pindobal / Alter).'),
        (v_alimentacao_id, 'cafe_lanchonete', 'Café & Lanchonete', 'coffee', 13, ARRAY['lanchonete', 'café', 'cafeteria', 'padaria', 'lanches', 'salgaderia', 'doceria', 'sorveteria', 'sucos'], 'route_corridor', 'Público se published.'),
        (v_alimentacao_id, 'mercado_conveniencia', 'Mercado & Conveniência', 'shopping-cart', 14, ARRAY['mercado', 'mercadinho', 'conveniencia', 'mercearia', 'supermercado', 'empório', 'armazém', 'quitanda', 'minimercado'], 'both', 'Público se published. Apoio essencial ao turista no corredor e na cidade.'),
        (v_alimentacao_id, 'feira_livre', 'Feira & Mercado Produtor', 'store', 15, ARRAY['feira', 'feiras', 'feira livre', 'mercado municipal', 'feira do produtor', 'mercado de peixe', 'feira agroecológica'], 'both', 'Público se published. Patrimônio gastronômico e abastecimento.'),
        (v_atrativos_id, 'atrativo_natural', 'Atrativo Natural & Trilha', 'trees', 20, ARRAY['atrativos naturais', 'atrativo natural', 'natureza', 'ponto turistico', 'trilha', 'floresta', 'igarapé', 'lago', 'encontro das águas'], 'route_corridor', 'Público institucional (published). Soberania SEMTUR para patrimônio natural.'),
        (v_atrativos_id, 'praia_fluvial', 'Praia Fluvial', 'sun', 21, ARRAY['praias fluviais', 'praia fluvial', 'praia', 'ponta de pedras', 'pindobal', 'maracanã', 'carapanari', 'ilha do amor', 'cururu'], 'route_corridor', 'Público institucional (published). Soberania SEMTUR. Selo SEMTUR.'),
        (v_atrativos_id, 'ilha', 'Ilha & Bancada de Areia', 'waves', 22, ARRAY['ilhas', 'ilha', 'arquipélago', 'bancada de areia', 'banco de areia'], 'route_corridor', 'Público institucional (published).'),
        (v_atrativos_id, 'serra_mirante', 'Serra & Mirante Panorâmico', 'mountain', 23, ARRAY['serras', 'serra', 'mirante', 'morro', 'vista panoramica', 'serra da piroca', 'serra do saubal'], 'route_corridor', 'Público institucional (published).'),
        (v_atrativos_id, 'unidade_conservacao', 'Unidade de Conservação & APA', 'shield-check', 24, ARRAY['unidade de conservação', 'área de proteção ambiental', 'apa', 'flona tapajós', 'parna', 'resex tapajós-arapiuns', 'parque ambiental', 'uc'], 'both', 'Público institucional (published). Máxima relevância socioambiental.'),
        (v_atrativos_id, 'patrimonio_cultural', 'Patrimônio Cultural & Histórico', 'landmark', 25, ARRAY['edificações e arquiteturas', 'obras de arte', 'instituições culturais', 'bibliotecas', 'patrimonio', 'centro cultural', 'museu', 'monumento', 'teatro'], 'both', 'Público institucional (published). Selo SEMTUR.'),
        (v_atrativos_id, 'templo_religioso', 'Igreja & Templo Histórico', 'church', 26, ARRAY['igrejas e templos', 'igreja', 'templo', 'religioso', 'catedral', 'capela', 'santuário', 'paróquia', 'matriz'], 'both', 'Público se published. Atração histórico-cultural e referência de comunidade.'),
        (v_atrativos_id, 'lazer_balneario', 'Balneário & Clube de Lazer', 'umbrella', 27, ARRAY['balneários/chácaras', 'balneário', 'chácara', 'clubes sociais, desportivos e de lazer', 'serviços/equipamentos de lazer', 'parque aquático', 'clube'], 'route_corridor', 'Público se published.'),
        (v_hospedagem_id, 'pousada_hotel', 'Hotel & Pousada', 'bed', 30, ARRAY['hospedagem', 'hotel', 'pousada', 'hostel', 'albergue', 'resort', 'dormitório', 'suítes', 'ecopousada'], 'route_corridor', 'Público se published. Selo SEMTUR se cadastrado na prefeitura.'),
        (v_hospedagem_id, 'casa_temporada', 'Casa de Temporada & Camping', 'home', 31, ARRAY['casas de temporada', 'casa de temporada', 'aluguel temporada', 'chalé', 'bangalô', 'flat', 'camping', 'area de camping', 'casa de praia'], 'route_corridor', 'Público se published. Modalidade essencial em Alter do Chão e Pindobal.'),
        (v_artesanato_id, 'artesanato_local', 'Artesanato & Produção Comunitária', 'palette', 40, ARRAY['artesanato', 'artesao', 'trançado', 'cerâmica tapajônica', 'cuia', 'souvenir', 'lembranças', 'associação de artesãos', 'arte indígena', 'biojoias'], 'route_corridor', 'Público se published. Foco em economia solidária e fomento comunitário; selo SEMTUR.'),
        (v_transporte_id, 'terminal_aeroporto', 'Aeroporto & Pistas de Pouso', 'plane', 50, ARRAY['aeroporto', 'aeroporto de santarem', 'maestro wilson fonseca', 'pista de pouso', 'taxi aereo', 'táxi aéreo em santarem e regioes', 'aerodromo'], 'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'terminal_porto', 'Porto & Terminal Hidroviário', 'anchor', 51, ARRAY['porto', 'terminal hidroviario', 'hidroviaria', 'balsa', 'transporte fluvial em Santarém', 'transporte fluvial', 'cais', 'embarcadouro', 'porto de santarém'], 'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'terminal_rodoviario', 'Rodoviária & Transporte Coletivo', 'bus', 52, ARRAY['rodoviaria', 'terminal rodoviario', 'ponto de onibus', 'vans', 'vans e micro-ônibus', 'transporte intermunicipal', 'transfer', 'coletivo'], 'both', 'Público institucional (published). Origem canônica do contrato de rota.'),
        (v_transporte_id, 'catraia_travessia', 'Catraia & Travessia Fluvial', 'ship', 53, ARRAY['catraias em alter do chão', 'catraias', 'catraia', 'catraieiro', 'travessia ilha do amor', 'canoa', 'voadeira', 'barqueiro'], 'route_corridor', 'Público se published. Patrimônio cultural imaterial e transporte local.'),
        (v_transporte_id, 'posto_combustivel', 'Posto de Combustível', 'fuel', 54, ARRAY['posto de gasolina', 'combustível', 'gasolina', 'etanol', 'diesel', 'posto', 'abastecimento', 'posto 24h'], 'both', 'Público se published. Infraestrutura viária vital no corredor da rodovia e na cidade.'),
        (v_transporte_id, 'locadora_mobilidade', 'Locadora de Veículos & Táxi', 'car', 55, ARRAY['locadoras de veículos', 'locadora veículos', 'aluguel de carro', 'rent a car', 'taxi', 'mototaxi', 'ponto de taxi'], 'both', 'Público se published.'),
        (v_transporte_id, 'agencia_turismo', 'Agência de Turismo & Receptivo', 'briefcase', 56, ARRAY['agências', 'agência turismo', 'agências de passagens aéreas', 'receptivo', 'operadora de turismo', 'guias', 'passeios de barco'], 'both', 'Público se published.'),
        (v_saude_id, 'hospital_upa', 'Hospital & Pronto Socorro', 'heart-pulse', 60, ARRAY['hospital/UPA', 'hospital', 'upa', 'pronto socorro', 'unidade de pronto atendimento', 'emergencia medica', 'samu', 'hospital municipal', 'hospital regional'], 'citywide_essential', 'Serviço Essencial Vital: Visível na cidade e sob demanda na rota.'),
        (v_saude_id, 'posto_saude_ubs', 'UBS & Posto de Saúde', 'cross', 61, ARRAY['posto de saúde', 'posto de saude', 'ubs', 'unidade basica de saude', 'centro de saude', 'posto medico', 'saude da familia', 'ambulatorio'], 'citywide_essential', 'Serviço Essencial: Atenção primária municipal.'),
        (v_saude_id, 'farmacia', 'Farmácia & Drogaria', 'pill', 62, ARRAY['farmácia', 'farmacia', 'drogaria', 'medicamentos', 'remédios', 'plantão farmácia', 'drogaria 24h'], 'both', 'Serviço de Saúde & Apoio: Visível na cidade e no corredor em deslocamentos.'),
        (v_seguranca_id, 'seguranca_publica', 'Polícia, Delegacia & Bombeiros', 'shield', 70, ARRAY['delegacia', 'bombeiros', 'seguranca', 'segurança', 'polícia militar', 'polícia civil', 'corpo de bombeiros', 'guarda municipal', 'defesa civil', 'resgate', '4 gbm'], 'citywide_essential', 'Serviço Essencial de Proteção: Visível na cidade e sob demanda na rota. Selo SEMTUR se oficial.'),
        (v_seguranca_id, 'conselho_tutelar_protecao', 'Conselho Tutelar & Proteção Social', 'scale', 71, ARRAY['conselho tutelar', 'proteção social', 'cidadania', 'direitos humanos', 'vara da infância', 'assistência social', 'cras', 'creas'], 'citywide_essential', 'Proteção Social & Cidadania: Serviço público essencial.'),
        (v_outros_id, 'servicos_publicos_cartorios', 'Serviços Públicos & Cartórios', 'landmark', 90, ARRAY['cartórios', 'cartório', 'cartorios', 'serviço público', 'repartição pública', 'prefeitura', 'fórum', 'tabelionato', 'registro civil'], 'citywide_essential', 'Público institucional (published).'),
        (v_outros_id, 'comercio_eventos', 'Comércio & Serviços para Eventos', 'store', 91, ARRAY['para eventos', 'serviços para eventos', 'serviços/equipamentos para eventos', 'shopping/lojas de departamento', 'shopping/lojas', 'loja', 'decoração', 'som e iluminação'], 'both', 'Curadoria Editorial (review / published se auditado).'),
        (v_outros_id, 'nao_classificado', 'Não Classificado / Triagem', 'help-circle', 99, ARRAY['indefinido', 'desconhecido', 'outros', 'nao classificado', 'a classificar', 'sem categoria'], 'route_corridor', 'Retenção na Fila de Triagem Editorial (draft / review).')
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

