begin;

-- Existing-row upserts must read every submitted column to resolve the result.
grant select (
  district_code,
  updated_at
) on table public.profiles to service_role;

commit;
