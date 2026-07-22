begin;

-- The application contract has always treated finance as a first-class
-- rectification evidence domain. The initial durable SQL contract omitted it,
-- so a valid technical packet containing D2/D11 evidence was rejected only at
-- the create RPC boundary as conversational_action_conflict.
do $migration$
declare
  v_signature text;
  v_definition text;
  v_updated_definition text;
  v_old_domains constant text := '''career'', ''education'', ''relocation'', ''relationship'', ''family'', ''other''';
  v_new_domains constant text := '''career'', ''education'', ''finance'', ''relocation'', ''relationship'', ''family'', ''other''';
begin
  foreach v_signature in array array[
    'public.conversational_rectification_valid_evidence_request(jsonb)',
    'public.conversational_rectification_valid_life_event_evidence(jsonb)',
    'public.conversational_rectification_valid_private_candidate(jsonb)'
  ] loop
    select pg_catalog.pg_get_functiondef(v_signature::regprocedure)
      into v_definition;
    v_updated_definition := pg_catalog.replace(
      v_definition,
      v_old_domains,
      v_new_domains
    );
    if v_updated_definition is not distinct from v_definition then
      raise exception 'finance domain migration could not update %', v_signature;
    end if;
    execute v_updated_definition;
  end loop;
end;
$migration$;

-- Public recap rows may carry their domain so a resumed conversation can keep
-- domain-aware follow-up ordering. The TypeScript contract already allowed it.
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
          item, array['id', 'summary', 'dateLabel', 'domain', 'isCorrection']::text[]
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
        or (
          item ? 'domain'
          and (
            pg_catalog.jsonb_typeof(item -> 'domain') <> 'string'
            or item ->> 'domain' not in (
              'career', 'education', 'finance', 'relocation',
              'relationship', 'family', 'other'
            )
          )
        )
        or (
          item ? 'isCorrection'
          and pg_catalog.jsonb_typeof(item -> 'isCorrection') <> 'boolean'
        )
    );
$$;

alter table public.birth_time_rectification_event_evidence
  drop constraint if exists birth_time_rectification_event_evidence_domain_check;

alter table public.birth_time_rectification_event_evidence
  add constraint birth_time_rectification_event_evidence_domain_check
  check (
    domain in (
      'career', 'education', 'finance', 'relocation',
      'relationship', 'family', 'other'
    )
  );

commit;
