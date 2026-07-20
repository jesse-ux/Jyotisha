begin;

create or replace function public.reserve_conversational_rectification_fee(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_price integer
)
returns table (
  success boolean,
  credits integer,
  billing_state text,
  error_code text
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_orphan public.birth_time_rectification_billing%rowtype;
  v_receipt_action_id uuid :=
    public.conversational_rectification_billing_receipt_action_id(
      p_action_id,
      'reserve_fee'
    );
  v_balance integer;
  v_response jsonb;
  v_recovery_action_id uuid;
  v_recovery_fingerprint text;
  v_recovery_response jsonb;
  v_fingerprint text := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    pg_catalog.jsonb_build_object(
      'kind', 'reserve_fee', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'price', p_price
    )::text,
    'UTF8'
  )), 'hex');
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is distinct from 0
    or p_price is null or not (p_price between 1 and 1000000) then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if p_case_id is distinct from p_action_id then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  -- The account lock prevents two different start actions from reserving two
  -- fees before either action has created its case. The action lock preserves
  -- exact replay for the same request.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':conversational-rectification-case',
      0
    )
  );
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );

  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = v_receipt_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'reserve_fee'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return query select
      (v_receipt.response ->> 'success')::boolean,
      nullif(v_receipt.response ->> 'credits', '')::integer,
      nullif(v_receipt.response ->> 'billing_state', ''),
      nullif(v_receipt.response ->> 'error_code', '');
    return;
  end if;

  -- A public action identifies one start attempt even if a buggy caller loses
  -- its case id. Reusing that action for another case is a conflict, never a
  -- second debit.
  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.user_id = p_user_id
    and r.action_id = v_receipt_action_id
    and r.action_kind = 'reserve_fee'
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  perform 1
  from public.birth_time_rectification_cases active_case
  where active_case.user_id = p_user_id
    and active_case.id <> p_case_id
    and active_case.journey_protocol = 'conversational-evidence-v3'
    and active_case.status in ('starting', 'active', 'paused', 'confirming')
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select profile.credits into v_balance
  from public.profiles profile
  where profile.id = p_user_id
  for update;
  if not found then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  -- Reservation intentionally precedes the external first-turn calculation,
  -- so it cannot share a transaction with case creation. A process/device
  -- loss in that gap leaves no case for the account resume RPC to expose.
  -- A fresh account-scoped start deterministically releases every such orphan
  -- under the same account/profile locks before it attempts another debit.
  for v_orphan in
    select orphan_billing.*
    from public.birth_time_rectification_billing orphan_billing
    left join public.birth_time_rectification_cases orphan_case
      on orphan_case.id = orphan_billing.case_id
    where orphan_billing.user_id = p_user_id
      and orphan_billing.case_id <> p_case_id
      and orphan_billing.state = 'reserved'
      and orphan_case.id is null
    order by orphan_billing.reserved_at, orphan_billing.case_id
    for update of orphan_billing
  loop
    v_recovery_action_id :=
      public.conversational_rectification_billing_receipt_action_id(
        v_orphan.reserve_action_id,
        'recover_fee'
      );
    v_recovery_fingerprint := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
      pg_catalog.jsonb_build_object(
        'kind', 'recover_fee', 'userId', p_user_id, 'caseId', v_orphan.case_id,
        'expectedVersion', 0, 'actionId', v_recovery_action_id,
        'reserveActionId', v_orphan.reserve_action_id
      )::text,
      'UTF8'
    )), 'hex');

    update public.profiles profile
    set credits = profile.credits + v_orphan.price,
        updated_at = pg_catalog.now()
    where profile.id = p_user_id
    returning profile.credits into v_balance;
    if not found then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;

    insert into public.credit_transactions (
      user_id, transaction_type, amount, balance_after, request_id
    ) values (
      p_user_id, 'refund', v_orphan.price, v_balance,
      'rectification:' || v_orphan.case_id::text
    );

    update public.birth_time_rectification_billing orphan_billing
    set state = 'released',
        release_action_id = v_recovery_action_id,
        balance_after = v_balance,
        released_at = pg_catalog.now(),
        updated_at = pg_catalog.now()
    where orphan_billing.case_id = v_orphan.case_id
      and orphan_billing.user_id = p_user_id
      and orphan_billing.state = 'reserved';
    if not found then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;

    v_recovery_response := pg_catalog.jsonb_build_object(
      'success', true, 'credits', v_balance,
      'billing_state', 'released', 'error_code', null
    );
    insert into public.birth_time_rectification_action_receipts (
      case_id, action_id, user_id, action_kind, expected_turn_version,
      result_turn_version, request_fingerprint, request, response
    ) values (
      v_orphan.case_id, v_recovery_action_id, p_user_id, 'recover_fee', 0,
      0, v_recovery_fingerprint,
      public.conversational_rectification_action_request(
        'recover_fee', p_user_id, v_orphan.case_id, 0,
        v_recovery_action_id, v_recovery_fingerprint
      ),
      v_recovery_response
    );
  end loop;

  select b.* into v_billing
  from public.birth_time_rectification_billing b
  where b.case_id = p_case_id
  for update;
  if found then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  if v_balance < p_price then
    v_response := pg_catalog.jsonb_build_object(
      'success', false, 'credits', v_balance,
      'billing_state', null, 'error_code', 'insufficient_credits'
    );
    insert into public.birth_time_rectification_action_receipts (
      case_id, action_id, user_id, action_kind, expected_turn_version,
      result_turn_version, request_fingerprint, request, response
    ) values (
      p_case_id, v_receipt_action_id, p_user_id, 'reserve_fee', 0,
      0, v_fingerprint,
      public.conversational_rectification_action_request(
        'reserve_fee', p_user_id, p_case_id, 0, p_action_id, v_fingerprint
      ),
      v_response
    );
    return query select false, v_balance, null::text, 'insufficient_credits'::text;
    return;
  end if;

  update public.profiles profile
  set credits = profile.credits - p_price,
      updated_at = pg_catalog.now()
  where profile.id = p_user_id and profile.credits >= p_price
  returning profile.credits into v_balance;
  if not found then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;

  insert into public.credit_transactions (
    user_id, transaction_type, amount, balance_after, request_id
  ) values (
    p_user_id, 'reserve', -p_price, v_balance,
    'rectification:' || p_case_id::text
  );

  insert into public.birth_time_rectification_billing (
    case_id, user_id, price, state, reservation_id, reserve_action_id,
    balance_after, reserved_at
  ) values (
    p_case_id, p_user_id, p_price, 'reserved',
    pg_catalog.gen_random_uuid(), p_action_id, v_balance, pg_catalog.now()
  );

  v_response := pg_catalog.jsonb_build_object(
    'success', true, 'credits', v_balance,
    'billing_state', 'reserved', 'error_code', null
  );
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, v_receipt_action_id, p_user_id, 'reserve_fee', 0,
    0, v_fingerprint,
    public.conversational_rectification_action_request(
      'reserve_fee', p_user_id, p_case_id, 0, p_action_id, v_fingerprint
    ),
    v_response
  );

  return query select true, v_balance, 'reserved'::text, null::text;
end;
$$;

create or replace function public.complete_conversational_rectification_fee(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid
)
returns table (
  success boolean,
  credits integer,
  billing_state text,
  error_code text
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt_action_id uuid :=
    public.conversational_rectification_billing_receipt_action_id(
      p_action_id,
      'complete_fee'
    );
  v_balance integer;
  v_response jsonb;
  v_success boolean;
  v_error_code text;
  v_state text;
  v_fingerprint text := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    pg_catalog.jsonb_build_object(
      'kind', 'complete_fee', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id
    )::text,
    'UTF8'
  )), 'hex');
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0 then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if p_case_id is distinct from p_action_id then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;

  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = v_receipt_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'complete_fee'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return query select
      (v_receipt.response ->> 'success')::boolean,
      nullif(v_receipt.response ->> 'credits', '')::integer,
      nullif(v_receipt.response ->> 'billing_state', ''),
      nullif(v_receipt.response ->> 'error_code', '');
    return;
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
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
    v_success := false;
    v_state := null;
    v_error_code := 'billing_missing';
  elsif v_billing.state = 'charged' then
    v_success := true;
    v_state := 'charged';
    v_error_code := null;
  elsif v_billing.state = 'released' then
    v_success := false;
    v_state := 'released';
    v_error_code := 'reservation_released';
  elsif v_billing.state = 'migration_waived' then
    v_success := true;
    v_state := 'migration_waived';
    v_error_code := null;
  else
    update public.birth_time_rectification_billing
    set state = 'charged',
        billing_receipt_id = pg_catalog.gen_random_uuid(),
        complete_action_id = p_action_id,
        charged_at = pg_catalog.now(),
        updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id and state = 'reserved';
    if not found then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;
    v_success := true;
    v_state := 'charged';
    v_error_code := null;
  end if;

  v_response := pg_catalog.jsonb_build_object(
    'success', v_success, 'credits', v_balance,
    'billing_state', v_state, 'error_code', v_error_code
  );
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, v_receipt_action_id, p_user_id, 'complete_fee', p_expected_version,
    v_case.turn_version, v_fingerprint,
    public.conversational_rectification_action_request(
      'complete_fee', p_user_id, p_case_id, p_expected_version,
      p_action_id, v_fingerprint
    ),
    v_response
  );
  return query select v_success, v_balance, v_state, v_error_code;
end;
$$;

create or replace function public.release_conversational_rectification_fee(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_price integer
)
returns table (
  success boolean,
  credits integer,
  billing_state text,
  error_code text
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_receipt public.birth_time_rectification_action_receipts%rowtype;
  v_billing public.birth_time_rectification_billing%rowtype;
  v_receipt_action_id uuid :=
    public.conversational_rectification_billing_receipt_action_id(
      p_action_id,
      'release_fee'
    );
  v_balance integer;
  v_result_version bigint := p_expected_version;
  v_response jsonb;
  v_success boolean := true;
  v_error_code text;
  v_state text := 'released';
  v_fingerprint text := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    pg_catalog.jsonb_build_object(
      'kind', 'release_fee', 'userId', p_user_id, 'caseId', p_case_id,
      'expectedVersion', p_expected_version, 'actionId', p_action_id,
      'price', p_price
    )::text,
    'UTF8'
  )), 'hex');
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0
    or p_price is null or not (p_price between 1 and 1000000) then
    raise exception 'conversational_billing_failed' using errcode = 'P0001';
  end if;
  if p_case_id is distinct from p_action_id then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_user_id::text || ':' || p_action_id::text, 0)
  );

  select r.* into v_receipt
  from public.birth_time_rectification_action_receipts r
  where r.case_id = p_case_id and r.action_id = v_receipt_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.action_kind is distinct from 'release_fee'
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.request_fingerprint is distinct from v_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return query select
      (v_receipt.response ->> 'success')::boolean,
      nullif(v_receipt.response ->> 'credits', '')::integer,
      nullif(v_receipt.response ->> 'billing_state', ''),
      nullif(v_receipt.response ->> 'error_code', '');
    return;
  end if;

  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id
  for update;
  if found then
    if v_case.user_id is distinct from p_user_id
      or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
      raise exception 'conversational_case_not_found' using errcode = 'P0001';
    end if;
    if v_case.turn_version is distinct from p_expected_version then
      raise exception 'conversational_stale_turn' using errcode = 'P0001';
    end if;
    v_result_version := v_case.turn_version;
  elsif p_expected_version is distinct from 0 then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
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
  where b.case_id = p_case_id
  for update;

  if not found then
    insert into public.birth_time_rectification_billing (
      case_id, user_id, price, state, release_action_id,
      balance_after, released_at
    ) values (
      p_case_id, p_user_id, p_price, 'released', p_action_id,
      v_balance, pg_catalog.now()
    );
  elsif v_billing.user_id is distinct from p_user_id then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  elsif v_billing.state = 'released' then
    v_state := 'released';
  elsif v_billing.state = 'charged' then
    v_success := false;
    v_state := 'charged';
    v_error_code := 'already_charged';
  elsif v_billing.state = 'migration_waived' then
    v_state := 'migration_waived';
  else
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
    where case_id = p_case_id and user_id = p_user_id and state = 'reserved';
    if not found then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;

    -- Creation and fee settlement are separate calls. If settlement fails
    -- after the case was created, releasing the reservation must also close
    -- that unfinished case or it would block every later account-level start.
    if v_case.id is not null
      and v_case.status in ('starting', 'active', 'paused', 'confirming') then
      update public.birth_time_rectification_cases c
      set status = 'abandoned',
          turn_state = case
            when pg_catalog.jsonb_typeof(c.turn_state) = 'object'
              then pg_catalog.jsonb_set(
                c.turn_state, '{status}', pg_catalog.to_jsonb('abandoned'::text), true
              )
            else c.turn_state
          end,
          journey_snapshot = case
            when pg_catalog.jsonb_typeof(c.journey_snapshot) = 'object'
              then pg_catalog.jsonb_set(
                c.journey_snapshot, '{status}', pg_catalog.to_jsonb('abandoned'::text), true
              )
            else c.journey_snapshot
          end,
          updated_at = pg_catalog.now()
      where c.id = p_case_id
        and c.user_id = p_user_id
        and c.journey_protocol = 'conversational-evidence-v3'
        and c.turn_version = p_expected_version
        and c.status in ('starting', 'active', 'paused', 'confirming');
      if not found then
        raise exception 'conversational_stale_turn' using errcode = 'P0001';
      end if;
    end if;
  end if;

  v_response := pg_catalog.jsonb_build_object(
    'success', v_success, 'credits', v_balance,
    'billing_state', v_state, 'error_code', v_error_code
  );
  insert into public.birth_time_rectification_action_receipts (
    case_id, action_id, user_id, action_kind, expected_turn_version,
    result_turn_version, request_fingerprint, request, response
  ) values (
    p_case_id, v_receipt_action_id, p_user_id, 'release_fee', p_expected_version,
    v_result_version, v_fingerprint,
    public.conversational_rectification_action_request(
      'release_fee', p_user_id, p_case_id, p_expected_version,
      p_action_id, v_fingerprint
    ),
    v_response
  );
  return query select v_success, v_balance, v_state, v_error_code;
end;
$$;

revoke all on function public.reserve_conversational_rectification_fee(
  uuid, uuid, bigint, uuid, integer
) from public, anon, authenticated;
revoke all on function public.complete_conversational_rectification_fee(
  uuid, uuid, bigint, uuid
) from public, anon, authenticated;
revoke all on function public.release_conversational_rectification_fee(
  uuid, uuid, bigint, uuid, integer
) from public, anon, authenticated;

grant execute on function public.reserve_conversational_rectification_fee(
  uuid, uuid, bigint, uuid, integer
) to service_role;
grant execute on function public.complete_conversational_rectification_fee(
  uuid, uuid, bigint, uuid
) to service_role;
grant execute on function public.release_conversational_rectification_fee(
  uuid, uuid, bigint, uuid, integer
) to service_role;

commit;
