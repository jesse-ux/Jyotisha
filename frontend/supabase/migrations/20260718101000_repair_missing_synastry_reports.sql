begin;

create table if not exists public.synastry_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  partner_name text not null default '对方',
  report jsonb not null check (jsonb_typeof(report) = 'object'),
  created_at timestamptz not null default now()
);

create index if not exists synastry_reports_user_created_at_idx
  on public.synastry_reports (user_id, created_at desc);

alter table public.synastry_reports enable row level security;

drop policy if exists synastry_reports_select_own on public.synastry_reports;
create policy synastry_reports_select_own
  on public.synastry_reports for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists synastry_reports_insert_own on public.synastry_reports;
create policy synastry_reports_insert_own
  on public.synastry_reports for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists synastry_reports_delete_own on public.synastry_reports;
create policy synastry_reports_delete_own
  on public.synastry_reports for delete to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.synastry_reports from anon, authenticated, service_role;
grant select on table public.synastry_reports to authenticated;
grant insert (id, user_id, partner_name, report, created_at) on table public.synastry_reports to authenticated;
grant delete on table public.synastry_reports to authenticated;

commit;
