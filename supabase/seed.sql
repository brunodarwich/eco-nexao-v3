-- Minimal local/test fixture hook.
-- Pindobal is imported by the reproducible Python command from backend/app/ingestion;
-- production APIs never read the source CSV/JSON files at runtime.

-- Canonical taxonomy categories (ADR 0010 / ECO-2302)
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
