-- Migration: 20260824025254_canonical_taxonomy_adr0010.sql
-- Description: Canonical taxonomy alignment (8 categories) and legacy emergency migration (ADR 0010 / ECO-2302)

-- 1. Ensure canonical categories exist in app_private.actor_categories
INSERT INTO app_private.actor_categories (id, slug, label, color, icon, sort_order)
VALUES
    (gen_random_uuid(), 'alimentacao', 'Alimentação', '#D97706', 'utensils', 1),
    (gen_random_uuid(), 'atrativos', 'Atrativos', '#059669', 'compass', 2),
    (gen_random_uuid(), 'hospedagem', 'Hospedagem', '#2563EB', 'bed', 3),
    (gen_random_uuid(), 'artesanato', 'Artesanato', '#7C3AED', 'palette', 4),
    (gen_random_uuid(), 'transporte', 'Transporte', '#0891B2', 'bus', 5),
    (gen_random_uuid(), 'saude', 'Saúde', '#DC2626', 'heart-pulse', 6),
    (gen_random_uuid(), 'seguranca', 'Segurança', '#1E3A8A', 'shield', 7),
    (gen_random_uuid(), 'outros', 'Outros', '#6B7280', 'help-circle', 99)
ON CONFLICT (slug) DO UPDATE SET
    label = EXCLUDED.label,
    color = EXCLUDED.color,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    updated_at = clock_timestamp();

-- 2. Migrate legacy 'emergencia' actors to 'seguranca' or 'saude'
DO $$
DECLARE
    v_emergencia_id UUID;
    v_saude_id UUID;
    v_seguranca_id UUID;
    v_outros_id UUID;
BEGIN
    SELECT id INTO v_emergencia_id FROM app_private.actor_categories WHERE slug = 'emergencia';
    SELECT id INTO v_saude_id FROM app_private.actor_categories WHERE slug = 'saude';
    SELECT id INTO v_seguranca_id FROM app_private.actor_categories WHERE slug = 'seguranca';
    SELECT id INTO v_outros_id FROM app_private.actor_categories WHERE slug = 'outros';

    IF v_emergencia_id IS NOT NULL THEN
        -- Reassign security-related actors
        UPDATE app_private.actors
        SET category_id = v_seguranca_id,
            updated_at = clock_timestamp()
        WHERE category_id = v_emergencia_id
          AND (
            LOWER(COALESCE(name, '') || ' ' || COALESCE(sub_category, '')) ~* '(polic|bombeir|guard|delegac)'
          );

        -- Reassign health-related actors
        UPDATE app_private.actors
        SET category_id = v_saude_id,
            updated_at = clock_timestamp()
        WHERE category_id = v_emergencia_id
          AND (
            LOWER(COALESCE(name, '') || ' ' || COALESCE(sub_category, '')) ~* '(hospit|saud|farmac|ubs|upa|pronto|posto|medico|clinica)'
          );

        -- Fallback remaining emergencia actors to outros
        UPDATE app_private.actors
        SET category_id = v_outros_id,
            updated_at = clock_timestamp()
        WHERE category_id = v_emergencia_id;

        -- Remove legacy 'emergencia' category if no actors remain referencing it
        DELETE FROM app_private.actor_categories
        WHERE id = v_emergencia_id
          AND NOT EXISTS (
              SELECT 1 FROM app_private.actors WHERE category_id = v_emergencia_id
          );
    END IF;
END $$;
