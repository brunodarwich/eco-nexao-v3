-- ECO-1503: make imported route geometry auditable and spatial relations safe.
ALTER TABLE app_private.route_geometries
    ADD COLUMN bounds JSONB,
    ADD COLUMN source_hash VARCHAR(64);

ALTER TABLE app_private.route_geometries
    ADD CONSTRAINT uq_route_geometries_origin_provider
        UNIQUE (route_origin_id, provider),
    ADD CONSTRAINT ck_route_geometries_source_hash
        CHECK (source_hash IS NULL OR source_hash ~ '^[0-9a-f]{64}$'),
    ADD CONSTRAINT ck_route_geometries_bounds
        CHECK (
            bounds IS NULL OR (
                bounds ?& ARRAY['min_lat', 'max_lat', 'min_lon', 'max_lon']
                AND jsonb_typeof(bounds->'min_lat') = 'number'
                AND jsonb_typeof(bounds->'max_lat') = 'number'
                AND jsonb_typeof(bounds->'min_lon') = 'number'
                AND jsonb_typeof(bounds->'max_lon') = 'number'
                AND (bounds->>'min_lat')::double precision
                    <= (bounds->>'max_lat')::double precision
                AND (bounds->>'min_lon')::double precision
                    <= (bounds->>'max_lon')::double precision
            )
        ),
    ADD CONSTRAINT ck_route_geometries_valid_linestring
        CHECK (
            NOT extensions.ST_IsEmpty(geometry::extensions.geometry)
            AND extensions.ST_IsValid(geometry::extensions.geometry)
            AND extensions.ST_NPoints(geometry::extensions.geometry) >= 2
            AND extensions.ST_SRID(geometry::extensions.geometry) = 4326
        );

ALTER TABLE app_private.route_actors
    ALTER COLUMN origin_flags SET NOT NULL,
    ADD CONSTRAINT ck_route_actors_segment_nonnegative
        CHECK (route_segment_index IS NULL OR route_segment_index >= 0);
