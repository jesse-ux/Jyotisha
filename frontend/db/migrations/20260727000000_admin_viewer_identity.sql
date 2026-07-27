-- Admin-host sessions may be created for read-only viewers. API authorization
-- remains server-side and is resolved from this persisted role on every request.
-- Existing identity migrations already grant admin_runtime these reads; repeat the
-- least-privilege user grant so drifted staging databases fail closed at login.

grant select on table identity.users to admin_runtime;
