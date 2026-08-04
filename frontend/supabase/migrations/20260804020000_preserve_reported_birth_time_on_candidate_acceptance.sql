begin;

-- The user declaration and the chart application are separate records.
-- `birth_time` remains a legacy compatibility field; new rectification writes
-- only the server-owned active chart time.
create or replace function public.guard_birth_time_journey()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.birth_time_source is null and new.birth_time is not null then
    new.birth_time_source := 'legacy_import';
  end if;
  if new.birth_time_status is null and new.active_birth_time is not null then
    new.birth_time_status := 'confirmed';
  end if;

  return new;
end;
$$;

-- Repair profiles selected through the Agentic candidate flow while preserving
-- genuine legacy imports. The adopted minute remains in active_birth_time.
with selected as (
  select distinct on (user_id)
    user_id,
    selected_time
  from public.agentic_rectification_results
  where selected_time is not null
  order by user_id, selected_at desc nulls last, created_at desc
)
update public.profiles p
set birth_time = case
      when p.birth_time_source = 'legacy_import' then p.reported_birth_time
      else null
    end,
    updated_at = pg_catalog.now()
from selected
where p.id = selected.user_id
  and p.birth_time_status in ('accepted', 'confirmed')
  and p.active_birth_time is not distinct from selected.selected_time
  and p.birth_time is not distinct from selected.selected_time;

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
    select * into v_profile
    from public.profiles
    where id = p_user_id
    for update;
    if not found
      or v_profile.active_birth_time is distinct from v_result.selected_time
      or v_profile.birth_time_status is distinct from (
        case when v_result.selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end
      ) then
      raise exception 'agentic_rectification_candidate_profile_changed' using errcode = 'P0001';
    end if;
    if v_result.selected_time is not distinct from p_time then
      return jsonb_build_object(
        'success', true,
        'saved_time', pg_catalog.to_char(v_result.selected_time, 'HH24:MI'),
        'status', case when v_result.selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end,
        'result_id', v_result.id,
        'idempotent', true
      );
    end if;
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

  if v_result.selected_time is null then
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
