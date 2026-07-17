begin;

alter table public.profiles
  add column if not exists reported_birth_time time without time zone,
  add column if not exists active_birth_time time without time zone,
  add column if not exists birth_time_source text,
  add column if not exists birth_time_period text,
  add column if not exists birth_time_clue text,
  add column if not exists uncertainty_before_minutes integer,
  add column if not exists uncertainty_after_minutes integer,
  add column if not exists birth_time_status text,
  add column if not exists rectification_confidence numeric(5, 2),
  add column if not exists rectification_case_id uuid;

update public.profiles
set
  reported_birth_time = coalesce(reported_birth_time, birth_time),
  active_birth_time = coalesce(active_birth_time, birth_time),
  birth_time_source = coalesce(birth_time_source, 'legacy_import'),
  birth_time_status = coalesce(birth_time_status, 'confirmed')
where birth_time is not null;

alter table public.profiles
  drop constraint if exists profiles_birth_time_source_check,
  drop constraint if exists profiles_birth_time_period_check,
  drop constraint if exists profiles_birth_time_status_check,
  drop constraint if exists profiles_uncertainty_before_range,
  drop constraint if exists profiles_uncertainty_after_range,
  drop constraint if exists profiles_rectification_confidence_range;

alter table public.profiles
  add constraint profiles_birth_time_source_check check (
    birth_time_source is null or birth_time_source in (
      'hospital_record',
      'family_exact',
      'approximate',
      'period_only',
      'unknown',
      'legacy_import'
    )
  ),
  add constraint profiles_birth_time_period_check check (
    birth_time_period is null or birth_time_period in (
      'early_morning',
      'morning',
      'afternoon',
      'evening',
      'late_night'
    )
  ),
  add constraint profiles_birth_time_status_check check (
    birth_time_status is null or birth_time_status in (
      'reported',
      'assessing',
      'rectifying',
      'candidate',
      'confirmed'
    )
  ),
  add constraint profiles_uncertainty_before_range check (
    uncertainty_before_minutes is null or uncertainty_before_minutes between 0 and 720
  ),
  add constraint profiles_uncertainty_after_range check (
    uncertainty_after_minutes is null or uncertainty_after_minutes between 0 and 720
  ),
  add constraint profiles_rectification_confidence_range check (
    rectification_confidence is null or rectification_confidence between 0 and 100
  );

create table if not exists public.birth_time_rectification_cases (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'assessing' check (
    status in ('assessing', 'rectifying', 'candidate', 'confirmed')
  ),
  reported_date date not null,
  reported_time time without time zone,
  reported_period text,
  source text not null,
  uncertainty_before_minutes integer,
  uncertainty_after_minutes integer,
  questionnaire jsonb not null default '{}'::jsonb check (jsonb_typeof(questionnaire) = 'object'),
  journey_snapshot jsonb not null default '{}'::jsonb check (jsonb_typeof(journey_snapshot) = 'object'),
  answers jsonb not null default '{}'::jsonb check (jsonb_typeof(answers) = 'object'),
  candidate_scan jsonb not null default '{}'::jsonb check (jsonb_typeof(candidate_scan) = 'object'),
  scoring_result jsonb not null default '{}'::jsonb check (jsonb_typeof(scoring_result) = 'object'),
  candidate_start time without time zone,
  candidate_end time without time zone,
  algorithm_version text not null default 'birth-time-journey-v1',
  ayanamsa text not null default 'lahiri',
  node_mode text not null default 'true',
  confirmed_time time without time zone,
  confirmed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles
  drop constraint if exists profiles_rectification_case_id_fkey,
  add constraint profiles_rectification_case_id_fkey
    foreign key (rectification_case_id)
    references public.birth_time_rectification_cases(id)
    on delete set null;

create or replace function public.guard_birth_time_journey()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if old.reported_birth_time is not null
     and new.reported_birth_time is distinct from old.reported_birth_time then
    raise exception 'reported_birth_time_is_immutable';
  end if;

  if new.active_birth_time is distinct from old.active_birth_time then
    new.birth_time := new.active_birth_time;
  elsif new.birth_time is distinct from old.birth_time then
    new.active_birth_time := new.birth_time;
  end if;

  if new.reported_birth_time is null and new.birth_time is not null then
    new.reported_birth_time := new.birth_time;
  end if;
  if new.birth_time_source is null and new.birth_time is not null then
    new.birth_time_source := 'legacy_import';
  end if;
  if new.birth_time_status is null and new.active_birth_time is not null then
    new.birth_time_status := 'confirmed';
  end if;

  return new;
end;
$$;

drop trigger if exists profiles_guard_birth_time_journey on public.profiles;
create trigger profiles_guard_birth_time_journey
before update of birth_time, reported_birth_time, active_birth_time on public.profiles
for each row execute function public.guard_birth_time_journey();

alter table public.birth_time_rectification_cases enable row level security;

drop policy if exists birth_time_cases_select_own on public.birth_time_rectification_cases;
create policy birth_time_cases_select_own
on public.birth_time_rectification_cases
for select to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists birth_time_cases_insert_own on public.birth_time_rectification_cases;
create policy birth_time_cases_insert_own
on public.birth_time_rectification_cases
for insert to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists birth_time_cases_update_own on public.birth_time_rectification_cases;
create policy birth_time_cases_update_own
on public.birth_time_rectification_cases
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

revoke all on table public.birth_time_rectification_cases from anon, authenticated, service_role;
grant all on table public.birth_time_rectification_cases to service_role;
grant select on table public.birth_time_rectification_cases to authenticated;
grant insert (
  id,
  user_id,
  status,
  reported_date,
  reported_time,
  reported_period,
  source,
  uncertainty_before_minutes,
  uncertainty_after_minutes,
  questionnaire,
  journey_snapshot,
  answers,
  candidate_scan,
  scoring_result,
  candidate_start,
  candidate_end,
  updated_at
) on table public.birth_time_rectification_cases to authenticated;
grant update (
  status,
  questionnaire,
  journey_snapshot,
  answers,
  candidate_scan,
  scoring_result,
  candidate_start,
  candidate_end,
  confirmed_time,
  confirmed_at,
  updated_at
) on table public.birth_time_rectification_cases to authenticated;

grant update (
  reported_birth_time,
  active_birth_time,
  birth_time_source,
  birth_time_period,
  birth_time_clue,
  uncertainty_before_minutes,
  uncertainty_after_minutes,
  birth_time_status,
  rectification_confidence,
  rectification_case_id
) on table public.profiles to authenticated;

commit;
