import assert from "node:assert/strict";
import test from "node:test";

import {
  isSelfHostedIdentityEnabled,
  readIdentityConfig,
  readSelfHostedIdentityConfig,
} from "../src/modules/identity/config.ts";

const selfHostedEnvironment = {
  AUTH_PROVIDER: "self-hosted",
  SELF_HOSTED_IDENTITY_ENABLED: "true",
  IDENTITY_DATABASE_URL:
    "postgresql://identity_runtime:test-password@postgres:5432/jyotisha?options=-csearch_path%3Didentity",
  AUTH_USER_ORIGIN: "https://staging.jyotisha.chat",
  AUTH_ADMIN_ORIGIN: "https://admin.staging.jyotisha.chat",
  BETTER_AUTH_USER_SECRET: "user-secret-that-is-at-least-32-bytes-long",
  BETTER_AUTH_ADMIN_SECRET: "admin-secret-that-is-at-least-32-bytes-long",
  RESEND_API_KEY: "re_test_key_that_must_not_be_printed",
  RESEND_FROM_EMAIL: "Jyotisha Staging <login@staging.jyotisha.chat>",
};

test("identity provider defaults to supabase without self-hosted settings", () => {
  assert.deepEqual(readIdentityConfig({}), { provider: "supabase" });
  assert.equal(isSelfHostedIdentityEnabled({}), false);
});

test("self-hosted identity can be enabled alongside the Supabase default", () => {
  const environment = {
    ...selfHostedEnvironment,
    AUTH_PROVIDER: "supabase",
  };

  assert.deepEqual(readIdentityConfig(environment), { provider: "supabase" });
  assert.equal(isSelfHostedIdentityEnabled(environment), true);
  assert.equal(
    readSelfHostedIdentityConfig(environment).databaseUrl,
    selfHostedEnvironment.IDENTITY_DATABASE_URL,
  );
});

test("identity config accepts a complete self-hosted environment", () => {
  const config = readIdentityConfig(selfHostedEnvironment);

  assert.equal(config.provider, "self-hosted");
  if (config.provider !== "self-hosted") {
    assert.fail("expected self-hosted identity configuration");
  }
  assert.equal(config.userOrigin, "https://staging.jyotisha.chat");
  assert.equal(config.adminOrigin, "https://admin.staging.jyotisha.chat");
  assert.equal(config.resendFrom, selfHostedEnvironment.RESEND_FROM_EMAIL);
});

test("identity config rejects unknown providers", () => {
  assert.throws(
    () => readIdentityConfig({ AUTH_PROVIDER: "firebase" }),
    /AUTH_PROVIDER must be supabase or self-hosted/,
  );
});

test("self-hosted provider requires its independent service flag", () => {
  assert.throws(
    () =>
      readIdentityConfig({
        ...selfHostedEnvironment,
        SELF_HOSTED_IDENTITY_ENABLED: "false",
      }),
    /SELF_HOSTED_IDENTITY_ENABLED must be true/,
  );
  assert.throws(
    () => isSelfHostedIdentityEnabled({ SELF_HOSTED_IDENTITY_ENABLED: "yes" }),
    /must be true or false/,
  );
});

test("self-hosted identity reports missing keys without leaking configured secrets", () => {
  const secret = "this-secret-must-never-appear-in-an-error";

  assert.throws(
    () =>
      readIdentityConfig({
        ...selfHostedEnvironment,
        BETTER_AUTH_USER_SECRET: secret,
        RESEND_API_KEY: "",
      }),
    (error: unknown) => {
      assert.ok(error instanceof Error);
      assert.match(error.message, /RESEND_API_KEY is required/);
      assert.doesNotMatch(error.message, new RegExp(secret));
      return true;
    },
  );
});

test("self-hosted identity validates database URL, origins, secrets, and sender", () => {
  const invalidCases: Array<[string, Record<string, string>, RegExp]> = [
    [
      "database URL",
      { IDENTITY_DATABASE_URL: "https://database.invalid" },
      /IDENTITY_DATABASE_URL must be a PostgreSQL URL/,
    ],
    [
      "production HTTP origin",
      { AUTH_USER_ORIGIN: "http://staging.jyotisha.chat" },
      /AUTH_USER_ORIGIN must use HTTPS/,
    ],
    [
      "origin path",
      { AUTH_ADMIN_ORIGIN: "https://admin.staging.jyotisha.chat/login" },
      /AUTH_ADMIN_ORIGIN must be an origin without a path/,
    ],
    [
      "short secret",
      { BETTER_AUTH_ADMIN_SECRET: "too-short" },
      /BETTER_AUTH_ADMIN_SECRET must be at least 32 characters/,
    ],
    [
      "shared secret",
      {
        BETTER_AUTH_ADMIN_SECRET:
          selfHostedEnvironment.BETTER_AUTH_USER_SECRET,
      },
      /user and admin secrets must be different/,
    ],
    [
      "shared origin",
      { AUTH_ADMIN_ORIGIN: selfHostedEnvironment.AUTH_USER_ORIGIN },
      /user and admin origins must be different/,
    ],
    [
      "invalid sender",
      { RESEND_FROM_EMAIL: "Jyotisha Staging" },
      /RESEND_FROM_EMAIL must contain a valid email address/,
    ],
  ];

  for (const [name, override, expected] of invalidCases) {
    assert.throws(
      () => readIdentityConfig({ ...selfHostedEnvironment, ...override }),
      expected,
      name,
    );
  }
});

test("localhost origins may use HTTP for local development", () => {
  const config = readIdentityConfig({
    ...selfHostedEnvironment,
    AUTH_USER_ORIGIN: "http://localhost:3000",
    AUTH_ADMIN_ORIGIN: "http://admin.localhost:3000",
  });

  assert.equal(config.provider, "self-hosted");
});
