-- Domain objects and extension types are explicitly schema-qualified.
-- Avoid changing name resolution globally for unrelated applications.
ALTER DATABASE postgres RESET search_path;
