-- Durable, server-owned protocol state for agent-guided rectification turns.
alter table public.birth_time_rectification_cases
  add column if not exists turn_version bigint not null default 0,
  add column if not exists turn_state jsonb not null default '{}'::jsonb,
  add column if not exists evidence_draft jsonb,
  add column if not exists processed_action_ids uuid[] not null default '{}'::uuid[],
  add column if not exists adaptive_round integer not null default 0,
  add column if not exists asked_domains text[] not null default '{}'::text[];

alter table public.birth_time_rectification_cases
  drop constraint if exists birth_time_rectification_cases_turn_state_check,
  drop constraint if exists birth_time_rectification_cases_evidence_draft_check,
  drop constraint if exists birth_time_rectification_cases_processed_action_ids_check,
  drop constraint if exists birth_time_rectification_cases_adaptive_round_check,
  drop constraint if exists birth_time_rectification_cases_asked_domains_check;

alter table public.birth_time_rectification_cases
  add constraint birth_time_rectification_cases_turn_state_check
    check (jsonb_typeof(turn_state) = 'object'),
  add constraint birth_time_rectification_cases_evidence_draft_check
    check (evidence_draft is null or jsonb_typeof(evidence_draft) = 'object'),
  add constraint birth_time_rectification_cases_processed_action_ids_check
    check (cardinality(processed_action_ids) <= 100),
  add constraint birth_time_rectification_cases_adaptive_round_check
    check (adaptive_round between 0 and 3),
  add constraint birth_time_rectification_cases_asked_domains_check
    check (asked_domains <@ array['education', 'relocation', 'relationship', 'career', 'health_pressure']::text[]);

create table if not exists public.birth_time_rectification_scoring_jobs (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.birth_time_rectification_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  evidence_fingerprint text not null,
  algorithm_version text not null,
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'completed', 'failed')),
  expires_at timestamptz not null,
  result jsonb,
  failure_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  unique (case_id, evidence_fingerprint, algorithm_version),
  check (result is null or jsonb_typeof(result) = 'object')
);

alter table public.birth_time_rectification_scoring_jobs enable row level security;
revoke all on table public.birth_time_rectification_scoring_jobs from anon, authenticated;
revoke all on table public.birth_time_rectification_scoring_jobs from service_role;
grant all on table public.birth_time_rectification_scoring_jobs to service_role;
