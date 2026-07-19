begin;

grant insert (
  reported_birth_time,
  birth_time_source,
  birth_time_period,
  birth_time_clue,
  uncertainty_before_minutes,
  uncertainty_after_minutes
) on table public.profiles to service_role;

grant select (
  reported_birth_time,
  birth_time_source,
  birth_time_period,
  birth_time_clue,
  uncertainty_before_minutes,
  uncertainty_after_minutes
) on table public.profiles to service_role;

commit;
