begin;
drop policy if exists chat_sessions_delete_own on public.chat_sessions;
create policy chat_sessions_delete_own
  on public.chat_sessions for delete to authenticated
  using ((select auth.uid()) = user_id);
grant delete on table public.chat_sessions to authenticated;
commit;

begin;

create function public.confirm_birth_time_dynamic_candidate(
  p_user_id uuid,
  p_case_id uuid,
  p_result_id uuid,
  p_time time without time zone,
  p_action_id uuid,
  p_expected_version bigint,
  p_snapshot jsonb,
  p_turn_state jsonb
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_private public.birth_time_rectification_dynamic_state%rowtype;
  v_new_version bigint;
  v_time text := to_char(p_time, 'HH24:MI');
  v_receipt jsonb := jsonb_build_object(
    'actionId', p_action_id::text,
    'kind', 'confirm_candidate',
    'turnVersion', p_expected_version,
    'resultId', p_result_id::text,
    'time', to_char(p_time, 'HH24:MI')
  );
begin
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'dynamic-choice-v2' then
    raise exception 'birth_time_dynamic_case_not_found';
  end if;

  select s.* into v_private
  from public.birth_time_rectification_dynamic_state s
  where s.case_id = p_case_id and s.user_id = p_user_id
  for update;
  if not found then raise exception 'birth_time_dynamic_private_state_missing'; end if;

  if p_action_id = any(v_case.processed_action_ids) then
    if v_case.turn_version is distinct from p_expected_version + 1
      or v_case.turn_state #>> '{nextAction,kind}' is distinct from 'ready'
      or v_case.turn_state #>> '{nextAction,activeTime}' is distinct from v_time
      or v_case.journey_snapshot ->> 'activeTime' is distinct from v_time
      or v_private.dynamic_control -> 'lastActionReceipt' is distinct from v_receipt then
      raise exception 'stale_birth_time_dynamic_candidate';
    end if;
    return v_case.turn_version;
  end if;

  if v_case.turn_version is distinct from p_expected_version
    or v_case.status is distinct from 'confirming'
    or v_case.journey_snapshot ->> 'state' is distinct from 'confirming'
    or v_case.journey_snapshot ->> 'input' is distinct from 'candidate_confirmation'
    or v_case.journey_snapshot ->> 'activeTime' is not null
    or (v_case.journey_snapshot ->> 'canApply')::boolean is not true
    or v_case.candidate_result_id is distinct from p_result_id
    or v_case.candidate_result ->> 'confidence' is distinct from 'high'
    or (v_case.candidate_result ->> 'canApply')::boolean is not true
    or v_case.candidate_result #>> '{winningSegment,representativeTime}' is distinct from v_time
    or v_case.turn_state #>> '{journeyProtocol}' is distinct from 'dynamic-choice-v2'
    or v_case.turn_state #>> '{nextAction,kind}' is distinct from 'request_candidate_confirmation'
    or v_case.turn_state #>> '{nextAction,resultId}' is distinct from p_result_id::text
    or (v_case.turn_state #>> '{permissions,canConfirmCandidate}')::boolean is not true
    or p_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_turn_state #>> '{nextAction,kind}' is distinct from 'ready'
    or p_turn_state #>> '{nextAction,activeTime}' is distinct from v_time
    or p_turn_state #>> '{progress,phase}' is distinct from 'ready'
    or (p_turn_state #>> '{permissions,canConfirmCandidate}')::boolean is not false
    or p_snapshot ->> 'state' is distinct from 'ready'
    or p_snapshot ->> 'route' is distinct from 'direct_chart'
    or p_snapshot ->> 'activeTime' is distinct from v_time
    or (p_snapshot ->> 'canApply')::boolean is not false then
    raise exception 'birth_time_dynamic_candidate_invalid';
  end if;

  update public.birth_time_rectification_cases
  set status = 'confirmed',
      journey_snapshot = p_snapshot,
      confirmed_time = p_time,
      confirmed_at = now(),
      turn_version = p_expected_version + 1,
      turn_state = p_turn_state,
      evidence_draft = null,
      processed_action_ids = case when cardinality(processed_action_ids) >= 100
        then processed_action_ids[2:100] || p_action_id
        else processed_action_ids || p_action_id end,
      updated_at = now()
  where id = p_case_id and user_id = p_user_id and turn_version = p_expected_version
  returning turn_version into v_new_version;
  if v_new_version is null then raise exception 'stale_birth_time_dynamic_candidate'; end if;

  update public.birth_time_rectification_dynamic_state
  set dynamic_control = jsonb_set(dynamic_control, '{lastActionReceipt}', v_receipt, true),
      updated_at = now()
  where case_id = p_case_id and user_id = p_user_id;
  if not found then raise exception 'birth_time_dynamic_private_state_missing'; end if;

  update public.profiles
  set active_birth_time = p_time,
      birth_time = p_time,
      birth_time_status = 'confirmed',
      rectification_case_id = p_case_id
  where id = p_user_id;
  if not found then raise exception 'birth_time_profile_not_found'; end if;

  return v_new_version;
end;
$$;

revoke all on function public.confirm_birth_time_dynamic_candidate(
  uuid, uuid, uuid, time without time zone, uuid, bigint, jsonb, jsonb
) from public, anon, authenticated;
grant execute on function public.confirm_birth_time_dynamic_candidate(
  uuid, uuid, uuid, time without time zone, uuid, bigint, jsonb, jsonb
) to service_role;

commit;
