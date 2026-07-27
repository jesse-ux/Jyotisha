begin;

create table public.birth_time_rectification_v4_cases (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  protocol text not null default 'rectification-evidence-v4' check (protocol = 'rectification-evidence-v4'),
  version bigint not null default 0 check (version >= 0),
  status text not null check (status in ('awaiting_answer', 'processing', 'range_ready', 'paused', 'abandoned')),
  phase text not null check (phase in ('collecting_evidence', 'extracting_evidence', 'scoring_candidates', 'checking_robustness', 'planning_question', 'complete')),
  calculation_spec jsonb not null check (jsonb_typeof(calculation_spec) = 'object' and octet_length(calculation_spec::text) <= 16384),
  calculation_spec_hash text not null check (calculation_spec_hash ~ '^[a-f0-9]{64}$'),
  evidence_set_hash text not null check (evidence_set_hash ~ '^[a-f0-9]{64}$'),
  current_question jsonb check (current_question is null or (jsonb_typeof(current_question) = 'object' and octet_length(current_question::text) <= 4096)),
  latest_snapshot_id uuid,
  accepted_range_start text check (accepted_range_start is null or accepted_range_start ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
  accepted_range_end text check (accepted_range_end is null or accepted_range_end ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((accepted_range_start is null) = (accepted_range_end is null)),
  check (accepted_range_start is null or accepted_range_start <> accepted_range_end)
);

create unique index birth_time_rectification_v4_one_active_case
  on public.birth_time_rectification_v4_cases(user_id)
  where status <> 'abandoned' and accepted_range_start is null;

create table public.birth_time_rectification_v4_actions (
  user_id uuid not null references auth.users(id) on delete cascade,
  action_id uuid not null,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  job_id uuid,
  created_at timestamptz not null default now(),
  primary key (user_id, action_id)
);

create table public.birth_time_rectification_v4_turns (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  case_version bigint not null check (case_version > 0),
  question_id uuid,
  question_domain text check (question_domain is null or question_domain in ('education', 'relocation', 'relationship', 'career', 'finance', 'health_pressure', 'family', 'other')),
  question_target_event_id uuid,
  question text not null check (length(btrim(question)) between 1 and 1000),
  answer text not null check (length(answer) <= 4000),
  action_id uuid not null,
  created_at timestamptz not null default now(),
  unique (user_id, action_id)
);

create table public.birth_time_rectification_v4_events (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (case_id, id)
);

alter table public.birth_time_rectification_v4_turns
  add constraint birth_time_rectification_v4_turn_target_event_fk
  foreign key (case_id, question_target_event_id)
  references public.birth_time_rectification_v4_events(case_id, id);

create table public.birth_time_rectification_v4_event_revisions (
  id uuid primary key,
  event_id uuid not null references public.birth_time_rectification_v4_events(id) on delete cascade,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  revision integer not null check (revision > 0),
  domain text not null check (domain in ('education', 'relocation', 'relationship', 'career', 'finance', 'health_pressure', 'family', 'other')),
  event_kind text not null check (event_kind in ('education_milestone', 'relocation', 'relationship_start', 'relationship_end', 'career_change', 'finance_change', 'health_event', 'family_event', 'other')),
  summary text not null check (length(btrim(summary)) between 1 and 1000),
  raw_text text not null check (length(btrim(raw_text)) between 1 and 4000),
  date_start date not null,
  date_end date not null,
  date_precision text not null check (date_precision in ('day', 'month', 'quarter', 'year', 'range')),
  date_label text not null check (length(btrim(date_label)) between 1 and 80),
  scoreability text not null check (scoreability in ('scoreable', 'context_only')),
  supersedes_revision_id uuid references public.birth_time_rectification_v4_event_revisions(id),
  created_at timestamptz not null default now(),
  unique (event_id, revision),
  check (date_start <= date_end),
  check (domain not in ('family', 'other') or scoreability = 'context_only'),
  check (domain <> 'relationship' or event_kind in ('relationship_start', 'relationship_end'))
);

create table public.birth_time_rectification_v4_candidate_snapshots (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  case_version bigint not null check (case_version >= 0),
  evidence_set_hash text not null check (evidence_set_hash ~ '^[a-f0-9]{64}$'),
  calculation_spec_hash text not null check (calculation_spec_hash ~ '^[a-f0-9]{64}$'),
  algorithm_version text not null check (algorithm_version = 'rectification-v4-range-scoring-1'),
  candidates jsonb not null check (jsonb_typeof(candidates) = 'array' and jsonb_array_length(candidates) between 1 and 1440 and octet_length(candidates::text) <= 524288),
  clusters jsonb not null check (jsonb_typeof(clusters) = 'array' and jsonb_array_length(clusters) <= 20 and octet_length(clusters::text) <= 32768),
  robustness jsonb not null check (jsonb_typeof(robustness) = 'object' and octet_length(robustness::text) <= 16384),
  can_confirm_exact_minute boolean not null default false check (can_confirm_exact_minute = false),
  can_accept_range boolean not null,
  gate_reasons jsonb not null check (jsonb_typeof(gate_reasons) = 'array' and jsonb_array_length(gate_reasons) <= 20),
  created_at timestamptz not null default now()
);

alter table public.birth_time_rectification_v4_cases
  add constraint birth_time_rectification_v4_latest_snapshot_fk
  foreign key (latest_snapshot_id) references public.birth_time_rectification_v4_candidate_snapshots(id);

create table public.birth_time_rectification_v4_jobs (
  id uuid primary key,
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  turn_id uuid not null references public.birth_time_rectification_v4_turns(id) on delete cascade,
  status text not null check (status in ('pending', 'processing', 'completed', 'failed', 'stale')),
  phase text not null check (phase in ('collecting_evidence', 'extracting_evidence', 'scoring_candidates', 'checking_robustness', 'planning_question', 'complete')),
  expected_case_version bigint not null check (expected_case_version >= 0),
  evidence_set_hash text not null check (evidence_set_hash ~ '^[a-f0-9]{64}$'),
  calculation_spec_hash text not null check (calculation_spec_hash ~ '^[a-f0-9]{64}$'),
  worker_id uuid,
  lease_expires_at timestamptz,
  result_snapshot_id uuid references public.birth_time_rectification_v4_candidate_snapshots(id),
  error_code text check (error_code is null or length(error_code) between 1 and 120),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.birth_time_rectification_v4_actions
  add constraint birth_time_rectification_v4_actions_job_fk
  foreign key (job_id) references public.birth_time_rectification_v4_jobs(id);

create index birth_time_rectification_v4_jobs_claim_idx
  on public.birth_time_rectification_v4_jobs(status, created_at)
  where status in ('pending', 'processing');

create table public.birth_time_rectification_v4_handoffs (
  case_id uuid primary key references public.birth_time_rectification_v4_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  question text not null check (length(btrim(question)) between 1 and 500),
  question_fingerprint text not null check (question_fingerprint ~ '^[a-f0-9]{64}$'),
  attached_case_version bigint not null check (attached_case_version >= 0),
  attach_action_id uuid not null,
  state text not null check (state in ('pending', 'claimed', 'executing', 'consumed')),
  attempt integer not null default 0 check (attempt between 0 and 1000),
  request_id uuid not null,
  claim_action_id uuid,
  lease_expires_at timestamptz,
  claimed_at timestamptz,
  consumed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, request_id),
  check ((state in ('claimed', 'executing')) = (claim_action_id is not null)),
  check ((state in ('claimed', 'executing')) = (lease_expires_at is not null)),
  check ((state = 'consumed') = (consumed_at is not null))
);

create table public.birth_time_rectification_v4_handoff_attach_receipts (
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  action_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  expected_case_version bigint not null check (expected_case_version >= 0),
  question_fingerprint text not null check (question_fingerprint ~ '^[a-f0-9]{64}$'),
  response jsonb not null,
  created_at timestamptz not null default now(),
  primary key (case_id, action_id)
);

create table public.birth_time_rectification_v4_handoff_settlements (
  case_id uuid not null references public.birth_time_rectification_v4_cases(id) on delete cascade,
  request_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  claim_action_id uuid not null,
  emitted boolean not null,
  response jsonb not null,
  created_at timestamptz not null default now(),
  primary key (case_id, request_id)
);

create index birth_time_rectification_v4_handoff_owner_state_idx
  on public.birth_time_rectification_v4_handoffs(user_id, state, updated_at desc);

alter table public.birth_time_rectification_v4_cases enable row level security;
alter table public.birth_time_rectification_v4_actions enable row level security;
alter table public.birth_time_rectification_v4_turns enable row level security;
alter table public.birth_time_rectification_v4_events enable row level security;
alter table public.birth_time_rectification_v4_event_revisions enable row level security;
alter table public.birth_time_rectification_v4_candidate_snapshots enable row level security;
alter table public.birth_time_rectification_v4_jobs enable row level security;
alter table public.birth_time_rectification_v4_handoffs enable row level security;
alter table public.birth_time_rectification_v4_handoff_attach_receipts enable row level security;
alter table public.birth_time_rectification_v4_handoff_settlements enable row level security;

revoke all on table public.birth_time_rectification_v4_cases, public.birth_time_rectification_v4_actions,
  public.birth_time_rectification_v4_turns, public.birth_time_rectification_v4_events,
  public.birth_time_rectification_v4_event_revisions, public.birth_time_rectification_v4_candidate_snapshots,
  public.birth_time_rectification_v4_jobs, public.birth_time_rectification_v4_handoffs,
  public.birth_time_rectification_v4_handoff_attach_receipts,
  public.birth_time_rectification_v4_handoff_settlements from public, anon, authenticated;
grant all on table public.birth_time_rectification_v4_cases, public.birth_time_rectification_v4_actions,
  public.birth_time_rectification_v4_turns, public.birth_time_rectification_v4_events,
  public.birth_time_rectification_v4_event_revisions, public.birth_time_rectification_v4_candidate_snapshots,
  public.birth_time_rectification_v4_jobs, public.birth_time_rectification_v4_handoffs,
  public.birth_time_rectification_v4_handoff_attach_receipts,
  public.birth_time_rectification_v4_handoff_settlements to service_role;

create function public.create_birth_time_rectification_v4_case(
  p_user_id uuid, p_case_id uuid, p_action_id uuid, p_status text, p_phase text,
  p_calculation_spec jsonb, p_calculation_spec_hash text, p_evidence_set_hash text,
  p_current_question jsonb, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_case public.birth_time_rectification_v4_cases%rowtype; v_case_id uuid;
begin
  select action.case_id into v_case_id from public.birth_time_rectification_v4_actions action
    where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_case_id is not null then return v_case_id; end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_user_id::text || ':rectification-v4-case', 0));
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.user_id = p_user_id and value.status <> 'abandoned'
      and value.accepted_range_start is null
    order by value.created_at desc limit 1 for update;
  if found and v_case.calculation_spec_hash = p_calculation_spec_hash then
    insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, created_at)
      values (p_user_id, p_action_id, v_case.id, p_now);
    return v_case.id;
  end if;
  if found then
    update public.birth_time_rectification_v4_cases set
      status = 'abandoned', phase = 'complete', current_question = null, updated_at = p_now
      where id = v_case.id;
    update public.birth_time_rectification_v4_jobs set
      status = 'stale', lease_expires_at = null, updated_at = p_now
      where case_id = v_case.id and status in ('pending', 'processing');
  end if;
  insert into public.birth_time_rectification_v4_cases (
    id, user_id, status, phase, calculation_spec, calculation_spec_hash,
    evidence_set_hash, current_question, created_at, updated_at
  ) values (
    p_case_id, p_user_id, p_status, p_phase, p_calculation_spec, p_calculation_spec_hash,
    p_evidence_set_hash, p_current_question, p_now, p_now
  );
  insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, created_at)
    values (p_user_id, p_action_id, p_case_id, p_now);
  return p_case_id;
end;
$$;

create function public.submit_birth_time_rectification_v4_answer(
  p_user_id uuid, p_case_id uuid, p_action_id uuid, p_expected_version bigint,
  p_turn_id uuid, p_question_id uuid, p_question_domain text, p_question_target_event_id uuid, p_question text,
  p_answer text, p_job_id uuid, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_case public.birth_time_rectification_v4_cases%rowtype; v_job_id uuid;
begin
  select action.job_id into v_job_id from public.birth_time_rectification_v4_actions action
    where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_job_id is not null then return v_job_id; end if;
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.id = p_case_id and value.user_id = p_user_id for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;
  if v_case.version <> p_expected_version then raise exception 'stale_rectification_v4_case'; end if;
  if v_case.status not in ('awaiting_answer', 'range_ready') then raise exception 'rectification_v4_case_not_awaiting_answer'; end if;
  insert into public.birth_time_rectification_v4_turns(
    id, case_id, user_id, case_version, question_id, question_domain, question_target_event_id, question, answer, action_id, created_at
  ) values (
    p_turn_id, p_case_id, p_user_id, p_expected_version + 1, p_question_id, p_question_domain, p_question_target_event_id,
    p_question, p_answer, p_action_id, p_now
  );
  update public.birth_time_rectification_v4_cases set
    version = p_expected_version + 1, status = 'processing', phase = 'extracting_evidence',
    current_question = null, updated_at = p_now
    where id = p_case_id;
  insert into public.birth_time_rectification_v4_jobs(
    id, case_id, user_id, turn_id, status, phase, expected_case_version,
    evidence_set_hash, calculation_spec_hash, created_at, updated_at
  ) values (
    p_job_id, p_case_id, p_user_id, p_turn_id, 'pending', 'extracting_evidence', p_expected_version + 1,
    v_case.evidence_set_hash, v_case.calculation_spec_hash, p_now, p_now
  );
  insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, job_id, created_at)
    values (p_user_id, p_action_id, p_case_id, p_job_id, p_now);
  return p_job_id;
end;
$$;

create function public.revise_birth_time_rectification_v4_event(
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
    date_start, date_end, date_precision, date_label, scoreability, supersedes_revision_id, created_at
  ) values (
    (p_revision->>'id')::uuid, v_event_id, p_case_id, p_user_id,
    (p_revision->>'revision')::integer, p_revision->>'domain', p_revision->>'eventKind',
    p_revision->>'summary', p_revision->>'rawText',
    (p_revision#>>'{dateRange,start}')::date, (p_revision#>>'{dateRange,end}')::date,
    p_revision#>>'{dateRange,precision}', p_revision#>>'{dateRange,label}', p_revision->>'scoreability',
    nullif(p_revision->>'supersedesRevisionId', '')::uuid, (p_revision->>'createdAt')::timestamptz
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

create function public.transition_birth_time_rectification_v4_case(
  p_user_id uuid, p_case_id uuid, p_action_id uuid, p_expected_version bigint,
  p_status text, p_phase text, p_accepted_range_start text, p_accepted_range_end text, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_case public.birth_time_rectification_v4_cases%rowtype; v_case_id uuid; v_snapshot public.birth_time_rectification_v4_candidate_snapshots%rowtype; v_primary jsonb;
begin
  select action.case_id into v_case_id from public.birth_time_rectification_v4_actions action
    where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_case_id is not null then return v_case_id; end if;
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.id = p_case_id and value.user_id = p_user_id for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;
  if v_case.version <> p_expected_version then raise exception 'stale_rectification_v4_case'; end if;
  if v_case.status = 'abandoned' then raise exception 'rectification_v4_case_invalid_state'; end if;
  if p_status = 'paused' and v_case.status not in ('awaiting_answer', 'range_ready') then raise exception 'rectification_v4_case_invalid_state'; end if;
  if p_status = 'awaiting_answer' and v_case.status <> 'paused' then raise exception 'rectification_v4_case_invalid_state'; end if;
  if p_status = 'range_ready' then
    if v_case.status not in ('awaiting_answer', 'range_ready') or v_case.latest_snapshot_id is null then raise exception 'rectification_v4_case_invalid_state'; end if;
    select value.* into v_snapshot from public.birth_time_rectification_v4_candidate_snapshots value where value.id = v_case.latest_snapshot_id;
    v_primary = v_snapshot.clusters->0;
    if not v_snapshot.can_accept_range
      or p_accepted_range_start is null or p_accepted_range_end is null
      or p_accepted_range_start = p_accepted_range_end
      or v_primary->>'startTime' <> p_accepted_range_start
      or v_primary->>'endTime' <> p_accepted_range_end then
      raise exception 'rectification_v4_range_not_acceptable';
    end if;
  elsif p_accepted_range_start is not null or p_accepted_range_end is not null then
    raise exception 'rectification_v4_range_not_acceptable';
  end if;
  update public.birth_time_rectification_v4_cases set
    version = p_expected_version + 1, status = p_status, phase = p_phase,
    accepted_range_start = case when p_status = 'range_ready' then p_accepted_range_start else accepted_range_start end,
    accepted_range_end = case when p_status = 'range_ready' then p_accepted_range_end else accepted_range_end end,
    current_question = case when p_status in ('abandoned', 'range_ready') then null else current_question end,
    updated_at = p_now
    where id = p_case_id;
  insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, created_at)
    values (p_user_id, p_action_id, p_case_id, p_now);
  return p_case_id;
end;
$$;

create function public.claim_next_birth_time_rectification_v4_job(
  p_worker_id uuid, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_job_id uuid;
begin
  select value.id into v_job_id from public.birth_time_rectification_v4_jobs value
    where value.status = 'pending'
       or (value.status = 'processing' and value.lease_expires_at <= p_now)
    order by value.created_at for update skip locked limit 1;
  if v_job_id is null then return null; end if;
  update public.birth_time_rectification_v4_jobs set
    status = 'processing', worker_id = p_worker_id, lease_expires_at = p_now + interval '10 minutes',
    error_code = null, updated_at = p_now
    where id = v_job_id;
  return v_job_id;
end;
$$;

create function public.update_birth_time_rectification_v4_job_phase(
  p_worker_id uuid, p_job_id uuid, p_phase text, p_now timestamptz
) returns void
language plpgsql security definer set search_path = '' as $$
declare v_case_id uuid;
begin
  update public.birth_time_rectification_v4_jobs set phase = p_phase, updated_at = p_now,
    lease_expires_at = p_now + interval '10 minutes'
    where id = p_job_id and worker_id = p_worker_id and status = 'processing'
      and lease_expires_at > p_now returning case_id into v_case_id;
  if v_case_id is null then raise exception 'rectification_v4_job_lease_lost'; end if;
  update public.birth_time_rectification_v4_cases set phase = p_phase, updated_at = p_now where id = v_case_id;
end;
$$;

create function public.complete_birth_time_rectification_v4_job(
  p_worker_id uuid, p_job_id uuid, p_expected_case_version bigint,
  p_input_evidence_set_hash text, p_output_evidence_set_hash text, p_calculation_spec_hash text,
  p_event_revisions jsonb, p_snapshot jsonb, p_next_question jsonb,
  p_status text, p_phase text, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  v_job public.birth_time_rectification_v4_jobs%rowtype;
  v_case public.birth_time_rectification_v4_cases%rowtype;
  item jsonb;
  v_snapshot_id uuid;
begin
  select value.* into v_job from public.birth_time_rectification_v4_jobs value
    where value.id = p_job_id for update;
  if not found or v_job.worker_id is distinct from p_worker_id or v_job.status <> 'processing'
    or v_job.lease_expires_at <= p_now then raise exception 'rectification_v4_job_lease_lost'; end if;
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.id = v_job.case_id for update;
  if v_case.version <> p_expected_case_version
    or v_case.evidence_set_hash <> p_input_evidence_set_hash
    or v_case.calculation_spec_hash <> p_calculation_spec_hash
    or v_job.expected_case_version <> p_expected_case_version
    or v_job.evidence_set_hash <> p_input_evidence_set_hash
    or v_job.calculation_spec_hash <> p_calculation_spec_hash then
    update public.birth_time_rectification_v4_jobs set status = 'stale', updated_at = p_now where id = p_job_id;
    raise exception 'stale_rectification_v4_job';
  end if;
  if jsonb_typeof(p_event_revisions) <> 'array' then raise exception 'invalid_rectification_v4_event_revisions'; end if;
  for item in select value from jsonb_array_elements(p_event_revisions) loop
    insert into public.birth_time_rectification_v4_events(id, case_id, user_id, created_at)
      values ((item->>'eventId')::uuid, v_case.id, v_case.user_id, (item->>'createdAt')::timestamptz)
      on conflict (id) do nothing;
    insert into public.birth_time_rectification_v4_event_revisions(
      id, event_id, case_id, user_id, revision, domain, event_kind, summary, raw_text,
      date_start, date_end, date_precision, date_label, scoreability, supersedes_revision_id, created_at
    ) values (
      (item->>'id')::uuid, (item->>'eventId')::uuid, v_case.id, v_case.user_id,
      (item->>'revision')::integer, item->>'domain', item->>'eventKind', item->>'summary', item->>'rawText',
      (item#>>'{dateRange,start}')::date, (item#>>'{dateRange,end}')::date,
      item#>>'{dateRange,precision}', item#>>'{dateRange,label}', item->>'scoreability',
      nullif(item->>'supersedesRevisionId', '')::uuid, (item->>'createdAt')::timestamptz
    );
  end loop;
  if p_snapshot is not null then
    v_snapshot_id = (p_snapshot->>'id')::uuid;
    if (p_snapshot->>'canConfirmExactMinute')::boolean then raise exception 'exact_minute_confirmation_forbidden'; end if;
    insert into public.birth_time_rectification_v4_candidate_snapshots(
      id, case_id, user_id, case_version, evidence_set_hash, calculation_spec_hash,
      algorithm_version, candidates, clusters, robustness, can_confirm_exact_minute,
      can_accept_range, gate_reasons, created_at
    ) values (
      v_snapshot_id, v_case.id, v_case.user_id, (p_snapshot->>'caseVersion')::bigint,
      p_snapshot->>'evidenceSetHash', p_snapshot->>'calculationSpecHash', p_snapshot->>'algorithmVersion',
      p_snapshot->'candidates', p_snapshot->'clusters', p_snapshot->'robustness', false,
      (p_snapshot->>'canAcceptRange')::boolean, p_snapshot->'gateReasons', (p_snapshot->>'createdAt')::timestamptz
    );
  end if;
  update public.birth_time_rectification_v4_cases set
    version = p_expected_case_version + 1, evidence_set_hash = p_output_evidence_set_hash,
    latest_snapshot_id = coalesce(v_snapshot_id, latest_snapshot_id), current_question = p_next_question,
    status = p_status, phase = p_phase, updated_at = p_now
    where id = v_case.id;
  update public.birth_time_rectification_v4_jobs set
    status = 'completed', phase = p_phase, result_snapshot_id = v_snapshot_id,
    lease_expires_at = null, updated_at = p_now
    where id = p_job_id;
  return v_case.id;
end;
$$;

create function public.fail_birth_time_rectification_v4_job(
  p_worker_id uuid, p_job_id uuid, p_expected_case_version bigint, p_error_code text,
  p_restore_question jsonb, p_now timestamptz
) returns void
language plpgsql security definer set search_path = '' as $$
declare v_case_id uuid;
begin
  update public.birth_time_rectification_v4_jobs set
    status = 'failed', error_code = p_error_code, lease_expires_at = null, updated_at = p_now
    where id = p_job_id and worker_id = p_worker_id and status = 'processing'
    returning case_id into v_case_id;
  if v_case_id is null then raise exception 'rectification_v4_job_lease_lost'; end if;
  update public.birth_time_rectification_v4_cases set
    status = 'awaiting_answer', phase = 'collecting_evidence', current_question = p_restore_question, updated_at = p_now
    where id = v_case_id and version = p_expected_case_version;
end;
$$;


create function public.birth_time_rectification_v4_handoff_projection(
  p_user_id uuid,
  p_case_id uuid
) returns jsonb
language sql stable security definer set search_path = '' as $$
  select pg_catalog.jsonb_build_object(
    'protocol', 'rectification-evidence-v4',
    'caseId', handoff.case_id,
    'caseVersion', case_value.version,
    'question', handoff.question,
    'questionFingerprint', handoff.question_fingerprint,
    'requestId', handoff.request_id,
    'status', case
      when handoff.state = 'pending' then 'pending'
      when handoff.state in ('claimed', 'executing')
        and handoff.lease_expires_at <= pg_catalog.now() then 'pending'
      when handoff.state in ('claimed', 'executing') then 'in_progress'
      else 'consumed'
    end,
    'acceptedRange', case
      when case_value.accepted_range_start is null then null
      else pg_catalog.jsonb_build_object(
        'start', case_value.accepted_range_start,
        'end', case_value.accepted_range_end
      )
    end
  )
  from public.birth_time_rectification_v4_handoffs handoff
  join public.birth_time_rectification_v4_cases case_value
    on case_value.id = handoff.case_id and case_value.user_id = handoff.user_id
  where handoff.case_id = p_case_id and handoff.user_id = p_user_id;
$$;

create function public.attach_birth_time_rectification_v4_question(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_question text,
  p_question_fingerprint text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_handoff public.birth_time_rectification_v4_handoffs%rowtype;
  v_receipt public.birth_time_rectification_v4_handoff_attach_receipts%rowtype;
  v_response jsonb;
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0
    or p_question is null or length(btrim(p_question)) not between 1 and 500
    or p_question_fingerprint is null or p_question_fingerprint !~ '^[a-f0-9]{64}$'
    or public.conversational_rectification_question_fingerprint(p_question)
      is distinct from p_question_fingerprint then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':rectification-v4-attach', 0
    )
  );

  select case_value.* into v_case
  from public.birth_time_rectification_v4_cases case_value
  where case_value.id = p_case_id and case_value.user_id = p_user_id
  for update;
  if not found then
    raise exception 'rectification_v4_case_not_found' using errcode = 'P0001';
  end if;

  select receipt.* into v_receipt
  from public.birth_time_rectification_v4_handoff_attach_receipts receipt
  where receipt.case_id = p_case_id and receipt.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.expected_case_version is distinct from p_expected_version
      or v_receipt.question_fingerprint is distinct from p_question_fingerprint then
      raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;

  if v_case.version is distinct from p_expected_version then
    raise exception 'stale_rectification_v4_case' using errcode = 'P0001';
  end if;
  if v_case.status = 'abandoned' then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  select handoff.* into v_handoff
  from public.birth_time_rectification_v4_handoffs handoff
  where handoff.case_id = p_case_id and handoff.user_id = p_user_id
  for update;

  if found then
    if v_handoff.question_fingerprint is distinct from p_question_fingerprint
      or v_handoff.question is distinct from p_question then
      raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
    end if;
  else
    insert into public.birth_time_rectification_v4_handoffs (
      case_id, user_id, question, question_fingerprint,
      attached_case_version, attach_action_id, state, attempt, request_id
    ) values (
      p_case_id, p_user_id, p_question, p_question_fingerprint,
      p_expected_version, p_action_id, 'pending', 0,
      public.conversational_rectification_handoff_request_id(p_case_id, 0)
    );
  end if;

  v_response := public.birth_time_rectification_v4_handoff_projection(
    p_user_id, p_case_id
  );
  insert into public.birth_time_rectification_v4_handoff_attach_receipts (
    case_id, action_id, user_id, expected_case_version,
    question_fingerprint, response
  ) values (
    p_case_id, p_action_id, p_user_id, p_expected_version,
    p_question_fingerprint, v_response
  );
  return v_response;
end;
$$;

create function public.load_birth_time_rectification_v4_handoff(
  p_user_id uuid,
  p_case_id uuid default null
) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare v_case_id uuid;
begin
  if p_user_id is null then return null; end if;
  if p_case_id is not null then
    v_case_id := p_case_id;
  else
    select handoff.case_id into v_case_id
    from public.birth_time_rectification_v4_handoffs handoff
    where handoff.user_id = p_user_id and handoff.state <> 'consumed'
    order by handoff.updated_at desc, handoff.created_at desc
    limit 1;
  end if;
  return public.birth_time_rectification_v4_handoff_projection(p_user_id, v_case_id);
end;
$$;

create function public.consume_birth_time_rectification_v4_handoff(
  p_user_id uuid,
  p_case_id uuid
) returns void
language plpgsql security definer set search_path = '' as $$
begin
  update public.birth_time_rectification_v4_handoffs
  set state = 'consumed', claim_action_id = null, lease_expires_at = null,
      consumed_at = coalesce(consumed_at, pg_catalog.now()), updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
end;
$$;

create function public.claim_birth_time_rectification_v4_handoff(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_question_fingerprint text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_handoff public.birth_time_rectification_v4_handoffs%rowtype;
  v_request_status text;
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0
    or p_question_fingerprint is null or p_question_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':rectification-v4-claim', 0
    )
  );

  select case_value.* into v_case
  from public.birth_time_rectification_v4_cases case_value
  where case_value.id = p_case_id and case_value.user_id = p_user_id
  for update;
  if not found then
    raise exception 'rectification_v4_case_not_found' using errcode = 'P0001';
  end if;
  if v_case.version is distinct from p_expected_version then
    raise exception 'stale_rectification_v4_case' using errcode = 'P0001';
  end if;
  if v_case.status is distinct from 'range_ready'
    or v_case.phase is distinct from 'complete'
    or v_case.accepted_range_start is null
    or v_case.accepted_range_end is null then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  select handoff.* into v_handoff
  from public.birth_time_rectification_v4_handoffs handoff
  where handoff.case_id = p_case_id and handoff.user_id = p_user_id
  for update;
  if not found or v_handoff.question_fingerprint is distinct from p_question_fingerprint then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;
  if v_handoff.state = 'consumed' then
    return public.birth_time_rectification_v4_handoff_projection(p_user_id, p_case_id);
  end if;

  if v_handoff.state in ('claimed', 'executing')
    and v_handoff.lease_expires_at > pg_catalog.now() then
    if v_handoff.state = 'claimed' and v_handoff.claim_action_id = p_action_id then
      return public.birth_time_rectification_v4_handoff_projection(p_user_id, p_case_id)
        || pg_catalog.jsonb_build_object('status', 'claimed');
    end if;
    return public.birth_time_rectification_v4_handoff_projection(p_user_id, p_case_id)
      || pg_catalog.jsonb_build_object('status', 'in_progress');
  end if;

  select request.status into v_request_status
  from public.consultation_requests request
  where request.user_id = p_user_id and request.request_id = v_handoff.request_id::text
  for update;
  if v_request_status = 'completed' then
    perform public.consume_birth_time_rectification_v4_handoff(p_user_id, p_case_id);
    return public.birth_time_rectification_v4_handoff_projection(p_user_id, p_case_id);
  end if;
  if v_request_status = 'cancelled' then
    update public.birth_time_rectification_v4_handoffs
    set attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        )
    where case_id = p_case_id and user_id = p_user_id
    returning * into v_handoff;
  end if;

  update public.birth_time_rectification_v4_handoffs
  set state = 'claimed', claim_action_id = p_action_id,
      lease_expires_at = pg_catalog.now() + interval '2 minutes',
      claimed_at = pg_catalog.now(), consumed_at = null, updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
  return public.birth_time_rectification_v4_handoff_projection(p_user_id, p_case_id)
    || pg_catalog.jsonb_build_object('status', 'claimed');
end;
$$;

create function public.begin_birth_time_rectification_v4_handoff_execution(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_claim_action_id uuid,
  p_request_id uuid,
  p_question_fingerprint text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_handoff public.birth_time_rectification_v4_handoffs%rowtype;
  v_request_status text;
  v_credits integer;
  v_accepted_range jsonb;
begin
  if p_user_id is null or p_case_id is null or p_claim_action_id is null
    or p_request_id is null or p_expected_version is null or p_expected_version < 0
    or p_question_fingerprint is null or p_question_fingerprint !~ '^[a-f0-9]{64}$' then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':rectification-v4-execute', 0
    )
  );

  select case_value.* into v_case
  from public.birth_time_rectification_v4_cases case_value
  where case_value.id = p_case_id and case_value.user_id = p_user_id
  for update;
  select handoff.* into v_handoff
  from public.birth_time_rectification_v4_handoffs handoff
  where handoff.case_id = p_case_id and handoff.user_id = p_user_id
  for update;

  if v_case.id is null or v_handoff.case_id is null
    or v_case.version is distinct from p_expected_version
    or v_case.status is distinct from 'range_ready'
    or v_case.phase is distinct from 'complete'
    or v_case.accepted_range_start is null
    or v_case.accepted_range_end is null
    or v_handoff.question_fingerprint is distinct from p_question_fingerprint
    or v_handoff.request_id is distinct from p_request_id then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  v_accepted_range := pg_catalog.jsonb_build_object(
    'start', v_case.accepted_range_start,
    'end', v_case.accepted_range_end
  );

  if v_handoff.state = 'consumed' then
    return pg_catalog.jsonb_build_object(
      'status', 'consumed', 'requestId', p_request_id, 'acceptedRange', v_accepted_range
    );
  end if;
  if v_handoff.claim_action_id is distinct from p_claim_action_id
    or v_handoff.lease_expires_at <= pg_catalog.now() then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;
  if v_handoff.state = 'executing' then
    return pg_catalog.jsonb_build_object(
      'status', 'in_progress', 'requestId', p_request_id, 'acceptedRange', v_accepted_range
    );
  end if;
  if v_handoff.state is distinct from 'claimed' then
    return pg_catalog.jsonb_build_object(
      'status', 'in_progress', 'requestId', p_request_id, 'acceptedRange', v_accepted_range
    );
  end if;

  select request.status into v_request_status
  from public.consultation_requests request
  where request.user_id = p_user_id and request.request_id = p_request_id::text
  for update;
  if v_request_status = 'completed' then
    perform public.consume_birth_time_rectification_v4_handoff(p_user_id, p_case_id);
    return pg_catalog.jsonb_build_object(
      'status', 'consumed', 'requestId', p_request_id, 'acceptedRange', v_accepted_range
    );
  end if;
  if v_request_status = 'cancelled' then
    update public.birth_time_rectification_v4_handoffs
    set state = 'pending', attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        ),
        claim_action_id = null, lease_expires_at = null,
        claimed_at = null, updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id;
    return pg_catalog.jsonb_build_object(
      'status', 'released', 'requestId', p_request_id, 'acceptedRange', v_accepted_range
    );
  end if;

  select profile.credits into v_credits
  from public.profiles profile where profile.id = p_user_id;
  update public.birth_time_rectification_v4_handoffs
  set state = 'executing', lease_expires_at = pg_catalog.now() + interval '2 minutes',
      updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
  return pg_catalog.jsonb_build_object(
    'status', 'ready',
    'requestId', p_request_id,
    'billingReused', coalesce(v_request_status = 'reserved', false),
    'credits', v_credits,
    'acceptedRange', v_accepted_range
  );
end;
$$;

create function public.settle_birth_time_rectification_v4_handoff(
  p_user_id uuid,
  p_case_id uuid,
  p_claim_action_id uuid,
  p_request_id uuid,
  p_emitted boolean
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_handoff public.birth_time_rectification_v4_handoffs%rowtype;
  v_receipt public.birth_time_rectification_v4_handoff_settlements%rowtype;
  v_success boolean;
  v_credits integer;
  v_error text;
  v_response jsonb;
begin
  if p_user_id is null or p_case_id is null or p_claim_action_id is null
    or p_request_id is null or p_emitted is null then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':rectification-v4-settle', 0
    )
  );

  select settlement.* into v_receipt
  from public.birth_time_rectification_v4_handoff_settlements settlement
  where settlement.case_id = p_case_id and settlement.request_id = p_request_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.claim_action_id is distinct from p_claim_action_id
      or v_receipt.emitted is distinct from p_emitted then
      raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;

  select handoff.* into v_handoff
  from public.birth_time_rectification_v4_handoffs handoff
  where handoff.case_id = p_case_id and handoff.user_id = p_user_id
  for update;
  if not found or v_handoff.request_id is distinct from p_request_id
    or v_handoff.claim_action_id is distinct from p_claim_action_id
    or v_handoff.state not in ('claimed', 'executing') then
    raise exception 'rectification_v4_handoff_conflict' using errcode = 'P0001';
  end if;

  if p_emitted then
    select result.success, result.credits, result.error_code
      into v_success, v_credits, v_error
    from public.complete_consultation_credit(p_user_id, p_request_id::text) result;
    if v_success is not true then
      raise exception 'rectification_v4_billing_failed' using errcode = 'P0001';
    end if;
    perform public.consume_birth_time_rectification_v4_handoff(p_user_id, p_case_id);
    v_response := pg_catalog.jsonb_build_object(
      'status', 'consumed', 'requestId', p_request_id, 'credits', v_credits
    );
  else
    select result.success, result.credits, result.error_code
      into v_success, v_credits, v_error
    from public.cancel_consultation_credit(p_user_id, p_request_id::text) result;
    if v_success is not true then
      raise exception 'rectification_v4_billing_failed' using errcode = 'P0001';
    end if;
    update public.birth_time_rectification_v4_handoffs
    set state = 'pending', attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        ),
        claim_action_id = null, lease_expires_at = null,
        claimed_at = null, updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id;
    v_response := pg_catalog.jsonb_build_object(
      'status', 'pending', 'requestId', p_request_id, 'credits', v_credits
    );
  end if;

  insert into public.birth_time_rectification_v4_handoff_settlements (
    case_id, request_id, user_id, claim_action_id, emitted, response
  ) values (
    p_case_id, p_request_id, p_user_id, p_claim_action_id, p_emitted, v_response
  );
  return v_response;
end;
$$;

revoke all on function public.create_birth_time_rectification_v4_case(uuid, uuid, uuid, text, text, jsonb, text, text, jsonb, timestamptz) from public, anon, authenticated;
revoke all on function public.submit_birth_time_rectification_v4_answer(uuid, uuid, uuid, bigint, uuid, uuid, text, uuid, text, text, uuid, timestamptz) from public, anon, authenticated;
revoke all on function public.revise_birth_time_rectification_v4_event(uuid, uuid, uuid, bigint, jsonb, text, uuid, uuid, timestamptz) from public, anon, authenticated;
revoke all on function public.transition_birth_time_rectification_v4_case(uuid, uuid, uuid, bigint, text, text, text, text, timestamptz) from public, anon, authenticated;
revoke all on function public.claim_next_birth_time_rectification_v4_job(uuid, timestamptz) from public, anon, authenticated;
revoke all on function public.update_birth_time_rectification_v4_job_phase(uuid, uuid, text, timestamptz) from public, anon, authenticated;
revoke all on function public.complete_birth_time_rectification_v4_job(uuid, uuid, bigint, text, text, text, jsonb, jsonb, jsonb, text, text, timestamptz) from public, anon, authenticated;
revoke all on function public.fail_birth_time_rectification_v4_job(uuid, uuid, bigint, text, jsonb, timestamptz) from public, anon, authenticated;
revoke all on function public.birth_time_rectification_v4_handoff_projection(uuid, uuid) from public, anon, authenticated, service_role;
revoke all on function public.consume_birth_time_rectification_v4_handoff(uuid, uuid) from public, anon, authenticated, service_role;
revoke all on function public.attach_birth_time_rectification_v4_question(uuid, uuid, bigint, uuid, text, text) from public, anon, authenticated;
revoke all on function public.load_birth_time_rectification_v4_handoff(uuid, uuid) from public, anon, authenticated;
revoke all on function public.claim_birth_time_rectification_v4_handoff(uuid, uuid, bigint, uuid, text) from public, anon, authenticated;
revoke all on function public.begin_birth_time_rectification_v4_handoff_execution(uuid, uuid, bigint, uuid, uuid, text) from public, anon, authenticated;
revoke all on function public.settle_birth_time_rectification_v4_handoff(uuid, uuid, uuid, uuid, boolean) from public, anon, authenticated;
grant execute on function public.create_birth_time_rectification_v4_case(uuid, uuid, uuid, text, text, jsonb, text, text, jsonb, timestamptz) to service_role;
grant execute on function public.submit_birth_time_rectification_v4_answer(uuid, uuid, uuid, bigint, uuid, uuid, text, uuid, text, text, uuid, timestamptz) to service_role;
grant execute on function public.revise_birth_time_rectification_v4_event(uuid, uuid, uuid, bigint, jsonb, text, uuid, uuid, timestamptz) to service_role;
grant execute on function public.transition_birth_time_rectification_v4_case(uuid, uuid, uuid, bigint, text, text, text, text, timestamptz) to service_role;
grant execute on function public.claim_next_birth_time_rectification_v4_job(uuid, timestamptz) to service_role;
grant execute on function public.update_birth_time_rectification_v4_job_phase(uuid, uuid, text, timestamptz) to service_role;
grant execute on function public.complete_birth_time_rectification_v4_job(uuid, uuid, bigint, text, text, text, jsonb, jsonb, jsonb, text, text, timestamptz) to service_role;
grant execute on function public.fail_birth_time_rectification_v4_job(uuid, uuid, bigint, text, jsonb, timestamptz) to service_role;
grant execute on function public.attach_birth_time_rectification_v4_question(uuid, uuid, bigint, uuid, text, text) to service_role;
grant execute on function public.load_birth_time_rectification_v4_handoff(uuid, uuid) to service_role;
grant execute on function public.claim_birth_time_rectification_v4_handoff(uuid, uuid, bigint, uuid, text) to service_role;
grant execute on function public.begin_birth_time_rectification_v4_handoff_execution(uuid, uuid, bigint, uuid, uuid, text) to service_role;
grant execute on function public.settle_birth_time_rectification_v4_handoff(uuid, uuid, uuid, uuid, boolean) to service_role;

commit;
