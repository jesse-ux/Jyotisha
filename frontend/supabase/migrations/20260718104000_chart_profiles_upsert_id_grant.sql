begin;

-- PostgREST upsert may include the unchanged conflict key in its update set.
grant update (id, role, profile, updated_at) on table public.chart_profiles to authenticated;

commit;
