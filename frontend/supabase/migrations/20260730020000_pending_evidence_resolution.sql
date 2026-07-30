begin;

update public.birth_time_rectification_v4_cases case_value
set latest_snapshot_id = null
where case_value.latest_snapshot_id is not null
  and exists (
    select 1
    from public.birth_time_rectification_v4_event_revisions event_value
    where event_value.case_id = case_value.id
      and event_value.user_id = case_value.user_id
      and event_value.event_kind = 'relationship_end'
      and event_value.scoreability = 'scoreable'
      and not exists (
        select 1
        from public.birth_time_rectification_v4_event_revisions newer
        where newer.event_id = event_value.event_id
          and newer.revision > event_value.revision
      )
  );

-- Keep the previous overload internal so completion cannot bypass pending-evidence closure.
revoke all on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) from public, anon, authenticated, service_role;

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
  p_resolved_pending_evidence jsonb,
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
  v_pending public.birth_time_rectification_pending_evidence%rowtype;
  v_case_id uuid;
  v_resolved_event_id uuid;
  v_was_completed boolean;
  v_updated_count integer;
  item jsonb;
begin
  if jsonb_typeof(p_resolved_pending_evidence) is distinct from 'array' then
    raise exception 'invalid_rectification_v5_resolved_pending_evidence';
  end if;
  if exists (
    select 1
    from pg_catalog.jsonb_array_elements(p_resolved_pending_evidence) value
    group by value->>'pendingEvidenceId'
    having count(*) > 1
  ) then
    raise exception 'duplicate_rectification_v5_resolved_pending_evidence';
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
  v_was_completed := v_job.status = 'completed';

  for item in select value from pg_catalog.jsonb_array_elements(p_resolved_pending_evidence) loop
    if jsonb_typeof(item) is distinct from 'object'
      or nullif(item->>'pendingEvidenceId', '') is null
      or nullif(item->>'resolvedEventId', '') is null then
      raise exception 'invalid_rectification_v5_resolved_pending_evidence';
    end if;
    v_resolved_event_id := (item->>'resolvedEventId')::uuid;
    select value.* into v_pending
    from public.birth_time_rectification_pending_evidence value
    where value.id = (item->>'pendingEvidenceId')::uuid
    for update;
    if not found
      or v_pending.case_id is distinct from v_case.id
      or v_pending.user_id is distinct from v_case.user_id then
      raise exception 'rectification_v5_pending_evidence_case_mismatch';
    end if;
    if v_pending.target_event_id is not null
      and v_pending.target_event_id is distinct from v_resolved_event_id then
      raise exception 'rectification_v5_pending_evidence_target_mismatch';
    end if;
    if v_was_completed then
      if v_pending.resolved_event_id is distinct from v_resolved_event_id
        or v_pending.resolved_at is null then
        raise exception 'rectification_v5_replay_payload_mismatch';
      end if;
    elsif v_pending.resolved_at is not null or v_pending.resolved_event_id is not null then
      raise exception 'rectification_v5_pending_evidence_already_resolved';
    end if;
  end loop;

  v_case_id := public.complete_birth_time_rectification_v5_job(
    p_worker_id,
    p_job_id,
    p_expected_case_version,
    p_input_evidence_set_hash,
    p_output_evidence_set_hash,
    p_calculation_spec_hash,
    p_completion_payload_hash,
    p_event_revisions,
    p_pending_evidence,
    p_snapshot,
    p_diagnostics,
    p_feature_snapshot,
    p_validated_decision,
    p_public_message,
    p_agent_run,
    p_next_question,
    p_status,
    p_phase,
    p_now
  );

  for item in select value from pg_catalog.jsonb_array_elements(p_resolved_pending_evidence) loop
    v_resolved_event_id := (item->>'resolvedEventId')::uuid;
    if not exists (
      select 1
      from public.birth_time_rectification_v4_events value
      where value.id = v_resolved_event_id
        and value.case_id = v_case.id
        and value.user_id = v_case.user_id
    ) then
      raise exception 'rectification_v5_pending_resolved_event_mismatch';
    end if;
    if not v_was_completed then
      update public.birth_time_rectification_pending_evidence
      set resolved_event_id = v_resolved_event_id,
          resolved_at = p_now
      where id = (item->>'pendingEvidenceId')::uuid
        and case_id = v_case.id
        and user_id = v_case.user_id
        and resolved_at is null
        and resolved_event_id is null;
      get diagnostics v_updated_count = row_count;
      if v_updated_count <> 1 then
        raise exception 'rectification_v5_pending_evidence_resolution_conflict';
      end if;
    end if;
  end loop;

  return v_case_id;
end;
$$;

revoke all on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) to service_role;

commit;
