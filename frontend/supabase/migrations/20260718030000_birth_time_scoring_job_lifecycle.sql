create or replace function public.create_birth_time_scoring_job(
  p_user_id uuid,
  p_case_id uuid,
  p_job_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_evidence_fingerprint text,
  p_algorithm_version text,
  p_expires_at timestamptz,
  p_snapshot jsonb,
  p_turn_state jsonb,
  p_life_events jsonb,
  p_adaptive_round integer,
  p_asked_domains text[]
)
returns uuid
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_case_id uuid;
begin
  if p_turn_state #>> '{nextAction,kind}' is distinct from 'score_pending'
    or p_turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or (p_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_expires_at <= now() then
    raise exception 'birth_time_scoring_turn_invalid';
  end if;

  update public.birth_time_rectification_cases
  set status = 'rectifying',
      journey_snapshot = p_snapshot,
      life_events = p_life_events,
      turn_version = p_expected_version + 1,
      turn_state = p_turn_state,
      evidence_draft = null,
      processed_action_ids = case
        when cardinality(processed_action_ids) >= 100
          then processed_action_ids[2:100] || p_action_id
        else processed_action_ids || p_action_id
      end,
      adaptive_round = p_adaptive_round,
      asked_domains = p_asked_domains,
      updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version
    and not (processed_action_ids @> array[p_action_id])
  returning id into v_case_id;

  if v_case_id is null then
    raise exception 'birth_time_scoring_turn_stale';
  end if;

  insert into public.birth_time_rectification_scoring_jobs (
    id, case_id, user_id, evidence_fingerprint, algorithm_version,
    status, expires_at
  ) values (
    p_job_id, p_case_id, p_user_id, p_evidence_fingerprint,
    p_algorithm_version, 'pending', p_expires_at
  );

  return p_job_id;
end;
$$;

create or replace function public.claim_birth_time_scoring_job(
  p_user_id uuid,
  p_case_id uuid,
  p_job_id uuid,
  p_evidence_fingerprint text,
  p_algorithm_version text,
  p_now timestamptz
)
returns table (claim_state text, algorithm_version text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_job public.birth_time_rectification_scoring_jobs%rowtype;
  v_case public.birth_time_rectification_cases%rowtype;
  v_candidate_result jsonb;
  v_action_kind text;
  v_result_confidence text;
  v_updated_id uuid;
begin
  select j.* into v_job
  from public.birth_time_rectification_scoring_jobs j
  where j.id = p_job_id
    and j.case_id = p_case_id
    and j.user_id = p_user_id;

  if not found then
    raise exception 'birth_time_scoring_job_not_found';
  end if;
  if v_job.evidence_fingerprint is distinct from p_evidence_fingerprint then
    raise exception 'birth_time_scoring_fingerprint_mismatch';
  end if;
  if v_job.algorithm_version is distinct from p_algorithm_version then
    raise exception 'birth_time_scoring_algorithm_mismatch';
  end if;

  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id;
  if not found then
    raise exception 'birth_time_scoring_turn_invalid';
  end if;

  if v_job.status = 'completed' then
    v_candidate_result = v_case.candidate_result;
    v_action_kind = v_case.turn_state #>> '{nextAction,kind}';
    v_result_confidence = v_job.result ->> 'confidence';
    if v_job.result is null
      or jsonb_typeof(v_job.result) is distinct from 'object'
      or v_candidate_result is distinct from v_job.result
      or (v_job.result ->> 'algorithmVersion') is distinct from p_algorithm_version
      or (v_case.turn_state ->> 'turnVersion') is distinct from v_case.turn_version::text
      or (
        v_result_confidence is distinct from 'low'
        and v_result_confidence is distinct from 'medium'
        and v_result_confidence is distinct from 'high'
      )
      or (
        v_result_confidence = 'low'
        and v_action_kind is distinct from 'ask_adaptive_evidence'
        and v_action_kind is distinct from 'review_evidence_draft'
        and v_action_kind is distinct from 'paused'
        and v_action_kind is distinct from 'present_low_result'
      )
      or (
        v_result_confidence = 'medium'
        and v_action_kind is distinct from 'present_medium_result'
        and v_action_kind is distinct from 'candidate_saved'
      )
      or (
        v_result_confidence = 'high'
        and v_action_kind is distinct from 'request_candidate_confirmation'
        and v_action_kind is distinct from 'ready'
      )
      or (
        v_action_kind in ('present_low_result', 'present_medium_result', 'candidate_saved', 'request_candidate_confirmation')
        and (v_case.turn_state #>> '{nextAction,resultId}')
          is distinct from (v_job.result ->> 'resultId')
      ) then
      raise exception 'birth_time_scoring_result_inconsistent';
    end if;
    return query select 'completed'::text, v_job.algorithm_version;
    return;
  end if;

  if v_case.turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or (
      v_case.turn_state #>> '{nextAction,kind}' is distinct from 'score_pending'
      and v_case.turn_state #>> '{nextAction,kind}' is distinct from 'retry_scoring'
    ) then
    raise exception 'birth_time_scoring_turn_invalid';
  end if;
  if v_job.status = 'processing'
    and v_job.updated_at > p_now - interval '60 seconds' then
    return query select 'processing'::text, v_job.algorithm_version;
    return;
  end if;

  update public.birth_time_rectification_scoring_jobs
  set status = 'processing',
      failure_code = null,
      expires_at = p_now + interval '15 minutes',
      updated_at = p_now
  where id = p_job_id
    and status = v_job.status
    and updated_at = v_job.updated_at
    and status in ('pending', 'failed', 'processing')
    and (
      v_job.status is distinct from 'processing'
      or v_job.updated_at <= p_now - interval '60 seconds'
    )
  returning id into v_updated_id;
  if v_updated_id is null then
    return query select 'processing'::text, v_job.algorithm_version;
    return;
  end if;
  return query select 'claimed'::text, v_job.algorithm_version;
end;
$$;

create or replace function public.complete_birth_time_scoring_job(
  p_user_id uuid,
  p_case_id uuid,
  p_job_id uuid,
  p_expected_version bigint,
  p_evidence_fingerprint text,
  p_snapshot jsonb,
  p_turn_state jsonb,
  p_candidate_result jsonb,
  p_candidate_start time without time zone,
  p_candidate_end time without time zone,
  p_adaptive_round integer,
  p_asked_domains text[]
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_job_id uuid;
  v_case_id uuid;
  v_case_status text;
begin
  if (p_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1 then
    raise exception 'birth_time_scoring_turn_invalid';
  end if;

  update public.birth_time_rectification_scoring_jobs
  set status = 'completed',
      result = p_candidate_result,
      failure_code = null,
      completed_at = now(),
      updated_at = now()
  where id = p_job_id
    and case_id = p_case_id
    and user_id = p_user_id
    and evidence_fingerprint = p_evidence_fingerprint
    and algorithm_version = (p_candidate_result ->> 'algorithmVersion')
    and status = 'processing'
  returning id into v_job_id;
  if v_job_id is null then
    raise exception 'birth_time_scoring_job_not_processing';
  end if;

  v_case_status = case p_snapshot ->> 'state'
    when 'confirming' then 'confirming'
    when 'candidate' then 'candidate'
    when 'ready' then 'confirmed'
    else 'rectifying'
  end;
  update public.birth_time_rectification_cases
  set status = v_case_status,
      journey_snapshot = p_snapshot,
      candidate_result = p_candidate_result,
      event_scoring_version = p_candidate_result ->> 'algorithmVersion',
      candidate_result_id = (p_candidate_result ->> 'resultId')::uuid,
      candidate_start = p_candidate_start,
      candidate_end = p_candidate_end,
      turn_version = p_expected_version + 1,
      turn_state = p_turn_state,
      evidence_draft = null,
      adaptive_round = p_adaptive_round,
      asked_domains = p_asked_domains,
      updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version
  returning id into v_case_id;
  if v_case_id is null then
    raise exception 'birth_time_scoring_turn_stale';
  end if;

  update public.profiles
  set birth_time_status = case when v_case_status = 'confirming' then 'candidate' else v_case_status end,
      rectification_confidence = (p_candidate_result ->> 'marginPercent')::numeric
  where id = p_user_id and rectification_case_id = p_case_id;
end;
$$;

create or replace function public.fail_birth_time_scoring_job(
  p_user_id uuid,
  p_case_id uuid,
  p_job_id uuid,
  p_expected_version bigint,
  p_evidence_fingerprint text,
  p_failure_code text,
  p_turn_state jsonb
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_job_id uuid;
  v_case_id uuid;
begin
  if p_turn_state #>> '{nextAction,kind}' is distinct from 'retry_scoring'
    or p_turn_state #>> '{nextAction,jobId}' is distinct from p_job_id::text
    or (p_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1 then
    raise exception 'birth_time_scoring_turn_invalid';
  end if;

  update public.birth_time_rectification_scoring_jobs
  set status = 'failed', failure_code = p_failure_code, updated_at = now()
  where id = p_job_id
    and case_id = p_case_id
    and user_id = p_user_id
    and evidence_fingerprint = p_evidence_fingerprint
    and status = 'processing'
  returning id into v_job_id;
  if v_job_id is null then
    raise exception 'birth_time_scoring_job_not_processing';
  end if;

  update public.birth_time_rectification_cases
  set turn_version = p_expected_version + 1,
      turn_state = p_turn_state,
      evidence_draft = null,
      updated_at = now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version
  returning id into v_case_id;
  if v_case_id is null then
    raise exception 'birth_time_scoring_turn_stale';
  end if;
end;
$$;

revoke all on function public.create_birth_time_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, timestamptz, jsonb, jsonb, jsonb, integer, text[]) from public, anon, authenticated;
revoke all on function public.claim_birth_time_scoring_job(uuid, uuid, uuid, text, text, timestamptz) from public, anon, authenticated;
revoke all on function public.complete_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb, time without time zone, time without time zone, integer, text[]) from public, anon, authenticated;
revoke all on function public.fail_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb) from public, anon, authenticated;

grant execute on function public.create_birth_time_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, timestamptz, jsonb, jsonb, jsonb, integer, text[]) to service_role;
grant execute on function public.claim_birth_time_scoring_job(uuid, uuid, uuid, text, text, timestamptz) to service_role;
grant execute on function public.complete_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb, time without time zone, time without time zone, integer, text[]) to service_role;
grant execute on function public.fail_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb) to service_role;
