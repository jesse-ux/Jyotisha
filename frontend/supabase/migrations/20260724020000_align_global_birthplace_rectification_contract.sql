begin;

-- Global birthplace intake stores provider identity and IANA timezone metadata
-- in the immutable rectification declaration. Keep the database validator in
-- lockstep with the strict TypeScript persistence contract so valid non-China
-- profiles are not surfaced as conversational_action_conflict.
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
        'city', 'placeId', 'placeType', 'provider', 'countryCode',
        'provinceCode', 'cityCode', 'districtCode', 'latitude', 'longitude',
        'timezoneId', 'timezoneSource', 'timezoneOffset'
      ]::text[]
    )
    or not (v_place ? 'timezoneOffset')
    or not ((v_place ? 'city') or (v_place ? 'cityCode') or (v_place ? 'placeId'))
    or pg_catalog.jsonb_typeof(v_place -> 'timezoneOffset') is distinct from 'number'
    or (v_place ->> 'timezoneOffset')::numeric not between -12 and 14
    or (v_place ? 'latitude') <> (v_place ? 'longitude') then return false; end if;
  foreach v_key in array array[
    'city', 'placeId', 'placeType', 'provider', 'provinceCode', 'cityCode',
    'districtCode', 'timezoneId', 'timezoneSource'
  ]::text[] loop
    if v_place ? v_key and (
      pg_catalog.jsonb_typeof(v_place -> v_key) is distinct from 'string'
      or public.conversational_rectification_text_utf16_length(
        v_place ->> v_key
      ) not between 1 and case
        when v_key = 'city' then 120
        when v_key = 'placeId' then 240
        when v_key = 'timezoneId' then 120
        else 80
      end
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

commit;
