begin;

alter table public.birth_time_rectification_v4_event_revisions
  add column if not exists date_provenance jsonb;

alter table public.birth_time_rectification_v4_event_revisions
  drop constraint if exists birth_time_rectification_v4_event_revisions_date_provenance_check;
alter table public.birth_time_rectification_v4_event_revisions
  add constraint birth_time_rectification_v4_event_revisions_date_provenance_check
  check (date_provenance is null or pg_catalog.jsonb_typeof(date_provenance) = 'object');

create or replace function public.revise_birth_time_rectification_v4_event(
  p_user_id uuid, p_case_id uuid, p_action_id uuid, p_expected_version bigint,
  p_revision jsonb, p_output_evidence_set_hash text, p_turn_id uuid, p_job_id uuid, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_case public.birth_time_rectification_v4_cases%rowtype; v_job_id uuid; v_event_id uuid;
begin
  select action.job_id into v_job_id from public.birth_time_rectification_v4_actions action
    where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_job_id is not null then return v_job_id; end if;
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.id = p_case_id and value.user_id = p_user_id for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;
  if v_case.version <> p_expected_version then raise exception 'stale_rectification_v4_case'; end if;
  if v_case.status in ('processing', 'abandoned', 'paused') then raise exception 'rectification_v4_case_invalid_state'; end if;
  if jsonb_typeof(p_revision) <> 'object' then raise exception 'invalid_rectification_v4_event_revision'; end if;
  v_event_id = (p_revision->>'eventId')::uuid;
  insert into public.birth_time_rectification_v4_events(id, case_id, user_id, created_at)
    values (v_event_id, p_case_id, p_user_id, p_now) on conflict (id) do nothing;
  insert into public.birth_time_rectification_v4_event_revisions(
    id, event_id, case_id, user_id, revision, domain, event_kind, summary, raw_text,
    date_start, date_end, date_precision, date_label, date_provenance, scoreability, supersedes_revision_id, created_at
  ) values (
    (p_revision->>'id')::uuid, v_event_id, p_case_id, p_user_id,
    (p_revision->>'revision')::integer, p_revision->>'domain', p_revision->>'eventKind',
    p_revision->>'summary', p_revision->>'rawText',
    (p_revision#>>'{dateRange,start}')::date, (p_revision#>>'{dateRange,end}')::date,
    p_revision#>>'{dateRange,precision}', p_revision#>>'{dateRange,label}',
    (select pg_catalog.jsonb_object_agg(entry.key, entry.value)
       from pg_catalog.jsonb_each(p_revision) entry
      where entry.key in ('dateSource', 'dateReliability', 'dateCorroboration', 'dateConflictStatus')),
    p_revision->>'scoreability', nullif(p_revision->>'supersedesRevisionId', '')::uuid,
    (p_revision->>'createdAt')::timestamptz
  );
  insert into public.birth_time_rectification_v4_turns(
    id, case_id, user_id, case_version, question, answer, action_id, created_at
  ) values (p_turn_id, p_case_id, p_user_id, p_expected_version + 1, '修订事件', '', p_action_id, p_now);
  update public.birth_time_rectification_v4_cases set
    version = p_expected_version + 1, status = 'processing', phase = 'scoring_candidates',
    evidence_set_hash = p_output_evidence_set_hash, current_question = null, updated_at = p_now
    where id = p_case_id;
  insert into public.birth_time_rectification_v4_jobs(
    id, case_id, user_id, turn_id, status, phase, expected_case_version,
    evidence_set_hash, calculation_spec_hash, created_at, updated_at
  ) values (
    p_job_id, p_case_id, p_user_id, p_turn_id, 'pending', 'scoring_candidates', p_expected_version + 1,
    p_output_evidence_set_hash, v_case.calculation_spec_hash, p_now, p_now
  );
  insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, job_id, created_at)
    values (p_user_id, p_action_id, p_case_id, p_job_id, p_now);
  return p_job_id;
end;
$$;

create or replace function public.complete_birth_time_rectification_v5_job(
  p_worker_id uuid,
  p_job_id uuid,
  p_expected_case_version bigint,
  p_input_evidence_set_hash text,
  p_output_evidence_set_hash text,
  p_calculation_spec_hash text,
  p_completion_payload_hash text,
  p_event_revisions jsonb,
  p_pending_evidence jsonb,
  p_snapshot jsonb,
  p_diagnostics jsonb,
  p_feature_snapshot jsonb,
  p_validated_decision jsonb,
  p_public_message jsonb,
  p_agent_run jsonb,
  p_next_question jsonb,
  p_status text,
  p_phase text,
  p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  v_job public.birth_time_rectification_v4_jobs%rowtype;
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_existing_run public.birth_time_rectification_agent_runs%rowtype;
  v_existing_message public.birth_time_rectification_public_messages%rowtype;
  item jsonb;
  v_snapshot_id uuid;
  v_feature_id uuid;
  v_diagnostics_id uuid;
  v_event_id uuid;
  v_supersedes_id uuid;
  v_pending_count integer;
begin
  if jsonb_typeof(p_event_revisions) is distinct from 'array'
    or jsonb_typeof(p_pending_evidence) is distinct from 'array'
    or jsonb_typeof(p_validated_decision) is distinct from 'object'
    or jsonb_typeof(p_public_message) is distinct from 'object'
    or jsonb_typeof(p_agent_run) is distinct from 'object'
    or p_output_evidence_set_hash !~ '^[a-f0-9]{64}$'
    or p_calculation_spec_hash !~ '^[a-f0-9]{64}$'
    or p_completion_payload_hash !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid_rectification_v5_completion_payload';
  end if;

  select value.* into v_job
  from public.birth_time_rectification_v4_jobs value
  where value.id = p_job_id
  for update;
  if not found then raise exception 'rectification_v4_job_lease_lost'; end if;

  select value.* into v_case
  from public.birth_time_rectification_v4_cases value
  where value.id = v_job.case_id
  for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;

  -- A network retry after commit is an idempotent read, never a second artifact write.
  if v_job.status = 'completed' then
    select value.* into v_existing_run
    from public.birth_time_rectification_agent_runs value
    where value.job_id = p_job_id;
    select value.* into v_existing_message
    from public.birth_time_rectification_public_messages value
    where value.job_id = p_job_id;
    select count(*) into v_pending_count
    from public.birth_time_rectification_pending_evidence value
    where value.turn_id = v_job.turn_id;
    if v_existing_run.id is null
      or v_existing_run.id is distinct from (p_agent_run->>'id')::uuid
      or v_existing_run.case_id is distinct from v_case.id
      or v_existing_run.case_version is distinct from p_expected_case_version
      or v_existing_run.validated_decision_json is distinct from p_validated_decision
      or v_existing_message.job_id is null
      or v_existing_message.message is distinct from p_public_message
      or v_job.completion_payload_hash is distinct from p_completion_payload_hash
      or v_pending_count is distinct from pg_catalog.jsonb_array_length(p_pending_evidence) then
      raise exception 'rectification_v5_replay_payload_mismatch';
    end if;
    for item in select value from pg_catalog.jsonb_array_elements(p_pending_evidence) loop
      if not exists (
        select 1 from public.birth_time_rectification_pending_evidence value
        where value.id = (item->>'id')::uuid
          and value.case_id = v_case.id
          and value.user_id = v_case.user_id
          and value.turn_id = v_job.turn_id
          and value.target_event_id is not distinct from nullif(item->>'targetEventId', '')::uuid
          and value.raw_text = item->>'rawText'
          and value.reason_code = item->>'reasonCode'
          and value.resolved_event_id is not distinct from nullif(item->>'resolvedEventId', '')::uuid
          and value.created_at = (item->>'createdAt')::timestamptz
          and value.resolved_at is not distinct from nullif(item->>'resolvedAt', '')::timestamptz
      ) then
        raise exception 'rectification_v5_replay_payload_mismatch';
      end if;
    end loop;
    return v_case.id;
  end if;

  if v_job.worker_id is distinct from p_worker_id
    or v_job.status <> 'processing'
    or v_job.lease_expires_at <= p_now then
    raise exception 'rectification_v4_job_lease_lost';
  end if;
  if v_case.version is distinct from p_expected_case_version
    or v_case.evidence_set_hash is distinct from p_input_evidence_set_hash
    or v_case.calculation_spec_hash is distinct from p_calculation_spec_hash
    or v_job.expected_case_version is distinct from p_expected_case_version
    or v_job.evidence_set_hash is distinct from p_input_evidence_set_hash
    or v_job.calculation_spec_hash is distinct from p_calculation_spec_hash then
    raise exception 'stale_rectification_v4_job';
  end if;

  if (p_agent_run->>'caseId')::uuid is distinct from v_case.id
    or (p_agent_run->>'jobId')::uuid is distinct from p_job_id
    or (p_agent_run->>'caseVersion')::bigint is distinct from p_expected_case_version
    or p_agent_run->>'deploymentMode' is distinct from v_case.deployment_mode
    or p_agent_run->'validatedDecision' is distinct from p_validated_decision
    or jsonb_typeof(p_agent_run->'toolCalls') is distinct from 'array'
    or pg_catalog.jsonb_array_length(p_agent_run->'toolCalls') > 8
    or p_validated_decision->>'mode' not in ('agent', 'deterministic_fallback') then
    raise exception 'invalid_rectification_v5_agent_run';
  end if;

  for item in select value from pg_catalog.jsonb_array_elements(p_event_revisions) loop
    v_event_id := (item->>'eventId')::uuid;
    v_supersedes_id := nullif(item->>'supersedesRevisionId', '')::uuid;
    if (item->>'caseId') is not null and (item->>'caseId')::uuid is distinct from v_case.id then
      raise exception 'rectification_v5_event_case_mismatch';
    end if;
    insert into public.birth_time_rectification_v4_events(
      id, case_id, user_id, created_at
    ) values (
      v_event_id, v_case.id, v_case.user_id, (item->>'createdAt')::timestamptz
    ) on conflict (id) do nothing;
    if not exists (
      select 1 from public.birth_time_rectification_v4_events value
      where value.id = v_event_id and value.case_id = v_case.id and value.user_id = v_case.user_id
    ) then
      raise exception 'rectification_v5_event_case_mismatch';
    end if;
    if v_supersedes_id is not null and not exists (
      select 1 from public.birth_time_rectification_v4_event_revisions value
      where value.id = v_supersedes_id and value.event_id = v_event_id and value.case_id = v_case.id
    ) then
      raise exception 'rectification_v5_superseded_revision_mismatch';
    end if;
    insert into public.birth_time_rectification_v4_event_revisions(
      id, event_id, case_id, user_id, revision, domain, event_kind, subject,
      related_person, summary, raw_text, date_start, date_end, date_precision,
      date_label, date_provenance, scoreability, supersedes_revision_id, created_at
    ) values (
      (item->>'id')::uuid, v_event_id, v_case.id, v_case.user_id,
      (item->>'revision')::integer, item->>'domain', item->>'eventKind', item->>'subject',
      nullif(item->>'relatedPerson', ''), item->>'summary', item->>'rawText',
      (item#>>'{dateRange,start}')::date, (item#>>'{dateRange,end}')::date,
      item#>>'{dateRange,precision}', item#>>'{dateRange,label}',
      (select pg_catalog.jsonb_object_agg(entry.key, entry.value)
         from pg_catalog.jsonb_each(item) entry
        where entry.key in ('dateSource', 'dateReliability', 'dateCorroboration', 'dateConflictStatus')),
      item->>'scoreability', v_supersedes_id, (item->>'createdAt')::timestamptz
    );
  end loop;

  for item in select value from pg_catalog.jsonb_array_elements(p_pending_evidence) loop
    if (item->>'caseId')::uuid is distinct from v_case.id
      or (item->>'turnId')::uuid is distinct from v_job.turn_id
      or item->>'reasonCode' not in ('date_unresolved', 'event_unparsed')
      or nullif(btrim(item->>'rawText'), '') is null
      or (nullif(item->>'resolvedEventId', '') is null) is distinct from (nullif(item->>'resolvedAt', '') is null) then
      raise exception 'invalid_rectification_v5_pending_evidence';
    end if;
    if nullif(item->>'targetEventId', '') is not null and not exists (
      select 1 from public.birth_time_rectification_v4_events value
      where value.id = (item->>'targetEventId')::uuid and value.case_id = v_case.id
    ) then
      raise exception 'rectification_v5_pending_target_event_mismatch';
    end if;
    if nullif(item->>'resolvedEventId', '') is not null and not exists (
      select 1 from public.birth_time_rectification_v4_events value
      where value.id = (item->>'resolvedEventId')::uuid and value.case_id = v_case.id
    ) then
      raise exception 'rectification_v5_pending_resolved_event_mismatch';
    end if;
    insert into public.birth_time_rectification_pending_evidence(
      id, case_id, user_id, turn_id, target_event_id, raw_text, reason_code,
      resolved_event_id, created_at, resolved_at
    ) values (
      (item->>'id')::uuid, v_case.id, v_case.user_id, (item->>'turnId')::uuid,
      nullif(item->>'targetEventId', '')::uuid, item->>'rawText', item->>'reasonCode',
      nullif(item->>'resolvedEventId', '')::uuid, (item->>'createdAt')::timestamptz,
      nullif(item->>'resolvedAt', '')::timestamptz
    );
  end loop;

  if p_snapshot is not null then
    if jsonb_typeof(p_snapshot) is distinct from 'object'
      or coalesce((p_snapshot->>'canConfirmExactMinute')::boolean, false) then
      raise exception 'exact_minute_confirmation_forbidden';
    end if;
    v_snapshot_id := (p_snapshot->>'id')::uuid;
    if (p_snapshot->>'caseId')::uuid is distinct from v_case.id
      or (p_snapshot->>'caseVersion')::bigint is distinct from p_expected_case_version
      or p_snapshot->>'evidenceSetHash' is distinct from p_output_evidence_set_hash
      or p_snapshot->>'calculationSpecHash' is distinct from p_calculation_spec_hash
      or p_snapshot->>'algorithmVersion' is distinct from v_case.algorithm_version then
      raise exception 'rectification_v5_snapshot_mismatch';
    end if;
    insert into public.birth_time_rectification_v4_candidate_snapshots(
      id, case_id, user_id, case_version, evidence_set_hash, calculation_spec_hash,
      algorithm_version, candidates, clusters, robustness, can_confirm_exact_minute,
      can_accept_range, gate_reasons, created_at
    ) values (
      v_snapshot_id, v_case.id, v_case.user_id, (p_snapshot->>'caseVersion')::bigint,
      p_snapshot->>'evidenceSetHash', p_snapshot->>'calculationSpecHash',
      p_snapshot->>'algorithmVersion', p_snapshot->'candidates', p_snapshot->'clusters',
      p_snapshot->'robustness', false, (p_snapshot->>'canAcceptRange')::boolean,
      p_snapshot->'gateReasons', (p_snapshot->>'createdAt')::timestamptz
    );
  end if;

  if p_feature_snapshot is not null then
    if jsonb_typeof(p_feature_snapshot) is distinct from 'object' then
      raise exception 'invalid_rectification_v5_feature_snapshot';
    end if;
    v_feature_id := (p_feature_snapshot->>'id')::uuid;
    if (p_feature_snapshot->>'caseId')::uuid is distinct from v_case.id
      or p_feature_snapshot->>'calculationSpecHash' is distinct from p_calculation_spec_hash
      or p_feature_snapshot->>'algorithmVersion' is distinct from v_case.algorithm_version then
      raise exception 'rectification_v5_feature_snapshot_mismatch';
    end if;
    insert into public.birth_time_rectification_candidate_feature_snapshots(
      id, case_id, user_id, calculation_spec_hash, algorithm_version,
      candidate_count, feature_hash, features, created_at
    ) values (
      v_feature_id, v_case.id, v_case.user_id,
      p_feature_snapshot->>'calculationSpecHash', p_feature_snapshot->>'algorithmVersion',
      (p_feature_snapshot->>'candidateCount')::integer, p_feature_snapshot->>'featureHash',
      p_feature_snapshot->'features', (p_feature_snapshot->>'createdAt')::timestamptz
    );
  end if;

  if p_diagnostics is not null then
    if jsonb_typeof(p_diagnostics) is distinct from 'object' or v_snapshot_id is null then
      raise exception 'invalid_rectification_v5_diagnostics';
    end if;
    v_diagnostics_id := (p_diagnostics->>'id')::uuid;
    if (p_diagnostics->>'caseId')::uuid is distinct from v_case.id
      or (p_diagnostics->>'snapshotId')::uuid is distinct from v_snapshot_id then
      raise exception 'rectification_v5_diagnostics_mismatch';
    end if;
    insert into public.birth_time_rectification_diagnostics(
      id, case_id, user_id, snapshot_id, summary, calculation_hash, created_at
    ) values (
      v_diagnostics_id, v_case.id, v_case.user_id, v_snapshot_id,
      p_diagnostics, p_diagnostics->>'calculationHash',
      (p_diagnostics->>'createdAt')::timestamptz
    );
  end if;

  if (p_diagnostics is null) is distinct from (p_snapshot is null)
    or (p_feature_snapshot is null) is distinct from (p_snapshot is null) then
    raise exception 'rectification_v5_artifact_set_incomplete';
  end if;

  insert into public.birth_time_rectification_agent_runs(
    id, case_id, job_id, user_id, case_version, model_id, skill_version,
    prompt_version, deployment_sha, deployment_mode, decision_json,
    validated_decision_json, tool_calls_json, tool_call_count, fallback_reason,
    input_token_count, output_token_count, latency_ms, created_at
  ) values (
    (p_agent_run->>'id')::uuid, v_case.id, p_job_id, v_case.user_id,
    (p_agent_run->>'caseVersion')::bigint, nullif(p_agent_run->>'modelId', ''),
    p_agent_run->>'skillVersion', p_agent_run->>'promptVersion',
    nullif(p_agent_run->>'deploymentSha', ''), p_agent_run->>'deploymentMode',
    p_agent_run->'decision', p_validated_decision, p_agent_run->'toolCalls',
    pg_catalog.jsonb_array_length(p_agent_run->'toolCalls'),
    nullif(p_agent_run->>'fallbackReason', ''),
    nullif(p_agent_run->>'inputTokenCount', '')::integer,
    nullif(p_agent_run->>'outputTokenCount', '')::integer,
    (p_agent_run->>'latencyMs')::integer,
    (p_agent_run->>'createdAt')::timestamptz
  );
  insert into public.birth_time_rectification_public_messages(
    job_id, case_id, user_id, message, created_at
  ) values (
    p_job_id, v_case.id, v_case.user_id, p_public_message, p_now
  );

  update public.birth_time_rectification_v4_cases
  set version = p_expected_case_version + 1,
      evidence_set_hash = p_output_evidence_set_hash,
      latest_snapshot_id = coalesce(v_snapshot_id, latest_snapshot_id),
      feature_snapshot_id = coalesce(v_feature_id, feature_snapshot_id),
      latest_diagnostics_id = coalesce(v_diagnostics_id, latest_diagnostics_id),
      agent_mode = p_validated_decision->>'mode',
      current_question = p_next_question,
      status = p_status,
      phase = p_phase,
      updated_at = p_now
  where id = v_case.id;
  update public.birth_time_rectification_v4_jobs
  set status = 'completed', phase = p_phase, result_snapshot_id = v_snapshot_id,
      completion_payload_hash = p_completion_payload_hash,
      lease_expires_at = null, updated_at = p_now
  where id = p_job_id;
  return v_case.id;
end;
$$;

revoke all on function public.revise_birth_time_rectification_v4_event(uuid, uuid, uuid, bigint, jsonb, text, uuid, uuid, timestamptz) from public, anon, authenticated;
grant execute on function public.revise_birth_time_rectification_v4_event(uuid, uuid, uuid, bigint, jsonb, text, uuid, uuid, timestamptz) to service_role;
revoke all on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) to service_role;

commit;
