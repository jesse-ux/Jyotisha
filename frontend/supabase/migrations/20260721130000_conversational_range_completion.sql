-- Complete conversational rectification with a saved range when evidence can
-- no longer justify additional questions. This deliberately does not update
-- the account's active birth minute.

create or replace function public.complete_conversational_rectification_with_range(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_evidence jsonb,
  p_validation_receipt jsonb,
  p_private_candidate jsonb,
  p_command_fingerprint text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_active_turn jsonb;
  v_response jsonb;
  v_expected_actions jsonb;
begin
  v_expected_actions := case
    when p_turn -> 'pendingConsultationQuestion' = 'null'::jsonb then '[]'::jsonb
    else '["continue_original_question"]'::jsonb
  end;
  if public.conversational_rectification_valid_public_turn(p_turn) is not true
    or p_turn ->> 'status' is distinct from 'completed'
    or p_turn #>> '{candidate,status}' is distinct from 'pending_validation'
    or p_turn -> 'evidenceRequest' is distinct from 'null'::jsonb
    or p_turn -> 'actions' is distinct from v_expected_actions then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  -- Reuse the established append-only evidence, candidate and idempotency
  -- transaction. The terminal projection is applied below in the same SQL
  -- transaction, so no active intermediate state can escape to another client.
  v_active_turn := pg_catalog.jsonb_set(p_turn, '{status}', '"active"'::jsonb, false);
  v_active_turn := pg_catalog.jsonb_set(v_active_turn, '{actions}', '[]'::jsonb, false);
  v_response := public.save_conversational_rectification_turn(
    p_user_id,
    p_case_id,
    p_expected_version,
    p_action_id,
    v_active_turn,
    p_evidence,
    p_validation_receipt,
    p_private_candidate,
    p_command_fingerprint
  );

  update public.birth_time_rectification_turns
  set narrative = p_turn ->> 'narrative',
      evidence_request = null,
      actions = p_turn -> 'actions'
  where case_id = p_case_id
    and turn_version = p_expected_version + 1;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  update public.birth_time_rectification_cases
  set status = 'completed',
      turn_state = p_turn,
      journey_snapshot = p_turn,
      updated_at = pg_catalog.now()
  where id = p_case_id
    and user_id = p_user_id
    and turn_version = p_expected_version + 1;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(p_user_id, p_case_id);
  update public.birth_time_rectification_action_receipts
  set response = v_response
  where case_id = p_case_id
    and action_id = p_action_id
    and user_id = p_user_id
    and action_kind = 'save_turn'
    and expected_turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  return v_response;
end;
$$;

revoke all on function public.complete_conversational_rectification_with_range(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text
) from public, anon;
grant execute on function public.complete_conversational_rectification_with_range(
  uuid, uuid, bigint, uuid, jsonb, jsonb, jsonb, jsonb, text
) to authenticated, service_role;
