create schema if not exists auth authorization schema_owner;

grant usage on schema public to anon, authenticated, service_role;
grant usage on schema auth to anon, authenticated, service_role;
revoke all on schema auth from public;

create table if not exists auth.users (
  id uuid primary key,
  email text not null,
  raw_user_meta_data jsonb not null default '{}'::jsonb,
  email_confirmed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists auth_users_email_canonical_key
  on auth.users (lower(btrim(email)));

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

create or replace function auth.jwt()
returns jsonb
language sql
stable
as $$
  select jsonb_build_object(
    'sub', nullif(current_setting('request.jwt.claim.sub', true), ''),
    'email', nullif(current_setting('request.jwt.claim.email', true), '')
  )
$$;

revoke all on table auth.users from public, anon, authenticated, service_role;
grant select, insert, update, delete on table auth.users to service_role;
revoke all on function auth.uid() from public, anon;
revoke all on function auth.jwt() from public, anon;
grant execute on function auth.uid() to authenticated, service_role;
grant execute on function auth.jwt() to authenticated, service_role;
