begin;

-- Follow-up targeting is part of the language-first rectification contract.
-- Keep the legacy required keys stable, but allow the optional followUp object
-- that the application persists to distinguish a new event from a date/detail
-- clarification.
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
      array['domains', 'datePrecision', 'freeTextAllowed', 'followUp']::text[]
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
      not (p_value ? 'followUp')
      or (
        pg_catalog.jsonb_typeof(p_value -> 'followUp') = 'object'
        and public.conversational_rectification_has_only_keys(
          p_value -> 'followUp',
          array['kind', 'evidenceId']::text[]
        )
        and (p_value -> 'followUp') ?& array['kind', 'evidenceId']::text[]
        and p_value #>> '{followUp,kind}' in ('new_event', 'event_date', 'event_detail')
        and (
          p_value #>> '{followUp,evidenceId}' is null
          or public.conversational_rectification_valid_uuid_text(
            p_value #>> '{followUp,evidenceId}'
          )
        )
      )
    );
$$;

commit;
