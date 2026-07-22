begin;

-- The language-first evidence extractor and question planner use
-- health_pressure as a first-class rectification domain. The durable SQL
-- contract still rejected that domain in a public evidence request, so the
-- first scored answer could finish all calculation/model work and then fail
-- at save_conversational_rectification_turn with action_conflict.
do $migration$
declare
  v_signature text;
  v_definition text;
  v_updated_definition text;
  v_old_domains constant text := '''finance'', ''relocation''';
  v_new_domains constant text := '''finance'', ''health_pressure'', ''relocation''';
begin
  foreach v_signature in array array[
    'public.conversational_rectification_valid_evidence_request(jsonb)',
    'public.conversational_rectification_valid_evidence_recap(jsonb)',
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
      raise exception 'health pressure domain migration could not update %', v_signature;
    end if;
    execute v_updated_definition;
  end loop;
end;
$migration$;

alter table public.birth_time_rectification_event_evidence
  drop constraint if exists birth_time_rectification_event_evidence_domain_check;

alter table public.birth_time_rectification_event_evidence
  add constraint birth_time_rectification_event_evidence_domain_check
  check (
    domain in (
      'career', 'education', 'finance', 'health_pressure', 'relocation',
      'relationship', 'family', 'other'
    )
  );

commit;
