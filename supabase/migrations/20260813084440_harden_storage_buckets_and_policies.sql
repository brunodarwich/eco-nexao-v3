-- Migration: harden_storage_buckets_and_policies
-- Description: Enforce avatar ownership, prevent public object listing, and
--              align bucket visibility and MIME constraints with ADR 0008.

-- Bucket rows are Supabase-managed configuration data. This migration does not
-- create custom objects in the managed storage schema.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
    ('avatars', 'avatars', true, 5242880, ARRAY['image/webp']),
    ('editorial-media', 'editorial-media', true, 10485760, ARRAY['image/webp']),
    (
        'raw-ingestion',
        'raw-ingestion',
        false,
        20971520,
        ARRAY['image/jpeg', 'image/png', 'image/webp']
    )
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Public buckets are downloaded through /object/public without an RLS SELECT
-- policy. Removing broad SELECT policies prevents anon/authenticated clients
-- from listing every object in those buckets through the Storage API.
DROP POLICY IF EXISTS "Public Read Avatars" ON storage.objects;
DROP POLICY IF EXISTS "Public Read Editorial Media" ON storage.objects;

-- Recreate every avatar policy so projects that already applied the vulnerable
-- migration converge to the same secure state. Signed-in anonymous users also
-- use the authenticated database role, therefore folder ownership is mandatory.
DROP POLICY IF EXISTS "Authenticated User Select Own Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Upload Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Update Avatar" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated User Delete Avatar" ON storage.objects;

CREATE POLICY "Authenticated User Select Own Avatar"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
);

CREATE POLICY "Authenticated User Upload Avatar"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'avatars'
    AND cardinality(storage.foldername(name)) = 1
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
    AND lower(storage.extension(name)) = 'webp'
);

CREATE POLICY "Authenticated User Update Avatar"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
)
WITH CHECK (
    bucket_id = 'avatars'
    AND cardinality(storage.foldername(name)) = 1
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
    AND lower(storage.extension(name)) = 'webp'
);

CREATE POLICY "Authenticated User Delete Avatar"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = (SELECT auth.uid())::text
);

-- editorial-media and raw-ingestion deliberately have no client mutation
-- policies. The trusted FastAPI backend is the only writer and uses its secret
-- server-side credential after domain authorization.
