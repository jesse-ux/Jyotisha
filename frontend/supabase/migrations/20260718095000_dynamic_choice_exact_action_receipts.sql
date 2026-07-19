begin;

create or replace function public.save_birth_time_dynamic_turn(
  p_user_id uuid, p_case_id uuid, p_expected_version bigint, p_action_id uuid,
  p_public_turn_state jsonb, p_snapshot jsonb, p_candidate_result jsonb,
  p_private_state jsonb
) returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_private public.birth_time_rectification_dynamic_state%rowtype;
  v_receipt jsonb;
  v_new_version bigint;
begin
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id for update;
  if not found or v_case.journey_protocol is distinct from 'dynamic-choice-v2' then
    raise exception 'birth_time_dynamic_case_not_found';
  end if;
  select s.* into v_private from public.birth_time_rectification_dynamic_state s
  where s.case_id = p_case_id and s.user_id = p_user_id for update;
  if not found then raise exception 'birth_time_dynamic_private_state_missing'; end if;
  v_receipt = p_private_state #> '{dynamicControl,lastActionReceipt}';
  if jsonb_typeof(v_receipt) is distinct from 'object'
    or v_receipt ->> 'actionId' is distinct from p_action_id::text
    or (v_receipt ->> 'turnVersion')::bigint is distinct from p_expected_version then
    raise exception 'birth_time_dynamic_turn_invalid';
  end if;
  if p_action_id = any(v_case.processed_action_ids) then
    if v_case.turn_version is distinct from p_expected_version + 1
      or v_private.dynamic_control -> 'lastActionReceipt' is distinct from v_receipt
      or v_private.dynamic_control #>> '{lastActionReceipt,actionId}'
        is distinct from p_action_id::text then
      raise exception 'stale_birth_time_dynamic_turn';
    end if;
    return v_case.turn_version;
  end if;
  if v_case.turn_version is distinct from p_expected_version
    or p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or jsonb_typeof(p_private_state) is distinct from 'object'
    or jsonb_path_exists(p_public_turn_state, '$.**.partitionId')
    or jsonb_path_exists(p_public_turn_state, '$.**.candidateScores')
    or jsonb_path_exists(p_public_turn_state, '$.**.agentContext') then
    raise exception 'birth_time_dynamic_turn_invalid';
  end if;
  update public.birth_time_rectification_cases
  set status = case p_snapshot ->> 'state'
        when 'ready' then 'confirmed' when 'confirming' then 'confirming'
        when 'candidate' then 'candidate' else 'rectifying' end,
      journey_snapshot = p_snapshot,
      candidate_result = coalesce(p_candidate_result, '{}'::jsonb),
      event_scoring_version = p_candidate_result ->> 'algorithmVersion',
      candidate_result_id = case when p_candidate_result ? 'resultId'
        then (p_candidate_result ->> 'resultId')::uuid else null end,
      candidate_start = case
        when p_candidate_result #>> '{winningSegment,startTime}' is null then null
        else (p_candidate_result #>> '{winningSegment,startTime}')::time end,
      candidate_end = case
        when p_candidate_result #>> '{winningSegment,endTime}' is null then null
        else (p_candidate_result #>> '{winningSegment,endTime}')::time end,
      turn_version = p_expected_version + 1, turn_state = p_public_turn_state,
      evidence_draft = null,
      processed_action_ids = case when cardinality(processed_action_ids) >= 100
        then processed_action_ids[2:100] || p_action_id
        else processed_action_ids || p_action_id end,
      updated_at = now()
  where id = p_case_id and user_id = p_user_id and turn_version = p_expected_version
  returning turn_version into v_new_version;
  if v_new_version is null then raise exception 'stale_birth_time_dynamic_turn'; end if;
  perform public.persist_birth_time_dynamic_private_state(
    p_case_id, p_user_id, p_private_state
  );
  return v_new_version;
end;
$$;

revoke all on function public.save_birth_time_dynamic_turn(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb
) from public, anon, authenticated;
grant execute on function public.save_birth_time_dynamic_turn(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb
) to service_role;

commit;
