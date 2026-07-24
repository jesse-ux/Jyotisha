begin;

alter table public.profiles
  add column if not exists birth_place_label text,
  add column if not exists birth_place_type text,
  add column if not exists birth_place_provider text,
  add column if not exists birth_place_provider_id text,
  add column if not exists timezone_id text,
  add column if not exists timezone_source text;

alter table public.profiles
  drop constraint if exists profiles_birth_place_provider_check,
  drop constraint if exists profiles_timezone_source_check;

alter table public.profiles
  add constraint profiles_birth_place_provider_check
    check (birth_place_provider is null or birth_place_provider in ('geoapify', 'china_locations', 'mapbox', 'geonames')),
  add constraint profiles_timezone_source_check
    check (timezone_source is null or timezone_source in ('iana_historical'));

grant update (
  birth_place_label,
  birth_place_type,
  birth_place_provider,
  birth_place_provider_id,
  timezone_id,
  timezone_source
) on table public.profiles to authenticated;

grant select, insert, update (
  birth_place_label,
  birth_place_type,
  birth_place_provider,
  birth_place_provider_id,
  timezone_id,
  timezone_source
) on table public.profiles to service_role;

commit;
