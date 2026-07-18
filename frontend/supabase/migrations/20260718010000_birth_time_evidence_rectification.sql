begin;

alter table public.birth_time_rectification_cases
  add column if not exists life_events jsonb not null default '[]'::jsonb,
  add column if not exists candidate_result jsonb not null default '{}'::jsonb,
  add column if not exists event_scoring_version text,
  add column if not exists candidate_result_id uuid,
  add column if not exists candidate_saved_at timestamptz;

alter table public.birth_time_rectification_cases
  drop constraint if exists birth_time_rectification_cases_life_events_check,
  drop constraint if exists birth_time_rectification_cases_candidate_result_check,
  drop constraint if exists birth_time_rectification_cases_status_check;

alter table public.birth_time_rectification_cases
  add constraint birth_time_rectification_cases_life_events_check check (
    jsonb_typeof(life_events) = 'array'
  ),
  add constraint birth_time_rectification_cases_candidate_result_check check (
    jsonb_typeof(candidate_result) = 'object'
  ),
  add constraint birth_time_rectification_cases_status_check check (
    status in ('assessing', 'rectifying', 'candidate', 'confirming', 'confirmed')
  );

revoke update (
  life_events,
  candidate_result,
  event_scoring_version,
  candidate_result_id,
  candidate_saved_at,
  confirmed_time,
  confirmed_at
) on table public.birth_time_rectification_cases from authenticated;

grant all on table public.birth_time_rectification_cases to service_role;

create or replace function public.confirm_birth_time_candidate(
  p_user_id uuid,
  p_case_id uuid,
  p_result_id uuid,
  p_time time without time zone,
  p_snapshot jsonb
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.birth_time_rectification_cases
  set
    status = 'confirmed',
    journey_snapshot = p_snapshot,
    confirmed_time = p_time,
    confirmed_at = now(),
    updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and candidate_result_id = p_result_id
    and status = 'confirming'
    and candidate_result ->> 'confidence' = 'high'
    and (candidate_result ->> 'canApply')::boolean is true
    and candidate_result #>> '{winningSegment,representativeTime}' = to_char(p_time, 'HH24:MI');

  if not found then
    raise exception 'stale_or_ineligible_birth_time_candidate';
  end if;

  update public.profiles
  set
    active_birth_time = p_time,
    birth_time = p_time,
    birth_time_status = 'confirmed'
  where id = p_user_id
    and rectification_case_id = p_case_id;

  if not found then
    raise exception 'birth_time_profile_not_found';
  end if;
end;
$$;

revoke all on function public.confirm_birth_time_candidate(uuid, uuid, uuid, time without time zone, jsonb)
from public, anon, authenticated;
grant execute on function public.confirm_birth_time_candidate(uuid, uuid, uuid, time without time zone, jsonb)
to service_role;

commit;
