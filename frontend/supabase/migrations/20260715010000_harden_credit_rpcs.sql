begin;

-- Remove the earlier auth.uid()-based overloads if this project applied a draft migration.
drop function if exists public.reserve_credit(text, integer);
drop function if exists public.refund_credit(text);

-- A cancellation tombstone closes the "refund arrived before a delayed reserve" race.
create table if not exists public.credit_request_cancellations (
  user_id uuid not null references auth.users(id) on delete cascade,
  request_id text not null check (char_length(request_id) between 1 and 200),
  created_at timestamptz not null default now(),
  primary key (user_id, request_id)
);

alter table public.credit_request_cancellations enable row level security;
revoke all on public.credit_request_cancellations from anon, authenticated;

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

  perform pg_advisory_xact_lock(hashtextextended(v_user_id::text || ':' || v_request_id, 0));

  if exists (
    select 1 from public.credit_request_cancellations as cancellation
    where cancellation.user_id = v_user_id
      and cancellation.request_id = v_request_id
  ) then
    select p.credits into v_balance from public.profiles as p where p.id = v_user_id;
    return query select false, v_balance, 'request_cancelled'::text;
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
  v_reserve_found boolean;
begin
  if v_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  perform pg_advisory_xact_lock(hashtextextended(v_user_id::text || ':' || v_request_id, 0));

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
  v_reserve_found := found;

  insert into public.credit_request_cancellations (user_id, request_id)
  values (v_user_id, v_request_id)
  on conflict (user_id, request_id) do nothing;

  if not v_reserve_found then
    return query select true, v_balance, null::text;
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

-- CREATE OR REPLACE preserves ACLs, so explicitly clear every browser-accessible role.
revoke all on function public.reserve_credit(uuid, text, integer) from public, anon, authenticated;
revoke all on function public.refund_credit(uuid, text) from public, anon, authenticated;
grant execute on function public.reserve_credit(uuid, text, integer) to service_role;
grant execute on function public.refund_credit(uuid, text) to service_role;

commit;
