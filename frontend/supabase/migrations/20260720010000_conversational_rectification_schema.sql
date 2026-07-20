begin;

create or replace function public.conversational_rectification_has_only_keys(
  p_value jsonb,
  p_allowed text[]
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'object'
    and not exists (
      select 1
      from pg_catalog.jsonb_object_keys(p_value) key
      where not (key = any (p_allowed))
    );
$$;

create or replace function public.conversational_rectification_valid_time_text(p_value text)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select p_value ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$';
$$;

create or replace function public.conversational_rectification_valid_date_text(p_value text)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  return p_value ~ '^[1-9][0-9]{3}-[0-9]{2}-[0-9]{2}$'
    and pg_catalog.to_char(p_value::date, 'YYYY-MM-DD') = p_value;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_uuid_text(p_value text)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  if p_value !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
    return false;
  end if;
  perform p_value::uuid;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_text_utf16_length(
  p_value text
)
returns integer
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.char_length(p_value) + (
    select pg_catalog.count(*)::integer
    from pg_catalog.generate_series(
      1, pg_catalog.char_length(p_value)
    ) character_positions(character_index)
    where pg_catalog.octet_length(
      pg_catalog.substr(p_value, character_index, 1)
    ) = 4
  );
$$;

create or replace function public.conversational_rectification_text_is_nonblank(
  p_value text
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.btrim(
    p_value,
    U&'\0009\000A\000B\000C\000D\0020\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000\FEFF'
  ) <> '';
$$;

create or replace function public.conversational_rectification_numbers_are_stable(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_item jsonb;
  v_number numeric;
begin
  if pg_catalog.jsonb_typeof(p_value) = 'number' then
    v_number := (p_value #>> '{}')::numeric;
    if v_number = pg_catalog.trunc(v_number) then
      return pg_catalog.abs(v_number) <= 9007199254740991;
    end if;
    return pg_catalog.abs(v_number) between 0.000001 and 1000000
      and v_number = pg_catalog.trunc(v_number, 6);
  elsif pg_catalog.jsonb_typeof(p_value) = 'array' then
    for v_item in select value from pg_catalog.jsonb_array_elements(p_value) loop
      if public.conversational_rectification_numbers_are_stable(v_item) is not true then
        return false;
      end if;
    end loop;
  elsif pg_catalog.jsonb_typeof(p_value) = 'object' then
    for v_item in select value from pg_catalog.jsonb_each(p_value) loop
      if public.conversational_rectification_numbers_are_stable(v_item) is not true then
        return false;
      end if;
    end loop;
  end if;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_text_array_is_bounded(
  p_value jsonb,
  p_max_items integer,
  p_max_characters integer,
  p_max_bytes integer
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'array'
    and pg_catalog.jsonb_array_length(p_value) <= p_max_items
    and pg_catalog.octet_length(p_value::text) <= p_max_bytes
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(p_value) item
      where pg_catalog.jsonb_typeof(item) is distinct from 'string'
        or public.conversational_rectification_text_utf16_length(
          item #>> '{}'
        ) not between 1 and p_max_characters
        or public.conversational_rectification_text_is_nonblank(item #>> '{}') is not true
    );
$$;

create or replace function public.conversational_rectification_valid_candidate(p_value jsonb)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_key text;
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'object'
    or pg_catalog.octet_length(p_value::text) > 512
    or public.conversational_rectification_numbers_are_stable(p_value) is not true
    or not public.conversational_rectification_has_only_keys(
      p_value,
      array['status', 'representativeTime', 'rangeStart', 'rangeEnd']::text[]
    )
    or not (p_value ?& array['status', 'representativeTime', 'rangeStart', 'rangeEnd']::text[])
    or pg_catalog.jsonb_typeof(p_value -> 'status') is distinct from 'string'
    or p_value ->> 'status' not in (
      'declared', 'pending_validation', 'ready_for_confirmation', 'confirmed'
    ) then
    return false;
  end if;
  foreach v_key in array array['representativeTime', 'rangeStart', 'rangeEnd']::text[] loop
    if p_value -> v_key <> 'null'::jsonb
      and (
        pg_catalog.jsonb_typeof(p_value -> v_key) is distinct from 'string'
        or not public.conversational_rectification_valid_time_text(p_value ->> v_key)
      ) then
      return false;
    end if;
  end loop;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_technical_receipt(
  p_value jsonb
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'object'
    and pg_catalog.octet_length(p_value::text) <= 8192
    and public.conversational_rectification_numbers_are_stable(p_value)
    and public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'calculationVersion', 'stableLayers', 'sensitiveLayers',
        'candidateDifferenceRefs'
      ]::text[]
    )
    and p_value ?& array[
      'calculationVersion', 'stableLayers', 'sensitiveLayers',
      'candidateDifferenceRefs'
    ]::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'calculationVersion') = 'string'
    and public.conversational_rectification_text_utf16_length(
      p_value ->> 'calculationVersion'
    ) between 1 and 80
    and public.conversational_rectification_text_is_nonblank(
      p_value ->> 'calculationVersion'
    )
    and public.conversational_rectification_text_array_is_bounded(
      p_value -> 'stableLayers', 20, 80, 4096
    )
    and public.conversational_rectification_text_array_is_bounded(
      p_value -> 'sensitiveLayers', 20, 80, 4096
    )
    and public.conversational_rectification_text_array_is_bounded(
      p_value -> 'candidateDifferenceRefs', 40, 120, 8192
    );
$$;

create or replace function public.conversational_rectification_valid_evidence_request(
  p_value jsonb
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'object'
    and pg_catalog.octet_length(p_value::text) <= 2048
    and public.conversational_rectification_numbers_are_stable(p_value)
    and public.conversational_rectification_has_only_keys(
      p_value,
      array['domains', 'datePrecision', 'freeTextAllowed']::text[]
    )
    and p_value ?& array['domains', 'datePrecision', 'freeTextAllowed']::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'domains') = 'array'
    and pg_catalog.jsonb_array_length(p_value -> 'domains') between 2 and 4
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(p_value -> 'domains') domain
      where pg_catalog.jsonb_typeof(domain) is distinct from 'string'
        or domain #>> '{}' not in (
          'career', 'education', 'relocation', 'relationship', 'family', 'other'
        )
    )
    and pg_catalog.jsonb_typeof(p_value -> 'datePrecision') = 'string'
    and p_value ->> 'datePrecision' in ('month_preferred', 'year_accepted')
    and pg_catalog.jsonb_typeof(p_value -> 'freeTextAllowed') = 'boolean'
    and p_value -> 'freeTextAllowed' = 'true'::jsonb;
$$;

create or replace function public.conversational_rectification_valid_evidence_recap(
  p_value jsonb
)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'array'
    and pg_catalog.octet_length(p_value::text) <= 24576
    and public.conversational_rectification_numbers_are_stable(p_value)
    and pg_catalog.jsonb_array_length(p_value) <= 20
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(p_value) item
      where pg_catalog.jsonb_typeof(item) <> 'object'
        or pg_catalog.octet_length(item::text) > 4096
        or not public.conversational_rectification_has_only_keys(
          item, array['id', 'summary', 'dateLabel']::text[]
        )
        or not (item ?& array['id', 'summary', 'dateLabel']::text[])
        or pg_catalog.jsonb_typeof(item -> 'id') <> 'string'
        or not public.conversational_rectification_valid_uuid_text(item ->> 'id')
        or pg_catalog.jsonb_typeof(item -> 'summary') <> 'string'
        or public.conversational_rectification_text_utf16_length(
          item ->> 'summary'
        ) not between 1 and 1000
        or public.conversational_rectification_text_is_nonblank(
          item ->> 'summary'
        ) is not true
        or pg_catalog.jsonb_typeof(item -> 'dateLabel') <> 'string'
        or public.conversational_rectification_text_utf16_length(
          item ->> 'dateLabel'
        ) not between 1 and 80
        or public.conversational_rectification_text_is_nonblank(
          item ->> 'dateLabel'
        ) is not true
    );
$$;

create or replace function public.conversational_rectification_valid_actions(p_value jsonb)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'array'
    and pg_catalog.octet_length(p_value::text) <= 512
    and public.conversational_rectification_numbers_are_stable(p_value)
    and pg_catalog.jsonb_array_length(p_value) <= 5
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(p_value) action
      where pg_catalog.jsonb_typeof(action) is distinct from 'string'
        or action #>> '{}' not in (
        'answer', 'pause', 'abandon', 'confirm', 'continue_original_question'
      )
    );
$$;

create or replace function public.conversational_rectification_valid_validation_receipt(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'object'
    or pg_catalog.octet_length(p_value::text) > 8192
    or public.conversational_rectification_numbers_are_stable(p_value) is not true
    or not public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'modelId', 'schemaValidated', 'validatorVersion', 'validatedAt',
        'retryCount', 'fallbackUsed', 'issues'
      ]::text[]
    )
    or not (p_value ?& array['modelId', 'schemaValidated']::text[])
    or pg_catalog.jsonb_typeof(p_value -> 'modelId') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'modelId'
    ) not between 1 and 120
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'modelId'
    ) is not true
    or pg_catalog.jsonb_typeof(p_value -> 'schemaValidated') is distinct from 'boolean' then
    return false;
  end if;
  if p_value ? 'validatorVersion' and (
    pg_catalog.jsonb_typeof(p_value -> 'validatorVersion') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'validatorVersion'
    ) not between 1 and 80
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'validatorVersion'
    ) is not true
  ) then return false; end if;
  if p_value ? 'validatedAt' and (
    pg_catalog.jsonb_typeof(p_value -> 'validatedAt') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'validatedAt'
    ) not between 20 and 40
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'validatedAt'
    ) is not true
    or p_value ->> 'validatedAt' !~
      '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$'
    or (p_value ->> 'validatedAt')::timestamptz is null
  ) then return false; end if;
  if p_value ? 'retryCount' and (
    pg_catalog.jsonb_typeof(p_value -> 'retryCount') is distinct from 'number'
    or p_value ->> 'retryCount' !~ '^[0-9]+$'
    or (p_value ->> 'retryCount')::integer not between 0 and 2
  ) then return false; end if;
  if p_value ? 'fallbackUsed'
    and pg_catalog.jsonb_typeof(p_value -> 'fallbackUsed') is distinct from 'boolean' then
    return false;
  end if;
  if p_value ? 'issues' and not public.conversational_rectification_text_array_is_bounded(
    p_value -> 'issues', 20, 240, 8192
  ) then return false; end if;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_life_event_evidence(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'object'
    or pg_catalog.octet_length(p_value::text) > 16384
    or public.conversational_rectification_numbers_are_stable(p_value) is not true
    or not public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'id', 'rawText', 'domain', 'eventSummary', 'dateValue',
        'datePrecision', 'extractionStatus', 'scoreable'
      ]::text[]
    )
    or not (p_value ?& array[
      'id', 'rawText', 'domain', 'eventSummary', 'dateValue',
      'datePrecision', 'extractionStatus'
    ]::text[])
    or pg_catalog.jsonb_typeof(p_value -> 'id') is distinct from 'string'
    or not public.conversational_rectification_valid_uuid_text(p_value ->> 'id')
    or p_value ->> 'id' !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    or pg_catalog.jsonb_typeof(p_value -> 'rawText') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'rawText'
    ) not between 1 and 4000
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'rawText'
    ) is not true
    or pg_catalog.jsonb_typeof(p_value -> 'domain') is distinct from 'string'
    or p_value ->> 'domain' not in (
      'career', 'education', 'relocation', 'relationship', 'family', 'other'
    )
    or pg_catalog.jsonb_typeof(p_value -> 'eventSummary') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'eventSummary'
    ) not between 1 and 1000
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'eventSummary'
    ) is not true
    or not (p_value ? 'dateValue')
    or (
      p_value -> 'dateValue' <> 'null'::jsonb
      and (
        pg_catalog.jsonb_typeof(p_value -> 'dateValue') is distinct from 'string'
        or public.conversational_rectification_text_utf16_length(
          p_value ->> 'dateValue'
        ) not between 1 and 80
        or public.conversational_rectification_text_is_nonblank(
          p_value ->> 'dateValue'
        ) is not true
      )
    )
    or pg_catalog.jsonb_typeof(p_value -> 'datePrecision') is distinct from 'string'
    or p_value ->> 'datePrecision' not in ('day', 'month', 'year', 'range', 'unknown')
    or pg_catalog.jsonb_typeof(p_value -> 'extractionStatus') is distinct from 'string'
    or p_value ->> 'extractionStatus' not in (
      'clear', 'needs_clarification', 'corrected'
    )
    or (
      p_value ? 'scoreable'
      and pg_catalog.jsonb_typeof(p_value -> 'scoreable') is distinct from 'boolean'
    ) then
    return false;
  end if;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_life_event_evidence_array(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_item jsonb;
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'array'
    or pg_catalog.jsonb_array_length(p_value) > 20 then
    return false;
  end if;
  for v_item in select value from pg_catalog.jsonb_array_elements(p_value) loop
    if public.conversational_rectification_valid_life_event_evidence(v_item) is not true then
      return false;
    end if;
  end loop;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_private_candidate(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_item jsonb;
  v_key text;
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'object'
    or pg_catalog.octet_length(p_value::text) > 65536
    or public.conversational_rectification_numbers_are_stable(p_value) is not true
    or not public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'resultId', 'representativeTime', 'rangeStart', 'rangeEnd',
        'calculationVersion', 'candidateWeights', 'candidateModelRefs',
        'd1Stability', 'boundaryDistanceMinutes', 'supportedSensitiveLayers',
        'scoredHistoricalEvidence', 'suggestedDomains', 'futureWindows', 'workingState'
      ]::text[]
    )
    or not (p_value ? 'calculationVersion')
    or pg_catalog.jsonb_typeof(p_value -> 'calculationVersion') is distinct from 'string'
    or public.conversational_rectification_text_utf16_length(
      p_value ->> 'calculationVersion'
    ) not between 1 and 80
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'calculationVersion'
    ) is not true then
    return false;
  end if;
  if p_value ? 'resultId' and p_value -> 'resultId' <> 'null'::jsonb and (
    pg_catalog.jsonb_typeof(p_value -> 'resultId') is distinct from 'string'
    or not public.conversational_rectification_valid_uuid_text(p_value ->> 'resultId')
  ) then return false; end if;
  foreach v_key in array array['representativeTime', 'rangeStart', 'rangeEnd']::text[] loop
    if p_value ? v_key and p_value -> v_key <> 'null'::jsonb and (
      pg_catalog.jsonb_typeof(p_value -> v_key) is distinct from 'string'
      or not public.conversational_rectification_valid_time_text(p_value ->> v_key)
    ) then return false; end if;
  end loop;
  if (p_value ? 'rangeStart') <> (p_value ? 'rangeEnd')
    or (p_value -> 'rangeStart' = 'null'::jsonb) <> (p_value -> 'rangeEnd' = 'null'::jsonb) then
    return false;
  end if;
  if p_value ? 'candidateWeights' and (
    pg_catalog.jsonb_typeof(p_value -> 'candidateWeights') is distinct from 'array'
    or pg_catalog.jsonb_array_length(p_value -> 'candidateWeights') > 1440
    or exists (
      select 1 from pg_catalog.jsonb_array_elements(p_value -> 'candidateWeights') weight
      where pg_catalog.jsonb_typeof(weight) <> 'number'
        or (weight #>> '{}')::numeric not between 0 and 1
    )
  ) then return false; end if;
  if p_value ? 'candidateModelRefs' and not public.conversational_rectification_text_array_is_bounded(
    p_value -> 'candidateModelRefs', 80, 120, 16384
  ) then return false; end if;
  if p_value ? 'supportedSensitiveLayers' and not public.conversational_rectification_text_array_is_bounded(
    p_value -> 'supportedSensitiveLayers', 40, 80, 8192
  ) then return false; end if;
  if p_value ? 'd1Stability' and p_value ->> 'd1Stability' not in (
    'stable', 'sensitive', 'unavailable'
  ) then return false; end if;
  if p_value ? 'd1Stability'
    and pg_catalog.jsonb_typeof(p_value -> 'd1Stability') is distinct from 'string' then
    return false;
  end if;
  if p_value ? 'boundaryDistanceMinutes' and p_value -> 'boundaryDistanceMinutes' <> 'null'::jsonb and (
    pg_catalog.jsonb_typeof(p_value -> 'boundaryDistanceMinutes') is distinct from 'number'
    or p_value ->> 'boundaryDistanceMinutes' !~ '^[0-9]+$'
    or (p_value ->> 'boundaryDistanceMinutes')::integer not between 0 and 1440
  ) then return false; end if;
  if p_value ? 'suggestedDomains' and (
    pg_catalog.jsonb_typeof(p_value -> 'suggestedDomains') is distinct from 'array'
    or pg_catalog.jsonb_array_length(p_value -> 'suggestedDomains') > 6
    or exists (
      select 1 from pg_catalog.jsonb_array_elements(p_value -> 'suggestedDomains') domain
      where pg_catalog.jsonb_typeof(domain) is distinct from 'string'
        or domain #>> '{}' not in (
          'career', 'education', 'relocation', 'relationship', 'family', 'other'
        )
    )
  ) then return false; end if;
  if p_value ? 'scoredHistoricalEvidence' then
    if pg_catalog.jsonb_typeof(p_value -> 'scoredHistoricalEvidence') is distinct from 'array'
      or pg_catalog.jsonb_array_length(p_value -> 'scoredHistoricalEvidence') > 100 then
      return false;
    end if;
    for v_item in select value from pg_catalog.jsonb_array_elements(p_value -> 'scoredHistoricalEvidence') loop
      if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
        or pg_catalog.octet_length(v_item::text) > 8192
        or not public.conversational_rectification_has_only_keys(
          v_item, array['evidenceId', 'domain', 'candidateTime', 'score', 'ruleRefs']::text[]
        )
        or not (v_item ?& array['evidenceId', 'domain', 'candidateTime', 'score', 'ruleRefs']::text[])
        or pg_catalog.jsonb_typeof(v_item -> 'evidenceId') is distinct from 'string'
        or not public.conversational_rectification_valid_uuid_text(v_item ->> 'evidenceId')
        or pg_catalog.jsonb_typeof(v_item -> 'domain') is distinct from 'string'
        or v_item ->> 'domain' not in ('career', 'education', 'relocation', 'relationship', 'family', 'other')
        or (v_item -> 'candidateTime' <> 'null'::jsonb and (
          pg_catalog.jsonb_typeof(v_item -> 'candidateTime') is distinct from 'string'
          or not public.conversational_rectification_valid_time_text(v_item ->> 'candidateTime')
        ))
        or pg_catalog.jsonb_typeof(v_item -> 'score') is distinct from 'number'
        or (v_item ->> 'score')::numeric not between -1000000 and 1000000
        or not public.conversational_rectification_text_array_is_bounded(
          v_item -> 'ruleRefs', 40, 120, 8192
        ) then return false; end if;
    end loop;
  end if;
  if p_value ? 'futureWindows' then
    if pg_catalog.jsonb_typeof(p_value -> 'futureWindows') is distinct from 'array'
      or pg_catalog.jsonb_array_length(p_value -> 'futureWindows') > 20 then return false; end if;
    for v_item in select value from pg_catalog.jsonb_array_elements(p_value -> 'futureWindows') loop
      if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
        or pg_catalog.octet_length(v_item::text) > 2048
        or not public.conversational_rectification_has_only_keys(
          v_item, array['label', 'startDate', 'endDate', 'scoreable']::text[]
        )
        or not (v_item ?& array['label', 'startDate', 'endDate', 'scoreable']::text[])
        or pg_catalog.jsonb_typeof(v_item -> 'label') is distinct from 'string'
        or public.conversational_rectification_text_utf16_length(
          v_item ->> 'label'
        ) not between 1 and 240
        or public.conversational_rectification_text_is_nonblank(
          v_item ->> 'label'
        ) is not true
        or pg_catalog.jsonb_typeof(v_item -> 'startDate') is distinct from 'string'
        or pg_catalog.jsonb_typeof(v_item -> 'endDate') is distinct from 'string'
        or not public.conversational_rectification_valid_date_text(v_item ->> 'startDate')
        or not public.conversational_rectification_valid_date_text(v_item ->> 'endDate')
        or v_item ->> 'startDate' > v_item ->> 'endDate'
        or v_item -> 'scoreable' <> 'false'::jsonb then return false; end if;
    end loop;
  end if;
  if p_value ? 'workingState' then
    v_item := p_value -> 'workingState';
    if pg_catalog.jsonb_typeof(v_item) is distinct from 'object'
      or pg_catalog.octet_length(v_item::text) > 8192
      or not public.conversational_rectification_has_only_keys(
        v_item, array['phase', 'iteration', 'notes']::text[]
      )
      or not (v_item ?& array['phase', 'iteration', 'notes']::text[])
      or pg_catalog.jsonb_typeof(v_item -> 'phase') is distinct from 'string'
      or v_item ->> 'phase' not in ('initial', 'collecting_evidence', 'rescoring', 'ready', 'confirmed')
      or pg_catalog.jsonb_typeof(v_item -> 'iteration') is distinct from 'number'
      or v_item ->> 'iteration' !~ '^[0-9]+$'
      or (v_item ->> 'iteration')::integer not between 0 and 100
      or not public.conversational_rectification_text_array_is_bounded(
        v_item -> 'notes', 20, 240, 8192
      ) then return false; end if;
  end if;
  return true;
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_declared_birth_input(
  p_value jsonb
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  v_place jsonb;
  v_source text;
  v_key text;
  v_before integer;
  v_after integer;
begin
  if pg_catalog.jsonb_typeof(p_value) is distinct from 'object'
    or pg_catalog.octet_length(p_value::text) > 12000
    or public.conversational_rectification_numbers_are_stable(p_value) is not true
    or not public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'birthDate', 'source', 'birthTimeClue', 'birthplace', 'reportedTime',
        'reportedPeriod', 'uncertaintyBeforeMinutes', 'uncertaintyAfterMinutes'
      ]::text[]
    )
    or not (p_value ?& array['birthDate', 'source', 'birthTimeClue', 'birthplace']::text[])
    or pg_catalog.jsonb_typeof(p_value -> 'birthDate') is distinct from 'string'
    or not public.conversational_rectification_valid_date_text(p_value ->> 'birthDate')
    or pg_catalog.jsonb_typeof(p_value -> 'source') is distinct from 'string'
    or public.conversational_rectification_text_is_nonblank(
      p_value ->> 'source'
    ) is not true
    or p_value -> 'birthTimeClue' <> 'null'::jsonb and (
      pg_catalog.jsonb_typeof(p_value -> 'birthTimeClue') is distinct from 'string'
      or public.conversational_rectification_text_utf16_length(
        p_value ->> 'birthTimeClue'
      ) not between 1 and 240
      or public.conversational_rectification_text_is_nonblank(
        p_value ->> 'birthTimeClue'
      ) is not true
    ) then return false; end if;

  v_place := p_value -> 'birthplace';
  if pg_catalog.jsonb_typeof(v_place) is distinct from 'object'
    or pg_catalog.octet_length(v_place::text) > 4096
    or not public.conversational_rectification_has_only_keys(
      v_place,
      array[
        'city', 'countryCode', 'provinceCode', 'cityCode', 'districtCode',
        'latitude', 'longitude', 'timezoneOffset'
      ]::text[]
    )
    or not (v_place ? 'timezoneOffset')
    or not ((v_place ? 'city') or (v_place ? 'cityCode'))
    or pg_catalog.jsonb_typeof(v_place -> 'timezoneOffset') is distinct from 'number'
    or (v_place ->> 'timezoneOffset')::numeric not between -12 and 14
    or (v_place ? 'latitude') <> (v_place ? 'longitude') then return false; end if;
  foreach v_key in array array['city', 'provinceCode', 'cityCode', 'districtCode']::text[] loop
    if v_place ? v_key and (
      pg_catalog.jsonb_typeof(v_place -> v_key) is distinct from 'string'
      or public.conversational_rectification_text_utf16_length(
        v_place ->> v_key
      ) not between 1 and
        case when v_key = 'city' then 120 else 80 end
      or public.conversational_rectification_text_is_nonblank(
        v_place ->> v_key
      ) is not true
    ) then return false; end if;
  end loop;
  if v_place ? 'countryCode' and (
    pg_catalog.jsonb_typeof(v_place -> 'countryCode') is distinct from 'string'
    or v_place ->> 'countryCode' !~ '^[A-Z0-9-]{1,8}$'
  ) then return false; end if;
  if v_place ? 'latitude' and (
    pg_catalog.jsonb_typeof(v_place -> 'latitude') is distinct from 'number'
    or pg_catalog.jsonb_typeof(v_place -> 'longitude') is distinct from 'number'
    or (v_place ->> 'latitude')::numeric not between -90 and 90
    or (v_place ->> 'longitude')::numeric not between -180 and 180
  ) then return false; end if;

  v_source := p_value ->> 'source';
  if v_source not in (
    'hospital_record', 'family_exact', 'approximate', 'period_only', 'unknown', 'legacy_import'
  ) then return false; end if;
  if p_value ? 'reportedTime' and (
    pg_catalog.jsonb_typeof(p_value -> 'reportedTime') is distinct from 'string'
    or not public.conversational_rectification_valid_time_text(p_value ->> 'reportedTime')
  ) then return false; end if;
  if p_value ? 'reportedPeriod' and (
    pg_catalog.jsonb_typeof(p_value -> 'reportedPeriod') is distinct from 'string'
    or p_value ->> 'reportedPeriod' not in (
      'early_morning', 'morning', 'afternoon', 'evening', 'late_night'
    )
  ) then return false; end if;
  if p_value ? 'uncertaintyBeforeMinutes' then
    if pg_catalog.jsonb_typeof(p_value -> 'uncertaintyBeforeMinutes') is distinct from 'number'
      or pg_catalog.jsonb_typeof(p_value -> 'uncertaintyAfterMinutes') is distinct from 'number'
      or p_value ->> 'uncertaintyBeforeMinutes' !~ '^[0-9]+$'
      or p_value ->> 'uncertaintyAfterMinutes' !~ '^[0-9]+$' then
      return false;
    end if;
    v_before := (p_value ->> 'uncertaintyBeforeMinutes')::integer;
    v_after := (p_value ->> 'uncertaintyAfterMinutes')::integer;
  elsif p_value ? 'uncertaintyAfterMinutes' then
    return false;
  end if;

  if v_source = 'hospital_record' then
    return p_value ? 'reportedTime'
      and not (p_value ? 'reportedPeriod')
      and v_before = 2 and v_after = 2;
  elsif v_source = 'family_exact' then
    return p_value ? 'reportedTime'
      and not (p_value ? 'reportedPeriod')
      and v_before = v_after and v_before in (5, 10, 15);
  elsif v_source = 'approximate' then
    return p_value ? 'reportedTime'
      and not (p_value ? 'reportedPeriod')
      and v_before = v_after and v_before in (15, 30, 60);
  elsif v_source = 'period_only' then
    return p_value ? 'reportedPeriod'
      and not (p_value ? 'reportedTime')
      and not (p_value ? 'uncertaintyBeforeMinutes')
      and not (p_value ? 'uncertaintyAfterMinutes');
  elsif v_source = 'unknown' then
    return not (p_value ? 'reportedPeriod')
      and not (p_value ? 'reportedTime')
      and not (p_value ? 'uncertaintyBeforeMinutes')
      and not (p_value ? 'uncertaintyAfterMinutes');
  end if;
  return not ((p_value ? 'reportedTime') and (p_value ? 'reportedPeriod'))
    and ((p_value ? 'reportedTime') or v_before is null)
    and (v_before is null or (v_before between 0 and 720 and v_after between 0 and 720));
exception when others then
  return false;
end;
$$;

create or replace function public.conversational_rectification_valid_public_turn(p_value jsonb)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'object'
    and pg_catalog.octet_length(p_value::text) <= 65536
    and public.conversational_rectification_numbers_are_stable(p_value)
    and public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'caseId', 'journeyProtocol', 'status', 'turnVersion', 'narrative',
        'candidate', 'technicalReceipt', 'evidenceRequest', 'evidenceRecap',
        'actions', 'pendingConsultationQuestion'
      ]::text[]
    )
    and p_value ?& array[
      'caseId', 'journeyProtocol', 'status', 'turnVersion', 'narrative',
      'candidate', 'technicalReceipt', 'evidenceRequest', 'evidenceRecap',
      'actions', 'pendingConsultationQuestion'
    ]::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'caseId') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'caseId')
    and pg_catalog.jsonb_typeof(p_value -> 'journeyProtocol') = 'string'
    and p_value ->> 'journeyProtocol' = 'conversational-evidence-v3'
    and pg_catalog.jsonb_typeof(p_value -> 'status') = 'string'
    and p_value ->> 'status' in ('active', 'paused', 'confirming', 'completed', 'abandoned')
    and pg_catalog.jsonb_typeof(p_value -> 'turnVersion') = 'number'
    and p_value ->> 'turnVersion' ~ '^[0-9]+$'
    and pg_catalog.jsonb_typeof(p_value -> 'narrative') = 'string'
    and public.conversational_rectification_text_utf16_length(
      p_value ->> 'narrative'
    ) between 1 and 12000
    and public.conversational_rectification_text_is_nonblank(
      p_value ->> 'narrative'
    )
    and public.conversational_rectification_valid_candidate(p_value -> 'candidate')
    and public.conversational_rectification_valid_technical_receipt(p_value -> 'technicalReceipt')
    and (
      p_value -> 'evidenceRequest' = 'null'::jsonb
      or public.conversational_rectification_valid_evidence_request(p_value -> 'evidenceRequest')
    )
    and public.conversational_rectification_valid_evidence_recap(p_value -> 'evidenceRecap')
    and public.conversational_rectification_valid_actions(p_value -> 'actions')
    and (
      p_value -> 'pendingConsultationQuestion' = 'null'::jsonb
      or (
        pg_catalog.jsonb_typeof(p_value -> 'pendingConsultationQuestion') = 'string'
        and public.conversational_rectification_text_utf16_length(
          p_value ->> 'pendingConsultationQuestion'
        ) between 1 and 500
        and public.conversational_rectification_text_is_nonblank(
          p_value ->> 'pendingConsultationQuestion'
        )
      )
    );
$$;

create or replace function public.conversational_rectification_valid_action_request(p_value jsonb)
returns boolean
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_typeof(p_value) = 'object'
    and pg_catalog.octet_length(p_value::text) <= 2048
    and public.conversational_rectification_numbers_are_stable(p_value)
    and public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'kind', 'userId', 'caseId', 'expectedVersion', 'actionId', 'requestFingerprint'
      ]::text[]
    )
    and p_value ?& array[
      'kind', 'userId', 'caseId', 'expectedVersion', 'actionId', 'requestFingerprint'
    ]::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'kind') = 'string'
    and p_value ->> 'kind' in (
      'create', 'save_turn', 'pause', 'abandon', 'confirm', 'import_legacy',
      'reserve_fee', 'complete_fee', 'release_fee', 'recover_fee'
    )
    and pg_catalog.jsonb_typeof(p_value -> 'userId') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'userId')
    and pg_catalog.jsonb_typeof(p_value -> 'caseId') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'caseId')
    and pg_catalog.jsonb_typeof(p_value -> 'actionId') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'actionId')
    and pg_catalog.jsonb_typeof(p_value -> 'expectedVersion') = 'number'
    and p_value ->> 'expectedVersion' ~ '^[0-9]+$'
    and pg_catalog.jsonb_typeof(p_value -> 'requestFingerprint') = 'string'
    and p_value ->> 'requestFingerprint' ~ '^[0-9a-f]{64}$';
$$;

create or replace function public.conversational_rectification_action_request(
  p_kind text,
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_request_fingerprint text
)
returns jsonb
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.jsonb_build_object(
    'kind', p_kind,
    'userId', p_user_id,
    'caseId', p_case_id,
    'expectedVersion', p_expected_version,
    'actionId', p_action_id,
    'requestFingerprint', p_request_fingerprint
  );
$$;

create or replace function public.conversational_rectification_valid_action_response(
  p_value jsonb,
  p_action_kind text
)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  if p_action_kind in ('reserve_fee', 'complete_fee', 'release_fee', 'recover_fee') then
    return coalesce(pg_catalog.jsonb_typeof(p_value) = 'object'
      and pg_catalog.octet_length(p_value::text) <= 2048
      and public.conversational_rectification_numbers_are_stable(p_value)
      and public.conversational_rectification_has_only_keys(
        p_value, array['success', 'credits', 'billing_state', 'error_code']::text[]
      )
      and p_value ?& array['success', 'credits', 'billing_state', 'error_code']::text[]
      and pg_catalog.jsonb_typeof(p_value -> 'success') = 'boolean'
      and (
        p_value -> 'credits' = 'null'::jsonb
        or (
          pg_catalog.jsonb_typeof(p_value -> 'credits') = 'number'
          and p_value ->> 'credits' ~ '^[0-9]+$'
        )
      )
      and (
        p_value -> 'billing_state' = 'null'::jsonb
        or (
          pg_catalog.jsonb_typeof(p_value -> 'billing_state') = 'string'
          and p_value ->> 'billing_state' in (
            'reserved', 'charged', 'released', 'migration_waived'
          )
        )
      )
      and (
        p_value -> 'error_code' = 'null'::jsonb
        or (
          pg_catalog.jsonb_typeof(p_value -> 'error_code') = 'string'
          and public.conversational_rectification_text_utf16_length(
            p_value ->> 'error_code'
          ) between 1 and 80
          and public.conversational_rectification_text_is_nonblank(
            p_value ->> 'error_code'
          )
        )
      ), false);
  end if;
  return coalesce(pg_catalog.jsonb_typeof(p_value) = 'object'
    and pg_catalog.octet_length(p_value::text) <= 69632
    and public.conversational_rectification_numbers_are_stable(p_value)
    and public.conversational_rectification_has_only_keys(
      p_value,
      array[
        'case_id', 'user_id', 'status', 'turn_version', 'revision_of_case_id',
        'imported_from_case_id', 'baseline_active_time', 'pending_consultation_question',
        'billing_state', 'latest_turn'
      ]::text[]
    )
    and p_value ?& array[
      'case_id', 'user_id', 'status', 'turn_version', 'revision_of_case_id',
      'imported_from_case_id', 'baseline_active_time', 'pending_consultation_question',
      'billing_state', 'latest_turn'
    ]::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'case_id') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'case_id')
    and pg_catalog.jsonb_typeof(p_value -> 'user_id') = 'string'
    and public.conversational_rectification_valid_uuid_text(p_value ->> 'user_id')
    and pg_catalog.jsonb_typeof(p_value -> 'status') = 'string'
    and p_value ->> 'status' in ('starting', 'active', 'paused', 'confirming', 'completed', 'abandoned')
    and pg_catalog.jsonb_typeof(p_value -> 'turn_version') = 'number'
    and p_value ->> 'turn_version' ~ '^[0-9]+$'
    and (p_value -> 'revision_of_case_id' = 'null'::jsonb
      or (pg_catalog.jsonb_typeof(p_value -> 'revision_of_case_id') = 'string'
        and public.conversational_rectification_valid_uuid_text(
          p_value ->> 'revision_of_case_id'
        )))
    and (p_value -> 'imported_from_case_id' = 'null'::jsonb
      or (pg_catalog.jsonb_typeof(p_value -> 'imported_from_case_id') = 'string'
        and public.conversational_rectification_valid_uuid_text(
          p_value ->> 'imported_from_case_id'
        )))
    and (p_value -> 'baseline_active_time' = 'null'::jsonb
      or (pg_catalog.jsonb_typeof(p_value -> 'baseline_active_time') = 'string'
        and public.conversational_rectification_valid_time_text(
          p_value ->> 'baseline_active_time'
        )))
    and (p_value -> 'pending_consultation_question' = 'null'::jsonb
      or (pg_catalog.jsonb_typeof(p_value -> 'pending_consultation_question') = 'string'
        and public.conversational_rectification_text_utf16_length(
          p_value ->> 'pending_consultation_question'
        ) between 1 and 500
        and public.conversational_rectification_text_is_nonblank(
          p_value ->> 'pending_consultation_question'
        )))
    and (p_value -> 'billing_state' = 'null'::jsonb
      or (pg_catalog.jsonb_typeof(p_value -> 'billing_state') = 'string'
        and p_value ->> 'billing_state' in (
          'reserved', 'charged', 'released', 'migration_waived'
        )))
    and public.conversational_rectification_valid_public_turn(p_value -> 'latest_turn'), false);
exception when others then
  return false;
end;
$$;

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
  drop constraint if exists birth_time_rectification_cases_private_candidate_v3_check,
  drop constraint if exists birth_time_rectification_cases_turn_state_v3_check,
  drop constraint if exists birth_time_rectification_cases_journey_snapshot_v3_check,
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
      or (
        public.conversational_rectification_text_utf16_length(
          pending_consultation_question
        ) between 1 and 500
        and public.conversational_rectification_text_is_nonblank(
          pending_consultation_question
        )
      )
    ),
  add constraint birth_time_rectification_cases_declared_birth_input_check
    check (
      jsonb_typeof(declared_birth_input) = 'object'
      and octet_length(declared_birth_input::text) <= 12000
      and (
        journey_protocol <> 'conversational-evidence-v3'
        or public.conversational_rectification_valid_declared_birth_input(declared_birth_input) is true
      )
    ),
  add constraint birth_time_rectification_cases_private_candidate_v3_check
    check (
      journey_protocol <> 'conversational-evidence-v3'
      or public.conversational_rectification_valid_private_candidate(candidate_result) is true
    ),
  add constraint birth_time_rectification_cases_turn_state_v3_check
    check (
      journey_protocol <> 'conversational-evidence-v3'
      or public.conversational_rectification_valid_public_turn(turn_state) is true
    ),
  add constraint birth_time_rectification_cases_journey_snapshot_v3_check
    check (
      journey_protocol <> 'conversational-evidence-v3'
      or public.conversational_rectification_valid_public_turn(journey_snapshot) is true
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
    public.conversational_rectification_text_utf16_length(narrative) between 1 and 12000
    and public.conversational_rectification_text_is_nonblank(narrative)
  ),
  candidate jsonb not null check (
    public.conversational_rectification_valid_candidate(candidate) is true
  ),
  technical_receipt jsonb not null check (
    public.conversational_rectification_valid_technical_receipt(technical_receipt) is true
  ),
  evidence_request jsonb check (
    evidence_request is null
    or public.conversational_rectification_valid_evidence_request(evidence_request) is true
  ),
  evidence_recap jsonb not null default '[]'::jsonb check (
    public.conversational_rectification_valid_evidence_recap(evidence_recap) is true
  ),
  actions jsonb not null default '[]'::jsonb check (
    public.conversational_rectification_valid_actions(actions) is true
  ),
  output_validation_receipt jsonb not null check (
    public.conversational_rectification_valid_validation_receipt(output_validation_receipt) is true
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
    public.conversational_rectification_text_utf16_length(raw_text) between 1 and 4000
    and public.conversational_rectification_text_is_nonblank(raw_text)
  ),
  domain text not null check (
    domain in ('career', 'education', 'relocation', 'relationship', 'family', 'other')
  ),
  event_summary text not null check (
    public.conversational_rectification_text_utf16_length(event_summary) between 1 and 1000
    and public.conversational_rectification_text_is_nonblank(event_summary)
  ),
  date_value text check (
    date_value is null
    or (
      public.conversational_rectification_text_utf16_length(date_value) between 1 and 80
      and public.conversational_rectification_text_is_nonblank(date_value)
    )
  ),
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
    'reserve_fee', 'complete_fee', 'release_fee', 'recover_fee'
  )),
  expected_turn_version bigint not null check (expected_turn_version >= 0),
  result_turn_version bigint not null check (result_turn_version >= 0),
  request_fingerprint text not null check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  request jsonb not null check (
    public.conversational_rectification_valid_action_request(request) is true
  ),
  response jsonb not null check (
    public.conversational_rectification_valid_action_response(response, action_kind) is true
  ),
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
revoke all on function public.conversational_rectification_numbers_are_stable(jsonb)
  from public, anon, authenticated;
revoke all on function public.conversational_rectification_text_utf16_length(text)
  from public, anon, authenticated;
revoke all on function public.conversational_rectification_text_is_nonblank(text)
  from public, anon, authenticated;
revoke all on function public.conversational_rectification_valid_life_event_evidence(jsonb)
  from public, anon, authenticated;
revoke all on function public.conversational_rectification_valid_life_event_evidence_array(jsonb)
  from public, anon, authenticated;
grant execute on function public.conversational_rectification_numbers_are_stable(jsonb)
  to service_role;
grant execute on function public.conversational_rectification_text_utf16_length(text)
  to service_role;
grant execute on function public.conversational_rectification_text_is_nonblank(text)
  to service_role;
grant execute on function public.conversational_rectification_valid_life_event_evidence(jsonb)
  to service_role;
grant execute on function public.conversational_rectification_valid_life_event_evidence_array(jsonb)
  to service_role;

commit;
