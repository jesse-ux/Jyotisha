create or replace function public.upgrade_birth_time_legacy_case(
  p_user_id uuid, p_case_id uuid, p_expected_version bigint,
  p_public_turn_state jsonb, p_private_state jsonb
)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_action text;
begin
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id for update;
  if not found then raise exception 'birth_time_legacy_case_not_found'; end if;
  if v_case.journey_protocol = 'dynamic-choice-v2' then return v_case.turn_version; end if;
  v_action = v_case.turn_state #>> '{nextAction,kind}';
  if v_case.journey_snapshot ->> 'state' in ('candidate', 'confirming', 'ready')
    or v_action in ('present_low_result', 'present_medium_result', 'candidate_saved',
      'request_candidate_confirmation', 'ready') then
    raise exception 'birth_time_legacy_case_terminal';
  end if;
  if v_case.turn_version is distinct from p_expected_version
    or p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version
    or jsonb_typeof(p_private_state) is distinct from 'object' then
    raise exception 'stale_birth_time_legacy_upgrade';
  end if;
  update public.birth_time_rectification_cases
  set journey_protocol = 'dynamic-choice-v2', turn_state = p_public_turn_state,
      evidence_draft = null
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' and turn_version = p_expected_version;
  if not found then raise exception 'stale_birth_time_legacy_upgrade'; end if;
  perform public.persist_birth_time_dynamic_private_state(p_case_id, p_user_id, p_private_state);
  return p_expected_version;
end;
$$;

create or replace function public.complete_birth_time_dynamic_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid, p_expected_version bigint,
  p_evidence_fingerprint text, p_algorithm_version text,
  p_public_turn_state jsonb, p_snapshot jsonb, p_candidate_result jsonb,
  p_private_state jsonb
)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_job public.birth_time_rectification_scoring_jobs%rowtype;
begin
  select j.* into v_job from public.birth_time_rectification_scoring_jobs j
  where j.id = p_job_id and j.case_id = p_case_id and j.user_id = p_user_id for update;
  if not found then raise exception 'birth_time_dynamic_scoring_job_not_found'; end if;
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
    and c.journey_protocol = 'dynamic-choice-v2' for update;
  if not found then raise exception 'birth_time_dynamic_case_not_found'; end if;
  if v_job.evidence_fingerprint is distinct from p_evidence_fingerprint then
    raise exception 'birth_time_dynamic_scoring_fingerprint_mismatch';
  end if;
  if v_job.algorithm_version is distinct from p_algorithm_version then
    raise exception 'birth_time_dynamic_scoring_algorithm_mismatch';
  end if;
  if v_job.status = 'completed' then
    if v_job.result is distinct from p_candidate_result
      or v_case.turn_version is distinct from p_expected_version + 1 then
      raise exception 'stale_birth_time_dynamic_scoring_job';
    end if;
    return v_case.turn_version;
  end if;
  if v_job.status is distinct from 'processing'
    or v_case.turn_version is distinct from p_expected_version
    or v_case.turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or coalesce(v_case.turn_state #>> '{nextAction,kind}', '') not in ('score_pending', 'retry_scoring')
    or p_candidate_result ->> 'algorithmVersion' is distinct from p_algorithm_version
    or p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or jsonb_path_exists(p_public_turn_state, '$.**.partitionId')
    or jsonb_path_exists(p_public_turn_state, '$.**.candidateScores')
    or jsonb_path_exists(p_public_turn_state, '$.**.agentContext')
    or jsonb_typeof(p_private_state) is distinct from 'object' then
    raise exception 'stale_birth_time_dynamic_scoring_job';
  end if;
  update public.birth_time_rectification_scoring_jobs
  set status = 'completed', result = p_candidate_result, failure_code = null,
      completed_at = now(), updated_at = now()
  where id = p_job_id and status = 'processing';
  update public.birth_time_rectification_cases
  set status = case p_snapshot ->> 'state'
        when 'ready' then 'confirmed' when 'confirming' then 'confirming'
        when 'candidate' then 'candidate' else 'rectifying' end,
      journey_snapshot = p_snapshot, candidate_result = p_candidate_result,
      event_scoring_version = p_algorithm_version,
      candidate_result_id = (p_candidate_result ->> 'resultId')::uuid,
      candidate_start = (p_candidate_result #>> '{winningSegment,startTime}')::time,
      candidate_end = (p_candidate_result #>> '{winningSegment,endTime}')::time,
      turn_version = p_expected_version + 1, turn_state = p_public_turn_state,
      evidence_draft = null, updated_at = now()
  where id = p_case_id and user_id = p_user_id and turn_version = p_expected_version;
  if not found then raise exception 'stale_birth_time_dynamic_scoring_job'; end if;
  perform public.persist_birth_time_dynamic_private_state(p_case_id, p_user_id, p_private_state);
  return p_expected_version + 1;
end;
$$;

create or replace function public.fail_birth_time_dynamic_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid, p_expected_version bigint,
  p_evidence_fingerprint text, p_algorithm_version text, p_failure_code text,
  p_public_turn_state jsonb, p_private_state jsonb
)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_job public.birth_time_rectification_scoring_jobs%rowtype;
begin
  select j.* into v_job from public.birth_time_rectification_scoring_jobs j
  where j.id = p_job_id and j.case_id = p_case_id and j.user_id = p_user_id for update;
  if not found then raise exception 'birth_time_dynamic_scoring_job_not_found'; end if;
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
    and c.journey_protocol = 'dynamic-choice-v2' for update;
  if not found then raise exception 'birth_time_dynamic_case_not_found'; end if;
  if v_job.evidence_fingerprint is distinct from p_evidence_fingerprint then
    raise exception 'birth_time_dynamic_scoring_fingerprint_mismatch';
  end if;
  if v_job.algorithm_version is distinct from p_algorithm_version then
    raise exception 'birth_time_dynamic_scoring_algorithm_mismatch';
  end if;
  if v_job.status = 'failed' then
    if v_job.failure_code is distinct from p_failure_code
      or v_case.turn_version is distinct from p_expected_version + 1 then
      raise exception 'stale_birth_time_dynamic_scoring_job';
    end if;
    return v_case.turn_version;
  end if;
  if v_job.status is distinct from 'processing'
    or v_case.turn_version is distinct from p_expected_version
    or v_case.turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or coalesce(v_case.turn_state #>> '{nextAction,kind}', '') not in ('score_pending', 'retry_scoring')
    or p_public_turn_state #>> '{nextAction,kind}' is distinct from 'retry_scoring'
    or p_public_turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or jsonb_path_exists(p_public_turn_state, '$.**.partitionId')
    or jsonb_path_exists(p_public_turn_state, '$.**.candidateScores')
    or jsonb_path_exists(p_public_turn_state, '$.**.agentContext')
    or jsonb_typeof(p_private_state) is distinct from 'object' then
    raise exception 'stale_birth_time_dynamic_scoring_job';
  end if;
  update public.birth_time_rectification_scoring_jobs
  set status = 'failed', failure_code = p_failure_code, updated_at = now()
  where id = p_job_id and status = 'processing';
  update public.birth_time_rectification_cases
  set turn_version = p_expected_version + 1, turn_state = p_public_turn_state,
      evidence_draft = null, updated_at = now()
  where id = p_case_id and user_id = p_user_id and turn_version = p_expected_version;
  if not found then raise exception 'stale_birth_time_dynamic_scoring_job'; end if;
  perform public.persist_birth_time_dynamic_private_state(p_case_id, p_user_id, p_private_state);
  return p_expected_version + 1;
end;
$$;

revoke all on function public.upgrade_birth_time_legacy_case(uuid, uuid, bigint, jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.complete_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb, jsonb, jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.fail_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, text, text, text, jsonb, jsonb) from public, anon, authenticated;
grant execute on function public.upgrade_birth_time_legacy_case(uuid, uuid, bigint, jsonb, jsonb) to service_role;
grant execute on function public.complete_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb, jsonb, jsonb, jsonb) to service_role;
grant execute on function public.fail_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, text, text, text, jsonb, jsonb) to service_role;
