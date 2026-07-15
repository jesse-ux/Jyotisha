-- The service-role JWT bypasses RLS, but it still needs explicit table privileges.
-- Keep these grants limited to the direct table operations used by server routes.
grant usage on schema public to service_role;

grant select, insert on table public.redemption_codes to service_role;
grant select, update on table public.credit_transactions to service_role;
