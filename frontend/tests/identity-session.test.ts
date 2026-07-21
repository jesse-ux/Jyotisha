import assert from "node:assert/strict";
import test from "node:test";

import {
  IdentityAuthorizationError,
  readIdentitySession,
  requireIdentityAdmin,
  requireIdentityUser,
  type IdentitySessionReader,
} from "../src/modules/identity/session.ts";

function readerFor(role: string | null): IdentitySessionReader {
  return {
    async getSession() {
      if (role === null) return null;
      return {
        session: { expiresAt: new Date("2030-01-01T00:00:00.000Z") },
        user: {
          id: "018f4e6d-7a11-7000-8000-000000000001",
          email: "Person@Example.com",
          emailVerified: true,
          name: "Person",
          image: null,
          role,
        },
      };
    },
  };
}

test("identity session mapper returns a narrow normalized DTO", async () => {
  const session = await readIdentitySession(readerFor("user,admin"), new Headers());

  assert.deepEqual(session, {
    expiresAt: new Date("2030-01-01T00:00:00.000Z"),
    user: {
      id: "018f4e6d-7a11-7000-8000-000000000001",
      email: "person@example.com",
      emailVerified: true,
      name: "Person",
      image: null,
      role: ["user", "admin"],
    },
  });
  assert.equal("token" in (session ?? {}), false);
});

test("require user rejects a missing server-side session", async () => {
  await assert.rejects(
    requireIdentityUser(readerFor(null), new Headers({ cookie: "present=1" })),
    (error: unknown) => {
      assert.ok(error instanceof IdentityAuthorizationError);
      assert.equal(error.status, 401);
      return true;
    },
  );
});

test("require admin checks persisted session roles, not cookie presence", async () => {
  await assert.rejects(
    requireIdentityAdmin(
      readerFor("user"),
      new Headers({ cookie: "jyotisha-admin.session_token=present" }),
    ),
    (error: unknown) => {
      assert.ok(error instanceof IdentityAuthorizationError);
      assert.equal(error.status, 403);
      return true;
    },
  );

  const admin = await requireIdentityAdmin(
    readerFor("user,admin"),
    new Headers(),
  );
  assert.deepEqual(admin.role, ["user", "admin"]);
});
