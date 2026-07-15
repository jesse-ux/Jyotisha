begin;

alter table public.profiles
  add column if not exists latitude double precision,
  add column if not exists longitude double precision,
  add column if not exists timezone_offset double precision;

alter table public.profiles
  drop constraint if exists profiles_latitude_range,
  drop constraint if exists profiles_longitude_range,
  drop constraint if exists profiles_timezone_offset_range;

alter table public.profiles
  add constraint profiles_latitude_range check (latitude is null or latitude between -90 and 90),
  add constraint profiles_longitude_range check (longitude is null or longitude between -180 and 180),
  add constraint profiles_timezone_offset_range check (timezone_offset is null or timezone_offset between -12 and 14);

grant update (latitude, longitude, timezone_offset)
  on table public.profiles to authenticated;

commit;
