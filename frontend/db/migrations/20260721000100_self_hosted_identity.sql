create table if not exists identity.users (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null,
  email_verified boolean not null default false,
  email_verified_at timestamptz,
  image text,
  role text not null default 'user',
  banned boolean not null default false,
  ban_reason text,
  ban_expires timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists identity_users_email_canonical_key
  on identity.users (lower(btrim(email)));

create table if not exists identity.sessions (
  id uuid primary key default gen_random_uuid(),
  token text not null unique,
  user_id uuid not null references identity.users(id) on delete cascade,
  expires_at timestamptz not null,
  ip_address text,
  user_agent text,
  impersonated_by uuid references identity.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists identity_sessions_user_id_idx
  on identity.sessions (user_id);
create index if not exists identity_sessions_expires_at_idx
  on identity.sessions (expires_at);

create table if not exists identity.accounts (
  id uuid primary key default gen_random_uuid(),
  account_id text not null,
  provider_id text not null,
  user_id uuid not null references identity.users(id) on delete cascade,
  access_token text,
  refresh_token text,
  id_token text,
  access_token_expires_at timestamptz,
  refresh_token_expires_at timestamptz,
  scope text,
  password text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider_id, account_id)
);

create index if not exists identity_accounts_user_id_idx
  on identity.accounts (user_id);

create table if not exists identity.verifications (
  id uuid primary key default gen_random_uuid(),
  identifier text not null,
  value text not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists identity_verifications_identifier_idx
  on identity.verifications (identifier);
create index if not exists identity_verifications_expires_at_idx
  on identity.verifications (expires_at);

create table if not exists identity.otp_rate_limits (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  count integer not null default 0 check (count >= 0),
  last_request bigint not null
);

revoke all on table
  identity.users,
  identity.sessions,
  identity.accounts,
  identity.verifications,
  identity.otp_rate_limits
from public, app_runtime, backup_reader, migration_runner;

grant select, insert, update, delete on table
  identity.users,
  identity.sessions,
  identity.accounts,
  identity.verifications,
  identity.otp_rate_limits
to identity_runtime;

grant select on table
  identity.users,
  identity.sessions,
  identity.accounts,
  identity.verifications,
  identity.otp_rate_limits
to admin_runtime;
