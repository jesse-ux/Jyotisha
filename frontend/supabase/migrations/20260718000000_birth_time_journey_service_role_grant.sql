begin;

-- The birth-time journey route persists through the service-role client.
-- RLS bypass does not replace the explicit column privileges required by PostgREST.
grant update (
  reported_birth_time,
  active_birth_time,
  birth_time,
  birth_time_source,
  birth_time_period,
  birth_time_clue,
  uncertainty_before_minutes,
  uncertainty_after_minutes,
  birth_time_status,
  rectification_confidence,
  rectification_case_id
) on table public.profiles to service_role;

commit;
