-- ECO-2302 remediation: make the accepted visual taxonomy an enforceable invariant.
-- Forward-only because 20260824025254 may already exist in remote migration history.
BEGIN;

ALTER TABLE app_private.actor_categories
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN,
    ADD COLUMN IF NOT EXISTS spatial_scope VARCHAR(32);

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

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM app_private.actor_categories
        WHERE slug NOT IN (
            'alimentacao', 'atrativos', 'hospedagem', 'artesanato',
            'transporte', 'saude', 'seguranca', 'outros'
        )
    ) THEN
        RAISE EXCEPTION
            'ECO-2302 requires editorial review of non-canonical actor category slugs';
    END IF;
END;
$$;

ALTER TABLE app_private.actor_categories
    ALTER COLUMN icon SET NOT NULL,
    ALTER COLUMN color SET NOT NULL,
    ALTER COLUMN is_public SET DEFAULT true,
    ALTER COLUMN is_public SET NOT NULL,
    ALTER COLUMN spatial_scope SET NOT NULL;

ALTER TABLE app_private.actor_categories
    DROP CONSTRAINT IF EXISTS chk_actor_categories_canonical_metadata,
    ADD CONSTRAINT chk_actor_categories_canonical_metadata CHECK (
        (slug = 'alimentacao' AND label = 'Alimentação' AND color = '#D97706' AND icon = 'utensils' AND sort_order = 1 AND is_public AND spatial_scope = 'route_corridor') OR
        (slug = 'atrativos' AND label = 'Atrativos' AND color = '#059669' AND icon = 'compass' AND sort_order = 2 AND is_public AND spatial_scope = 'route_corridor') OR
        (slug = 'hospedagem' AND label = 'Hospedagem' AND color = '#2563EB' AND icon = 'bed' AND sort_order = 3 AND is_public AND spatial_scope = 'route_corridor') OR
        (slug = 'artesanato' AND label = 'Artesanato' AND color = '#7C3AED' AND icon = 'palette' AND sort_order = 4 AND is_public AND spatial_scope = 'route_corridor') OR
        (slug = 'transporte' AND label = 'Transporte' AND color = '#0891B2' AND icon = 'bus' AND sort_order = 5 AND is_public AND spatial_scope = 'both') OR
        (slug = 'saude' AND label = 'Saúde' AND color = '#DC2626' AND icon = 'heart-pulse' AND sort_order = 6 AND is_public AND spatial_scope = 'citywide_essential') OR
        (slug = 'seguranca' AND label = 'Segurança' AND color = '#1E3A8A' AND icon = 'shield' AND sort_order = 7 AND is_public AND spatial_scope = 'citywide_essential') OR
        (slug = 'outros' AND label = 'Outros' AND color = '#6B7280' AND icon = 'help-circle' AND sort_order = 99 AND is_public AND spatial_scope = 'route_corridor')
    );

ALTER TABLE app_private.actor_categories ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_private.actor_categories FROM PUBLIC, anon, authenticated;

COMMIT;
