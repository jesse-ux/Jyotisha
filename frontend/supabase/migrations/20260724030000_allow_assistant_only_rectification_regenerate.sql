-- Regenerating a rectification reply replaces the assistant side of the latest
-- exchange. It must not persist the same user message again, otherwise a reload
-- renders a duplicate user bubble. Ordinary answer turns still pass a non-null
-- message and retain the existing validation.

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
  if p_user_message is not null and (
    public.conversational_rectification_text_utf16_length(p_user_message) not between 1 and 4000
    or public.conversational_rectification_text_is_nonblank(p_user_message) is not true
  ) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  v_response := public.save_conversational_rectification_turn(
    p_user_id, p_case_id, p_expected_version, p_action_id, p_turn, p_evidence,
    p_validation_receipt, p_private_candidate, p_command_fingerprint
  );
  update public.birth_time_rectification_turns
  set user_message = case
    when p_user_message is null then user_message
    else coalesce(user_message, p_user_message)
  end
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
  if p_user_message is not null and (
    public.conversational_rectification_text_utf16_length(p_user_message) not between 1 and 4000
    or public.conversational_rectification_text_is_nonblank(p_user_message) is not true
  ) then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  v_response := public.complete_conversational_rectification_with_range(
    p_user_id, p_case_id, p_expected_version, p_action_id, p_turn, p_evidence,
    p_validation_receipt, p_private_candidate, p_command_fingerprint
  );
  update public.birth_time_rectification_turns
  set user_message = case
    when p_user_message is null then user_message
    else coalesce(user_message, p_user_message)
  end
  where case_id = p_case_id
    and turn_version = p_expected_version + 1
  returning user_message into v_saved_user_message;
  if not found or v_saved_user_message is distinct from p_user_message then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  return v_response;
end;
$$;

revoke all on function public.save_conversational_rectification_turn_with_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) from public, anon, authenticated;
revoke all on function public.complete_conversational_rectification_with_range_and_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) from public, anon, authenticated;
grant execute on function public.save_conversational_rectification_turn_with_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) to service_role;
grant execute on function public.complete_conversational_rectification_with_range_and_history(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text, text
) to service_role;
