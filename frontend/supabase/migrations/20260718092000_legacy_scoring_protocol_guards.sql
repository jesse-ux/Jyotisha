begin;

alter function public.create_birth_time_scoring_job(
  uuid, uuid, uuid, bigint, uuid, text, text, timestamptz,
  jsonb, jsonb, jsonb, integer, text[]
) rename to create_birth_time_scoring_job_without_protocol_guard;
alter function public.claim_birth_time_scoring_job(
  uuid, uuid, uuid, text, text, timestamptz
) rename to claim_birth_time_scoring_job_without_protocol_guard;
alter function public.complete_birth_time_scoring_job(
  uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb,
  time without time zone, time without time zone, integer, text[]
) rename to complete_birth_time_scoring_job_without_protocol_guard;
alter function public.fail_birth_time_scoring_job(
  uuid, uuid, uuid, bigint, text, text, jsonb
) rename to fail_birth_time_scoring_job_without_protocol_guard;

create function public.create_birth_time_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_expected_version bigint, p_action_id uuid,
  p_evidence_fingerprint text, p_algorithm_version text,
  p_expires_at timestamptz, p_snapshot jsonb, p_turn_state jsonb,
  p_life_events jsonb, p_adaptive_round integer, p_asked_domains text[]
) returns uuid language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  return public.create_birth_time_scoring_job_without_protocol_guard(
    p_user_id, p_case_id, p_job_id, p_expected_version, p_action_id,
    p_evidence_fingerprint, p_algorithm_version, p_expires_at,
    p_snapshot, p_turn_state, p_life_events, p_adaptive_round, p_asked_domains
  );
end;
$$;

create function public.claim_birth_time_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_evidence_fingerprint text, p_algorithm_version text, p_now timestamptz
) returns table (claim_state text, algorithm_version text)
language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  return query select *
  from public.claim_birth_time_scoring_job_without_protocol_guard(
    p_user_id, p_case_id, p_job_id, p_evidence_fingerprint,
    p_algorithm_version, p_now
  );
end;
$$;

create function public.complete_birth_time_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_expected_version bigint, p_evidence_fingerprint text,
  p_snapshot jsonb, p_turn_state jsonb, p_candidate_result jsonb,
  p_candidate_start time without time zone,
  p_candidate_end time without time zone,
  p_adaptive_round integer, p_asked_domains text[]
) returns void language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  perform public.complete_birth_time_scoring_job_without_protocol_guard(
    p_user_id, p_case_id, p_job_id, p_expected_version,
    p_evidence_fingerprint, p_snapshot, p_turn_state, p_candidate_result,
    p_candidate_start, p_candidate_end, p_adaptive_round, p_asked_domains
  );
end;
$$;

create function public.fail_birth_time_scoring_job(
  p_user_id uuid, p_case_id uuid, p_job_id uuid,
  p_expected_version bigint, p_evidence_fingerprint text,
  p_failure_code text, p_turn_state jsonb
) returns void language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  perform public.fail_birth_time_scoring_job_without_protocol_guard(
    p_user_id, p_case_id, p_job_id, p_expected_version,
    p_evidence_fingerprint, p_failure_code, p_turn_state
  );
end;
$$;

revoke all on function public.create_birth_time_scoring_job_without_protocol_guard(uuid, uuid, uuid, bigint, uuid, text, text, timestamptz, jsonb, jsonb, jsonb, integer, text[]) from public, anon, authenticated, service_role;
revoke all on function public.claim_birth_time_scoring_job_without_protocol_guard(uuid, uuid, uuid, text, text, timestamptz) from public, anon, authenticated, service_role;
revoke all on function public.complete_birth_time_scoring_job_without_protocol_guard(uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb, time without time zone, time without time zone, integer, text[]) from public, anon, authenticated, service_role;
revoke all on function public.fail_birth_time_scoring_job_without_protocol_guard(uuid, uuid, uuid, bigint, text, text, jsonb) from public, anon, authenticated, service_role;
revoke all on function public.create_birth_time_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, timestamptz, jsonb, jsonb, jsonb, integer, text[]) from public, anon, authenticated;
revoke all on function public.claim_birth_time_scoring_job(uuid, uuid, uuid, text, text, timestamptz) from public, anon, authenticated;
revoke all on function public.complete_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb, time without time zone, time without time zone, integer, text[]) from public, anon, authenticated;
revoke all on function public.fail_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb) from public, anon, authenticated;
grant execute on function public.create_birth_time_scoring_job(uuid, uuid, uuid, bigint, uuid, text, text, timestamptz, jsonb, jsonb, jsonb, integer, text[]) to service_role;
grant execute on function public.claim_birth_time_scoring_job(uuid, uuid, uuid, text, text, timestamptz) to service_role;
grant execute on function public.complete_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, jsonb, jsonb, jsonb, time without time zone, time without time zone, integer, text[]) to service_role;
grant execute on function public.fail_birth_time_scoring_job(uuid, uuid, uuid, bigint, text, text, jsonb) to service_role;

commit;
