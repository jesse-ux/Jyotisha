begin;

create table if not exists public.consultation_requests (
  user_id uuid not null references auth.users(id) on delete cascade,
  request_id text not null check (char_length(request_id) between 1 and 200),
  status text not null check (status in ('reserved', 'completed', 'cancelled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, request_id)
);

create index if not exists consultation_requests_user_created_idx
  on public.consultation_requests (user_id, created_at);

alter table public.consultation_requests enable row level security;
revoke all on public.consultation_requests from public, anon, authenticated;

create or replace function public.begin_consultation_credit(p_user_id uuid, p_request_id text)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_request_id text := btrim(p_request_id);
  v_balance integer;
begin
  if p_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_user_id::text || ':' || v_request_id, 0));

  if exists (
    select 1 from public.consultation_requests as request
    where request.user_id = p_user_id and request.request_id = v_request_id
  ) then
    select profile.credits into v_balance
    from public.profiles as profile
    where profile.id = p_user_id;
    return query select false, v_balance, 'request_conflict'::text;
    return;
  end if;

  update public.profiles as profile
  set credits = profile.credits - 1,
      updated_at = now()
  where profile.id = p_user_id and profile.credits >= 1
  returning profile.credits into v_balance;

  if not found then
    select profile.credits into v_balance
    from public.profiles as profile
    where profile.id = p_user_id;
    return query select false, v_balance, case when v_balance is null then 'profile_missing' else 'insufficient_credits' end;
    return;
  end if;

  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id
  ) values (
    p_user_id, 'reserve', -1, v_balance, v_request_id
  );

  insert into public.consultation_requests (user_id, request_id, status)
  values (p_user_id, v_request_id, 'reserved');

  return query select true, v_balance, null::text;
end;
$$;

create or replace function public.complete_consultation_credit(p_user_id uuid, p_request_id text)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_request_id text := btrim(p_request_id);
  v_balance integer;
  v_status text;
begin
  if p_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_user_id::text || ':' || v_request_id, 0));

  select request.status into v_status
  from public.consultation_requests as request
  where request.user_id = p_user_id and request.request_id = v_request_id
  for update;

  select profile.credits into v_balance
  from public.profiles as profile
  where profile.id = p_user_id;

  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  if v_status = 'completed' then
    return query select true, v_balance, null::text;
    return;
  end if;

  if v_status is null then
    return query select false, v_balance, 'request_missing'::text;
    return;
  end if;

  if v_status = 'cancelled' then
    return query select false, v_balance, 'request_cancelled'::text;
    return;
  end if;

  update public.consultation_requests as request
  set status = 'completed', updated_at = now()
  where request.user_id = p_user_id and request.request_id = v_request_id;

  return query select true, v_balance, null::text;
end;
$$;

create or replace function public.cancel_consultation_credit(p_user_id uuid, p_request_id text)
returns table (success boolean, credits integer, error_code text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_request_id text := btrim(p_request_id);
  v_balance integer;
  v_status text;
  v_reserve public.credit_transactions%rowtype;
  v_refund public.credit_transactions%rowtype;
  v_recent_missing integer;
begin
  if p_user_id is null then
    return query select false, null::integer, 'unauthorized'::text;
    return;
  end if;

  if v_request_id is null or char_length(v_request_id) not between 1 and 200 then
    return query select false, null::integer, 'invalid_request'::text;
    return;
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_user_id::text || ':' || v_request_id, 0));

  select request.status into v_status
  from public.consultation_requests as request
  where request.user_id = p_user_id and request.request_id = v_request_id
  for update;

  select profile.credits into v_balance
  from public.profiles as profile
  where profile.id = p_user_id
  for update;

  if not found then
    return query select false, null::integer, 'profile_missing'::text;
    return;
  end if;

  if v_status = 'completed' then
    return query select false, v_balance, 'request_completed'::text;
    return;
  end if;

  if v_status = 'cancelled' then
    return query select true, v_balance, null::text;
    return;
  end if;

  if v_status is null then
    delete from public.consultation_requests as stale
    where stale.user_id = p_user_id
      and stale.status = 'cancelled'
      and stale.created_at < now() - interval '1 day'
      and not exists (
        select 1 from public.credit_transactions as tx
        where tx.user_id = stale.user_id and tx.request_id = stale.request_id
      );

    select count(*) into v_recent_missing
    from public.consultation_requests as recent
    where recent.user_id = p_user_id
      and recent.status = 'cancelled'
      and recent.created_at >= now() - interval '1 hour';

    if v_recent_missing >= 60 then
      return query select false, v_balance, 'rate_limited'::text;
      return;
    end if;

    insert into public.consultation_requests (user_id, request_id, status)
    values (p_user_id, v_request_id, 'cancelled');
    return query select true, v_balance, null::text;
    return;
  end if;

  select tx.* into v_refund
  from public.credit_transactions as tx
  where tx.user_id = p_user_id
    and tx.transaction_type = 'refund'
    and tx.request_id = v_request_id;

  if found then
    update public.consultation_requests as request
    set status = 'cancelled', updated_at = now()
    where request.user_id = p_user_id and request.request_id = v_request_id;
    return query select true, v_refund.balance_after, null::text;
    return;
  end if;

  select tx.* into v_reserve
  from public.credit_transactions as tx
  where tx.user_id = p_user_id
    and tx.transaction_type = 'reserve'
    and tx.request_id = v_request_id;

  if not found then
    return query select false, v_balance, 'reservation_missing'::text;
    return;
  end if;

  update public.profiles as profile
  set credits = profile.credits - v_reserve.amount,
      updated_at = now()
  where profile.id = p_user_id
  returning profile.credits into v_balance;

  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id
  ) values (
    p_user_id, 'refund', -v_reserve.amount, v_balance, v_request_id
  );

  update public.consultation_requests as request
  set status = 'cancelled', updated_at = now()
  where request.user_id = p_user_id and request.request_id = v_request_id;

  return query select true, v_balance, null::text;
end;
$$;

revoke all on function public.begin_consultation_credit(uuid, text) from public, anon, authenticated;
revoke all on function public.complete_consultation_credit(uuid, text) from public, anon, authenticated;
revoke all on function public.cancel_consultation_credit(uuid, text) from public, anon, authenticated;
grant execute on function public.begin_consultation_credit(uuid, text) to service_role;
grant execute on function public.complete_consultation_credit(uuid, text) to service_role;
grant execute on function public.cancel_consultation_credit(uuid, text) to service_role;

commit;
