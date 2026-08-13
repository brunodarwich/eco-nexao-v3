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
