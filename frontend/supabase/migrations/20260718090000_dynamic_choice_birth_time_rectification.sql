alter table public.birth_time_rectification_cases
  add column if not exists journey_protocol text not null default 'legacy-guided-v1';

alter table public.birth_time_rectification_cases
  drop constraint if exists birth_time_rectification_cases_journey_protocol_check,
  add constraint birth_time_rectification_cases_journey_protocol_check
    check (journey_protocol in ('legacy-guided-v1', 'dynamic-choice-v2'));

create or replace function public.birth_time_dynamic_agent_context_valid(value jsonb)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(value) = 'array'
    and not pg_catalog.jsonb_path_exists(value, '$[*] ? (@.type() != "string")')
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements_text(value) as item(note)
      where pg_catalog.length(note) > 240
    );
$$;

create table if not exists public.birth_time_rectification_dynamic_state (
  case_id uuid primary key references public.birth_time_rectification_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  candidate_model jsonb,
  current_choice_question jsonb,
  choice_answers jsonb not null default '[]'::jsonb,
  choice_evidence jsonb not null default '[]'::jsonb,
  dynamic_control jsonb not null,
  agent_context jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (candidate_model is null or jsonb_typeof(candidate_model) = 'object'),
  check (current_choice_question is null or jsonb_typeof(current_choice_question) = 'object'),
  check (jsonb_typeof(choice_answers) = 'array' and jsonb_array_length(choice_answers) <= 50),
  check (jsonb_typeof(choice_evidence) = 'array' and jsonb_array_length(choice_evidence) <= 10),
  check (jsonb_typeof(dynamic_control) = 'object'),
  check (jsonb_typeof(agent_context) = 'array' and jsonb_array_length(agent_context) <= 10),
  check (public.birth_time_dynamic_agent_context_valid(agent_context))
);

alter table public.birth_time_rectification_dynamic_state enable row level security;
revoke all on table public.birth_time_rectification_dynamic_state from anon, authenticated;
revoke all on table public.birth_time_rectification_dynamic_state from service_role;
grant all on table public.birth_time_rectification_dynamic_state to service_role;

revoke all on function public.birth_time_dynamic_agent_context_valid(jsonb) from public, anon, authenticated;
grant execute on function public.birth_time_dynamic_agent_context_valid(jsonb) to service_role;

create or replace function public.persist_birth_time_dynamic_private_state(
  p_case_id uuid,
  p_user_id uuid,
  p_private_state jsonb
)
returns void
language plpgsql
set search_path = ''
as $$
begin
  if pg_catalog.jsonb_typeof(p_private_state) is distinct from 'object' then
    raise exception 'birth_time_dynamic_private_state_invalid';
  end if;
  insert into public.birth_time_rectification_dynamic_state (
    case_id, user_id, candidate_model, current_choice_question,
    choice_answers, choice_evidence, dynamic_control, agent_context, updated_at
  ) values (
    p_case_id, p_user_id,
    nullif(p_private_state -> 'candidateModel', 'null'::jsonb),
    nullif(p_private_state -> 'currentChoiceQuestion', 'null'::jsonb),
    coalesce(p_private_state -> 'choiceAnswers', '[]'::jsonb),
    coalesce(p_private_state -> 'choiceEvidence', '[]'::jsonb),
    p_private_state -> 'dynamicControl',
    coalesce(p_private_state -> 'agentContext', '[]'::jsonb), now()
  ) on conflict (case_id) do update set
    user_id = excluded.user_id,
    candidate_model = excluded.candidate_model,
    current_choice_question = excluded.current_choice_question,
    choice_answers = excluded.choice_answers,
    choice_evidence = excluded.choice_evidence,
    dynamic_control = excluded.dynamic_control,
    agent_context = excluded.agent_context,
    updated_at = excluded.updated_at;
end;
$$;

create or replace function public.create_birth_time_dynamic_case(
  p_user_id uuid,
  p_public_case jsonb,
  p_private_state jsonb,
  p_profile jsonb
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case_id uuid;
begin
  if jsonb_typeof(p_public_case) is distinct from 'object'
    or jsonb_typeof(p_private_state) is distinct from 'object'
    or jsonb_typeof(p_profile) is distinct from 'object'
    or p_public_case ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or p_public_case #>> '{turnState,journeyProtocol}' is distinct from 'dynamic-choice-v2'
    or (p_public_case #>> '{turnState,turnVersion}')::bigint is distinct from 0
    or jsonb_path_exists(p_public_case, '$.**.partitionId')
    or jsonb_path_exists(p_public_case, '$.**.candidateScores')
    or jsonb_path_exists(p_public_case, '$.**.agentContext') then
    raise exception 'birth_time_dynamic_case_invalid';
  end if;

  insert into public.birth_time_rectification_cases (
    user_id, journey_protocol, status, reported_date, reported_time,
    reported_period, source, uncertainty_before_minutes,
    uncertainty_after_minutes, questionnaire, journey_snapshot,
    candidate_scan, turn_state, candidate_start, candidate_end,
    confirmed_time, confirmed_at
  ) values (
    p_user_id, 'dynamic-choice-v2', p_public_case ->> 'status',
    (p_public_case ->> 'reportedDate')::date,
    nullif(p_public_case ->> 'reportedTime', '')::time,
    nullif(p_public_case ->> 'reportedPeriod', ''),
    p_public_case ->> 'source',
    nullif(p_public_case ->> 'uncertaintyBeforeMinutes', '')::integer,
    nullif(p_public_case ->> 'uncertaintyAfterMinutes', '')::integer,
    coalesce(p_public_case -> 'questionnaire', '{}'::jsonb),
    p_public_case -> 'journeySnapshot',
    coalesce(p_public_case -> 'candidateScan', '{}'::jsonb),
    p_public_case -> 'turnState',
    nullif(p_public_case ->> 'candidateStart', '')::time,
    nullif(p_public_case ->> 'candidateEnd', '')::time,
    nullif(p_public_case ->> 'confirmedTime', '')::time,
    nullif(p_public_case ->> 'confirmedAt', '')::timestamptz
  ) returning id into v_case_id;

  perform public.persist_birth_time_dynamic_private_state(
    v_case_id, p_user_id, p_private_state
  );

  update public.profiles
  set reported_birth_time = nullif(p_profile ->> 'reportedBirthTime', '')::time,
      active_birth_time = nullif(p_profile ->> 'activeBirthTime', '')::time,
      birth_time = nullif(p_profile ->> 'birthTime', '')::time,
      birth_time_source = p_profile ->> 'birthTimeSource',
      birth_time_period = nullif(p_profile ->> 'birthTimePeriod', ''),
      birth_time_clue = nullif(p_profile ->> 'birthTimeClue', ''),
      uncertainty_before_minutes = nullif(p_profile ->> 'uncertaintyBeforeMinutes', '')::integer,
      uncertainty_after_minutes = nullif(p_profile ->> 'uncertaintyAfterMinutes', '')::integer,
      birth_time_status = p_profile ->> 'birthTimeStatus',
      rectification_confidence = null,
      rectification_case_id = v_case_id
  where id = p_user_id;
  if not found then
    raise exception 'birth_time_dynamic_profile_not_found';
  end if;
  return v_case_id;
end;
$$;

create or replace function public.save_birth_time_dynamic_turn(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_public_turn_state jsonb,
  p_snapshot jsonb,
  p_candidate_result jsonb,
  p_private_state jsonb
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_new_version bigint;
begin
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'dynamic-choice-v2' then
    raise exception 'birth_time_dynamic_case_not_found';
  end if;
  if p_action_id = any(v_case.processed_action_ids) then
    return v_case.turn_version;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'stale_birth_time_dynamic_turn';
  end if;
  if p_public_turn_state ->> 'journeyProtocol' is distinct from 'dynamic-choice-v2'
    or (p_public_turn_state ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or jsonb_typeof(p_private_state) is distinct from 'object'
    or jsonb_path_exists(p_public_turn_state, '$.**.partitionId')
    or jsonb_path_exists(p_public_turn_state, '$.**.candidateScores')
    or jsonb_path_exists(p_public_turn_state, '$.**.agentContext') then
    raise exception 'birth_time_dynamic_turn_invalid';
  end if;

  update public.birth_time_rectification_cases
  set status = case p_snapshot ->> 'state'
        when 'ready' then 'confirmed'
        when 'confirming' then 'confirming'
        when 'candidate' then 'candidate'
        else 'rectifying'
      end,
      journey_snapshot = p_snapshot,
      candidate_result = coalesce(p_candidate_result, '{}'::jsonb),
      event_scoring_version = p_candidate_result ->> 'algorithmVersion',
      candidate_result_id = case
        when p_candidate_result ? 'resultId' then (p_candidate_result ->> 'resultId')::uuid
        else null
      end,
      candidate_start = case
        when p_candidate_result #>> '{winningSegment,startTime}' is null then null
        else (p_candidate_result #>> '{winningSegment,startTime}')::time
      end,
      candidate_end = case
        when p_candidate_result #>> '{winningSegment,endTime}' is null then null
        else (p_candidate_result #>> '{winningSegment,endTime}')::time
      end,
      turn_version = p_expected_version + 1,
      turn_state = p_public_turn_state,
      evidence_draft = null,
      processed_action_ids = case
        when cardinality(processed_action_ids) >= 100
          then processed_action_ids[2:100] || p_action_id
        else processed_action_ids || p_action_id
      end,
      updated_at = now()
  where id = p_case_id and user_id = p_user_id and turn_version = p_expected_version
  returning turn_version into v_new_version;
  if v_new_version is null then
    raise exception 'stale_birth_time_dynamic_turn';
  end if;

  perform public.persist_birth_time_dynamic_private_state(
    p_case_id, p_user_id, p_private_state
  );
  return v_new_version;
end;
$$;


revoke all on function public.create_birth_time_dynamic_case(uuid, jsonb, jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.persist_birth_time_dynamic_private_state(uuid, uuid, jsonb) from public, anon, authenticated, service_role;
revoke all on function public.save_birth_time_dynamic_turn(uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb) from public, anon, authenticated;

grant execute on function public.create_birth_time_dynamic_case(uuid, jsonb, jsonb, jsonb) to service_role;
grant execute on function public.save_birth_time_dynamic_turn(uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb) to service_role;
