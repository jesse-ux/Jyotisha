begin;

grant select, insert, update on table public.profiles to service_role;

grant select (
  id,
  email,
  credits,
  created_at,
  updated_at,
  name,
  birth_date,
  birth_time,
  country_code,
  province_code,
  city_code,
  district_code,
  latitude,
  longitude,
  timezone_offset
) on public.profiles to service_role;

grant insert (
  id,
  email,
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
) on public.profiles to service_role;

grant update (
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
) on public.profiles to service_role;

commit;
