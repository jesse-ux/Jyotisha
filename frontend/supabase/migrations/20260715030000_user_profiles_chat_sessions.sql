begin;

alter table public.profiles
  add column if not exists name text,
  add column if not exists birth_date date,
  add column if not exists birth_time time without time zone,
  add column if not exists country_code text,
  add column if not exists province_code text,
  add column if not exists city_code text,
  add column if not exists district_code text;

alter table public.profiles enable row level security;

drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own
  on public.profiles
  for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

revoke update on table public.profiles from anon, authenticated;
grant update (
  name,
  birth_date,
  birth_time,
  country_code,
  province_code,
  city_code,
  district_code,
  updated_at
) on table public.profiles to authenticated;

create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default '新对话',
  theme text not null default 'general'
    check (theme in ('career', 'marriage', 'timing', 'general')),
  messages jsonb not null default '[]'::jsonb
    check (jsonb_typeof(messages) = 'array'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chat_sessions_user_updated_at_idx
  on public.chat_sessions (user_id, updated_at desc);

alter table public.chat_sessions enable row level security;

drop policy if exists chat_sessions_select_own on public.chat_sessions;
create policy chat_sessions_select_own
  on public.chat_sessions
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists chat_sessions_insert_own on public.chat_sessions;
create policy chat_sessions_insert_own
  on public.chat_sessions
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists chat_sessions_update_own on public.chat_sessions;
create policy chat_sessions_update_own
  on public.chat_sessions
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

revoke all on table public.chat_sessions from anon, authenticated, service_role;
grant select on table public.chat_sessions to authenticated;
grant insert (id, user_id, title, theme, messages, updated_at)
  on table public.chat_sessions to authenticated;
grant update (title, theme, messages, updated_at)
  on table public.chat_sessions to authenticated;

commit;
