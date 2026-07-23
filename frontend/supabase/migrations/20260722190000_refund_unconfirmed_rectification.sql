-- A birth-time rectification fee is earned only when a gated minute is
-- explicitly confirmed. Range-only completion and abandonment refund the
-- already charged reservation in the same transaction as the terminal state.

create or replace function public.conversational_rectification_refund_unconfirmed_case(
  p_user_id uuid,
  p_case_id uuid,
  p_action_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_balance integer;
begin
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found
    or v_case.journey_protocol is distinct from 'conversational-evidence-v3'
    or v_case.status not in ('completed', 'abandoned')
    or v_case.turn_state #>> '{candidate,status}' = 'confirmed' then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select profile.credits into v_balance
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id and b.user_id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  if v_billing.state = 'charged' then
    update public.profiles profile
    set credits = profile.credits + v_billing.price,
        updated_at = pg_catalog.now()
    where profile.id = p_user_id
    returning profile.credits into v_balance;

    insert into public.credit_transactions (
      user_id, transaction_type, amount, balance_after, request_id
    ) values (
      p_user_id, 'refund', v_billing.price, v_balance,
      'rectification:' || p_case_id::text
    );

    update public.birth_time_rectification_billing
    set state = 'released',
        release_action_id = p_action_id,
        balance_after = v_balance,
        released_at = pg_catalog.now(),
        updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id and state = 'charged';
    if not found then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;
  elsif v_billing.state not in ('released', 'migration_waived') then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  return public.conversational_rectification_case_projection(p_user_id, p_case_id);
end;
$$;

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

  v_active_turn := pg_catalog.jsonb_set(p_turn, '{status}', '"active"'::jsonb, false);
  v_active_turn := pg_catalog.jsonb_set(v_active_turn, '{actions}', '[]'::jsonb, false);
  perform public.save_conversational_rectification_turn(
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

  v_response := public.conversational_rectification_refund_unconfirmed_case(
    p_user_id, p_case_id, p_action_id
  );
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

create or replace function public.abandon_conversational_rectification_without_result(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_turn jsonb,
  p_validation_receipt jsonb,
  p_command_fingerprint text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_response jsonb;
begin
  perform public.abandon_conversational_rectification_case(
    p_user_id,
    p_case_id,
    p_expected_version,
    p_action_id,
    p_turn,
    p_validation_receipt,
    p_command_fingerprint
  );
  v_response := public.conversational_rectification_refund_unconfirmed_case(
    p_user_id, p_case_id, p_action_id
  );
  update public.birth_time_rectification_action_receipts
  set response = v_response
  where case_id = p_case_id
    and action_id = p_action_id
    and user_id = p_user_id
    and action_kind = 'abandon'
    and expected_turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  return v_response;
end;
$$;

revoke all on function public.conversational_rectification_refund_unconfirmed_case(
  uuid, uuid, uuid
) from public, anon, authenticated;
revoke all on function public.abandon_conversational_rectification_without_result(
  uuid, uuid, bigint, uuid, jsonb, jsonb, text
) from public, anon;
grant execute on function public.abandon_conversational_rectification_without_result(
  uuid, uuid, bigint, uuid, jsonb, jsonb, text
) to authenticated, service_role;
