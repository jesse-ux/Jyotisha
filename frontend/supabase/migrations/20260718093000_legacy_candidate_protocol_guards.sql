begin;

alter function public.confirm_birth_time_candidate(
  uuid, uuid, uuid, time without time zone, jsonb
) rename to confirm_birth_time_candidate_without_protocol_guard;
alter function public.save_guided_birth_time_candidate(
  uuid, uuid, uuid, uuid, integer, jsonb
) rename to save_guided_birth_time_candidate_without_protocol_guard;
alter function public.confirm_guided_birth_time_candidate(
  uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb
) rename to confirm_guided_birth_time_candidate_without_protocol_guard;

create function public.confirm_birth_time_candidate(
  p_user_id uuid, p_case_id uuid, p_result_id uuid,
  p_time time without time zone, p_snapshot jsonb
) returns void language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  perform public.confirm_birth_time_candidate_without_protocol_guard(
    p_user_id, p_case_id, p_result_id, p_time, p_snapshot
  );
end;
$$;

create function public.save_guided_birth_time_candidate(
  p_user_id uuid, p_case_id uuid, p_result_id uuid,
  p_action_id uuid, p_expected_version integer, p_turn_state jsonb
) returns void language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  perform public.save_guided_birth_time_candidate_without_protocol_guard(
    p_user_id, p_case_id, p_result_id, p_action_id,
    p_expected_version, p_turn_state
  );
end;
$$;

create function public.confirm_guided_birth_time_candidate(
  p_user_id uuid, p_case_id uuid, p_result_id uuid,
  p_time time without time zone, p_action_id uuid,
  p_expected_version integer, p_snapshot jsonb, p_turn_state jsonb
) returns void language plpgsql security definer set search_path = '' as $$
begin
  perform 1 from public.birth_time_rectification_cases
  where id = p_case_id and user_id = p_user_id
    and journey_protocol = 'legacy-guided-v1' for update;
  if not found then raise exception 'birth_time_legacy_protocol_required'; end if;
  perform public.confirm_guided_birth_time_candidate_without_protocol_guard(
    p_user_id, p_case_id, p_result_id, p_time, p_action_id,
    p_expected_version, p_snapshot, p_turn_state
  );
end;
$$;

revoke all on function public.confirm_birth_time_candidate_without_protocol_guard(uuid, uuid, uuid, time without time zone, jsonb) from public, anon, authenticated, service_role;
revoke all on function public.save_guided_birth_time_candidate_without_protocol_guard(uuid, uuid, uuid, uuid, integer, jsonb) from public, anon, authenticated, service_role;
revoke all on function public.confirm_guided_birth_time_candidate_without_protocol_guard(uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb) from public, anon, authenticated, service_role;
revoke all on function public.confirm_birth_time_candidate(uuid, uuid, uuid, time without time zone, jsonb) from public, anon, authenticated;
revoke all on function public.save_guided_birth_time_candidate(uuid, uuid, uuid, uuid, integer, jsonb) from public, anon, authenticated;
revoke all on function public.confirm_guided_birth_time_candidate(uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb) from public, anon, authenticated;
grant execute on function public.confirm_birth_time_candidate(uuid, uuid, uuid, time without time zone, jsonb) to service_role;
grant execute on function public.save_guided_birth_time_candidate(uuid, uuid, uuid, uuid, integer, jsonb) to service_role;
grant execute on function public.confirm_guided_birth_time_candidate(uuid, uuid, uuid, time without time zone, uuid, integer, jsonb, jsonb) to service_role;

commit;
