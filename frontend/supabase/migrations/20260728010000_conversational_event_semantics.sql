begin;

alter table public.birth_time_rectification_event_evidence
  add column if not exists event_kind text check (
    event_kind is null or (
      public.conversational_rectification_text_utf16_length(event_kind) between 1 and 120
      and public.conversational_rectification_text_is_nonblank(event_kind)
    )
  ),
  add column if not exists subject text check (
    subject is null or subject in ('self', 'family', 'partner', 'other')
  ),
  add column if not exists related_person text check (
    related_person is null or related_person in (
      'father', 'mother', 'grandparent', 'sibling', 'partner'
    )
  ),
  add column if not exists scoreability text check (
    scoreability is null or scoreability in (
      'scoreable', 'context_only', 'pending_review', 'unsupported'
    )
  );

-- Keep old rows valid while persisting the richer optional semantics emitted by
-- the application. Patch the deployed function bodies because these RPCs were
-- created by earlier immutable migrations.
do $migration$
declare
  v_definition text;
  v_updated text;
  v_signature text;
begin
  select pg_catalog.pg_get_functiondef(
    'public.conversational_rectification_valid_life_event_evidence(jsonb)'::regprocedure
  ) into v_definition;
  v_updated := pg_catalog.replace(
    v_definition,
    '''datePrecision'', ''extractionStatus'', ''scoreable'', ''correctsEvidenceIds''',
    '''datePrecision'', ''extractionStatus'', ''eventKind'', ''subject'', ''relatedPerson'', ''scoreability'', ''scoreable'', ''correctsEvidenceIds'''
  );
  v_updated := pg_catalog.replace(
    v_updated,
    $$    or pg_catalog.jsonb_typeof(p_value -> 'eventSummary') is distinct from 'string'$$,
    $$    or (
      p_value ? 'eventKind'
      and (
        pg_catalog.jsonb_typeof(p_value -> 'eventKind') is distinct from 'string'
        or public.conversational_rectification_text_utf16_length(
          p_value ->> 'eventKind'
        ) not between 1 and 120
        or public.conversational_rectification_text_is_nonblank(
          p_value ->> 'eventKind'
        ) is not true
      )
    )
    or (
      p_value ? 'subject'
      and (
        pg_catalog.jsonb_typeof(p_value -> 'subject') is distinct from 'string'
        or p_value ->> 'subject' not in ('self', 'family', 'partner', 'other')
      )
    )
    or (
      p_value ? 'relatedPerson'
      and p_value -> 'relatedPerson' <> 'null'::jsonb
      and (
        pg_catalog.jsonb_typeof(p_value -> 'relatedPerson') is distinct from 'string'
        or p_value ->> 'relatedPerson' not in (
          'father', 'mother', 'grandparent', 'sibling', 'partner'
        )
      )
    )
    or (
      p_value ? 'scoreability'
      and (
        pg_catalog.jsonb_typeof(p_value -> 'scoreability') is distinct from 'string'
        or p_value ->> 'scoreability' not in (
          'scoreable', 'context_only', 'pending_review', 'unsupported'
        )
      )
    )
    or pg_catalog.jsonb_typeof(p_value -> 'eventSummary') is distinct from 'string'$$
  );
  if v_updated is not distinct from v_definition then
    raise exception 'event semantics migration could not update evidence validator';
  end if;
  execute v_updated;

  foreach v_signature in array array[
    'public.save_conversational_rectification_turn(uuid,uuid,bigint,uuid,jsonb,jsonb,jsonb,jsonb,text)',
    'public.import_legacy_conversational_rectification_case(uuid,uuid,uuid,bigint,uuid,integer,text,jsonb,jsonb,jsonb,jsonb,jsonb)'
  ] loop
    select pg_catalog.pg_get_functiondef(v_signature::regprocedure) into v_definition;
    v_updated := pg_catalog.replace(
      v_definition,
      'date_value, date_precision, extraction_status, corrects_evidence_ids, scoreable',
      'date_value, date_precision, extraction_status, corrects_evidence_ids, event_kind, subject, related_person, scoreability, scoreable'
    );
    v_updated := pg_catalog.replace(
      v_updated,
      $$date_value, date_precision, extraction_status, scoreable,
    corrects_evidence_ids$$,
      $$date_value, date_precision, extraction_status, event_kind, subject,
    related_person, scoreability, scoreable, corrects_evidence_ids$$
    );
    v_updated := pg_catalog.replace(
      v_updated,
      $$    ) else '{}'::uuid[] end,
    case when item ? 'scoreable' then (item ->> 'scoreable')::boolean$$,
      $$    ) else '{}'::uuid[] end,
    item ->> 'eventKind', item ->> 'subject', item ->> 'relatedPerson',
    item ->> 'scoreability',
    case when item ? 'scoreable' then (item ->> 'scoreable')::boolean$$
    );
    v_updated := pg_catalog.replace(
      v_updated,
      $$    item ->> 'extractionStatus', (item ->> 'scoreable')::boolean,
    array(select value::uuid$$,
      $$    item ->> 'extractionStatus', item ->> 'eventKind', item ->> 'subject',
    item ->> 'relatedPerson', item ->> 'scoreability',
    (item ->> 'scoreable')::boolean,
    array(select value::uuid$$
    );
    if v_updated is not distinct from v_definition then
      raise exception 'event semantics migration could not update %', v_signature;
    end if;
    execute v_updated;
  end loop;
end;
$migration$;

commit;
