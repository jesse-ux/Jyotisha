begin;

create or replace function public.save_guided_birth_time_candidate(
  p_user_id uuid,
  p_case_id uuid,
  p_result_id uuid,
  p_action_id uuid,
  p_expected_version integer,
  p_turn_state jsonb
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  current_version integer;
  receipts uuid[];
begin
  select turn_version, processed_action_ids
  into current_version, receipts
  from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
  for update;

  if not found then raise exception 'invalid_guided_candidate_turn'; end if;
  if p_action_id = any(receipts) then return; end if;
  if current_version <> p_expected_version then raise exception 'stale_guided_candidate_turn'; end if;
  if (p_turn_state ->> 'turnVersion')::integer <> p_expected_version + 1
    or p_turn_state #>> '{nextAction,kind}' <> 'candidate_saved'
    or p_turn_state #>> '{nextAction,resultId}' <> p_result_id::text
  then raise exception 'invalid_guided_candidate_turn'; end if;

  update public.birth_time_rectification_cases
  set candidate_saved_at = now(),
      turn_version = p_expected_version + 1,
      turn_state = p_turn_state,
      processed_action_ids = (array_append(processed_action_ids, p_action_id))[
        greatest(cardinality(processed_action_ids) + 2 - 100, 1):cardinality(processed_action_ids) + 1
      ],
      updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version
    and candidate_result_id = p_result_id
    and status = 'candidate'
    and candidate_result ->> 'confidence' = 'medium'
    and (
      (
        turn_state #>> '{nextAction,kind}' = 'present_medium_result'
        and turn_state #>> '{nextAction,resultId}' = p_result_id::text
      )
      or turn_state is null
      or turn_state = '{}'::jsonb
    );
  if not found then raise exception 'invalid_guided_candidate_turn'; end if;
end;
$$;

create or replace function public.confirm_guided_birth_time_candidate(
  p_user_id uuid,
  p_case_id uuid,
  p_result_id uuid,
  p_time time without time zone,
  p_action_id uuid,
  p_expected_version integer,
  p_snapshot jsonb,
  p_turn_state jsonb
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  current_version integer;
  receipts uuid[];
begin
  select turn_version, processed_action_ids
  into current_version, receipts
  from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
  for update;

  if not found then raise exception 'invalid_guided_candidate_turn'; end if;
  if p_action_id = any(receipts) then return; end if;
  if current_version <> p_expected_version then raise exception 'stale_guided_candidate_turn'; end if;
  if (p_turn_state ->> 'turnVersion')::integer <> p_expected_version + 1
    or p_turn_state #>> '{nextAction,kind}' <> 'ready'
    or p_turn_state #>> '{nextAction,activeTime}' <> to_char(p_time, 'HH24:MI')
    or p_snapshot ->> 'activeTime' <> to_char(p_time, 'HH24:MI')
  then raise exception 'invalid_guided_candidate_turn'; end if;

  update public.birth_time_rectification_cases
  set status = 'confirmed', journey_snapshot = p_snapshot,
      confirmed_time = p_time, confirmed_at = now(),
      turn_version = p_expected_version + 1, turn_state = p_turn_state,
      processed_action_ids = (array_append(processed_action_ids, p_action_id))[
        greatest(cardinality(processed_action_ids) + 2 - 100, 1):cardinality(processed_action_ids) + 1
      ],
      updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version
    and candidate_result_id = p_result_id
    and status = 'confirming'
    and candidate_result ->> 'confidence' = 'high'
    and (candidate_result ->> 'canApply')::boolean is true
    and candidate_result #>> '{winningSegment,representativeTime}' = to_char(p_time, 'HH24:MI')
    and (
      (
        turn_state #>> '{nextAction,kind}' = 'request_candidate_confirmation'
        and turn_state #>> '{nextAction,resultId}' = p_result_id::text
      )
      or turn_state is null
      or turn_state = '{}'::jsonb
    );
  if not found then raise exception 'invalid_guided_candidate_turn'; end if;

  update public.profiles
  set active_birth_time = p_time, birth_time = p_time, birth_time_status = 'confirmed'
  where id = p_user_id and rectification_case_id = p_case_id;
  if not found then raise exception 'birth_time_profile_not_found'; end if;
end;
$$;

revoke all on function public.save_guided_birth_time_candidate(uuid, uuid, uuid, uuid, integer, jsonb)
from public, anon, authenticated;
grant execute on function public.save_guided_birth_time_candidate(uuid, uuid, uuid, uuid, integer, jsonb)
to service_role;
revoke all on function public.confirm_guided_birth_time_candidate(uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb)
from public, anon, authenticated;
grant execute on function public.confirm_guided_birth_time_candidate(uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb)
to service_role;

commit;
