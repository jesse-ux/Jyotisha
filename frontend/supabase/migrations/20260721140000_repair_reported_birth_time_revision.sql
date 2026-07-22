begin;

-- The reported declaration belongs to the user and can be revised from the
-- profile editor. Candidate or confirmed application times remain separate.
create or replace function public.guard_birth_time_journey()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.active_birth_time is distinct from old.active_birth_time then
    new.birth_time := new.active_birth_time;
  elsif new.birth_time is distinct from old.birth_time then
    new.active_birth_time := new.birth_time;
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

-- Earlier trigger behavior copied an applied candidate minute into the
-- reported field even when the user had declared only a period or no time.
update public.profiles
set reported_birth_time = null,
    updated_at = pg_catalog.now()
where birth_time_source in ('period_only', 'unknown')
  and reported_birth_time is not null;

alter table public.profiles
  drop constraint if exists profiles_reported_birth_time_source_consistency,
  add constraint profiles_reported_birth_time_source_consistency check (
    birth_time_source not in ('period_only', 'unknown')
    or reported_birth_time is null
  );

commit;
