-- A Case is resumable only when the client can answer it or a worker still owns active work.
-- Scoring v2 changes Event Kind semantics, so unfinished v1 Cases must not be resumed under v2.

alter table public.birth_time_rectification_v4_cases
  alter column algorithm_version set default 'rectification-v5-matrix-scoring-2';

alter table public.birth_time_rectification_v4_candidate_snapshots
  alter column algorithm_version set default 'rectification-v5-matrix-scoring-2';

do $$
declare value record;
begin
  for value in
    select constraint_value.conname
    from pg_catalog.pg_constraint constraint_value
    where constraint_value.conrelid = 'public.birth_time_rectification_v4_candidate_snapshots'::regclass
      and constraint_value.contype = 'c'
      and pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%algorithm_version%'
  loop
    execute pg_catalog.format(
      'alter table public.birth_time_rectification_v4_candidate_snapshots drop constraint %I',
      value.conname
    );
  end loop;
end $$;

alter table public.birth_time_rectification_v4_candidate_snapshots
  add constraint birth_time_rectification_scoring_v2_candidate_snapshots_algorithm_check
    check (algorithm_version in (
      'rectification-v4-range-scoring-1',
      'rectification-v5-matrix-scoring-1',
      'rectification-v5-matrix-scoring-2'
    ));

update public.birth_time_rectification_v4_jobs job
set status = 'stale', lease_expires_at = null, updated_at = pg_catalog.now()
from public.birth_time_rectification_v4_cases case_value
where job.case_id = case_value.id
  and job.status in ('pending', 'processing')
  and case_value.algorithm_version <> 'rectification-v5-matrix-scoring-2'
  and case_value.accepted_range_start is null
  and case_value.status <> 'abandoned';

update public.birth_time_rectification_v4_cases
set status = 'abandoned', phase = 'complete', current_question = null, updated_at = pg_catalog.now()
where algorithm_version <> 'rectification-v5-matrix-scoring-2'
  and accepted_range_start is null
  and status <> 'abandoned';

create or replace function public.create_birth_time_rectification_v5_case(
  p_user_id uuid,
  p_case_id uuid,
  p_action_id uuid,
  p_status text,
  p_phase text,
  p_calculation_spec jsonb,
  p_calculation_spec_hash text,
  p_evidence_set_hash text,
  p_current_question jsonb,
  p_orchestration_model_id text,
  p_narration_model_id text,
  p_skill_version text,
  p_prompt_version text,
  p_algorithm_version text,
  p_deployment_mode text,
  p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_case_id uuid;
  v_protocol text;
begin
  if p_deployment_mode not in ('v4_legacy', 'v5_shadow', 'v5_agent') then
    raise exception 'invalid_rectification_v5_deployment_mode';
  end if;
  if p_algorithm_version <> 'rectification-v5-matrix-scoring-2' then
    raise exception 'invalid_rectification_v5_algorithm_version';
  end if;
  v_protocol := case when p_deployment_mode = 'v4_legacy'
    then 'rectification-evidence-v4' else 'rectification-evidence-v5' end;

  select action.case_id into v_case_id
  from public.birth_time_rectification_v4_actions action
  where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_case_id is not null then return v_case_id; end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':rectification-v5-case', 0)
  );
  select value.* into v_case
  from public.birth_time_rectification_v4_cases value
  where value.user_id = p_user_id
    and value.status <> 'abandoned'
    and value.accepted_range_start is null
  order by value.created_at desc
  limit 1
  for update;

  if found
    and v_case.calculation_spec_hash = p_calculation_spec_hash
    and v_case.algorithm_version = p_algorithm_version
    and (
      (v_case.status = 'awaiting_answer' and v_case.current_question is not null)
      or (
        v_case.status = 'processing'
        and exists (
          select 1
          from public.birth_time_rectification_v4_jobs job
          where job.case_id = v_case.id
            and job.status in ('pending', 'processing')
        )
      )
    ) then
    insert into public.birth_time_rectification_v4_actions(
      user_id, action_id, case_id, created_at
    ) values (
      p_user_id, p_action_id, v_case.id, p_now
    );
    return v_case.id;
  end if;

  if found then
    update public.birth_time_rectification_v4_cases
    set status = 'abandoned', phase = 'complete', current_question = null, updated_at = p_now
    where id = v_case.id;
    update public.birth_time_rectification_v4_jobs
    set status = 'stale', lease_expires_at = null, updated_at = p_now
    where case_id = v_case.id and status in ('pending', 'processing');
  end if;

  insert into public.birth_time_rectification_v4_cases (
    id, user_id, protocol, status, phase, calculation_spec, calculation_spec_hash,
    evidence_set_hash, current_question, orchestration_model_id, narration_model_id,
    skill_version, prompt_version, algorithm_version, deployment_mode, agent_mode,
    created_at, updated_at
  ) values (
    p_case_id, p_user_id, v_protocol, p_status, p_phase, p_calculation_spec,
    p_calculation_spec_hash, p_evidence_set_hash, p_current_question,
    nullif(btrim(p_orchestration_model_id), ''), nullif(btrim(p_narration_model_id), ''),
    p_skill_version, p_prompt_version, p_algorithm_version, p_deployment_mode,
    'deterministic_fallback', p_now, p_now
  );
  insert into public.birth_time_rectification_v4_actions(
    user_id, action_id, case_id, created_at
  ) values (
    p_user_id, p_action_id, p_case_id, p_now
  );
  return p_case_id;
end;
$$;
