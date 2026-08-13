-- Pin the trigger function lookup path to remove role-dependent resolution.
ALTER FUNCTION app_private.update_updated_at_column()
    SET search_path = pg_catalog, app_private;
