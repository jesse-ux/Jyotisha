begin;

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
      when h.state in ('claimed', 'executing')
        and h.lease_expires_at <= pg_catalog.now() then 'pending'
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

commit;
