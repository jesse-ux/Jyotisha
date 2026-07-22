select 'create role anon nologin nosuperuser nocreatedb nocreaterole noinherit'
where not exists (select 1 from pg_roles where rolname = 'anon') \gexec
select 'create role authenticated nologin nosuperuser nocreatedb nocreaterole noinherit'
where not exists (select 1 from pg_roles where rolname = 'authenticated') \gexec
select 'create role service_role nologin nosuperuser nocreatedb nocreaterole noinherit bypassrls'
where not exists (select 1 from pg_roles where rolname = 'service_role') \gexec

alter role service_role bypassrls;

grant authenticated to app_runtime;
grant service_role to admin_runtime;
