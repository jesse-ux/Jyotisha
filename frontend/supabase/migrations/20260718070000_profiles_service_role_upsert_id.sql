begin;

-- PostgREST upsert on an existing profile updates the conflict key column
-- even when the submitted id is unchanged. Keep this grant scoped to id so
-- the service role can perform current /api/account upserts without restoring
-- table-wide profile update privileges.
grant update (id) on table public.profiles to service_role;

commit;
