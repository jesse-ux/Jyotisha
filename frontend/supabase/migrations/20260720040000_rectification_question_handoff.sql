begin;

create table if not exists public.birth_time_rectification_question_handoffs (
  case_id uuid primary key
    references public.birth_time_rectification_cases(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  question text not null check (
    public.conversational_rectification_text_utf16_length(question) between 1 and 500
    and public.conversational_rectification_text_is_nonblank(question)
  ),
  question_fingerprint text not null check (question_fingerprint ~ '^[0-9a-f]{64}$'),
  attached_turn_version bigint not null check (attached_turn_version >= 0),
  attach_action_id uuid not null,
  state text not null check (state in ('pending', 'claimed', 'executing', 'consumed')),
  attempt integer not null default 0 check (attempt between 0 and 1000),
  request_id uuid not null,
  claim_action_id uuid,
  lease_expires_at timestamptz,
  claimed_at timestamptz,
  consumed_at timestamptz,
  created_at timestamptz not null default pg_catalog.now(),
  updated_at timestamptz not null default pg_catalog.now(),
  unique (user_id, request_id),
  check ((state in ('claimed', 'executing')) = (claim_action_id is not null)),
  check ((state in ('claimed', 'executing')) = (lease_expires_at is not null)),
  check ((state = 'consumed') = (consumed_at is not null))
);

create table if not exists public.birth_time_rectification_handoff_attach_receipts (
  case_id uuid not null references public.birth_time_rectification_cases(id) on delete cascade,
  action_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  expected_turn_version bigint not null check (expected_turn_version >= 0),
  question_fingerprint text not null check (question_fingerprint ~ '^[0-9a-f]{64}$'),
  response jsonb not null,
  created_at timestamptz not null default pg_catalog.now(),
  primary key (case_id, action_id)
);

create table if not exists public.birth_time_rectification_handoff_settlements (
  case_id uuid not null references public.birth_time_rectification_cases(id) on delete cascade,
  request_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  claim_action_id uuid not null,
  emitted boolean not null,
  response jsonb not null,
  created_at timestamptz not null default pg_catalog.now(),
  primary key (case_id, request_id)
);

create index if not exists birth_time_rectification_handoff_owner_state_idx
  on public.birth_time_rectification_question_handoffs (user_id, state, updated_at desc);

alter table public.birth_time_rectification_question_handoffs enable row level security;
alter table public.birth_time_rectification_handoff_attach_receipts enable row level security;
alter table public.birth_time_rectification_handoff_settlements enable row level security;

revoke all on table public.birth_time_rectification_question_handoffs
  from public, anon, authenticated;
revoke all on table public.birth_time_rectification_handoff_attach_receipts
  from public, anon, authenticated;
revoke all on table public.birth_time_rectification_handoff_settlements
  from public, anon, authenticated;
grant all on table public.birth_time_rectification_question_handoffs to service_role;
grant all on table public.birth_time_rectification_handoff_attach_receipts to service_role;
grant all on table public.birth_time_rectification_handoff_settlements to service_role;

create or replace function public.conversational_rectification_handoff_request_id(
  p_case_id uuid,
  p_attempt integer
)
returns uuid
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.md5(
    p_case_id::text || ':ordinary-consultation-handoff:' || p_attempt::text
  )::uuid;
$$;

create or replace function public.conversational_rectification_question_fingerprint(
  p_question text
)
returns text
language sql
immutable
strict
set search_path = ''
as $$
  select pg_catalog.encode(
    pg_catalog.sha256(pg_catalog.convert_to(p_question, 'UTF8')),
    'hex'
  );
$$;

create or replace function public.conversational_rectification_handoff_projection(
  p_user_id uuid,
  p_case_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select pg_catalog.jsonb_build_object(
    'caseId', h.case_id,
    'turnVersion', c.turn_version,
    'question', h.question,
    'questionFingerprint', h.question_fingerprint,
    'requestId', h.request_id,
    'status', case
      when h.state = 'pending' then 'pending'
      when h.state in ('claimed', 'executing') then 'in_progress'
      else 'consumed'
    end,
    'turn', public.conversational_rectification_case_projection(
      p_user_id, p_case_id
    ) -> 'latest_turn'
  )
  from public.birth_time_rectification_question_handoffs h
  join public.birth_time_rectification_cases c
    on c.id = h.case_id and c.user_id = h.user_id
  where h.case_id = p_case_id and h.user_id = p_user_id;
$$;

create or replace function public.seed_conversational_rectification_handoff()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.journey_protocol = 'conversational-evidence-v3'
    and new.pending_consultation_question is not null then
    insert into public.birth_time_rectification_question_handoffs (
      case_id, user_id, question, question_fingerprint,
      attached_turn_version, attach_action_id, state, attempt, request_id
    ) values (
      new.id, new.user_id, new.pending_consultation_question,
      public.conversational_rectification_question_fingerprint(
        new.pending_consultation_question
      ),
      new.turn_version, new.id, 'pending', 0,
      public.conversational_rectification_handoff_request_id(new.id, 0)
    ) on conflict (case_id) do nothing;
  end if;
  return new;
end;
$$;

drop trigger if exists birth_time_rectification_seed_question_handoff
  on public.birth_time_rectification_cases;
create trigger birth_time_rectification_seed_question_handoff
after insert on public.birth_time_rectification_cases
for each row execute function public.seed_conversational_rectification_handoff();

insert into public.birth_time_rectification_question_handoffs (
  case_id, user_id, question, question_fingerprint,
  attached_turn_version, attach_action_id, state, attempt, request_id
)
select
  c.id, c.user_id, c.pending_consultation_question,
  public.conversational_rectification_question_fingerprint(
    c.pending_consultation_question
  ),
  c.turn_version, c.id, 'pending', 0,
  public.conversational_rectification_handoff_request_id(c.id, 0)
from public.birth_time_rectification_cases c
where c.journey_protocol = 'conversational-evidence-v3'
  and c.pending_consultation_question is not null
on conflict (case_id) do nothing;

create or replace function public.attach_conversational_rectification_question(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_question text,
  p_question_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_handoff public.birth_time_rectification_question_handoffs%rowtype;
  v_receipt public.birth_time_rectification_handoff_attach_receipts%rowtype;
  v_response jsonb;
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0
    or p_question is null or p_question_fingerprint is null
    or p_question_fingerprint !~ '^[0-9a-f]{64}$'
    or public.conversational_rectification_text_utf16_length(p_question) not between 1 and 500
    or public.conversational_rectification_text_is_nonblank(p_question) is not true
    or public.conversational_rectification_question_fingerprint(p_question)
      is distinct from p_question_fingerprint then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':attach-question', 0
    )
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;

  select r.* into v_receipt
  from public.birth_time_rectification_handoff_attach_receipts r
  where r.case_id = p_case_id and r.action_id = p_action_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.expected_turn_version is distinct from p_expected_version
      or v_receipt.question_fingerprint is distinct from p_question_fingerprint then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;

  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;
  if v_case.status not in ('starting', 'active', 'paused', 'confirming') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select h.* into v_handoff
  from public.birth_time_rectification_question_handoffs h
  where h.case_id = p_case_id and h.user_id = p_user_id
  for update;
  if found and v_handoff.state <> 'pending' then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  insert into public.birth_time_rectification_question_handoffs (
    case_id, user_id, question, question_fingerprint,
    attached_turn_version, attach_action_id, state, attempt, request_id,
    claim_action_id, lease_expires_at, claimed_at, consumed_at, updated_at
  ) values (
    p_case_id, p_user_id, p_question, p_question_fingerprint,
    p_expected_version, p_action_id, 'pending', 0,
    public.conversational_rectification_handoff_request_id(p_case_id, 0),
    null, null, null, null, pg_catalog.now()
  ) on conflict (case_id) do update set
    question = excluded.question,
    question_fingerprint = excluded.question_fingerprint,
    attached_turn_version = excluded.attached_turn_version,
    attach_action_id = excluded.attach_action_id,
    state = 'pending',
    attempt = 0,
    request_id = excluded.request_id,
    claim_action_id = null,
    lease_expires_at = null,
    claimed_at = null,
    consumed_at = null,
    updated_at = pg_catalog.now();

  update public.birth_time_rectification_cases
  set pending_consultation_question = p_question,
      turn_state = pg_catalog.jsonb_set(
        turn_state, '{pendingConsultationQuestion}', pg_catalog.to_jsonb(p_question), true
      ),
      journey_snapshot = pg_catalog.jsonb_set(
        journey_snapshot, '{pendingConsultationQuestion}', pg_catalog.to_jsonb(p_question), true
      ),
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id
    and turn_version = p_expected_version;
  if not found then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;

  v_response := public.conversational_rectification_case_projection(
    p_user_id, p_case_id
  );
  insert into public.birth_time_rectification_handoff_attach_receipts (
    case_id, action_id, user_id, expected_turn_version,
    question_fingerprint, response
  ) values (
    p_case_id, p_action_id, p_user_id, p_expected_version,
    p_question_fingerprint, v_response
  );
  return v_response;
end;
$$;

create or replace function public.load_conversational_rectification_handoff(
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
  v_case_id uuid;
begin
  if p_user_id is null then
    return null;
  end if;
  if p_case_id is not null then
    v_case_id := p_case_id;
  else
    select h.case_id into v_case_id
    from public.birth_time_rectification_question_handoffs h
    where h.user_id = p_user_id and h.state <> 'consumed'
    order by h.updated_at desc, h.created_at desc
    limit 1;
  end if;
  return public.conversational_rectification_handoff_projection(
    p_user_id, v_case_id
  );
end;
$$;

create or replace function public.consume_conversational_rectification_handoff(
  p_user_id uuid,
  p_case_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_actions jsonb;
begin
  select coalesce(pg_catalog.jsonb_agg(action.value), '[]'::jsonb)
    into v_actions
  from public.birth_time_rectification_cases c
  join public.birth_time_rectification_turns t
    on t.case_id = c.id and t.turn_version = c.turn_version
  cross join lateral pg_catalog.jsonb_array_elements(t.actions) action(value)
  where c.id = p_case_id and c.user_id = p_user_id
    and action.value #>> '{}' <> 'continue_original_question';

  update public.birth_time_rectification_turns t
  set actions = coalesce(v_actions, '[]'::jsonb)
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
    and t.case_id = c.id and t.turn_version = c.turn_version;

  update public.birth_time_rectification_cases
  set pending_consultation_question = null,
      turn_state = pg_catalog.jsonb_set(
        pg_catalog.jsonb_set(
          turn_state, '{pendingConsultationQuestion}', 'null'::jsonb, true
        ),
        '{actions}', coalesce(v_actions, '[]'::jsonb), true
      ),
      journey_snapshot = pg_catalog.jsonb_set(
        pg_catalog.jsonb_set(
          journey_snapshot, '{pendingConsultationQuestion}', 'null'::jsonb, true
        ),
        '{actions}', coalesce(v_actions, '[]'::jsonb), true
      ),
      updated_at = pg_catalog.now()
  where id = p_case_id and user_id = p_user_id;

  update public.birth_time_rectification_question_handoffs
  set state = 'consumed', claim_action_id = null, lease_expires_at = null,
      consumed_at = coalesce(consumed_at, pg_catalog.now()),
      updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
end;
$$;

create or replace function public.claim_conversational_rectification_handoff(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_action_id uuid,
  p_question_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_handoff public.birth_time_rectification_question_handoffs%rowtype;
  v_request_status text;
begin
  if p_user_id is null or p_case_id is null or p_action_id is null
    or p_expected_version is null or p_expected_version < 0
    or p_question_fingerprint is null
    or p_question_fingerprint !~ '^[0-9a-f]{64}$' then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':claim-handoff', 0
    )
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  if not found or v_case.journey_protocol is distinct from 'conversational-evidence-v3' then
    raise exception 'conversational_case_not_found' using errcode = 'P0001';
  end if;
  if v_case.turn_version is distinct from p_expected_version then
    raise exception 'conversational_stale_turn' using errcode = 'P0001';
  end if;
  if v_case.status is distinct from 'completed' then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  select h.* into v_handoff
  from public.birth_time_rectification_question_handoffs h
  where h.case_id = p_case_id and h.user_id = p_user_id
  for update;
  if not found
    or v_handoff.question_fingerprint is distinct from p_question_fingerprint then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if v_handoff.state = 'consumed' then
    return public.conversational_rectification_handoff_projection(p_user_id, p_case_id);
  end if;
  if v_case.pending_consultation_question is distinct from v_handoff.question then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  if v_handoff.state in ('claimed', 'executing')
    and v_handoff.lease_expires_at > pg_catalog.now() then
    if v_handoff.state = 'claimed' and v_handoff.claim_action_id = p_action_id then
      return public.conversational_rectification_handoff_projection(p_user_id, p_case_id)
        || pg_catalog.jsonb_build_object('status', 'claimed');
    end if;
    return public.conversational_rectification_handoff_projection(p_user_id, p_case_id)
      || pg_catalog.jsonb_build_object('status', 'in_progress');
  end if;

  select request.status into v_request_status
  from public.consultation_requests request
  where request.user_id = p_user_id and request.request_id = v_handoff.request_id::text
  for update;
  if v_request_status = 'completed' then
    perform public.consume_conversational_rectification_handoff(p_user_id, p_case_id);
    return public.conversational_rectification_handoff_projection(p_user_id, p_case_id);
  end if;
  if v_request_status = 'cancelled' then
    update public.birth_time_rectification_question_handoffs
    set attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        )
    where case_id = p_case_id and user_id = p_user_id;
  end if;

  update public.birth_time_rectification_question_handoffs
  set state = 'claimed', claim_action_id = p_action_id,
      lease_expires_at = pg_catalog.now() + interval '2 minutes',
      claimed_at = pg_catalog.now(), consumed_at = null,
      updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
  return public.conversational_rectification_handoff_projection(p_user_id, p_case_id)
    || pg_catalog.jsonb_build_object('status', 'claimed');
end;
$$;

create or replace function public.begin_conversational_rectification_handoff_execution(
  p_user_id uuid,
  p_case_id uuid,
  p_expected_version bigint,
  p_claim_action_id uuid,
  p_request_id uuid,
  p_question_fingerprint text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_case public.birth_time_rectification_cases%rowtype;
  v_handoff public.birth_time_rectification_question_handoffs%rowtype;
  v_request_status text;
  v_credits integer;
begin
  if p_user_id is null or p_case_id is null or p_claim_action_id is null
    or p_request_id is null or p_expected_version is null or p_expected_version < 0
    or p_question_fingerprint is null
    or p_question_fingerprint !~ '^[0-9a-f]{64}$' then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':execute-handoff', 0
    )
  );
  select c.* into v_case
  from public.birth_time_rectification_cases c
  where c.id = p_case_id and c.user_id = p_user_id
  for update;
  select h.* into v_handoff
  from public.birth_time_rectification_question_handoffs h
  where h.case_id = p_case_id and h.user_id = p_user_id
  for update;
  if v_case.id is null or v_handoff.case_id is null
    or v_case.journey_protocol is distinct from 'conversational-evidence-v3'
    or v_case.status is distinct from 'completed'
    or v_case.turn_version is distinct from p_expected_version
    or v_handoff.question_fingerprint is distinct from p_question_fingerprint
    or v_handoff.request_id is distinct from p_request_id then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if v_handoff.state = 'consumed' then
    return pg_catalog.jsonb_build_object(
      'status', 'consumed', 'requestId', v_handoff.request_id
    );
  end if;
  if v_handoff.claim_action_id is distinct from p_claim_action_id
    or v_handoff.lease_expires_at <= pg_catalog.now() then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  if v_handoff.state = 'executing' then
    return pg_catalog.jsonb_build_object(
      'status', 'in_progress', 'requestId', v_handoff.request_id
    );
  end if;
  if v_handoff.state is distinct from 'claimed' then
    return pg_catalog.jsonb_build_object(
      'status', case when v_handoff.state = 'consumed' then 'consumed' else 'in_progress' end,
      'requestId', v_handoff.request_id
    );
  end if;

  select request.status into v_request_status
  from public.consultation_requests request
  where request.user_id = p_user_id and request.request_id = p_request_id::text
  for update;
  if v_request_status = 'completed' then
    perform public.consume_conversational_rectification_handoff(p_user_id, p_case_id);
    return pg_catalog.jsonb_build_object('status', 'consumed', 'requestId', p_request_id);
  end if;
  if v_request_status = 'cancelled' then
    update public.birth_time_rectification_question_handoffs
    set state = 'pending', attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        ),
        claim_action_id = null, lease_expires_at = null, updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id;
    return pg_catalog.jsonb_build_object('status', 'released', 'requestId', p_request_id);
  end if;

  select profile.credits into v_credits
  from public.profiles profile where profile.id = p_user_id;
  update public.birth_time_rectification_question_handoffs
  set state = 'executing',
      lease_expires_at = pg_catalog.now() + interval '2 minutes',
      updated_at = pg_catalog.now()
  where case_id = p_case_id and user_id = p_user_id;
  return pg_catalog.jsonb_build_object(
    'status', 'ready',
    'requestId', p_request_id,
    'billingReused', coalesce(v_request_status = 'reserved', false),
    'credits', v_credits
  );
end;
$$;

create or replace function public.settle_conversational_rectification_handoff(
  p_user_id uuid,
  p_case_id uuid,
  p_claim_action_id uuid,
  p_request_id uuid,
  p_emitted boolean
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_handoff public.birth_time_rectification_question_handoffs%rowtype;
  v_receipt public.birth_time_rectification_handoff_settlements%rowtype;
  v_success boolean;
  v_credits integer;
  v_error text;
  v_response jsonb;
begin
  if p_user_id is null or p_case_id is null or p_claim_action_id is null
    or p_request_id is null or p_emitted is null then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      p_user_id::text || ':' || p_case_id::text || ':settle-handoff', 0
    )
  );
  select s.* into v_receipt
  from public.birth_time_rectification_handoff_settlements s
  where s.case_id = p_case_id and s.request_id = p_request_id
  for update;
  if found then
    if v_receipt.user_id is distinct from p_user_id
      or v_receipt.claim_action_id is distinct from p_claim_action_id
      or v_receipt.emitted is distinct from p_emitted then
      raise exception 'conversational_action_conflict' using errcode = 'P0001';
    end if;
    return v_receipt.response;
  end if;

  select h.* into v_handoff
  from public.birth_time_rectification_question_handoffs h
  where h.case_id = p_case_id and h.user_id = p_user_id
  for update;
  if not found or v_handoff.request_id is distinct from p_request_id
    or v_handoff.claim_action_id is distinct from p_claim_action_id
    or v_handoff.state not in ('claimed', 'executing') then
    raise exception 'conversational_action_conflict' using errcode = 'P0001';
  end if;

  if p_emitted then
    select result.success, result.credits, result.error_code
      into v_success, v_credits, v_error
    from public.complete_consultation_credit(
      p_user_id, p_request_id::text
    ) result;
    if v_success is not true then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;
    perform public.consume_conversational_rectification_handoff(p_user_id, p_case_id);
    v_response := pg_catalog.jsonb_build_object(
      'status', 'consumed', 'requestId', p_request_id, 'credits', v_credits
    );
  else
    select result.success, result.credits, result.error_code
      into v_success, v_credits, v_error
    from public.cancel_consultation_credit(
      p_user_id, p_request_id::text
    ) result;
    if v_success is not true then
      raise exception 'conversational_billing_failed' using errcode = 'P0001';
    end if;
    update public.birth_time_rectification_question_handoffs
    set state = 'pending', attempt = attempt + 1,
        request_id = public.conversational_rectification_handoff_request_id(
          p_case_id, attempt + 1
        ),
        claim_action_id = null, lease_expires_at = null,
        claimed_at = null, updated_at = pg_catalog.now()
    where case_id = p_case_id and user_id = p_user_id;
    v_response := pg_catalog.jsonb_build_object(
      'status', 'pending', 'requestId', p_request_id, 'credits', v_credits
    );
  end if;

  insert into public.birth_time_rectification_handoff_settlements (
    case_id, request_id, user_id, claim_action_id, emitted, response
  ) values (
    p_case_id, p_request_id, p_user_id, p_claim_action_id, p_emitted, v_response
  );
  return v_response;
end;
$$;

revoke all on function public.conversational_rectification_handoff_request_id(uuid, integer)
  from public, anon, authenticated, service_role;
revoke all on function public.conversational_rectification_question_fingerprint(text)
  from public, anon, authenticated, service_role;
revoke all on function public.conversational_rectification_handoff_projection(uuid, uuid)
  from public, anon, authenticated, service_role;
revoke all on function public.seed_conversational_rectification_handoff()
  from public, anon, authenticated, service_role;
revoke all on function public.consume_conversational_rectification_handoff(uuid, uuid)
  from public, anon, authenticated, service_role;

revoke all on function public.attach_conversational_rectification_question(
  uuid, uuid, bigint, uuid, text, text
) from public, anon, authenticated;
revoke all on function public.load_conversational_rectification_handoff(uuid, uuid)
  from public, anon, authenticated;
revoke all on function public.claim_conversational_rectification_handoff(
  uuid, uuid, bigint, uuid, text
) from public, anon, authenticated;
revoke all on function public.begin_conversational_rectification_handoff_execution(
  uuid, uuid, bigint, uuid, uuid, text
) from public, anon, authenticated;
revoke all on function public.settle_conversational_rectification_handoff(
  uuid, uuid, uuid, uuid, boolean
) from public, anon, authenticated;

grant execute on function public.attach_conversational_rectification_question(
  uuid, uuid, bigint, uuid, text, text
) to service_role;
grant execute on function public.load_conversational_rectification_handoff(uuid, uuid)
  to service_role;
grant execute on function public.claim_conversational_rectification_handoff(
  uuid, uuid, bigint, uuid, text
) to service_role;
grant execute on function public.begin_conversational_rectification_handoff_execution(
  uuid, uuid, bigint, uuid, uuid, text
) to service_role;
grant execute on function public.settle_conversational_rectification_handoff(
  uuid, uuid, uuid, uuid, boolean
) to service_role;

commit;
