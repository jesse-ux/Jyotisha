import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(
  new URL("../supabase/migrations/20260727010000_refine_admin_redemption_audit.sql", import.meta.url),
  "utf8",
);
const auth = readFileSync(new URL("../src/lib/admin/auth.ts", import.meta.url), "utf8");
const authPolicy = readFileSync(new URL("../src/lib/admin/auth-policy.ts", import.meta.url), "utf8");
const codesRoute = readFileSync(new URL("../src/app/api/admin/codes/route.ts", import.meta.url), "utf8");
const codeRoute = readFileSync(new URL("../src/app/api/admin/codes/[id]/route.ts", import.meta.url), "utf8");
const providers = readFileSync(new URL("../src/lib/admin/providers.ts", import.meta.url), "utf8");
const readonlyRoutes = ["users", "credit-transactions", "consultations", "audit-logs"].map((resource) =>
  readFileSync(new URL(`../src/app/api/admin/${resource}/route.ts`, import.meta.url), "utf8"),
);
const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("admin APIs use persisted Better Auth roles with admin and viewer boundaries", () => {
  assert.match(auth, /requireIdentityUser/);
  assert.match(authPolicy, /user\.role\.includes\("admin"\)/);
  assert.match(authPolicy, /user\.role\.includes\("viewer"\)/);
  assert.match(authPolicy, /access === "write" && role !== "admin"/);
  assert.doesNotMatch(auth, /ADMIN_EMAILS|isAdminEmail/);
  assert.match(auth, /APP_ENV\?\.trim\(\) === "production"/);
  assert.match(codesRoute, /requireAdminSession\("write"\)/);
  assert.match(codeRoute, /requireAdminSession\("write"\)/g);
});

test("readonly resources cannot be mutated through Refine access control", () => {
  for (const resource of ["users", "credit-transactions", "consultations", "audit-logs"]) {
    assert.match(providers, new RegExp(`"${resource}"`));
  }
  assert.match(providers, /readOnlyResources\.has/);
  assert.match(providers, /此资源只读/);
  for (const route of readonlyRoutes) {
    assert.match(route, /export const POST = readonlyAdminMutation/);
    assert.match(route, /export const PATCH = readonlyAdminMutation/);
    assert.match(route, /export const DELETE = readonlyAdminMutation/);
  }
});

test("redemption code writes are atomic with append-only redacted audit", () => {
  assert.match(migration, /create table if not exists audit\.admin_audit_logs/);
  assert.match(migration, /admin_audit_logs_append_only/);
  assert.match(migration, /redemption_code\.create/);
  assert.match(migration, /redemption_code\.update/);
  assert.match(migration, /redemption_code\.revoke/);
  assert.match(migration, /before_value is null or not \(before_value \?\| array\['code', 'code_hash', 'token', 'secret', 'key'\]\)/);
  assert.match(migration, /insert into audit\.admin_audit_logs/);
  assert.match(migration, /redeemed codes are immutable/);
  assert.match(migration, /revoked codes are immutable/);
  assert.match(migration, /v_code\.revoked_at is not null/);
  assert.match(migration, /'revoked_code'/);
  assert.match(migration, /set local role service_role|profiles_admin_read/);
  assert.match(migration, /p_codes is null or jsonb_typeof\(p_codes\) is distinct from 'array'/);
  assert.match(migration, /admin_verified_actor_email/);
});

test("plaintext code is returned only by create and never enters audit snapshots", () => {
  assert.match(codesRoute, /plainCodes\.map/);
  assert.match(codesRoute, /code,/);
  assert.doesNotMatch(codeRoute, /codeHash|code_hash|plainCodes/);
  const snapshot = migration.match(/create or replace function public\.admin_redemption_code_snapshot[\s\S]*?revoke all on function/);
  assert.ok(snapshot);
  assert.doesNotMatch(snapshot[0], /code_hash|'code'/);
  assert.match(snapshot[0], /'mask'/);
});

test("Refine dependencies and same-origin admin data provider are present", () => {
  for (const dependency of ["@refinedev/core", "@refinedev/antd", "@refinedev/nextjs-router", "antd"]) {
    assert.ok(packageJson.dependencies[dependency], `${dependency} missing`);
  }
  assert.match(providers, /const apiBase = "\/api\/admin"/);
  assert.doesNotMatch(providers, /https?:\/\//);
});
