create or replace function identity.sync_user_to_business_auth()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, auth
as $$
begin
  if tg_op = 'DELETE' then
    delete from auth.users where id = old.id;
    return old;
  end if;

  insert into auth.users (
    id,
    email,
    raw_user_meta_data,
    email_confirmed_at,
    created_at,
    updated_at
  ) values (
    new.id,
    new.email,
    jsonb_build_object('full_name', new.name),
    case when new.email_verified then coalesce(new.email_verified_at, now()) end,
    new.created_at,
    new.updated_at
  )
  on conflict (id) do update set
    email = excluded.email,
    raw_user_meta_data = excluded.raw_user_meta_data,
    email_confirmed_at = excluded.email_confirmed_at,
    updated_at = excluded.updated_at;

  return new;
end;
$$;

drop trigger if exists identity_user_business_auth_sync on identity.users;
create trigger identity_user_business_auth_sync
after insert or update or delete on identity.users
for each row execute function identity.sync_user_to_business_auth();

insert into auth.users (
  id,
  email,
  raw_user_meta_data,
  email_confirmed_at,
  created_at,
  updated_at
)
select
  id,
  email,
  jsonb_build_object('full_name', name),
  case when email_verified then coalesce(email_verified_at, now()) end,
  created_at,
  updated_at
from identity.users
on conflict (id) do update set
  email = excluded.email,
  raw_user_meta_data = excluded.raw_user_meta_data,
  email_confirmed_at = excluded.email_confirmed_at,
  updated_at = excluded.updated_at;

revoke all on function identity.sync_user_to_business_auth() from public;
