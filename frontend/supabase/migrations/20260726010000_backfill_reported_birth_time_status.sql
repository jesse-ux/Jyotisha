begin;

-- Repair declarations saved while the account route failed to derive the
-- server-owned status. Applied/candidate/confirmed minutes remain untouched.
update public.profiles
set birth_time_status = 'reported',
    updated_at = pg_catalog.now()
where birth_time_status is null
  and active_birth_time is null
  and birth_time is null
  and rectification_case_id is null
  and birth_date is not null
  and (
    (
      birth_time_source = 'hospital_record'
      and reported_birth_time is not null
      and birth_time_period is null
      and uncertainty_before_minutes = 2
      and uncertainty_after_minutes = 2
    )
    or (
      birth_time_source = 'family_exact'
      and reported_birth_time is not null
      and birth_time_period is null
      and uncertainty_before_minutes in (5, 10, 15)
      and uncertainty_after_minutes = uncertainty_before_minutes
    )
    or (
      birth_time_source = 'approximate'
      and reported_birth_time is not null
      and birth_time_period is null
      and uncertainty_before_minutes in (15, 30, 60)
      and uncertainty_after_minutes = uncertainty_before_minutes
    )
    or (
      birth_time_source = 'period_only'
      and reported_birth_time is null
      and birth_time_period in ('early_morning', 'morning', 'afternoon', 'evening', 'late_night')
      and uncertainty_before_minutes is null
      and uncertainty_after_minutes is null
    )
    or (
      birth_time_source = 'unknown'
      and reported_birth_time is null
      and birth_time_period is null
      and uncertainty_before_minutes is null
      and uncertainty_after_minutes is null
    )
    or (
      birth_time_source = 'legacy_import'
      and reported_birth_time is not null
      and birth_time_period is null
      and uncertainty_before_minutes is null
      and uncertainty_after_minutes is null
    )
  );

commit;
