-- Persist Agentic Rectification candidates and atomically apply a user-selected candidate.
-- A user selection is usable chart time (`accepted`) without claiming the engine uniquely confirmed it.

begin;

alter table public.profiles
  drop constraint if exists profiles_birth_time_status_check;

alter table public.profiles
  add constraint profiles_birth_time_status_check check (
    birth_time_status is null or birth_time_status in (
      'reported',
      'assessing',
      'rectifying',
      'candidate',
      'accepted',
      'confirmed'
    )
  );

create table public.agentic_rectification_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  engine_result_id text not null,
  canonical_input_hash text not null,
  algorithm_version text not null,
  candidate_range jsonb not null,
  candidates jsonb not null check (jsonb_typeof(candidates) = 'array'),
  overall_confidence text not null check (overall_confidence in ('low', 'medium', 'high')),
  margin_percent numeric,
  selection_allowed boolean not null default false,
  confirmation_allowed boolean not null default false,
  representative_time time without time zone,
  baseline_birth_date date not null,
  baseline_reported_birth_time time without time zone,
  baseline_active_birth_time time without time zone,
  baseline_birth_time_source text,
  baseline_birth_time_period text,
  baseline_uncertainty_before_minutes integer,
  baseline_uncertainty_after_minutes integer,
  baseline_latitude double precision not null,
  baseline_longitude double precision not null,
  baseline_timezone_offset double precision not null,
  selected_time time without time zone,
  selection_kind text check (selection_kind in ('user_accepted', 'engine_confirmed')),
  selected_at timestamptz,
  invalidated_at timestamptz,
  expires_at timestamptz not null default (now() + interval '30 days'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, session_id, engine_result_id)
);

create index agentic_rectification_results_latest_idx
  on public.agentic_rectification_results (user_id, session_id, created_at desc)
  where invalidated_at is null;

alter table public.agentic_rectification_results enable row level security;

create policy agentic_rectification_results_select_own
  on public.agentic_rectification_results
  for select to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.agentic_rectification_results from public, anon, authenticated, service_role;
grant select on table public.agentic_rectification_results to authenticated;
grant all on table public.agentic_rectification_results to service_role;

create or replace function public.invalidate_agentic_rectification_results_on_profile_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if old.birth_date is distinct from new.birth_date
    or old.reported_birth_time is distinct from new.reported_birth_time
    or old.birth_time_source is distinct from new.birth_time_source
    or old.birth_time_period is distinct from new.birth_time_period
    or old.uncertainty_before_minutes is distinct from new.uncertainty_before_minutes
    or old.uncertainty_after_minutes is distinct from new.uncertainty_after_minutes
    or old.latitude is distinct from new.latitude
    or old.longitude is distinct from new.longitude
    or old.timezone_offset is distinct from new.timezone_offset
    or (
      (old.active_birth_time is distinct from new.active_birth_time
        or old.birth_time_status is distinct from new.birth_time_status)
      and coalesce(new.birth_time_status, '') not in ('accepted', 'confirmed')
    ) then
    update public.agentic_rectification_results
    set invalidated_at = pg_catalog.now(),
        updated_at = pg_catalog.now()
    where user_id = new.id
      and invalidated_at is null;
  end if;
  return new;
end;
$$;

revoke all on function public.invalidate_agentic_rectification_results_on_profile_change()
  from public, anon, authenticated;

drop trigger if exists profiles_invalidate_agentic_rectification_results on public.profiles;
create trigger profiles_invalidate_agentic_rectification_results
after update of birth_date, reported_birth_time, active_birth_time, birth_time_status,
  birth_time_source, birth_time_period, uncertainty_before_minutes, uncertainty_after_minutes,
  latitude, longitude, timezone_offset
on public.profiles
for each row execute function public.invalidate_agentic_rectification_results_on_profile_change();

create or replace function public.accept_agentic_rectification_candidate(
  p_user_id uuid,
  p_session_id uuid,
  p_result_id uuid,
  p_time time without time zone
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_result public.agentic_rectification_results%rowtype;
  v_profile public.profiles%rowtype;
  v_status text;
  v_selection_kind text;
begin
  if p_user_id is null or p_session_id is null or p_result_id is null or p_time is null
    or extract(second from p_time) is distinct from 0 then
    raise exception 'agentic_rectification_candidate_invalid_input' using errcode = 'P0001';
  end if;

  select * into v_result
  from public.agentic_rectification_results
  where id = p_result_id
    and user_id = p_user_id
    and session_id = p_session_id
  for update;

  if not found then
    raise exception 'agentic_rectification_candidate_not_found' using errcode = 'P0001';
  end if;
  if v_result.invalidated_at is not null or v_result.expires_at <= pg_catalog.now() then
    raise exception 'agentic_rectification_candidate_expired' using errcode = 'P0001';
  end if;
  if not v_result.selection_allowed then
    raise exception 'agentic_rectification_candidate_selection_blocked' using errcode = 'P0001';
  end if;
  if not exists (
    select 1
    from pg_catalog.jsonb_array_elements(v_result.candidates) candidate
    where candidate ->> 'time' = pg_catalog.to_char(p_time, 'HH24:MI')
  ) then
    raise exception 'agentic_rectification_candidate_time_not_allowed' using errcode = 'P0001';
  end if;

  if v_result.selected_time is not null then
    if v_result.selected_time is distinct from p_time then
      raise exception 'agentic_rectification_candidate_already_selected' using errcode = 'P0001';
    end if;
    select * into v_profile
    from public.profiles
    where id = p_user_id
    for update;
    if not found
      or v_profile.active_birth_time is distinct from v_result.selected_time
      or v_profile.birth_time is distinct from v_result.selected_time
      or v_profile.birth_time_status is distinct from (
        case when v_result.selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end
      ) then
      raise exception 'agentic_rectification_candidate_profile_changed' using errcode = 'P0001';
    end if;
    return jsonb_build_object(
      'success', true,
      'saved_time', pg_catalog.to_char(v_result.selected_time, 'HH24:MI'),
      'status', case when v_result.selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end,
      'result_id', v_result.id,
      'idempotent', true
    );
  end if;

  if exists (
    select 1
    from public.agentic_rectification_results newer
    where newer.user_id = p_user_id
      and newer.session_id = p_session_id
      and newer.invalidated_at is null
      and newer.created_at > v_result.created_at
  ) then
    raise exception 'agentic_rectification_candidate_superseded' using errcode = 'P0001';
  end if;

  select * into v_profile
  from public.profiles
  where id = p_user_id
  for update;

  if not found
    or v_profile.birth_date is distinct from v_result.baseline_birth_date
    or v_profile.reported_birth_time is distinct from v_result.baseline_reported_birth_time
    or v_profile.active_birth_time is distinct from v_result.baseline_active_birth_time
    or v_profile.birth_time_source is distinct from v_result.baseline_birth_time_source
    or v_profile.birth_time_period is distinct from v_result.baseline_birth_time_period
    or v_profile.uncertainty_before_minutes is distinct from v_result.baseline_uncertainty_before_minutes
    or v_profile.uncertainty_after_minutes is distinct from v_result.baseline_uncertainty_after_minutes
    or v_profile.latitude is distinct from v_result.baseline_latitude
    or v_profile.longitude is distinct from v_result.baseline_longitude
    or v_profile.timezone_offset is distinct from v_result.baseline_timezone_offset then
    raise exception 'agentic_rectification_candidate_profile_changed' using errcode = 'P0001';
  end if;

  v_selection_kind := case
    when v_result.confirmation_allowed
      and v_result.representative_time is not distinct from p_time
      then 'engine_confirmed'
    else 'user_accepted'
  end;
  v_status := case when v_selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end;

  update public.profiles
  set active_birth_time = p_time,
      birth_time = p_time,
      birth_time_status = v_status,
      rectification_confidence = case
        when v_result.overall_confidence = 'high' then 100
        when v_result.overall_confidence = 'medium' then 70
        else 40
      end,
      updated_at = pg_catalog.now()
  where id = p_user_id;

  update public.agentic_rectification_results
  set selected_time = p_time,
      selection_kind = v_selection_kind,
      selected_at = pg_catalog.now(),
      updated_at = pg_catalog.now()
  where id = v_result.id;

  update public.agentic_rectification_results
  set invalidated_at = pg_catalog.now(),
      updated_at = pg_catalog.now()
  where user_id = p_user_id
    and id <> v_result.id
    and invalidated_at is null
    and selected_time is null;

  return jsonb_build_object(
    'success', true,
    'saved_time', pg_catalog.to_char(p_time, 'HH24:MI'),
    'status', v_status,
    'result_id', v_result.id,
    'idempotent', false
  );
end;
$$;

revoke all on function public.accept_agentic_rectification_candidate(uuid, uuid, uuid, time without time zone)
  from public, anon, authenticated;
grant execute on function public.accept_agentic_rectification_candidate(uuid, uuid, uuid, time without time zone)
  to service_role;

commit;
