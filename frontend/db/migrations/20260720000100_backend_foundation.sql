create schema if not exists identity authorization schema_owner;
create schema if not exists audit authorization schema_owner;
revoke all on schema public from public;
revoke all on schema identity from public;
revoke all on schema audit from public;
grant usage on schema identity to identity_runtime, admin_runtime;
grant usage on schema public to app_runtime, admin_runtime;
grant usage on schema audit to admin_runtime;

alter default privileges for role schema_owner in schema identity
  revoke all on tables from public;
alter default privileges for role schema_owner in schema public
  revoke all on tables from public;
alter default privileges for role schema_owner in schema audit
  revoke all on tables from public;
alter default privileges for role schema_owner in schema identity
  grant select, insert, update, delete on tables to identity_runtime;
alter default privileges for role schema_owner in schema identity
  grant select on tables to admin_runtime;
alter default privileges for role schema_owner in schema public
  grant select, insert, update, delete on tables to app_runtime, admin_runtime;
alter default privileges for role schema_owner in schema audit
  grant select, insert on tables to admin_runtime;
