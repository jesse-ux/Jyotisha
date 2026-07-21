#!/usr/bin/env bash
set -euo pipefail
set +x

required=(
  POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
  SCHEMA_OWNER_PASSWORD IDENTITY_RUNTIME_PASSWORD APP_RUNTIME_PASSWORD
  ADMIN_RUNTIME_PASSWORD MIGRATION_RUNNER_PASSWORD BACKUP_READER_PASSWORD
)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required database bootstrap variable is missing: $key" >&2
    exit 1
  fi
done

psql --set ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set database_name="$POSTGRES_DB" \
  --set schema_owner_password="$SCHEMA_OWNER_PASSWORD" \
  --set identity_runtime_password="$IDENTITY_RUNTIME_PASSWORD" \
  --set app_runtime_password="$APP_RUNTIME_PASSWORD" \
  --set admin_runtime_password="$ADMIN_RUNTIME_PASSWORD" \
  --set migration_runner_password="$MIGRATION_RUNNER_PASSWORD" \
  --set backup_reader_password="$BACKUP_READER_PASSWORD" <<'SQL'
SELECT format(
  'CREATE ROLE schema_owner WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'schema_owner_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'schema_owner'
) \gexec
SELECT format(
  'CREATE ROLE identity_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'identity_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'identity_runtime'
) \gexec
SELECT format(
  'CREATE ROLE app_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'app_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime'
) \gexec
SELECT format(
  'CREATE ROLE admin_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'admin_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'admin_runtime'
) \gexec
SELECT format(
  'CREATE ROLE migration_runner WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'migration_runner_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'migration_runner'
) \gexec
SELECT format(
  'CREATE ROLE backup_reader WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'backup_reader_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'backup_reader'
) \gexec

SELECT format(
  'GRANT CONNECT, CREATE ON DATABASE %I TO schema_owner',
  :'database_name'
) \gexec
SELECT format(
  'GRANT CONNECT ON DATABASE %I TO identity_runtime, app_runtime, admin_runtime, migration_runner, backup_reader',
  :'database_name'
) \gexec

ALTER SCHEMA public OWNER TO schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
SQL
