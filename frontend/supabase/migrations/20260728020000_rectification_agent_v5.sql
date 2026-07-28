begin;

alter table public.birth_time_rectification_v4_cases
  add column if not exists orchestration_model_id text,
  add column if not exists narration_model_id text,
  add column if not exists skill_version text not null default 'birth-time-rectification-v5',
  add column if not exists prompt_version text not null default 'rectification-agent-v5-1',
  add column if not exists algorithm_version text not null default 'rectification-v5-matrix-scoring-1',
  add column if not exists deployment_mode text not null default 'v4_legacy',
  add column if not exists feature_snapshot_id uuid,
  add column if not exists latest_diagnostics_id uuid,
  add column if not exists agent_mode text not null default 'deterministic_fallback',
  add column if not exists privacy_retention_until timestamptz;

-- The original protocol check was created inline and therefore has an implementation-defined name.
do $$
declare value record;
begin
  for value in
    select constraint_value.conname
    from pg_catalog.pg_constraint constraint_value
    where constraint_value.conrelid = 'public.birth_time_rectification_v4_cases'::regclass
      and constraint_value.contype = 'c'
      and pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%protocol%rectification-evidence-v4%'
  loop
    execute pg_catalog.format(
      'alter table public.birth_time_rectification_v4_cases drop constraint %I',
      value.conname
    );
  end loop;
end $$;

alter table public.birth_time_rectification_v4_cases
  add constraint birth_time_rectification_v5_protocol_check
    check (protocol in ('rectification-evidence-v4', 'rectification-evidence-v5')),
  drop constraint if exists birth_time_rectification_v4_cases_phase_check;
alter table public.birth_time_rectification_v4_cases
  add constraint birth_time_rectification_v4_cases_phase_check
    check (phase in (
      'collecting_evidence', 'extracting_evidence', 'scoring_candidates',
      'checking_robustness', 'planning_question', 'reasoning', 'rendering', 'complete'
    ));

-- V5 owns the worker phase machine as well as the Case phase machine.
alter table public.birth_time_rectification_v4_jobs
  add column if not exists completion_payload_hash text;
do $$
declare value record;
begin
  for value in
    select constraint_value.conname
    from pg_catalog.pg_constraint constraint_value
    where constraint_value.conrelid = 'public.birth_time_rectification_v4_jobs'::regclass
      and constraint_value.contype = 'c'
      and pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%phase%'
  loop
    execute pg_catalog.format(
      'alter table public.birth_time_rectification_v4_jobs drop constraint %I',
      value.conname
    );
  end loop;
end $$;
alter table public.birth_time_rectification_v4_jobs
  add constraint birth_time_rectification_v5_jobs_phase_check
    check (phase in (
      'collecting_evidence', 'extracting_evidence', 'scoring_candidates',
      'checking_robustness', 'planning_question', 'reasoning', 'rendering', 'complete'
    )),
  drop constraint if exists birth_time_rectification_v5_jobs_completion_payload_hash_check;
alter table public.birth_time_rectification_v4_jobs
  add constraint birth_time_rectification_v5_jobs_completion_payload_hash_check
    check (completion_payload_hash is null or completion_payload_hash ~ '^[a-f0-9]{64}$');

-- Candidate snapshots are durable algorithm artifacts; never label a V5 matrix result as V4.
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
  add constraint birth_time_rectification_v5_candidate_snapshots_algorithm_check
    check (algorithm_version in (
      'rectification-v4-range-scoring-1',
      'rectification-v5-matrix-scoring-1'
    ));

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_cases'::regclass
      and conname = 'birth_time_rectification_v5_deployment_mode_check'
  ) then
    alter table public.birth_time_rectification_v4_cases
      add constraint birth_time_rectification_v5_deployment_mode_check
      check (deployment_mode in ('v4_legacy', 'v5_shadow', 'v5_agent'));
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_cases'::regclass
      and conname = 'birth_time_rectification_v5_agent_mode_check'
  ) then
    alter table public.birth_time_rectification_v4_cases
      add constraint birth_time_rectification_v5_agent_mode_check
      check (agent_mode in ('agent', 'deterministic_fallback'));
  end if;
end $$;

alter table public.birth_time_rectification_v4_event_revisions
  add column if not exists subject text not null default 'self',
  add column if not exists related_person text,
  drop constraint if exists birth_time_rectification_v4_event_revisions_event_kind_check;
alter table public.birth_time_rectification_v4_event_revisions
  add constraint birth_time_rectification_v4_event_revisions_event_kind_check
    check (event_kind in (
      'education_milestone', 'relocation', 'relationship_start', 'relationship_end',
      'relationship_change', 'career_change', 'finance_change', 'self_health_event',
      'family_health_event', 'family_bereavement', 'family_event', 'other'
    ));

-- Replace the two anonymous V4 scoreability checks and the relationship-kind check.
do $$
declare value record;
begin
  for value in
    select constraint_value.conname
    from pg_catalog.pg_constraint constraint_value
    where constraint_value.conrelid = 'public.birth_time_rectification_v4_event_revisions'::regclass
      and constraint_value.contype = 'c'
      and (
        pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%scoreability%'
        or (
          pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%relationship%'
          and pg_catalog.pg_get_constraintdef(constraint_value.oid) like '%event_kind%'
        )
      )
  loop
    execute pg_catalog.format(
      'alter table public.birth_time_rectification_v4_event_revisions drop constraint %I',
      value.conname
    );
  end loop;
end $$;
alter table public.birth_time_rectification_v4_event_revisions
  add constraint birth_time_rectification_v5_event_revisions_scoreability_check
    check (scoreability in ('scoreable', 'context_only', 'pending_review', 'unsupported')),
  add constraint birth_time_rect_v5_event_revision_domain_score_check
    check (domain not in ('family', 'other') or scoreability <> 'scoreable'),
  add constraint birth_time_rect_v5_event_revision_relationship_kind_check
    check (domain <> 'relationship' or event_kind in (
      'relationship_start', 'relationship_end', 'relationship_change'
    ));

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_event_revisions'::regclass
      and conname = 'birth_time_rectification_v5_subject_check'
  ) then
    alter table public.birth_time_rectification_v4_event_revisions
      add constraint birth_time_rectification_v5_subject_check
      check (subject in ('self', 'family', 'partner', 'other'));
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_event_revisions'::regclass
      and conname = 'birth_time_rectification_v5_related_person_check'
  ) then
    alter table public.birth_time_rectification_v4_event_revisions
      add constraint birth_time_rectification_v5_related_person_check
      check (related_person is null or related_person in ('father', 'mother', 'grandparent', 'sibling', 'partner'));
  end if;
end $$;

create table if not exists public.birth_time_rectification_candidate_feature_snapshots (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  calculation_spec_hash text not null check (calculation_spec_hash ~ '^[a-f0-9]{64}$'),
  algorithm_version text not null,
  candidate_count integer not null check (candidate_count between 1 and 1440),
  feature_hash text not null check (feature_hash ~ '^[a-f0-9]{64}$'),
  features jsonb not null check (jsonb_typeof(features) = 'array'),
  created_at timestamptz not null
);

create table if not exists public.birth_time_rectification_diagnostics (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  snapshot_id uuid not null references public.birth_time_rectification_v4_candidate_snapshots(id) on delete cascade,
  summary jsonb not null check (jsonb_typeof(summary) = 'object'),
  calculation_hash text not null check (calculation_hash ~ '^[a-f0-9]{64}$'),
  created_at timestamptz not null,
  unique (snapshot_id)
);

create table if not exists public.birth_time_rectification_agent_runs (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  job_id uuid not null unique references public.birth_time_rectification_v4_jobs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  case_version bigint not null,
  model_id text,
  skill_version text not null,
  prompt_version text not null,
  deployment_sha text,
  deployment_mode text not null check (deployment_mode in ('v4_legacy', 'v5_shadow', 'v5_agent')),
  decision_json jsonb,
  validated_decision_json jsonb not null check (jsonb_typeof(validated_decision_json) = 'object'),
  tool_calls_json jsonb not null check (jsonb_typeof(tool_calls_json) = 'array'),
  tool_call_count integer not null check (tool_call_count between 0 and 8),
  fallback_reason text,
  input_token_count integer,
  output_token_count integer,
  latency_ms integer not null check (latency_ms between 0 and 300000),
  created_at timestamptz not null
);

-- Forward-complete an earlier partial V5 draft before constraints/functions depend on it.
alter table public.birth_time_rectification_agent_runs
  add column if not exists deployment_mode text,
  add column if not exists validated_decision_json jsonb,
  add column if not exists tool_calls_json jsonb,
  add column if not exists tool_call_count integer,
  add column if not exists fallback_reason text,
  add column if not exists input_token_count integer,
  add column if not exists output_token_count integer,
  add column if not exists latency_ms integer;

update public.birth_time_rectification_agent_runs run
set deployment_mode = coalesce(
      case when run.deployment_mode in ('v4_legacy', 'v5_shadow', 'v5_agent') then run.deployment_mode end,
      value.deployment_mode,
      'v4_legacy'
    ),
    validated_decision_json = case
      when jsonb_typeof(run.validated_decision_json) = 'object' then run.validated_decision_json
      else jsonb_build_object(
        'decision', coalesce(run.decision_json, jsonb_build_object(
          'action', 'stop_low_confidence',
          'reasonCodes', jsonb_build_array('legacy_run_missing_decision')
        )),
        'mode', 'deterministic_fallback',
        'validationIssues', jsonb_build_array('legacy_agent_run_backfill'),
        'selectedOpportunity', null
      )
    end,
    tool_calls_json = case
      when jsonb_typeof(run.tool_calls_json) = 'array'
        and jsonb_array_length(run.tool_calls_json) between 0 and 8 then run.tool_calls_json
      else '[]'::jsonb
    end,
    tool_call_count = case
      when jsonb_typeof(run.tool_calls_json) = 'array'
        and jsonb_array_length(run.tool_calls_json) between 0 and 8
        then jsonb_array_length(run.tool_calls_json)
      else 0
    end,
    input_token_count = case when run.input_token_count >= 0 then run.input_token_count end,
    output_token_count = case when run.output_token_count >= 0 then run.output_token_count end,
    latency_ms = greatest(0, least(coalesce(run.latency_ms, 0), 300000))
from public.birth_time_rectification_v4_cases value
where value.id = run.case_id;

alter table public.birth_time_rectification_agent_runs
  alter column deployment_mode set not null,
  alter column validated_decision_json set not null,
  alter column tool_calls_json set not null,
  alter column tool_call_count set not null,
  alter column latency_ms set not null;

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_deployment_mode_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_deployment_mode_check
      check (deployment_mode in ('v4_legacy', 'v5_shadow', 'v5_agent'));
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_validated_decision_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_validated_decision_check
      check (jsonb_typeof(validated_decision_json) = 'object');
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_tool_calls_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_tool_calls_check
      check (jsonb_typeof(tool_calls_json) = 'array');
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_tool_count_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_tool_count_check
      check (tool_call_count between 0 and 8 and tool_call_count = jsonb_array_length(tool_calls_json));
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_latency_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_latency_check
      check (latency_ms between 0 and 300000);
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_agent_runs'::regclass
      and conname = 'birth_time_rectification_v5_agent_runs_token_count_check'
  ) then
    alter table public.birth_time_rectification_agent_runs
      add constraint birth_time_rectification_v5_agent_runs_token_count_check
      check (
        (input_token_count is null or input_token_count >= 0)
        and (output_token_count is null or output_token_count >= 0)
      );
  end if;
end $$;

create table if not exists public.birth_time_rectification_public_messages (
  job_id uuid primary key references public.birth_time_rectification_v4_jobs(id) on delete cascade,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  message jsonb not null check (jsonb_typeof(message) = 'object'),
  created_at timestamptz not null
);

create table if not exists public.birth_time_rectification_pending_evidence (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  turn_id uuid references public.birth_time_rectification_v4_turns(id) on delete cascade,
  target_event_id uuid references public.birth_time_rectification_v4_events(id),
  raw_text text not null check (length(btrim(raw_text)) between 1 and 4000),
  reason_code text not null,
  resolved_event_id uuid references public.birth_time_rectification_v4_events(id),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

alter table public.birth_time_rectification_pending_evidence
  alter column turn_id set not null;

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_pending_evidence'::regclass
      and conname = 'birth_time_rectification_v5_pending_reason_check'
  ) then
    alter table public.birth_time_rectification_pending_evidence
      add constraint birth_time_rectification_v5_pending_reason_check
      check (reason_code in ('date_unresolved', 'event_unparsed'));
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_pending_evidence'::regclass
      and conname = 'birth_time_rectification_v5_pending_resolution_check'
  ) then
    alter table public.birth_time_rectification_pending_evidence
      add constraint birth_time_rectification_v5_pending_resolution_check
      check ((resolved_at is null) = (resolved_event_id is null));
  end if;
end $$;

create index if not exists birth_time_rectification_feature_snapshots_case_created_idx
  on public.birth_time_rectification_candidate_feature_snapshots(case_id, created_at desc);
create index if not exists birth_time_rectification_feature_snapshots_user_created_idx
  on public.birth_time_rectification_candidate_feature_snapshots(user_id, created_at desc);
create index if not exists birth_time_rectification_diagnostics_case_created_idx
  on public.birth_time_rectification_diagnostics(case_id, created_at desc);
create index if not exists birth_time_rectification_diagnostics_user_created_idx
  on public.birth_time_rectification_diagnostics(user_id, created_at desc);
create index if not exists birth_time_rectification_diagnostics_snapshot_idx
  on public.birth_time_rectification_diagnostics(snapshot_id);
create index if not exists birth_time_rectification_agent_runs_case_created_idx
  on public.birth_time_rectification_agent_runs(case_id, created_at desc);
create index if not exists birth_time_rectification_agent_runs_user_created_idx
  on public.birth_time_rectification_agent_runs(user_id, created_at desc);
create index if not exists birth_time_rectification_public_messages_case_created_idx
  on public.birth_time_rectification_public_messages(case_id, created_at desc);
create index if not exists birth_time_rectification_pending_evidence_case_created_idx
  on public.birth_time_rectification_pending_evidence(case_id, created_at desc);
create index if not exists birth_time_rectification_pending_evidence_target_event_idx
  on public.birth_time_rectification_pending_evidence(target_event_id)
  where target_event_id is not null;

-- Add the circular Case -> latest artifact references only after the artifact tables exist.
do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_cases'::regclass
      and conname = 'birth_time_rectification_v5_feature_snapshot_fk'
  ) then
    alter table public.birth_time_rectification_v4_cases
      add constraint birth_time_rectification_v5_feature_snapshot_fk
      foreign key (feature_snapshot_id)
      references public.birth_time_rectification_candidate_feature_snapshots(id);
  end if;
  if not exists (
    select 1 from pg_catalog.pg_constraint
    where conrelid = 'public.birth_time_rectification_v4_cases'::regclass
      and conname = 'birth_time_rectification_v5_latest_diagnostics_fk'
  ) then
    alter table public.birth_time_rectification_v4_cases
      add constraint birth_time_rectification_v5_latest_diagnostics_fk
      foreign key (latest_diagnostics_id)
      references public.birth_time_rectification_diagnostics(id);
  end if;
end $$;

alter table public.birth_time_rectification_candidate_feature_snapshots enable row level security;
alter table public.birth_time_rectification_diagnostics enable row level security;
alter table public.birth_time_rectification_agent_runs enable row level security;
alter table public.birth_time_rectification_public_messages enable row level security;
alter table public.birth_time_rectification_pending_evidence enable row level security;

revoke all on table
  public.birth_time_rectification_candidate_feature_snapshots,
  public.birth_time_rectification_diagnostics,
  public.birth_time_rectification_agent_runs,
  public.birth_time_rectification_public_messages,
  public.birth_time_rectification_pending_evidence
from public, anon, authenticated;
grant all on table
  public.birth_time_rectification_candidate_feature_snapshots,
  public.birth_time_rectification_diagnostics,
  public.birth_time_rectification_agent_runs,
  public.birth_time_rectification_public_messages,
  public.birth_time_rectification_pending_evidence
to service_role;

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

  -- An in-flight Case keeps the deployment mode and protocol it was created with.
  if found and v_case.calculation_spec_hash = p_calculation_spec_hash then
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

drop function if exists public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
);
drop function if exists public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
);

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
      date_label, scoreability, supersedes_revision_id, created_at
    ) values (
      (item->>'id')::uuid, v_event_id, v_case.id, v_case.user_id,
      (item->>'revision')::integer, item->>'domain', item->>'eventKind', item->>'subject',
      nullif(item->>'relatedPerson', ''), item->>'summary', item->>'rawText',
      (item#>>'{dateRange,start}')::date, (item#>>'{dateRange,end}')::date,
      item#>>'{dateRange,precision}', item#>>'{dateRange,label}', item->>'scoreability',
      v_supersedes_id, (item->>'createdAt')::timestamptz
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

revoke all on function public.create_birth_time_rectification_v5_case(
  uuid, uuid, uuid, text, text, jsonb, text, text, jsonb, text, text, text, text, text, text, timestamptz
) from public, anon, authenticated;
revoke all on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.create_birth_time_rectification_v5_case(
  uuid, uuid, uuid, text, text, jsonb, text, text, jsonb, text, text, text, text, text, text, timestamptz
) to service_role;
grant execute on function public.complete_birth_time_rectification_v5_job(
  uuid, uuid, bigint, text, text, text, text,
  jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb,
  text, text, timestamptz
) to service_role;

commit;
