begin;

alter table public.profiles
  add column if not exists onboarding_payload jsonb,
  add column if not exists onboarding_version text,
  add column if not exists onboarding_generated_at timestamptz;

alter table public.profiles
  drop constraint if exists profiles_onboarding_payload_object;
alter table public.profiles
  add constraint profiles_onboarding_payload_object
  check (onboarding_payload is null or jsonb_typeof(onboarding_payload) = 'object');

-- The browser can read its own profile through the existing RLS policy, but only
-- authenticated server routes may write the generated onboarding cache.
grant select, update (
  onboarding_payload,
  onboarding_version,
  onboarding_generated_at
) on table public.profiles to service_role;

commit;
