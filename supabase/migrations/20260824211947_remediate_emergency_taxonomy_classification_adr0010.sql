-- ECO-2302 P1 remediation: reclassify only exclusive, normatively recognized
-- health/security candidates left in `outros` by the original emergency split.
BEGIN;

CREATE TABLE IF NOT EXISTS app_private.eco_2302_taxonomy_remediation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_version TEXT NOT NULL,
    actor_id UUID NOT NULL REFERENCES app_private.actors(id) ON DELETE RESTRICT,
    from_category_id UUID NOT NULL REFERENCES app_private.actor_categories(id) ON DELETE RESTRICT,
    to_category_id UUID NOT NULL REFERENCES app_private.actor_categories(id) ON DELETE RESTRICT,
    matched_rule TEXT NOT NULL CHECK (matched_rule IN ('health_only', 'security_only')),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_eco_2302_taxonomy_remediation_event
        UNIQUE (migration_version, actor_id),
    CONSTRAINT chk_eco_2302_taxonomy_remediation_category_change
        CHECK (from_category_id <> to_category_id)
);

CREATE INDEX IF NOT EXISTS idx_eco_2302_taxonomy_remediation_actor
    ON app_private.eco_2302_taxonomy_remediation_events (actor_id);
CREATE INDEX IF NOT EXISTS idx_eco_2302_taxonomy_remediation_from_category
    ON app_private.eco_2302_taxonomy_remediation_events (from_category_id);
CREATE INDEX IF NOT EXISTS idx_eco_2302_taxonomy_remediation_to_category
    ON app_private.eco_2302_taxonomy_remediation_events (to_category_id);

ALTER TABLE app_private.eco_2302_taxonomy_remediation_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_private.eco_2302_taxonomy_remediation_events
    FROM PUBLIC, anon, authenticated;

DO $$
DECLARE
    v_outros_id UUID;
    v_saude_id UUID;
    v_seguranca_id UUID;
BEGIN
    SELECT id INTO v_outros_id
    FROM app_private.actor_categories
    WHERE slug = 'outros';

    SELECT id INTO v_saude_id
    FROM app_private.actor_categories
    WHERE slug = 'saude';

    SELECT id INTO v_seguranca_id
    FROM app_private.actor_categories
    WHERE slug = 'seguranca';

    IF v_outros_id IS NULL OR v_saude_id IS NULL OR v_seguranca_id IS NULL THEN
        RAISE EXCEPTION 'ECO-2302 canonical taxonomy categories are missing';
    END IF;

    WITH normalized AS (
        SELECT
            actor.id,
            translate(
                lower(concat_ws(' ', coalesce(actor.name, ''), coalesce(actor.sub_category, ''))),
                'áàâãäéèêëíìîïóòôõöúùûüç',
                'aaaaaeeeeiiiiooooouuuuc'
            ) AS text_value
        FROM app_private.actors AS actor
        WHERE actor.category_id = v_outros_id
    ), candidates AS (
        SELECT
            id,
            text_value ~
                '(^|[^a-z0-9])(hospital|hospitais|farmacia|farmacias|ubs|upa|clinica|clinicas|saude|posto[[:space:]]+de[[:space:]]+saude|pronto[[:space:]]+atendimento)([^a-z0-9]|$)'
                AS health_match,
            text_value ~
                '(^|[^a-z0-9])(policia|policial|delegacia|bombeiro|bombeiros|guarda[[:space:]]+municipal)([^a-z0-9]|$)'
                AS security_match
        FROM normalized
    )
    INSERT INTO app_private.eco_2302_taxonomy_remediation_events (
        migration_version,
        actor_id,
        from_category_id,
        to_category_id,
        matched_rule
    )
    SELECT
        '20260824211947',
        candidates.id,
        v_outros_id,
        CASE
            WHEN candidates.health_match AND NOT candidates.security_match THEN v_saude_id
            WHEN candidates.security_match AND NOT candidates.health_match THEN v_seguranca_id
        END,
        CASE
            WHEN candidates.health_match AND NOT candidates.security_match THEN 'health_only'
            WHEN candidates.security_match AND NOT candidates.health_match THEN 'security_only'
        END
    FROM candidates
    WHERE
        (candidates.health_match AND NOT candidates.security_match)
        OR (candidates.security_match AND NOT candidates.health_match)
    ON CONFLICT (migration_version, actor_id) DO NOTHING;

    UPDATE app_private.actors AS actor
    SET category_id = event.to_category_id,
        updated_at = clock_timestamp()
    FROM app_private.eco_2302_taxonomy_remediation_events AS event
    WHERE event.migration_version = '20260824211947'
      AND actor.id = event.actor_id
      AND actor.category_id = event.from_category_id;
END;
$$;

-- Rollback is a later forward migration, never an edit of this applied file:
-- restore event.from_category_id only when the actor's current category_id still
-- equals event.to_category_id. That condition preserves later editorial changes.

COMMIT;
