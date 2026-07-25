begin;

-- Repair the structured date validator after the initial migration shipped a
-- redundant aggregate date regex with unbalanced parentheses. The precision-
-- specific checks below are the single source of truth.
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
      array['domains', 'datePrecision', 'freeTextAllowed', 'prompt', 'followUp']::text[]
    )
    and p_value ?& array['domains', 'datePrecision', 'freeTextAllowed']::text[]
    and pg_catalog.jsonb_typeof(p_value -> 'domains') = 'array'
    and pg_catalog.jsonb_array_length(p_value -> 'domains') between 1 and 4
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(p_value -> 'domains') domain
      where pg_catalog.jsonb_typeof(domain) is distinct from 'string'
        or domain #>> '{}' not in (
          'career', 'education', 'finance', 'health_pressure', 'relocation',
          'relationship', 'family', 'other'
        )
    )
    and pg_catalog.jsonb_typeof(p_value -> 'datePrecision') = 'string'
    and p_value ->> 'datePrecision' in ('month_preferred', 'year_accepted')
    and pg_catalog.jsonb_typeof(p_value -> 'freeTextAllowed') = 'boolean'
    and p_value -> 'freeTextAllowed' = 'true'::jsonb
    and (
      not (p_value ? 'prompt')
      or (
        pg_catalog.jsonb_typeof(p_value -> 'prompt') = 'string'
        and pg_catalog.char_length(pg_catalog.btrim(p_value ->> 'prompt')) between 1 and 1000
      )
    )
    and (
      not (p_value ? 'followUp')
      or (
        pg_catalog.jsonb_typeof(p_value -> 'followUp') = 'object'
        and public.conversational_rectification_has_only_keys(
          p_value -> 'followUp',
          array['kind', 'evidenceId', 'answerMode', 'proposedDate']::text[]
        )
        and (p_value -> 'followUp') ?& array['kind', 'evidenceId']::text[]
        and p_value #>> '{followUp,kind}' in ('new_event', 'event_date', 'event_detail')
        and (
          not ((p_value -> 'followUp') ? 'answerMode')
          or (
            pg_catalog.jsonb_typeof(p_value #> '{followUp,answerMode}') = 'string'
            and p_value #>> '{followUp,answerMode}' in ('free_text', 'yes_no')
          )
        )
        and (
          not ((p_value -> 'followUp') ? 'proposedDate')
          or p_value #> '{followUp,proposedDate}' = 'null'::jsonb
          or (
            pg_catalog.jsonb_typeof(p_value #> '{followUp,proposedDate}') = 'object'
            and public.conversational_rectification_has_only_keys(
              p_value #> '{followUp,proposedDate}',
              array['value', 'precision']::text[]
            )
            and (p_value #> '{followUp,proposedDate}') ?& array['value', 'precision']::text[]
            and pg_catalog.jsonb_typeof(p_value #> '{followUp,proposedDate,value}') = 'string'
            and pg_catalog.jsonb_typeof(p_value #> '{followUp,proposedDate,precision}') = 'string'
            and (
              (p_value #>> '{followUp,proposedDate,precision}' = 'year'
                and p_value #>> '{followUp,proposedDate,value}' ~ '^[0-9]{4}$')
              or (p_value #>> '{followUp,proposedDate,precision}' = 'month'
                and p_value #>> '{followUp,proposedDate,value}' ~ '^[0-9]{4}-((0[1-9])|(1[0-2]))$')
              or (p_value #>> '{followUp,proposedDate,precision}' = 'day'
                and p_value #>> '{followUp,proposedDate,value}'
                  ~ '^[0-9]{4}-((0[1-9])|(1[0-2]))-((0[1-9])|([12][0-9])|(3[01]))$')
            )
          )
        )
        and (
          (p_value #>> '{followUp,kind}' = 'new_event'
            and p_value #>> '{followUp,evidenceId}' is null)
          or (p_value #>> '{followUp,kind}' <> 'new_event'
            and public.conversational_rectification_valid_uuid_text(
              p_value #>> '{followUp,evidenceId}'
            ))
        )
        and (
          (p_value #>> '{followUp,answerMode}' = 'yes_no'
            and p_value #>> '{followUp,kind}' = 'event_date'
            and pg_catalog.jsonb_typeof(p_value #> '{followUp,proposedDate}') = 'object')
          or (p_value #>> '{followUp,answerMode}' is distinct from 'yes_no'
            and (
              not ((p_value -> 'followUp') ? 'proposedDate')
              or p_value #> '{followUp,proposedDate}' = 'null'::jsonb
            ))
        )
      )
    );
$$;

commit;
