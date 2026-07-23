-- Preserve the real user/Agent exchange across reloads. The durable public turn
-- remains unchanged; history is returned only by the service-role resume RPC.

alter table public.birth_time_rectification_turns
  add column if not exists user_message text;

alter table public.birth_time_rectification_turns
  drop constraint if exists birth_time_rectification_turns_user_message_check;

alter table public.birth_time_rectification_turns
  add constraint birth_time_rectification_turns_user_message_check check (
    user_message is null or (
      public.conversational_rectification_text_utf16_length(user_message) between 1 and 4000
      and public.conversational_rectification_text_is_nonblank(user_message)
    )
  );

-- Older answer turns already point to their extracted evidence. Recover the
-- original raw answer where it is unambiguous instead of inventing UI copy.
update public.birth_time_rectification_turns turn_row
set user_message = (
  select event.raw_text
  from public.birth_time_rectification_event_evidence event
  where event.case_id = turn_row.case_id
    and event.source_turn_id = turn_row.id
  order by event.created_at, event.id
  limit 1
)
where turn_row.user_message is null
  and exists (
    select 1
    from public.birth_time_rectification_event_evidence event
    where event.case_id = turn_row.case_id
      and event.source_turn_id = turn_row.id
  );

create or replace function public.load_conversational_rectification_case_with_history(
  p_user_id uuid,
  p_case_id uuid default null
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_loaded jsonb;
  v_case_id uuid;
begin
  v_loaded := public.load_conversational_rectification_case(p_user_id, p_case_id);
  if v_loaded is null then
    return null;
  end if;
  v_case_id := (v_loaded ->> 'case_id')::uuid;
  return v_loaded || pg_catalog.jsonb_build_object(
    'message_history', coalesce((
      select pg_catalog.jsonb_agg(
        pg_catalog.jsonb_build_object(
          'turnVersion', turn_row.turn_version,
          'userMessage', turn_row.user_message,
          'narrative', turn_row.narrative
        ) order by turn_row.turn_version
      )
      from (
        select history.turn_version, history.user_message, history.narrative
        from public.birth_time_rectification_turns history
        where history.case_id = v_case_id
        order by history.turn_version desc
        limit 200
      ) turn_row
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function public.save_conversational_rectification_turn_with_history(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_evidence jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb,
  p_command_fingerprint text,
  p_user_message text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_response jsonb;
  v_saved_user_message text;
begin
  if p_user_message is null
    or public.conversational_rectification_text_utf16_length(p_user_message) not between 1 and 4000
    or public.conversational_rectification_text_is_nonblank(p_user_message) is not true then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  v_response := public.save_conversational_rectification_turn(
    p_user_id, p_case_id, p_expected_version, p_action_id, p_turn, p_evidence,
    p_validation_receipt, p_private_candidate, p_command_fingerprint
  );
  update public.birth_time_rectification_turns
  set user_message = coalesce(user_message, p_user_message)
  where case_id = p_case_id
    and turn_version = p_expected_version + 1
  returning user_message into v_saved_user_message;
  if not found or v_saved_user_message is distinct from p_user_message then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  return v_response;
end;
$$;

create or replace function public.complete_conversational_rectification_with_range_and_history(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_evidence jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb,
  p_command_fingerprint text,
  p_user_message text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_response jsonb;
  v_saved_user_message text;
begin
  if p_user_message is null
    or public.conversational_rectification_text_utf16_length(p_user_message) not between 1 and 4000
    or public.conversational_rectification_text_is_nonblank(p_user_message) is not true then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  v_response := public.complete_conversational_rectification_with_range(
    p_user_id, p_case_id, p_expected_version, p_action_id, p_turn, p_evidence,
    p_validation_receipt, p_private_candidate, p_command_fingerprint
  );
  update public.birth_time_rectification_turns
  set user_message = coalesce(user_message, p_user_message)
  where case_id = p_case_id
    and turn_version = p_expected_version + 1
  returning user_message into v_saved_user_message;
  if not found or v_saved_user_message is distinct from p_user_message then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  return v_response;
end;
$$;

revoke all on function public.load_conversational_rectification_case_with_history(uuid, uuid)
  from public, anon, authenticated;
revoke all on function public.save_conversational_rectification_turn_with_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) from public, anon, authenticated;
revoke all on function public.complete_conversational_rectification_with_range_and_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) from public, anon, authenticated;

grant execute on function public.load_conversational_rectification_case_with_history(uuid, uuid)
  to service_role;
grant execute on function public.save_conversational_rectification_turn_with_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) to service_role;
grant execute on function public.complete_conversational_rectification_with_range_and_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) to service_role;
