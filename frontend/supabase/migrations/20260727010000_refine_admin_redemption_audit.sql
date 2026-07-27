alter table public.redemption_codes
  add column if not exists revoked_at timestamptz,
  add column if not exists revoked_by uuid;

alter table public.redemption_codes
  drop constraint if exists redemption_codes_redeemed_or_revoked_check;
alter table public.redemption_codes
  add constraint redemption_codes_redeemed_or_revoked_check check (
    not (redeemed_at is not null and revoked_at is not null)
    and ((revoked_by is null and revoked_at is null)
      or (revoked_by is not null and revoked_at is not null))
  );

create index if not exists redemption_codes_revoked_at_idx
  on public.redemption_codes (revoked_at)
  where revoked_at is not null;

create schema if not exists audit;
revoke all on schema audit from public, anon, authenticated;
grant usage on schema audit to service_role;

create table if not exists audit.admin_audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid not null,
  actor_email text not null check (actor_email = lower(btrim(actor_email)) and char_length(actor_email) between 3 and 320),
  actor_role text not null check (actor_role in ('admin', 'viewer')),
  action text not null check (action in ('redemption_code.create', 'redemption_code.update', 'redemption_code.revoke')),
  target_type text not null check (target_type = 'redemption_code'),
  target_id uuid not null,
  before_value jsonb,
  after_value jsonb,
  request_id text not null check (char_length(request_id) between 1 and 200),
  created_at timestamptz not null default clock_timestamp(),
  check (before_value is null or not (before_value ?| array['code', 'code_hash', 'token', 'secret', 'key'])),
  check (after_value is null or not (after_value ?| array['code', 'code_hash', 'token', 'secret', 'key'])),
  unique (actor_user_id, request_id, action, target_id)
);

create index if not exists admin_audit_logs_created_at_idx
  on audit.admin_audit_logs (created_at desc);
create index if not exists admin_audit_logs_actor_idx
  on audit.admin_audit_logs (actor_user_id, created_at desc);

alter table audit.admin_audit_logs enable row level security;
revoke all on table audit.admin_audit_logs from public, anon, authenticated, service_role;
grant select on table audit.admin_audit_logs to service_role;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'admin_runtime') then
    grant usage on schema audit to admin_runtime;
    grant select on table audit.admin_audit_logs to admin_runtime;
    grant select (id, email, credits, name, birth_date, birth_time_status,
      birth_place_label) on table public.profiles to admin_runtime;
    grant select (id, code_mask, credits, expires_at, note, created_at,
      redeemed_by, redeemed_email, redeemed_at, revoked_by, revoked_at)
      on table public.redemption_codes to admin_runtime;
    grant select (id, user_id, transaction_type, amount, balance_after,
      request_id, model, input_tokens, output_tokens, created_at)
      on table public.credit_transactions to admin_runtime;
    grant select (user_id, request_id, status, created_at, updated_at)
      on table public.consultation_requests to admin_runtime;

    drop policy if exists profiles_admin_read on public.profiles;
    create policy profiles_admin_read on public.profiles
      for select to admin_runtime using (true);
    drop policy if exists redemption_codes_admin_read on public.redemption_codes;
    create policy redemption_codes_admin_read on public.redemption_codes
      for select to admin_runtime using (true);
    drop policy if exists credit_transactions_admin_read on public.credit_transactions;
    create policy credit_transactions_admin_read on public.credit_transactions
      for select to admin_runtime using (true);
    drop policy if exists consultation_requests_admin_read on public.consultation_requests;
    create policy consultation_requests_admin_read on public.consultation_requests
      for select to admin_runtime using (true);
    drop policy if exists admin_audit_logs_admin_read on audit.admin_audit_logs;
    create policy admin_audit_logs_admin_read on audit.admin_audit_logs
      for select to admin_runtime using (true);
  end if;
end;
$$;

create or replace function public.reject_admin_audit_mutation()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception 'admin audit logs are append-only' using errcode = '55000';
end;
$$;

revoke all on function public.reject_admin_audit_mutation() from public, anon, authenticated, service_role;

drop trigger if exists admin_audit_logs_append_only on audit.admin_audit_logs;
create trigger admin_audit_logs_append_only
  before update or delete on audit.admin_audit_logs
  for each row execute function public.reject_admin_audit_mutation();

create or replace function public.admin_redemption_code_snapshot(p_code public.redemption_codes)
returns jsonb
language sql
stable
set search_path = ''
as $$
  select jsonb_build_object(
    'id', p_code.id,
    'mask', p_code.code_mask,
    'credits', p_code.credits,
    'expiresAt', p_code.expires_at,
    'note', p_code.note,
    'status', case
      when p_code.redeemed_at is not null then 'redeemed'
      when p_code.revoked_at is not null then 'revoked'
      when p_code.expires_at is not null and p_code.expires_at <= now() then 'expired'
      else 'available'
    end,
    'redeemedAt', p_code.redeemed_at,
    'revokedAt', p_code.revoked_at
  )
$$;

revoke all on function public.admin_redemption_code_snapshot(public.redemption_codes)
  from public, anon, authenticated, service_role;

create or replace function public.admin_verified_actor_email(
  p_actor_user_id uuid,
  p_actor_email text,
  p_actor_role text
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email text;
  v_role text;
  v_banned boolean;
  v_ban_expires timestamptz;
begin
  select lower(btrim(u.email)), u.role, u.banned, u.ban_expires
  into v_email, v_role, v_banned, v_ban_expires
  from identity.users u
  where u.id = p_actor_user_id;

  if not found or p_actor_role <> 'admin'
    or v_role is null
    or not ('admin' = any(string_to_array(replace(v_role, ' ', ''), ',')))
    or v_email is distinct from lower(btrim(p_actor_email))
    or (v_banned and (v_ban_expires is null or v_ban_expires > now())) then
    raise exception 'administrator access required' using errcode = '42501';
  end if;
  return v_email;
end;
$$;

revoke all on function public.admin_verified_actor_email(uuid, text, text)
  from public, anon, authenticated, service_role;

create or replace function public.admin_create_redemption_codes(
  p_actor_user_id uuid,
  p_actor_email text,
  p_actor_role text,
  p_request_id text,
  p_codes jsonb
)
returns table (
  id uuid,
  code_mask text,
  credits integer,
  expires_at timestamptz,
  note text,
  created_at timestamptz,
  redeemed_by uuid,
  redeemed_email text,
  redeemed_at timestamptz,
  revoked_by uuid,
  revoked_at timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_item jsonb;
  v_code public.redemption_codes%rowtype;
  v_email text := lower(btrim(p_actor_email));
  v_request_id text := btrim(p_request_id);
begin
  v_email := public.admin_verified_actor_email(
    p_actor_user_id, p_actor_email, p_actor_role
  );
  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    raise exception 'invalid request id' using errcode = '22023';
  end if;
  if p_codes is null or jsonb_typeof(p_codes) is distinct from 'array'
    or jsonb_array_length(p_codes) not between 1 and 100 then
    raise exception 'codes must contain between 1 and 100 items' using errcode = '22023';
  end if;

  for v_item in select value from jsonb_array_elements(p_codes)
  loop
    insert into public.redemption_codes (
      code_hash, code_mask, credits, expires_at, note, created_by
    ) values (
      v_item ->> 'codeHash',
      v_item ->> 'codeMask',
      (v_item ->> 'credits')::integer,
      nullif(v_item ->> 'expiresAt', '')::timestamptz,
      nullif(btrim(v_item ->> 'note'), ''),
      p_actor_user_id
    ) returning * into v_code;

    insert into audit.admin_audit_logs (
      actor_user_id, actor_email, actor_role, action, target_type,
      target_id, before_value, after_value, request_id
    ) values (
      p_actor_user_id, v_email, p_actor_role, 'redemption_code.create',
      'redemption_code', v_code.id, null,
      public.admin_redemption_code_snapshot(v_code), v_request_id
    );

    id := v_code.id;
    code_mask := v_code.code_mask;
    credits := v_code.credits;
    expires_at := v_code.expires_at;
    note := v_code.note;
    created_at := v_code.created_at;
    redeemed_by := v_code.redeemed_by;
    redeemed_email := v_code.redeemed_email;
    redeemed_at := v_code.redeemed_at;
    revoked_by := v_code.revoked_by;
    revoked_at := v_code.revoked_at;
    return next;
  end loop;
end;
$$;

create or replace function public.admin_update_redemption_code(
  p_actor_user_id uuid,
  p_actor_email text,
  p_actor_role text,
  p_request_id text,
  p_code_id uuid,
  p_set_note boolean,
  p_note text,
  p_set_expires_at boolean,
  p_expires_at timestamptz
)
returns table (
  id uuid,
  code_mask text,
  credits integer,
  expires_at timestamptz,
  note text,
  created_at timestamptz,
  redeemed_by uuid,
  redeemed_email text,
  redeemed_at timestamptz,
  revoked_by uuid,
  revoked_at timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_before public.redemption_codes%rowtype;
  v_after public.redemption_codes%rowtype;
  v_email text := lower(btrim(p_actor_email));
begin
  v_email := public.admin_verified_actor_email(
    p_actor_user_id, p_actor_email, p_actor_role
  );
  if p_request_id is null or char_length(btrim(p_request_id)) not between 1 and 200 then
    raise exception 'invalid request id' using errcode = '22023';
  end if;
  if not coalesce(p_set_note, false) and not coalesce(p_set_expires_at, false) then
    raise exception 'no editable field supplied' using errcode = '22023';
  end if;
  if p_set_note and p_note is not null and char_length(p_note) > 500 then
    raise exception 'note is too long' using errcode = '22023';
  end if;

  select rc.* into v_before
  from public.redemption_codes rc
  where rc.id = p_code_id
  for update;
  if not found then
    raise exception 'redemption code not found' using errcode = 'P0002';
  end if;
  if v_before.redeemed_at is not null then
    raise exception 'redeemed codes are immutable' using errcode = '55000';
  end if;
  if v_before.revoked_at is not null then
    raise exception 'revoked codes are immutable' using errcode = '55000';
  end if;

  update public.redemption_codes rc
  set note = case when p_set_note then nullif(btrim(p_note), '') else rc.note end,
      expires_at = case when p_set_expires_at then p_expires_at else rc.expires_at end
  where rc.id = p_code_id
  returning * into v_after;

  insert into audit.admin_audit_logs (
    actor_user_id, actor_email, actor_role, action, target_type,
    target_id, before_value, after_value, request_id
  ) values (
    p_actor_user_id, v_email, p_actor_role, 'redemption_code.update',
    'redemption_code', v_after.id,
    public.admin_redemption_code_snapshot(v_before),
    public.admin_redemption_code_snapshot(v_after), btrim(p_request_id)
  );

  return query select
    v_after.id, v_after.code_mask, v_after.credits, v_after.expires_at,
    v_after.note, v_after.created_at, v_after.redeemed_by,
    v_after.redeemed_email, v_after.redeemed_at, v_after.revoked_by,
    v_after.revoked_at;
end;
$$;

create or replace function public.admin_revoke_redemption_code(
  p_actor_user_id uuid,
  p_actor_email text,
  p_actor_role text,
  p_request_id text,
  p_code_id uuid
)
returns table (
  id uuid,
  code_mask text,
  credits integer,
  expires_at timestamptz,
  note text,
  created_at timestamptz,
  redeemed_by uuid,
  redeemed_email text,
  redeemed_at timestamptz,
  revoked_by uuid,
  revoked_at timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_before public.redemption_codes%rowtype;
  v_after public.redemption_codes%rowtype;
  v_email text := lower(btrim(p_actor_email));
begin
  v_email := public.admin_verified_actor_email(
    p_actor_user_id, p_actor_email, p_actor_role
  );
  if p_request_id is null or char_length(btrim(p_request_id)) not between 1 and 200 then
    raise exception 'invalid request id' using errcode = '22023';
  end if;

  select rc.* into v_before
  from public.redemption_codes rc
  where rc.id = p_code_id
  for update;
  if not found then
    raise exception 'redemption code not found' using errcode = 'P0002';
  end if;
  if v_before.redeemed_at is not null then
    raise exception 'redeemed codes cannot be revoked' using errcode = '55000';
  end if;
  if v_before.revoked_at is not null then
    raise exception 'redemption code is already revoked' using errcode = '55000';
  end if;

  update public.redemption_codes rc
  set revoked_at = clock_timestamp(), revoked_by = p_actor_user_id
  where rc.id = p_code_id
  returning * into v_after;

  insert into audit.admin_audit_logs (
    actor_user_id, actor_email, actor_role, action, target_type,
    target_id, before_value, after_value, request_id
  ) values (
    p_actor_user_id, v_email, p_actor_role, 'redemption_code.revoke',
    'redemption_code', v_after.id,
    public.admin_redemption_code_snapshot(v_before),
    public.admin_redemption_code_snapshot(v_after), btrim(p_request_id)
  );

  return query select
    v_after.id, v_after.code_mask, v_after.credits, v_after.expires_at,
    v_after.note, v_after.created_at, v_after.redeemed_by,
    v_after.redeemed_email, v_after.redeemed_at, v_after.revoked_by,
    v_after.revoked_at;
end;
$$;

create or replace function public.redeem_code(p_code_hash text)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_email text := auth.jwt() ->> 'email';
  v_code public.redemption_codes%rowtype;
  v_balance integer;
begin
  if v_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;
  if p_code_hash is null or p_code_hash !~ '^[0-9a-f]{64}$' then
    return query select false, null::integer, 'invalid_code'::text;
    return;
  end if;

  select rc.* into v_code
  from public.redemption_codes rc
  where rc.code_hash = p_code_hash
  for update;
  if not found then
    return query select false, null::integer, 'invalid_code'::text;
    return;
  end if;
  if v_code.redeemed_by is not null then
    return query select false, null::integer, 'already_redeemed'::text;
    return;
  end if;
  if v_code.revoked_at is not null then
    return query select false, null::integer, 'revoked_code'::text;
    return;
  end if;
  if v_code.expires_at is not null and v_code.expires_at <= now() then
    return query select false, null::integer, 'expired_code'::text;
    return;
  end if;

  select p.credits into v_balance
  from public.profiles p
  where p.id = v_user_id
  for update;
  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  update public.redemption_codes rc
  set redeemed_by = v_user_id, redeemed_email = v_email, redeemed_at = now()
  where rc.id = v_code.id;
  update public.profiles p
  set credits = p.credits + v_code.credits, updated_at = now()
  where p.id = v_user_id
  returning p.credits into v_balance;
  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id, redemption_code_id
  ) values (
    v_user_id, 'redeem', v_code.credits, v_balance, v_code.id::text, v_code.id
  );
  return query select true, v_balance, null::text;
end;
$$;

revoke all on function public.admin_create_redemption_codes(uuid, text, text, text, jsonb)
  from public, anon, authenticated;
revoke all on function public.admin_update_redemption_code(uuid, text, text, text, uuid, boolean, text, boolean, timestamptz)
  from public, anon, authenticated;
revoke all on function public.admin_revoke_redemption_code(uuid, text, text, text, uuid)
  from public, anon, authenticated;
grant execute on function public.admin_create_redemption_codes(uuid, text, text, text, jsonb) to service_role;
grant execute on function public.admin_update_redemption_code(uuid, text, text, text, uuid, boolean, text, boolean, timestamptz) to service_role;
grant execute on function public.admin_revoke_redemption_code(uuid, text, text, text, uuid) to service_role;

revoke all on function public.redeem_code(text) from public, anon;
grant execute on function public.redeem_code(text) to authenticated;
