begin;

alter table public.birth_time_rectification_v4_turns
  add column model_id text
  check (model_id is null or length(btrim(model_id)) between 1 and 120);

drop function public.submit_birth_time_rectification_v4_answer(
  uuid, uuid, uuid, bigint, uuid, uuid, text, uuid, text, text, uuid, timestamptz
);

create function public.submit_birth_time_rectification_v4_answer(
  p_user_id uuid, p_case_id uuid, p_action_id uuid, p_expected_version bigint,
  p_turn_id uuid, p_question_id uuid, p_question_domain text, p_question_target_event_id uuid, p_question text,
  p_answer text, p_model_id text, p_job_id uuid, p_now timestamptz
) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_case public.birth_time_rectification_v4_cases%rowtype; v_job_id uuid;
begin
  select action.job_id into v_job_id from public.birth_time_rectification_v4_actions action
    where action.user_id = p_user_id and action.action_id = p_action_id;
  if v_job_id is not null then return v_job_id; end if;
  select value.* into v_case from public.birth_time_rectification_v4_cases value
    where value.id = p_case_id and value.user_id = p_user_id for update;
  if not found then raise exception 'rectification_v4_case_not_found'; end if;
  if v_case.version <> p_expected_version then raise exception 'stale_rectification_v4_case'; end if;
  if v_case.status not in ('awaiting_answer', 'range_ready') then raise exception 'rectification_v4_case_not_awaiting_answer'; end if;
  insert into public.birth_time_rectification_v4_turns(
    id, case_id, user_id, case_version, question_id, question_domain, question_target_event_id,
    question, answer, model_id, action_id, created_at
  ) values (
    p_turn_id, p_case_id, p_user_id, p_expected_version + 1, p_question_id, p_question_domain, p_question_target_event_id,
    p_question, p_answer, nullif(btrim(p_model_id), ''), p_action_id, p_now
  );
  update public.birth_time_rectification_v4_cases set
    version = p_expected_version + 1, status = 'processing', phase = 'extracting_evidence',
    current_question = null, updated_at = p_now
    where id = p_case_id;
  insert into public.birth_time_rectification_v4_jobs(
    id, case_id, user_id, turn_id, status, phase, expected_case_version,
    evidence_set_hash, calculation_spec_hash, created_at, updated_at
  ) values (
    p_job_id, p_case_id, p_user_id, p_turn_id, 'pending', 'extracting_evidence', p_expected_version + 1,
    v_case.evidence_set_hash, v_case.calculation_spec_hash, p_now, p_now
  );
  insert into public.birth_time_rectification_v4_actions(user_id, action_id, case_id, job_id, created_at)
    values (p_user_id, p_action_id, p_case_id, p_job_id, p_now);
  return p_job_id;
end;
$$;

revoke all on function public.submit_birth_time_rectification_v4_answer(
  uuid, uuid, uuid, bigint, uuid, uuid, text, uuid, text, text, text, uuid, timestamptz
) from public, anon, authenticated;
grant execute on function public.submit_birth_time_rectification_v4_answer(
  uuid, uuid, uuid, bigint, uuid, uuid, text, uuid, text, text, text, uuid, timestamptz
) to service_role;

commit;
