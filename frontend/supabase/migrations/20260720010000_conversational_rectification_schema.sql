begin;

alter table public.birth_time_rectification_cases
  add column if not exists revision_of_case_id uuid,
  add column if not exists imported_from_case_id uuid,
  add column if not exists baseline_active_time time without time zone,
  add column if not exists pending_consultation_question text,
  add column if not exists declared_birth_input jsonb not null default '{}'::jsonb;

alter table public.birth_time_rectification_cases
  drop constraint if exists birth_time_rectification_cases_revision_of_case_id_fkey,
  drop constraint if exists birth_time_rectification_cases_imported_from_case_id_fkey,
  drop constraint if exists birth_time_rectification_cases_pending_question_check,
  drop constraint if exists birth_time_rectification_cases_declared_birth_input_check,
  drop constraint if exists birth_time_rectification_cases_journey_protocol_check,
  drop constraint if exists birth_time_rectification_cases_status_check;

alter table public.birth_time_rectification_cases
  add constraint birth_time_rectification_cases_revision_of_case_id_fkey
    foreign key (revision_of_case_id)
    references public.birth_time_rectification_cases(id) on delete set null,
  add constraint birth_time_rectification_cases_imported_from_case_id_fkey
    foreign key (imported_from_case_id)
    references public.birth_time_rectification_cases(id) on delete set null,
  add constraint birth_time_rectification_cases_pending_question_check
    check (
      pending_consultation_question is null
      or char_length(pending_consultation_question) between 1 and 500
    ),
  add constraint birth_time_rectification_cases_declared_birth_input_check
    check (
      jsonb_typeof(declared_birth_input) = 'object'
      and octet_length(declared_birth_input::text) <= 12000
    ),
  add constraint birth_time_rectification_cases_journey_protocol_check
    check (journey_protocol in (
      'legacy-guided-v1',
      'dynamic-choice-v2',
      'conversational-evidence-v3'
    )),
  add constraint birth_time_rectification_cases_status_check
    check (status in (
      'assessing', 'rectifying', 'candidate', 'confirming', 'confirmed',
      'starting', 'active', 'paused', 'completed', 'abandoned'
    ));

-- Billing and case creation are phases of one public start action. Billing
-- phases use deterministic internal receipt ids so the public action can stay
-- stable without colliding with the case-transition receipt key.
create or replace function public.conversational_rectification_billing_receipt_action_id(
  p_action_id uuid,
  p_action_kind text
)
returns uuid
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.md5(p_action_id::text || ':' || p_action_kind)::uuid;
$$;

create table if not exists public.birth_time_rectification_turns (
  id uuid not null default gen_random_uuid(),
  case_id uuid not null
    references public.birth_time_rectification_cases(id) on delete cascade,
  turn_version bigint not null check (turn_version >= 0),
  narrative text not null check (
    char_length(narrative) between 1 and 12000
    and char_length(btrim(narrative)) > 0
  ),
  candidate jsonb not null check (jsonb_typeof(candidate) = 'object'),
  technical_receipt jsonb not null check (jsonb_typeof(technical_receipt) = 'object'),
  evidence_request jsonb check (
    evidence_request is null or jsonb_typeof(evidence_request) = 'object'
  ),
  evidence_recap jsonb not null default '[]'::jsonb check (
    jsonb_typeof(evidence_recap) = 'array'
    and jsonb_array_length(evidence_recap) <= 20
  ),
  actions jsonb not null default '[]'::jsonb check (
    jsonb_typeof(actions) = 'array'
    and jsonb_array_length(actions) <= 5
  ),
  output_validation_receipt jsonb not null default '{}'::jsonb check (
    jsonb_typeof(output_validation_receipt) = 'object'
  ),
  created_at timestamptz not null default now(),
  primary key (case_id, turn_version),
  unique (case_id, id),
  check (not jsonb_path_exists(
    jsonb_build_object(
      'candidate', candidate,
      'technicalReceipt', technical_receipt,
      'evidenceRequest', evidence_request,
      'evidenceRecap', evidence_recap,
      'outputValidationReceipt', output_validation_receipt
    ),
    '$.**.candidateWeights'
  )),
  check (not jsonb_path_exists(candidate, '$.**.candidateScores')),
  check (not jsonb_path_exists(candidate, '$.**.partitionId')),
  check (not jsonb_path_exists(technical_receipt, '$.**.rawModelOutput')),
  check (not jsonb_path_exists(output_validation_receipt, '$.**.systemPrompt'))
);

create table if not exists public.birth_time_rectification_event_evidence (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null,
  source_turn_id uuid not null,
  raw_text text not null check (
    char_length(raw_text) between 1 and 4000
    and char_length(btrim(raw_text)) > 0
  ),
  domain text not null check (
    domain in ('career', 'education', 'relocation', 'relationship', 'family', 'other')
  ),
  event_summary text not null check (char_length(event_summary) between 1 and 1000),
  date_value text check (date_value is null or char_length(date_value) between 1 and 80),
  date_precision text not null check (
    date_precision in ('day', 'month', 'year', 'range', 'unknown')
  ),
  extraction_status text not null check (
    extraction_status in ('clear', 'needs_clarification', 'corrected')
  ),
  scoreable boolean not null default false,
  created_at timestamptz not null default now(),
  foreign key (case_id, source_turn_id)
    references public.birth_time_rectification_turns(case_id, id) on delete cascade
);

create table if not exists public.birth_time_rectification_action_receipts (
  -- Billing reservation happens before the case exists, so receipts cannot
  -- depend on the case row. The service-only RPCs preserve ownership.
  case_id uuid not null,
  action_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  action_kind text not null check (action_kind in (
    'create', 'save_turn', 'pause', 'abandon', 'confirm', 'import_legacy',
    'reserve_fee', 'complete_fee', 'release_fee'
  )),
  expected_turn_version bigint not null check (expected_turn_version >= 0),
  result_turn_version bigint not null check (result_turn_version >= 0),
  request_fingerprint text not null check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  response jsonb not null check (jsonb_typeof(response) = 'object'),
  created_at timestamptz not null default now(),
  primary key (case_id, action_id),
  check (not jsonb_path_exists(response, '$.**.candidateWeights')),
  check (not jsonb_path_exists(response, '$.**.candidateScores')),
  check (not jsonb_path_exists(response, '$.**.partitionId')),
  check (not jsonb_path_exists(response, '$.**.rawModelOutput')),
  check (not jsonb_path_exists(response, '$.**.systemPrompt'))
);

create table if not exists public.birth_time_rectification_billing (
  -- A reservation is the first durable start record and therefore precedes
  -- case creation. The case transition RPC claims this row atomically.
  case_id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  price integer not null check (price between 1 and 1000000),
  state text not null check (
    state in ('reserved', 'charged', 'released', 'migration_waived')
  ),
  reservation_id uuid unique,
  billing_receipt_id uuid unique,
  reserve_action_id uuid,
  complete_action_id uuid,
  release_action_id uuid,
  balance_after integer check (balance_after is null or balance_after >= 0),
  reserved_at timestamptz,
  charged_at timestamptz,
  released_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    state not in ('reserved', 'charged')
    or (reservation_id is not null and reserve_action_id is not null and reserved_at is not null)
  ),
  check (
    state <> 'charged'
    or (billing_receipt_id is not null and complete_action_id is not null and charged_at is not null)
  ),
  check (state <> 'released' or (release_action_id is not null and released_at is not null)),
  unique (user_id, reserve_action_id)
);

create index if not exists birth_time_rectification_cases_v3_account_idx
  on public.birth_time_rectification_cases (user_id, updated_at desc)
  where journey_protocol = 'conversational-evidence-v3';
create index if not exists birth_time_rectification_evidence_case_idx
  on public.birth_time_rectification_event_evidence (case_id, created_at);
create unique index if not exists birth_time_rectification_reserve_action_idx
  on public.birth_time_rectification_action_receipts (user_id, action_id)
  where action_kind = 'reserve_fee';

alter table public.birth_time_rectification_turns enable row level security;
alter table public.birth_time_rectification_event_evidence enable row level security;
alter table public.birth_time_rectification_action_receipts enable row level security;
alter table public.birth_time_rectification_billing enable row level security;

revoke all on table public.birth_time_rectification_cases from public, anon, authenticated;
revoke all on table public.birth_time_rectification_turns from public, anon, authenticated;
revoke all on table public.birth_time_rectification_event_evidence from public, anon, authenticated;
revoke all on table public.birth_time_rectification_action_receipts from public, anon, authenticated;
revoke all on table public.birth_time_rectification_billing from public, anon, authenticated;

revoke all on table public.birth_time_rectification_cases from service_role;
revoke all on table public.birth_time_rectification_turns from service_role;
revoke all on table public.birth_time_rectification_event_evidence from service_role;
revoke all on table public.birth_time_rectification_action_receipts from service_role;
revoke all on table public.birth_time_rectification_billing from service_role;

grant all on table public.birth_time_rectification_cases to service_role;
grant all on table public.birth_time_rectification_turns to service_role;
grant all on table public.birth_time_rectification_event_evidence to service_role;
grant all on table public.birth_time_rectification_action_receipts to service_role;
grant all on table public.birth_time_rectification_billing to service_role;

revoke all on function public.conversational_rectification_billing_receipt_action_id(
  uuid, text
) from public, anon, authenticated, service_role;

commit;
