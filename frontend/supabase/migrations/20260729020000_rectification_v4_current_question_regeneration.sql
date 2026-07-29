begin;

create or replace function public.replace_birth_time_rectification_v4_current_question(
  p_user_id uuid,
  p_case_id uuid,
  p_action_id uuid,
  p_expected_version bigint,
  p_question jsonb,
  p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  v_case public.birth_time_rectification_v4_cases%rowtype;
  v_case_id uuid;
  v_question jsonb;
begin
  select action.case_id into v_case_id
  from public.birth_time_rectification_v4_actions action
  where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_case_id is not null then return v_case_id; end if;

  select value.* into v_case
  from public.birth_time_rectification_v4_cases value
  where value.id = p_case_id and value.user_id = p_user_id
  for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;

  select action.case_id into v_case_id
  from public.birth_time_rectification_v4_actions action
  where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_case_id is not null then return v_case_id; end if;

  if v_case.version <> p_expected_version then raise exception 'stale_rectification_v4_case'; end if;
  if v_case.deployment_mode <> 'v5_agent'
    or v_case.status not in ('awaiting_answer', 'range_ready')
    or v_case.current_question is null then
    raise exception 'rectification_v4_question_not_regenerable';
  end if;
  if p_question is null or pg_catalog.jsonb_typeof(p_question) <> 'object' then
    raise exception 'invalid_rectification_v4_question';
  end if;
  if nullif(pg_catalog.btrim(p_question->>'id'), '') is null
    or (p_question->>'id') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    or nullif(pg_catalog.btrim(p_question->>'prompt'), '') is null
    or pg_catalog.length(pg_catalog.btrim(p_question->>'prompt')) > 1000
    or p_question->>'recallCost' not in ('low', 'medium', 'high')
    or nullif(pg_catalog.btrim(p_question->>'reason'), '') is null
    or pg_catalog.length(pg_catalog.btrim(p_question->>'reason')) > 240 then
    raise exception 'invalid_rectification_v4_question';
  end if;

  v_question := p_question || pg_catalog.jsonb_build_object(
    'domain', v_case.current_question->'domain',
    'targetEventId', v_case.current_question->'targetEventId'
  );

  update public.birth_time_rectification_v4_cases
  set version = p_expected_version + 1,
      current_question = v_question,
      updated_at = p_now
  where id = p_case_id;

  insert into public.birth_time_rectification_v4_actions(
    user_id, action_id, case_id, created_at
  ) values (
    p_user_id, p_action_id, p_case_id, p_now
  );

  return p_case_id;
end;
$$;

revoke all on function public.replace_birth_time_rectification_v4_current_question(
  uuid, uuid, uuid, bigint, jsonb, timestamptz
) from public, anon, authenticated, service_role;
grant execute on function public.replace_birth_time_rectification_v4_current_question(
  uuid, uuid, uuid, bigint, jsonb, timestamptz
) to service_role;

commit;
