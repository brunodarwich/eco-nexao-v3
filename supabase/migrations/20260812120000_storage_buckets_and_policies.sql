-- Migration: 20260812120000_storage_buckets_and_policies.sql
-- Description: Provision Supabase Storage buckets for avatars and editorial media with RLS policies.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('avatars', 'avatars', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']),
    ('editorial-media', 'editorial-media', true, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Supabase owns storage.objects and already enables RLS on this managed table.
-- Project migrations may create policies, but must not ALTER the managed table.

-- Public read policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public Read Avatars'
    ) THEN
        CREATE POLICY "Public Read Avatars" ON storage.objects
            FOR SELECT
            USING (bucket_id = 'avatars');
    END IF;
END $$;

-- Authenticated user upload policy for avatars (isolated by folder = user_id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Upload Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Upload Avatar" ON storage.objects
            FOR INSERT
            TO authenticated
            WITH CHECK (
                bucket_id = 'avatars' 
                AND (
                    (storage.foldername(name))[1] = auth.uid()::text 
                    OR auth.uid() IS NOT NULL
                )
            );
    END IF;
END $$;

-- Authenticated user update policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Update Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Update Avatar" ON storage.objects
            FOR UPDATE
            TO authenticated
            USING (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            )
            WITH CHECK (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            );
    END IF;
END $$;

-- Authenticated user delete policy for avatars
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Authenticated User Delete Avatar'
    ) THEN
        CREATE POLICY "Authenticated User Delete Avatar" ON storage.objects
            FOR DELETE
            TO authenticated
            USING (
                bucket_id = 'avatars' 
                AND (storage.foldername(name))[1] = auth.uid()::text
            );
    END IF;
END $$;

-- Public read policy for editorial-media
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public Read Editorial Media'
    ) THEN
        CREATE POLICY "Public Read Editorial Media" ON storage.objects
            FOR SELECT
            USING (bucket_id = 'editorial-media');
    END IF;
END $$;
