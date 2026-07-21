begin;

create unique index if not exists birth_time_rectification_cases_one_v3_import_per_legacy
  on public.birth_time_rectification_cases (imported_from_case_id)
  where imported_from_case_id is not null
    and journey_protocol = 'conversational-evidence-v3';

create or replace function public.conversational_rectification_project_legacy_event_evidence(
  p_life_events jsonb,
  p_birth_date date,
  p_as_of_date date
)
returns jsonb
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_item jsonb;
  v_id uuid;
  v_domain text;
  v_imported_domain text;
  v_label text;
  v_precision text;
  v_date text;
  v_day date;
  v_seen uuid[] := '{}'::uuid[];
  v_result jsonb := '[]'::jsonb;
begin
  if pg_catalog.jsonb_typeof(p_life_events) is distinct from 'array' then
    return '[]'::jsonb;
  end if;

  for v_item in
    select item.value
    from pg_catalog.jsonb_array_elements(p_life_events) with ordinality item(value, ordinality)
    order by item.ordinality
  loop
    begin
      if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
        or not public.conversational_rectification_has_only_keys(
          v_item, array['id', 'domain', 'precision', 'date']
        )
        or public.conversational_rectification_valid_uuid_text(v_item ->> 'id') is not true then
        continue;
      end if;
      v_id := (v_item ->> 'id')::uuid;
      if v_id = any(v_seen) then continue; end if;
      v_domain := v_item ->> 'domain';
      v_precision := v_item ->> 'precision';
      v_date := v_item ->> 'date';
      if v_domain not in (
          'career', 'education', 'relocation', 'relationship', 'finance', 'health_pressure'
        ) or v_precision not in ('year', 'month', 'day') then
        continue;
      end if;
      if v_precision = 'year' then
        if v_date !~ '^(19|20)[0-9]{2}$'
          or v_date < pg_catalog.to_char(p_birth_date, 'YYYY')
          or v_date > pg_catalog.to_char(p_as_of_date, 'YYYY') then
          continue;
        end if;
      elsif v_precision = 'month' then
        if v_date !~ '^(19|20)[0-9]{2}-(0[1-9]|1[0-2])$'
          or v_date < pg_catalog.to_char(p_birth_date, 'YYYY-MM')
          or v_date > pg_catalog.to_char(p_as_of_date, 'YYYY-MM') then
          continue;
        end if;
      else
        if v_date !~ '^(19|20)[0-9]{2}-(0[1-9]|1[0-2])-([0-2][0-9]|3[01])$' then
          continue;
        end if;
        v_day := v_date::date;
        if pg_catalog.to_char(v_day, 'YYYY-MM-DD') is distinct from v_date
          or v_day < p_birth_date or v_day > p_as_of_date then
          continue;
        end if;
      end if;

      v_imported_domain := case
        when v_domain in ('finance', 'health_pressure') then 'other'
        else v_domain
      end;
      v_label := case v_imported_domain
        when 'career' then '事业'
        when 'education' then '学业'
        when 'relocation' then '迁居'
        when 'relationship' then '关系'
        when 'family' then '家庭'
        else '其他'
      end;
      v_result := v_result || pg_catalog.jsonb_build_array(
        pg_catalog.jsonb_build_object(
          'id', v_id,
          'rawText', '旧校时记录中的' || v_label || '事件（' || v_date || '）',
          'domain', v_imported_domain,
          'eventSummary', '旧校时记录中的' || v_label || '事件',
          'dateValue', v_date,
          'datePrecision', v_precision,
          'extractionStatus', 'clear',
          'scoreable', true,
          'correctsEvidenceIds', '[]'::jsonb
        )
      );
      v_seen := pg_catalog.array_append(v_seen, v_id);
      if pg_catalog.jsonb_array_length(v_result) > 20 then
        v_result := v_result - 0;
      end if;
    exception when others then
      -- Old rows predate the strict v3 evidence contract. An invalid fragment
      -- stays in the immutable source row instead of aborting or becoming fact.
      continue;
    end;
  end loop;
  return v_result;
end;
$$;

drop function if exists public.import_legacy_conversational_rectification_case(
  uuid, uuid, uuid, bigint, uuid, integer, text, jsonb, jsonb, jsonb
);

create or replace function public.import_legacy_conversational_rectification_case(
  p_user_id uuid,
  p_case_id uuid,
  p_legacy_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_price integer,
  p_pending_consultation_question text,
  p_declared_birth_input jsonb,
  p_evidence jsonb,
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
  v_expected_declared jsonb;
  v_expected_evidence jsonb;
  v_expected_recap jsonb;
  v_expected_range_start time without time zone;
  v_expected_range_end time without time zone;
  v_first_turn_id uuid;
  v_response jsonb;
  v_fingerprint text := public.conversational_rectification_fingerprint(
    pg_catalog.jsonb_build_object(
      'kind', 'import_legacy', 'userId', p_user_id, 'caseId', p_case_id,
      'legacyCaseId', p_legacy_case_id, 'expectedVersion', p_expected_version,
      'actionId', p_action_id, 'price', p_price,
      'pendingConsultationQuestion', p_pending_consultation_question,
      'declaredBirthInput', p_declared_birth_input, 'evidence', p_evidence,
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
      p_user_id::text || ':conversational-rectification-case', 0
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
      or v_case.journey_protocol is distinct from 'conversational-evidence-v3'
      or v_case.imported_from_case_id is distinct from p_legacy_case_id then
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
  if exists (
    select 1
    from public.birth_time_rectification_cases imported
    where imported.imported_from_case_id = p_legacy_case_id
      and imported.journey_protocol = 'conversational-evidence-v3'
  ) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if exists (
    select 1
    from public.birth_time_rectification_cases active_case
    where active_case.user_id = p_user_id
      and active_case.id <> p_case_id
      and active_case.id <> p_legacy_case_id
      and active_case.journey_protocol = 'conversational-evidence-v3'
      and active_case.status in ('starting', 'active', 'paused', 'confirming')
  ) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select profile.* into v_profile
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  v_profile.credits := public.recover_conversational_rectification_orphan_reservations(
    p_user_id, null::uuid
  );
  v_expected_declared := pg_catalog.jsonb_build_object(
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
    v_expected_declared := v_expected_declared || pg_catalog.jsonb_build_object(
      'reportedTime', pg_catalog.to_char(v_legacy.reported_time, 'HH24:MI')
    );
  end if;
  if v_legacy.reported_period is not null then
    v_expected_declared := v_expected_declared || pg_catalog.jsonb_build_object(
      'reportedPeriod', v_legacy.reported_period
    );
  end if;
  if v_legacy.uncertainty_before_minutes is not null
    or v_legacy.uncertainty_after_minutes is not null then
    v_expected_declared := v_expected_declared || pg_catalog.jsonb_build_object(
      'uncertaintyBeforeMinutes', v_legacy.uncertainty_before_minutes,
      'uncertaintyAfterMinutes', v_legacy.uncertainty_after_minutes
    );
  end if;
  v_expected_evidence := public.conversational_rectification_project_legacy_event_evidence(
    v_legacy.life_events, v_legacy.reported_date, current_date
  );
  if v_legacy.journey_protocol = 'dynamic-choice-v2'
    and v_legacy.turn_state #>> '{progress,currentRange,startTime}'
      ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
    and v_legacy.turn_state #>> '{progress,currentRange,endTime}'
      ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$' then
    v_expected_range_start := (
      v_legacy.turn_state #>> '{progress,currentRange,startTime}'
    )::time;
    v_expected_range_end := (
      v_legacy.turn_state #>> '{progress,currentRange,endTime}'
    )::time;
  elsif v_legacy.candidate_start is not null and v_legacy.candidate_end is not null then
    v_expected_range_start := v_legacy.candidate_start;
    v_expected_range_end := v_legacy.candidate_end;
  end if;
  select coalesce(pg_catalog.jsonb_agg(
    pg_catalog.jsonb_build_object(
      'id', item.value ->> 'id',
      'summary', item.value ->> 'eventSummary',
      'dateLabel', item.value ->> 'dateValue'
    ) order by item.ordinality
  ), '[]'::jsonb) into v_expected_recap
  from pg_catalog.jsonb_array_elements(v_expected_evidence)
    with ordinality item(value, ordinality);

  if p_declared_birth_input is distinct from v_expected_declared
    or p_evidence is distinct from v_expected_evidence
    or public.conversational_rectification_valid_declared_birth_input(
      p_declared_birth_input
    ) is not true
    or public.conversational_rectification_valid_life_event_evidence_array(
      p_evidence
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
    or p_first_turn ->> 'status' not in ('active', 'confirming')
    or p_first_turn -> 'evidenceRecap' is distinct from v_expected_recap
    or p_first_turn -> 'candidate' ->> 'rangeStart'
      is distinct from p_private_candidate ->> 'rangeStart'
    or p_first_turn -> 'candidate' ->> 'rangeEnd'
      is distinct from p_private_candidate ->> 'rangeEnd'
    or (v_expected_range_start is not null and (
      nullif(p_private_candidate ->> 'rangeStart', '')::time
        is distinct from v_expected_range_start
      or nullif(p_private_candidate ->> 'rangeEnd', '')::time
        is distinct from v_expected_range_end
    ))
    or nullif(p_first_turn ->> 'pendingConsultationQuestion', '')
      is distinct from nullif(p_pending_consultation_question, '')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateWeights')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.candidateScores')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.partitionId')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.rawModelOutput')
    or pg_catalog.jsonb_path_exists(p_first_turn, '$.**.systemPrompt') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if exists (
    select 1 from public.birth_time_rectification_billing b
    where b.user_id = p_user_id and b.state = 'reserved'
    for update
  ) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_cases (
    id, user_id, journey_protocol, status, reported_date, reported_time,
    reported_period, source, uncertainty_before_minutes,
    uncertainty_after_minutes, declared_birth_input,
    questionnaire, answers, life_events, candidate_scan,
    journey_snapshot, turn_version, turn_state,
    candidate_result, candidate_result_id, candidate_start, candidate_end,
    event_scoring_version, imported_from_case_id, baseline_active_time,
    pending_consultation_question, updated_at
  ) values (
    p_case_id, p_user_id, 'conversational-evidence-v3',
    p_first_turn ->> 'status', v_legacy.reported_date, v_legacy.reported_time,
    v_legacy.reported_period, v_legacy.source, v_legacy.uncertainty_before_minutes,
    v_legacy.uncertainty_after_minutes, p_declared_birth_input,
    '{}'::jsonb, '{}'::jsonb, '[]'::jsonb, '{}'::jsonb,
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
    p_first_turn -> 'evidenceRecap', p_first_turn -> 'actions', p_validation_receipt
  ) returning id into v_first_turn_id;
  insert into public.birth_time_rectification_event_evidence (
    id, case_id, source_turn_id, raw_text, domain, event_summary,
    date_value, date_precision, extraction_status, scoreable,
    corrects_evidence_ids
  )
  select (item ->> 'id')::uuid, p_case_id, v_first_turn_id,
    item ->> 'rawText', item ->> 'domain', item ->> 'eventSummary',
    nullif(item ->> 'dateValue', ''), item ->> 'datePrecision',
    item ->> 'extractionStatus', (item ->> 'scoreable')::boolean,
    array(select value::uuid from pg_catalog.jsonb_array_elements_text(
      coalesce(item -> 'correctsEvidenceIds', '[]'::jsonb)
    ) correction(value))
  from pg_catalog.jsonb_array_elements(p_evidence) evidence(item);
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

revoke all on function public.conversational_rectification_project_legacy_event_evidence(
  jsonb, date, date
) from public, anon, authenticated, service_role;
revoke all on function public.import_legacy_conversational_rectification_case(
  uuid, uuid, uuid, bigint, uuid, integer, text, jsonb, jsonb, jsonb, jsonb, jsonb
) from public, anon, authenticated;
grant execute on function public.import_legacy_conversational_rectification_case(
  uuid, uuid, uuid, bigint, uuid, integer, text, jsonb, jsonb, jsonb, jsonb, jsonb
) to service_role;

commit;
