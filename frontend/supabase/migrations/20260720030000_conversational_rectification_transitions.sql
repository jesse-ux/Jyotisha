begin;

create or replace function public.conversational_rectification_fingerprint(value jsonb)
returns text
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.encode(
    pg_catalog.sha256(pg_catalog.convert_to(value::text, 'UTF8')),
    'hex'
  );
$$;

create or replace function public.guard_imported_rectification_history()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (
    select 1
    from public.birth_time_rectification_cases imported
    where imported.imported_from_case_id = old.id
      and imported.journey_protocol = 'conversational-evidence-v3'
  ) then
    raise exception 'conversational_imported_case_read_only' using errcode = 'P0001';
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

drop trigger if exists birth_time_rectification_imported_history_update
  on public.birth_time_rectification_cases;
create trigger birth_time_rectification_imported_history_update
before update on public.birth_time_rectification_cases
for each row execute function public.guard_imported_rectification_history();

drop trigger if exists birth_time_rectification_imported_history_delete
  on public.birth_time_rectification_cases;
create trigger birth_time_rectification_imported_history_delete
before delete on public.birth_time_rectification_cases
for each row execute function public.guard_imported_rectification_history();

create or replace function public.conversational_rectification_case_projection(
  p_user_id uuid,
  p_case_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select pg_catalog.jsonb_build_object(
    'case_id', c.id,
    'user_id', c.user_id,
    'status', c.status,
    'turn_version', c.turn_version,
    'revision_of_case_id', c.revision_of_case_id,
    'imported_from_case_id', c.imported_from_case_id,
    'baseline_active_time', case when c.baseline_active_time is null then null
      else pg_catalog.to_char(c.baseline_active_time, 'HH24:MI') end,
    'pending_consultation_question', c.pending_consultation_question,
    'billing_state', billing.state,
    'latest_turn', pg_catalog.jsonb_build_object(
      'caseId', c.id,
      'journeyProtocol', 'conversational-evidence-v3',
      'status', c.status,
      'turnVersion', turn.turn_version,
      'narrative', turn.narrative,
      'candidate', turn.candidate,
      'technicalReceipt', turn.technical_receipt,
      'evidenceRequest', turn.evidence_request,
      'evidenceRecap', turn.evidence_recap,
      'actions', turn.actions,
      'pendingConsultationQuestion', c.pending_consultation_question
    )
  )
  from public.birth_time_rectification_cases c
  join public.birth_time_rectification_turns turn
    on turn.case_id = c.id and turn.turn_version = c.turn_version
  left join public.birth_time_rectification_billing billing
    on billing.case_id = c.id and billing.user_id = c.user_id
  where c.id = p_case_id
    and c.user_id = p_user_id
    and c.journey_protocol = 'conversational-evidence-v3';
$$;

create or replace function public.load_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid default null
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_case_id uuid;
  v_projection jsonb;
begin
  if p_user_id is null then
    return null;
  end if;
  if p_case_id is not null then
    v_case_id := p_case_id;
  else
    select c.id into v_case_id
    from public.birth_time_rectification_cases c
    where c.user_id = p_user_id
      and c.journey_protocol = 'conversational-evidence-v3'
      and c.status in ('starting', 'active', 'paused', 'confirming')
    order by c.updated_at desc, c.created_at desc
    limit 1;
  end if;
  v_projection := public.conversational_rectification_case_projection(
    p_user_id,
    v_case_id
  );
  if v_projection is null then
    return null;
  end if;

  -- This RPC is service-role-only. Mutation receipts continue to use the
  -- public projection above, while account resume additionally receives the
  -- private working state needed to continue on another device.
  return v_projection || pg_catalog.jsonb_build_object(
    'declared_birth_input', (
      select c.declared_birth_input
      from public.birth_time_rectification_cases c
      where c.id = v_case_id and c.user_id = p_user_id
    ),
    'private_candidate', (
      select c.candidate_result
      from public.birth_time_rectification_cases c
      where c.id = v_case_id and c.user_id = p_user_id
    ),
    'event_evidence', coalesce((
      select pg_catalog.jsonb_agg(
        pg_catalog.jsonb_build_object(
          'id', evidence.id,
          'rawText', evidence.raw_text,
          'domain', evidence.domain,
          'eventSummary', evidence.event_summary,
          'dateValue', evidence.date_value,
          'datePrecision', evidence.date_precision,
          'extractionStatus', evidence.extraction_status,
          'scoreable', evidence.scoreable
        ) order by evidence.created_at, evidence.id
      )
      from public.birth_time_rectification_event_evidence evidence
      where evidence.case_id = v_case_id
    ), '[]'::jsonb),
    'validation_receipts', coalesce((
      select pg_catalog.jsonb_agg(
        turn.output_validation_receipt order by turn.turn_version
      )
      from public.birth_time_rectification_turns turn
      where turn.case_id = v_case_id
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function public.create_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_revision_of_case_id uuid,
  p_pending_consultation_question text,
  p_declared_birth_input jsonb,
  p_first_turn jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_profile public.profiles%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'create', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'revisionOfCaseId', p_revision_of_case_id,
      'pendingConsultationQuestion', p_pending_consultation_question,
      'declaredBirthInput', p_declared_birth_input,
      'firstTurn', p_first_turn, 'validationReceipt', p_validation_receipt,
      'privateCandidate', p_private_candidate
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_case_id is distinct from p_action_id
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':conversational-rectification-case',
      0
    )
  );
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );

  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id
  for update;
  if found then
    if v_case.user_id is distinct from p_user_id
      or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
      raise exception 'conversational_case_not_found' using errcode = 'P0001';
    end if;
    select r.* into v_receipt
    from public.birth_time_rectification_action_receipts r
    where r.case_id = p_case_id and r.action_id = p_action_id
    for update;
    if found
      and v_receipt.user_id is not distinct from p_user_id
      and v_receipt.action_kind is not distinct from 'create'
      and v_receipt.expected_turn_version is not distinct from p_expected_version
      and v_receipt.request_fingerprint is not distinct from v_fingerprint then
      return v_receipt.response;
    end if;
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if p_expected_version is distinct from 0 then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  perform 1
  from public.birth_time_rectification_cases active_case
  where active_case.user_id = p_user_id
    and active_case.id <> p_case_id
    and active_case.journey_protocol = 'conversational-evidence-v3'
    and active_case.status in ('starting', 'active', 'paused', 'confirming')
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select profile.* into v_profile
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;

  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found
    or v_billing.reserve_action_id is distinct from p_action_id
    or v_billing.state not in ('reserved', 'charged') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if p_revision_of_case_id is not null then
    perform 1
    from public.birth_time_rectification_cases prior
    where prior.id = p_revision_of_case_id
      and prior.user_id = p_user_id
      and prior.journey_protocol = 'conversational-evidence-v3'
      and prior.status in ('completed', 'abandoned')
    for update;
    if not found then
      raise exception 'conversational_case_not_found' using errcode = 'P0001';
    end if;
  end if;

  if public.conversational_rectification_valid_declared_birth_input(
      p_declared_birth_input
    ) is not true
    or public.conversational_rectification_valid_public_turn(p_first_turn) is not true
    or public.conversational_rectification_valid_validation_receipt(
      p_validation_receipt
    ) is not true
    or public.conversational_rectification_valid_private_candidate(
      p_private_candidate
    ) is not true
    or p_first_turn ->> 'caseId' is distinct from p_case_id::text
    or p_first_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_first_turn ->> 'turnVersion')::bigint is distinct from 0
    or p_first_turn ->> 'status' is distinct from 'active'
    or nullif(p_first_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(p_pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_cases (
    id, user_id, journey_protocol, status, reported_date, reported_time,
    reported_period, source, uncertainty_before_minutes,
    uncertainty_after_minutes, declared_birth_input,
    journey_snapshot, turn_version, turn_state,
    candidate_result, candidate_result_id, candidate_start, candidate_end,
    event_scoring_version, revision_of_case_id, baseline_active_time,
    pending_consultation_question, updated_at
  ) values (
    p_case_id, p_user_id, 'conversational-evidence-v3', 'active',
    (p_declared_birth_input ->> 'birthDate')::date,
    nullif(p_declared_birth_input ->> 'reportedTime', '')::time,
    nullif(p_declared_birth_input ->> 'reportedPeriod', ''),
    p_declared_birth_input ->> 'source',
    nullif(p_declared_birth_input ->> 'uncertaintyBeforeMinutes', '')::integer,
    nullif(p_declared_birth_input ->> 'uncertaintyAfterMinutes', '')::integer,
    p_declared_birth_input, p_first_turn, 0, p_first_turn, p_private_candidate,
    nullif(p_private_candidate ->> 'resultId', '')::uuid,
    nullif(p_private_candidate ->> 'rangeStart', '')::time,
    nullif(p_private_candidate ->> 'rangeEnd', '')::time,
    nullif(p_private_candidate ->> 'calculationVersion', ''),
    p_revision_of_case_id, v_profile.active_birth_time,
    nullif(p_pending_consultation_question, ''), pg_catalog.now()
  );

  insert into public.birth_time_rectification_turns (
    case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    p_case_id, 0, p_first_turn ->> 'narrative', p_first_turn -> 'candidate',
    p_first_turn -> 'technicalReceipt',
    nullif(p_first_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_first_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_first_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'create', p_expected_version,
    0, v_fingerprint,
    public.conversational_rectification_action_request(
      'create', p_user_id, p_case_id, p_expected_version, p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

create or replace function public.save_conversational_rectification_turn(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_evidence jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_turn_id uuid := pg_catalog.gen_random_uuid();
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'save_turn', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'turn', p_turn, 'evidence', p_evidence,
      'validationReceipt', p_validation_receipt,
      'privateCandidate', p_private_candidate
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;

  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'save_turn'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found or v_billing.state not in ('charged', 'migration_waived') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  if v_case.status not in ('active', 'paused', 'confirming')
    or pg_catalog.jsonb_typeof(p_turn) is distinct from 'object'
    or pg_catalog.jsonb_typeof(p_evidence) is distinct from 'array'
    or pg_catalog.jsonb_array_length(p_evidence) > 20
    or pg_catalog.jsonb_typeof(p_validation_receipt) is distinct from 'object'
    or pg_catalog.jsonb_typeof(p_private_candidate) is distinct from 'object'
    or p_turn ->> 'caseId' is distinct from p_case_id::text
    or p_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_turn ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_turn ->> 'status' not in ('active', 'confirming')
    or nullif(p_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(v_case.pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_turns (
    id, case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    v_turn_id, p_case_id, p_expected_version + 1,
    p_turn ->> 'narrative', p_turn -> 'candidate', p_turn -> 'technicalReceipt',
    nullif(p_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );

  insert into public.birth_time_rectification_event_evidence (
    id, case_id, source_turn_id, raw_text, domain, event_summary,
    date_value, date_precision, extraction_status, scoreable
  )
  select
    (item ->> 'id')::uuid, p_case_id, v_turn_id, item ->> 'rawText',
    item ->> 'domain', item ->> 'eventSummary',
    nullif(item ->> 'dateValue', ''), item ->> 'datePrecision',
    item ->> 'extractionStatus',
    coalesce((item ->> 'scoreable')::boolean, false)
  from pg_catalog.jsonb_array_elements(p_evidence) item;

  update public.birth_time_rectification_cases
  set status = p_turn ->> 'status',
      turn_version = p_expected_version + 1,
      turn_state = p_turn,
      journey_snapshot = p_turn,
      candidate_result = p_private_candidate,
      candidate_result_id = nullif(p_private_candidate ->> 'resultId', '')::uuid,
      candidate_start = nullif(p_private_candidate ->> 'rangeStart', '')::time,
      candidate_end = nullif(p_private_candidate ->> 'rangeEnd', '')::time,
      event_scoring_version = nullif(p_private_candidate ->> 'calculationVersion', ''),
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id
    and turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'save_turn', p_expected_version,
    p_expected_version + 1, v_fingerprint,
    public.conversational_rectification_action_request(
      'save_turn', p_user_id, p_case_id, p_expected_version,
      p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

create or replace function public.pause_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_validation_receipt jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'pause', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'turn', p_turn, 'validationReceipt', p_validation_receipt
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'pause'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;
  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found or v_billing.state not in ('charged', 'migration_waived') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if v_case.status not in ('active', 'confirming')
    or pg_catalog.jsonb_typeof(p_turn) is distinct from 'object'
    or pg_catalog.jsonb_typeof(p_validation_receipt) is distinct from 'object'
    or p_turn ->> 'caseId' is distinct from p_case_id::text
    or p_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_turn ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_turn ->> 'status' is distinct from 'paused'
    or nullif(p_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(v_case.pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_turns (
    case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    p_case_id, p_expected_version + 1, p_turn ->> 'narrative',
    p_turn -> 'candidate', p_turn -> 'technicalReceipt',
    nullif(p_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );
  update public.birth_time_rectification_cases
  set status = 'paused', turn_version = p_expected_version + 1,
      turn_state = p_turn, journey_snapshot = p_turn,
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id
    and turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'pause', p_expected_version,
    p_expected_version + 1, v_fingerprint,
    public.conversational_rectification_action_request(
      'pause', p_user_id, p_case_id, p_expected_version, p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

create or replace function public.abandon_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_validation_receipt jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'abandon', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'turn', p_turn, 'validationReceipt', p_validation_receipt
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'abandon'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;
  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found or v_billing.state not in ('charged', 'migration_waived') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if v_case.status not in ('active', 'paused', 'confirming')
    or pg_catalog.jsonb_typeof(p_turn) is distinct from 'object'
    or pg_catalog.jsonb_typeof(p_validation_receipt) is distinct from 'object'
    or p_turn ->> 'caseId' is distinct from p_case_id::text
    or p_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_turn ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_turn ->> 'status' is distinct from 'abandoned'
    or nullif(p_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(v_case.pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_turns (
    case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    p_case_id, p_expected_version + 1, p_turn ->> 'narrative',
    p_turn -> 'candidate', p_turn -> 'technicalReceipt',
    nullif(p_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );
  update public.birth_time_rectification_cases
  set status = 'abandoned', turn_version = p_expected_version + 1,
      turn_state = p_turn, journey_snapshot = p_turn,
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id
    and turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'abandon', p_expected_version,
    p_expected_version + 1, v_fingerprint,
    public.conversational_rectification_action_request(
      'abandon', p_user_id, p_case_id, p_expected_version, p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

create or replace function public.confirm_conversational_rectification_candidate(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_result_id uuid,
  p_time time without time zone,
  p_calculation_version text,
  p_turn jsonb,
  p_validation_receipt jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_profile public.profiles%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_current_turn public.birth_time_rectification_turns%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_response jsonb;
  v_time text := pg_catalog.to_char(p_time, 'HH24:MI');
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'confirm', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'resultId', p_result_id, 'time', p_time,
      'calculationVersion', p_calculation_version, 'turn', p_turn,
      'validationReceipt', p_validation_receipt
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_result_id is null or p_time is null
    or extract(second from p_time) is distinct from 0
    or nullif(p_calculation_version, '') is null
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_candidate_changed' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'confirm'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found or v_billing.state not in ('charged', 'migration_waived') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  select turn.* into v_current_turn
  from public.birth_time_rectification_turns turn
  where turn.case_id = p_case_id and turn.turn_version = p_expected_version
  for update;
  if not found then
    raise exception 'conversational_candidate_changed' using errcode = 'P0001';
  end if;
  select profile.* into v_profile
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found or v_profile.active_birth_time is distinct from v_case.baseline_active_time then
    raise exception 'conversational_candidate_changed' using errcode = 'P0001';
  end if;

  if v_case.status is distinct from 'confirming'
    or v_case.candidate_result_id is distinct from p_result_id
    or v_case.candidate_result ->> 'resultId' is distinct from p_result_id::text
    or v_case.candidate_result ->> 'representativeTime' is distinct from v_time
    or v_case.candidate_result ->> 'calculationVersion'
      is distinct from p_calculation_version
    or v_case.event_scoring_version is distinct from p_calculation_version
    or v_current_turn.candidate ->> 'status' is distinct from 'ready_for_confirmation'
    or v_current_turn.candidate ->> 'representativeTime' is distinct from v_time
    or v_current_turn.technical_receipt ->> 'calculationVersion'
      is distinct from p_calculation_version
    or pg_catalog.jsonb_typeof(p_turn) is distinct from 'object'
    or pg_catalog.jsonb_typeof(p_validation_receipt) is distinct from 'object'
    or p_turn ->> 'caseId' is distinct from p_case_id::text
    or p_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_turn ->> 'turnVersion')::bigint is distinct from p_expected_version + 1
    or p_turn ->> 'status' is distinct from 'completed'
    or p_turn #>> '{candidate,status}' is distinct from 'confirmed'
    or p_turn #>> '{candidate,representativeTime}' is distinct from v_time
    or p_turn #>> '{technicalReceipt,calculationVersion}'
      is distinct from p_calculation_version
    or nullif(p_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(v_case.pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_turn, '$.**.systemPrompt') then
    raise exception 'conversational_candidate_changed' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_turns (
    case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    p_case_id, p_expected_version + 1, p_turn ->> 'narrative',
    p_turn -> 'candidate', p_turn -> 'technicalReceipt',
    nullif(p_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );
  update public.birth_time_rectification_cases
  set status = 'completed',
      turn_version = p_expected_version + 1,
      turn_state = p_turn,
      journey_snapshot = p_turn,
      confirmed_time = p_time,
      confirmed_at = pg_catalog.now(),
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id
    and turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  update public.profiles
  set active_birth_time = p_time,
      birth_time = p_time,
      birth_time_status = 'confirmed',
      rectification_case_id = p_case_id,
      updated_at = pg_catalog.now()
  where id = p_user_id
    and active_birth_time is not distinct from v_case.baseline_active_time;
  if not found then
    raise exception 'conversational_candidate_changed' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'confirm', p_expected_version,
    p_expected_version + 1, v_fingerprint,
    public.conversational_rectification_action_request(
      'confirm', p_user_id, p_case_id, p_expected_version, p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

create or replace function public.import_legacy_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid,
  p_legacy_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_price integer,
  p_pending_consultation_question text,
  p_first_turn jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_legacy public.birth_time_rectification_cases%rowtype;
  v_profile public.profiles%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_declared_birth_input jsonb;
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'import_legacy', 'userId', p_user_id, 'caseId', p_case_id,
      'legacyCaseId', p_legacy_case_id, 'expectedVersion', p_expected_version,
      'actionId', p_action_id, 'price', p_price,
      'pendingConsultationQuestion', p_pending_consultation_question,
      'firstTurn', p_first_turn, 'validationReceipt', p_validation_receipt,
      'privateCandidate', p_private_candidate
    )
  );
begin
  if p_user_id is null or p_case_id is null or p_legacy_case_id is null
    or p_action_id is null or p_case_id is distinct from p_action_id
    or p_expected_version is null or p_expected_version < 0
    or p_price is null or not (p_price between 1 and 1000000) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':conversational-rectification-case',
      0
    )
  );
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );

  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id
  for update;
  if found then
    if v_case.user_id is distinct from p_user_id
      or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
      raise exception 'conversational_case_not_found' using errcode = 'P0001';
    end if;
    select r.* into v_receipt
    from public.birth_time_rectification_action_receipts r
    where r.case_id = p_case_id and r.action_id = p_action_id
    for update;
    if found
      and v_receipt.user_id is not distinct from p_user_id
      and v_receipt.action_kind is not distinct from 'import_legacy'
      and v_receipt.expected_turn_version is not distinct from p_expected_version
      and v_receipt.request_fingerprint is not distinct from v_fingerprint then
      return v_receipt.response;
    end if;
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select legacy.* into v_legacy
  from public.birth_time_rectification_cases legacy
  where legacy.id = p_legacy_case_id and legacy.user_id = p_user_id
  for update;
  if not found
    or v_legacy.journey_protocol not in ('legacy-guided-v1', 'dynamic-choice-v2')
    or v_legacy.status in ('confirmed', 'completed', 'abandoned') then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  if v_legacy.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;
  perform 1
  from public.birth_time_rectification_cases imported
  where imported.user_id = p_user_id
    and imported.imported_from_case_id = p_legacy_case_id
    and imported.journey_protocol = 'conversational-evidence-v3'
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  perform 1
  from public.birth_time_rectification_cases active_case
  where active_case.user_id = p_user_id
    and active_case.id <> p_case_id
    and active_case.id <> p_legacy_case_id
    and active_case.journey_protocol = 'conversational-evidence-v3'
    and active_case.status in ('starting', 'active', 'paused', 'confirming')
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  select profile.* into v_profile
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  -- Preserve an explicit nullable clue while omitting inapplicable time-mode
  -- keys. This yields the same source-discriminated representation accepted
  -- by new starts and keeps legacy import round-trippable across devices.
  v_declared_birth_input := pg_catalog.jsonb_build_object(
    'birthDate', pg_catalog.to_char(v_legacy.reported_date, 'YYYY-MM-DD'),
    'source', v_legacy.source,
    'birthTimeClue', v_profile.birth_time_clue,
    'birthplace', pg_catalog.jsonb_strip_nulls(pg_catalog.jsonb_build_object(
      'countryCode', v_profile.country_code,
      'provinceCode', v_profile.province_code,
      'cityCode', v_profile.city_code,
      'districtCode', v_profile.district_code,
      'latitude', v_profile.latitude,
      'longitude', v_profile.longitude,
      'timezoneOffset', v_profile.timezone_offset
    ))
  );
  if v_legacy.reported_time is not null then
    v_declared_birth_input := v_declared_birth_input || pg_catalog.jsonb_build_object(
      'reportedTime', pg_catalog.to_char(v_legacy.reported_time, 'HH24:MI')
    );
  end if;
  if v_legacy.reported_period is not null then
    v_declared_birth_input := v_declared_birth_input || pg_catalog.jsonb_build_object(
      'reportedPeriod', v_legacy.reported_period
    );
  end if;
  if v_legacy.uncertainty_before_minutes is not null
    or v_legacy.uncertainty_after_minutes is not null then
    v_declared_birth_input := v_declared_birth_input || pg_catalog.jsonb_build_object(
      'uncertaintyBeforeMinutes', v_legacy.uncertainty_before_minutes,
      'uncertaintyAfterMinutes', v_legacy.uncertainty_after_minutes
    );
  end if;
  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.user_id = p_user_id and b.state = 'reserved'
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if public.conversational_rectification_valid_declared_birth_input(
      v_declared_birth_input
    ) is not true
    or public.conversational_rectification_valid_public_turn(p_first_turn) is not true
    or public.conversational_rectification_valid_validation_receipt(
      p_validation_receipt
    ) is not true
    or public.conversational_rectification_valid_private_candidate(
      p_private_candidate
    ) is not true
    or p_first_turn ->> 'caseId' is distinct from p_case_id::text
    or p_first_turn ->> 'journeyProtocol' is distinct from 'conversational-evidence-v3'
    or (p_first_turn ->> 'turnVersion')::bigint is distinct from 0
    or p_first_turn ->> 'status' is distinct from 'active'
    or nullif(p_first_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(p_pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_cases (
    id, user_id, journey_protocol, status, reported_date, reported_time,
    reported_period, source, uncertainty_before_minutes,
    uncertainty_after_minutes, declared_birth_input,
    questionnaire, answers, life_events,
    candidate_scan, journey_snapshot, turn_version, turn_state,
    candidate_result, candidate_result_id, candidate_start, candidate_end,
    event_scoring_version, imported_from_case_id, baseline_active_time,
    pending_consultation_question, updated_at
  ) values (
    p_case_id, p_user_id, 'conversational-evidence-v3', 'active',
    v_legacy.reported_date, v_legacy.reported_time, v_legacy.reported_period,
    v_legacy.source, v_legacy.uncertainty_before_minutes,
    v_legacy.uncertainty_after_minutes, v_declared_birth_input,
    v_legacy.questionnaire,
    v_legacy.answers, v_legacy.life_events, v_legacy.candidate_scan,
    p_first_turn, 0, p_first_turn, p_private_candidate,
    nullif(p_private_candidate ->> 'resultId', '')::uuid,
    nullif(p_private_candidate ->> 'rangeStart', '')::time,
    nullif(p_private_candidate ->> 'rangeEnd', '')::time,
    nullif(p_private_candidate ->> 'calculationVersion', ''),
    p_legacy_case_id, v_profile.active_birth_time,
    nullif(p_pending_consultation_question, ''), pg_catalog.now()
  );
  insert into public.birth_time_rectification_turns (
    case_id, turn_version, narrative, candidate, technical_receipt,
    evidence_request, evidence_recap, actions, output_validation_receipt
  ) values (
    p_case_id, 0, p_first_turn ->> 'narrative', p_first_turn -> 'candidate',
    p_first_turn -> 'technicalReceipt',
    nullif(p_first_turn -> 'evidenceRequest', 'null'::jsonb),
    coalesce(p_first_turn -> 'evidenceRecap', '[]'::jsonb),
    coalesce(p_first_turn -> 'actions', '[]'::jsonb),
    p_validation_receipt
  );

  insert into public.birth_time_rectification_billing (
    case_id, user_id, price, state, billing_receipt_id,
    complete_action_id, balance_after
  ) values (
    p_case_id, p_user_id, p_price, 'migration_waived', pg_catalog.gen_random_uuid(),
    p_action_id, v_profile.credits
  );

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, p_action_id, p_user_id, 'import_legacy', p_expected_version,
    0, v_fingerprint,
    public.conversational_rectification_action_request(
      'import_legacy', p_user_id, p_case_id, p_expected_version,
      p_action_id, v_fingerprint
    ),
    v_response
  );
  return v_response;
end;
$$;

revoke all on function public.conversational_rectification_fingerprint(jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.guard_imported_rectification_history()
  from public, anon, authenticated, service_role;
revoke all on function public.conversational_rectification_case_projection(uuid, uuid)
  from public, anon, authenticated, service_role;

revoke all on function public.load_conversational_rectification_case(uuid, uuid)
  from public, anon, authenticated;
revoke all on function public.create_conversational_rectification_case(
  uuid, uuid, bigint, uuid, uuid, text, jsonb, jsonb, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.save_conversational_rectification_turn(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.pause_conversational_rectification_case(
  uuid, uuid, bigint, uuid, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.abandon_conversational_rectification_case(
  uuid, uuid, bigint, uuid, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.confirm_conversational_rectification_candidate(
  uuid, uuid, bigint, uuid, uuid, time without time zone, text, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.import_legacy_conversational_rectification_case(
  uuid, uuid, uuid, bigint, uuid, integer, text, jsonb, jsonb, jsonb
) from public, anon, authenticated;

grant execute on function public.load_conversational_rectification_case(uuid, uuid)
  to service_role;
grant execute on function public.create_conversational_rectification_case(
  uuid, uuid, bigint, uuid, uuid, text, jsonb, jsonb, jsonb, jsonb
) to service_role;
grant execute on function public.save_conversational_rectification_turn(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb
) to service_role;
grant execute on function public.pause_conversational_rectification_case(
  uuid, uuid, bigint, uuid, jsonb, jsonb
) to service_role;
grant execute on function public.abandon_conversational_rectification_case(
  uuid, uuid, bigint, uuid, jsonb, jsonb
) to service_role;
grant execute on function public.confirm_conversational_rectification_candidate(
  uuid, uuid, bigint, uuid, uuid, time without time zone, text, jsonb, jsonb
) to service_role;
grant execute on function public.import_legacy_conversational_rectification_case(
  uuid, uuid, uuid, bigint, uuid, integer, text, jsonb, jsonb, jsonb
) to service_role;

commit;
