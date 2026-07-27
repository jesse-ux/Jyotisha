import assert from "node:assert/strict";
import test from "node:test";

import { authorizeAdminAccess } from "../src/lib/admin/auth-policy.ts";
import type { IdentityUser } from "../src/modules/identity/contracts.ts";

function user(role: string[]): IdentityUser {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    email: "admin@example.com",
    emailVerified: true,
    name: "Admin",
    image: null,
    role,
  };
}

test("anonymous admin access is 401", () => {
  assert.deepEqual(authorizeAdminAccess(null, "read"), {
    allowed: false,
    status: 401,
  });
});

test("viewer may read but may not write", () => {
  assert.deepEqual(authorizeAdminAccess(user(["user", "viewer"]), "read"), {
    allowed: true,
    role: "viewer",
  });
  assert.deepEqual(authorizeAdminAccess(user(["viewer"]), "write"), {
    allowed: false,
    status: 403,
  });
});

test("admin may read and write while unprivileged users are 403", () => {
  assert.deepEqual(authorizeAdminAccess(user(["admin"]), "read"), {
    allowed: true,
    role: "admin",
  });
  assert.deepEqual(authorizeAdminAccess(user(["admin"]), "write"), {
    allowed: true,
    role: "admin",
  });
  assert.deepEqual(authorizeAdminAccess(user(["user"]), "read"), {
    allowed: false,
    status: 403,
  });
});
