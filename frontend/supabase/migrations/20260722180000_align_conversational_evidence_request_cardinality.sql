begin;

-- Language-first rectification asks one focused domain at a time. The
-- application contract already permits that, while durable SQL still required
-- at least two domains and rejected otherwise-valid turns as action_conflict.
do $migration$
declare
  v_signature constant text :=
    'public.conversational_rectification_valid_evidence_request(jsonb)';
  v_definition text;
  v_updated_definition text;
begin
  select pg_catalog.pg_get_functiondef(v_signature::regprocedure)
    into v_definition;
  v_updated_definition := pg_catalog.replace(
    v_definition,
    'between 2 and 4',
    'between 1 and 4'
  );
  if v_updated_definition is not distinct from v_definition then
    raise exception 'evidence request cardinality migration could not update %',
      v_signature;
  end if;
  execute v_updated_definition;
end;
$migration$;

commit;
