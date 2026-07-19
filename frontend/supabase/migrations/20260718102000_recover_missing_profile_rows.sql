begin;

drop policy if exists profiles_insert_own on public.profiles;
create policy profiles_insert_own
  on public.profiles
  for insert
  to authenticated
  with check ((select auth.uid()) = id);

grant insert (
  id,
  name,
  birth_date,
  birth_time,
  country_code,
  province_code,
  city_code,
  district_code,
  latitude,
  longitude,
  timezone_offset,
  updated_at
) on public.profiles to authenticated;

commit;
