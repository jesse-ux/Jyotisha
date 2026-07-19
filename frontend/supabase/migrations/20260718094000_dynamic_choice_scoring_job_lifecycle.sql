begin;

create function public.create_birth_time_dynamic_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_expected_version bigint, p_action_id uuid, p_question_id text,
  p_evidence_fingerprint text, p_algorithm_version text,
  p_expires_at timestamptz, p_public_turn_state jsonb,
  p_snapshot jsonb, p_private_state jsonb
) returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_job public.birth_time_rectification_scoring_jobs%rowtype;
  v_new_version bigint;
begin
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
    and c.journey_protocol = 'dynamic-choice-v2' for update;
  if not found then raise exception 'birth_time_dynamic_case_not_found'; end if;

  if p_action_id = any(v_case.processed_action_ids) then
    select j.* into v_job from public.birth_time_rectification_scoring_jobs j
    where j.id = p_job_id and j.case_id = p_case_id and j.user_id = p_user_id;
    if not found
      or v_case.turn_version is distinct from p_expected_version + 1
      or v_case.turn_state #>> '{nextAction,kind}' is distinct from 'score_pending'
      or v_case.turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
      or v_job.evidence_fingerprint is distinct from p_evidence_fingerprint
      or v_job.algorithm_version is distinct from p_algorithm_version then
      raise exception 'stale_birth_time_dynamic_scoring_job';
    end if;
    return v_case.turn_version;
  end if;

  if v_case.turn_version is distinct from p_expected_version
    or v_case.turn_state #>> '{nextAction,kind}' is distinct from 'ask_dynamic_choice'
    or v_case.turn_state #>> '{nextAction,question,questionId}' is distinct from p_question_id
    or p_algorithm_version is distinct from 'birth-time-choice-scoring-v2'
    or coalesce(p_evidence_fingerprint, '') = ''
    or p_expires_at <= now()
    or p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_public_turn_state #>> '{nextAction,kind}' is distinct from 'score_pending'
    or p_public_turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or jsonb_typeof(p_private_state) is distinct from 'object'
    or p_private_state -> 'currentChoiceQuestion' is distinct from 'null'::jsonb
    or p_private_state #>> '{choiceAnswers,-1,questionId}' is distinct from p_question_id
    or jsonb_path_exists(p_public_turn_state, '$.**.partitionId')
    or jsonb_path_exists(p_public_turn_state, '$.**.candidateScores')
    or jsonb_path_exists(p_public_turn_state, '$.**.agentContext') then
    raise exception 'birth_time_dynamic_scoring_turn_invalid';
  end if;

  insert into public.birth_time_rectification_scoring_jobs (
    id, case_id, user_id, evidence_fingerprint, algorithm_version,
    status, expires_at
  ) values (
    p_job_id, p_case_id, p_user_id, p_evidence_fingerprint,
    p_algorithm_version, 'pending', p_expires_at
  );

  update public.birth_time_rectification_cases
  set status = 'rectifying', journey_snapshot = p_snapshot,
      turn_version = p_expected_version + 1, turn_state = p_public_turn_state,
      evidence_draft = null,
      processed_action_ids = case
        when cardinality(processed_action_ids) >= 100
          then processed_action_ids[2:100] || p_action_id
        else processed_action_ids || p_action_id end,
      updated_at = now()
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'dynamic-choice-v2'
    and turn_version = p_expected_version
  returning turn_version into v_new_version;
  if v_new_version is null then
    raise exception 'stale_birth_time_dynamic_scoring_job';
  end if;
  perform public.persist_birth_time_dynamic_private_state(
    p_case_id, p_user_id, p_private_state
  );
  return v_new_version;
end;
$$;

create function public.claim_birth_time_dynamic_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_evidence_fingerprint text, p_algorithm_version text, p_now timestamptz
) returns table (claim_state text, algorithm_version text)
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_job public.birth_time_rectification_scoring_jobs%rowtype;
  v_action text;
  v_confidence text;
  v_result_id text;
  v_updated_id uuid;
begin
  select c.* into v_case from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
    and c.journey_protocol = 'dynamic-choice-v2' for update;
  if not found then raise exception 'birth_time_dynamic_case_not_found'; end if;
  select j.* into v_job from public.birth_time_rectification_scoring_jobs j
  where j.id = p_job_id and j.case_id = p_case_id and j.user_id = p_user_id
  for update;
  if not found then raise exception 'birth_time_dynamic_scoring_job_not_found'; end if;
  if v_job.evidence_fingerprint is distinct from p_evidence_fingerprint then
    raise exception 'birth_time_dynamic_scoring_fingerprint_mismatch';
  end if;
  if v_job.algorithm_version is distinct from p_algorithm_version then
    raise exception 'birth_time_dynamic_scoring_algorithm_mismatch';
  end if;

  v_action = v_case.turn_state #>> '{nextAction,kind}';
  if v_job.status = 'completed' then
    v_confidence = v_job.result ->> 'confidence';
    v_result_id = v_job.result ->> 'resultId';
    if v_job.result is null
      or v_case.candidate_result is distinct from v_job.result
      or (v_job.result ->> 'algorithmVersion') is distinct from p_algorithm_version
      or (v_case.turn_state ->> 'turnVersion')::bigint is distinct from v_case.turn_version
      or (v_confidence = 'low' and v_action not in ('generate_dynamic_question', 'present_low_result'))
      or (v_confidence = 'medium' and v_action not in ('generate_dynamic_question', 'present_medium_result'))
      or (v_confidence = 'high' and v_action is distinct from 'request_candidate_confirmation')
      or v_confidence not in ('low', 'medium', 'high')
      or (v_action <> 'generate_dynamic_question'
        and v_case.turn_state #>> '{nextAction,resultId}' is distinct from v_result_id) then
      raise exception 'birth_time_dynamic_scoring_result_inconsistent';
    end if;
    return query select 'completed'::text, v_job.algorithm_version;
    return;
  end if;

  if v_case.turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or v_action not in ('score_pending', 'retry_scoring') then
    raise exception 'birth_time_dynamic_scoring_turn_invalid';
  end if;
  if v_job.status = 'processing'
    and v_job.updated_at > p_now - interval '60 seconds' then
    return query select 'processing'::text, v_job.algorithm_version;
    return;
  end if;
  update public.birth_time_rectification_scoring_jobs
  set status = 'processing', failure_code = null,
      expires_at = p_now + interval '15 minutes', updated_at = p_now
  where id = p_job_id and status = v_job.status and updated_at = v_job.updated_at
    and status in ('pending', 'failed', 'processing')
    and (v_job.status <> 'processing'
      or v_job.updated_at <= p_now - interval '60 seconds')
  returning id into v_updated_id;
  if v_updated_id is null then
    return query select 'processing'::text, v_job.algorithm_version;
    return;
  end if;
  return query select 'claimed'::text, v_job.algorithm_version;
end;
$$;

revoke all on function public.create_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, text, timestamptz, jsonb, jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.claim_birth_time_dynamic_scoring_job(uuid, uuid, uuid, text, text, timestamptz) from public, anon, authenticated;
grant execute on function public.create_birth_time_dynamic_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, text, timestamptz, jsonb, jsonb, jsonb) to service_role;
grant execute on function public.claim_birth_time_dynamic_scoring_job(uuid, uuid, uuid, text, text, timestamptz) to service_role;

commit;
