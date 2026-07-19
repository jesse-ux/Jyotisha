begin;

create table if not exists public.chart_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'other' check (role in ('self', 'other')),
  profile jsonb not null check (jsonb_typeof(profile) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chart_profiles_user_updated_at_idx
  on public.chart_profiles (user_id, updated_at desc);

create unique index if not exists chart_profiles_one_self_per_user_idx
  on public.chart_profiles (user_id)
  where role = 'self';

alter table public.chart_profiles enable row level security;

drop policy if exists chart_profiles_select_own on public.chart_profiles;
create policy chart_profiles_select_own
  on public.chart_profiles
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists chart_profiles_insert_own on public.chart_profiles;
create policy chart_profiles_insert_own
  on public.chart_profiles
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists chart_profiles_update_own on public.chart_profiles;
create policy chart_profiles_update_own
  on public.chart_profiles
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists chart_profiles_delete_own on public.chart_profiles;
create policy chart_profiles_delete_own
  on public.chart_profiles
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.chart_profiles from anon, authenticated, service_role;
grant select on table public.chart_profiles to authenticated;
grant insert (id, user_id, role, profile, updated_at) on table public.chart_profiles to authenticated;
grant update (role, profile, updated_at) on table public.chart_profiles to authenticated;
grant delete on table public.chart_profiles to authenticated;

commit;
