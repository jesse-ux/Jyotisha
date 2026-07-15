create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  credits integer not null default 0 check (credits >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.redemption_codes (
  id uuid primary key default gen_random_uuid(),
  code_hash text not null unique check (code_hash ~ '^[0-9a-f]{64}$'),
  code_mask text not null check (code_mask like 'JYOTISH-****-%'),
  credits integer not null check (credits > 0),
  expires_at timestamptz,
  note text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  redeemed_by uuid,
  redeemed_email text,
  redeemed_at timestamptz,
  check ((redeemed_by is null and redeemed_at is null) or (redeemed_by is not null and redeemed_at is not null))
);

create table if not exists public.credit_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  transaction_type text not null check (transaction_type in ('redeem', 'reserve', 'refund')),
  amount integer not null,
  check ((transaction_type = 'reserve' and amount < 0)
      or (transaction_type in ('redeem', 'refund') and amount > 0)),
  balance_after integer not null check (balance_after >= 0),
  request_id text not null check (char_length(request_id) between 1 and 200),
  redemption_code_id uuid unique references public.redemption_codes(id) on delete set null,
  model text,
  input_tokens integer check (input_tokens is null or input_tokens >= 0),
  output_tokens integer check (output_tokens is null or output_tokens >= 0),
  created_at timestamptz not null default now(),
  unique (user_id, transaction_type, request_id)
);

create index if not exists redemption_codes_created_at_idx
  on public.redemption_codes (created_at desc);
create index if not exists credit_transactions_user_created_at_idx
  on public.credit_transactions (user_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.redemption_codes enable row level security;
alter table public.credit_transactions enable row level security;

create policy profiles_select_own
  on public.profiles for select to authenticated
  using ((select auth.uid()) = id);

create policy credit_transactions_select_own
  on public.credit_transactions for select to authenticated
  using ((select auth.uid()) = user_id);

revoke all on public.profiles from anon, authenticated;
revoke all on public.redemption_codes from anon, authenticated;
revoke all on public.credit_transactions from anon, authenticated;
grant select on public.profiles to authenticated;
grant select on public.credit_transactions to authenticated;

create or replace function public.handle_new_jyotish_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

revoke all on function public.handle_new_jyotish_user() from public;

drop trigger if exists jyotish_profile_on_auth_user_created on auth.users;
create trigger jyotish_profile_on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_jyotish_user();

insert into public.profiles (id, email)
select id, email from auth.users
on conflict (id) do nothing;

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
  from public.redemption_codes as rc
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

  if v_code.expires_at is not null and v_code.expires_at <= now() then
    return query select false, null::integer, 'expired_code'::text;
    return;
  end if;

  select p.credits into v_balance
  from public.profiles as p
  where p.id = v_user_id
  for update;

  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  update public.redemption_codes as rc
  set redeemed_by = v_user_id,
      redeemed_email = v_email,
      redeemed_at = now()
  where rc.id = v_code.id;

  update public.profiles as p
  set credits = p.credits + v_code.credits,
      updated_at = now()
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

create or replace function public.reserve_credit(p_user_id uuid, p_request_id text, p_credits integer default 1)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user_id uuid := p_user_id;
  v_request_id text := btrim(p_request_id);
  v_balance integer;
  v_existing public.credit_transactions%rowtype;
begin
  if v_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200
     or p_credits is null or p_credits <= 0 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  select p.credits into v_balance
  from public.profiles as p
  where p.id = v_user_id
  for update;

  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  select tx.* into v_existing
  from public.credit_transactions as tx
  where tx.user_id = v_user_id
    and tx.transaction_type = 'reserve'
    and tx.request_id = v_request_id;

  if found then
    if v_existing.amount = -p_credits then
      return query select true, v_existing.balance_after, null::text;
    else
      return query select false, v_balance, 'request_conflict'::text;
    end if;
    return;
  end if;

  update public.profiles as p
  set credits = p.credits - p_credits,
      updated_at = now()
  where p.id = v_user_id and p.credits >= p_credits
  returning p.credits into v_balance;

  if not found then
    return query select false, v_balance, 'insufficient_credits'::text;
    return;
  end if;

  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id
  ) values (
    v_user_id, 'reserve', -p_credits, v_balance, v_request_id
  );

  return query select true, v_balance, null::text;
end;
$$;

create or replace function public.refund_credit(p_user_id uuid, p_request_id text)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user_id uuid := p_user_id;
  v_request_id text := btrim(p_request_id);
  v_balance integer;
  v_reserve public.credit_transactions%rowtype;
  v_refund public.credit_transactions%rowtype;
begin
  if v_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  select p.credits into v_balance
  from public.profiles as p
  where p.id = v_user_id
  for update;

  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  select tx.* into v_refund
  from public.credit_transactions as tx
  where tx.user_id = v_user_id
    and tx.transaction_type = 'refund'
    and tx.request_id = v_request_id;

  if found then
    return query select true, v_refund.balance_after, null::text;
    return;
  end if;

  select tx.* into v_reserve
  from public.credit_transactions as tx
  where tx.user_id = v_user_id
    and tx.transaction_type = 'reserve'
    and tx.request_id = v_request_id;

  if not found then
    return query select false, v_balance, 'reservation_not_found'::text;
    return;
  end if;

  update public.profiles as p
  set credits = p.credits - v_reserve.amount,
      updated_at = now()
  where p.id = v_user_id
  returning p.credits into v_balance;

  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id
  ) values (
    v_user_id, 'refund', -v_reserve.amount, v_balance, v_request_id
  );

  return query select true, v_balance, null::text;
end;
$$;

revoke all on function public.redeem_code(text) from public, anon;
revoke all on function public.reserve_credit(uuid, text, integer) from public, anon, authenticated;
revoke all on function public.refund_credit(uuid, text) from public, anon, authenticated;
grant execute on function public.redeem_code(text) to authenticated;
grant execute on function public.reserve_credit(uuid, text, integer) to service_role;
grant execute on function public.refund_credit(uuid, text) to service_role;
