import assert from "node:assert/strict";
import test from "node:test";
import type { Pool } from "pg";

import {
  buildAuthOptions,
  createEmailOtpOptions,
  type AdminUserAuthorizer,
} from "../src/modules/identity/auth-factory.ts";
import {
  createDatabaseAdminAuthorizer,
  createIdentityPool,
} from "../src/modules/identity/auth.ts";
import { FakeEmailOtpSender } from "../src/modules/identity/email/fake-email-otp-sender.ts";
import type { SelfHostedIdentityConfig } from "../src/modules/identity/config.ts";

const config: SelfHostedIdentityConfig = {
  provider: "self-hosted",
  databaseUrl:
    "postgresql://identity_runtime:test-password@postgres:5432/jyotisha",
  userOrigin: "https://staging.jyotisha.chat",
  adminOrigin: "https://admin.staging.jyotisha.chat",
  userSecret: "user-secret-that-is-at-least-32-bytes-long",
  adminSecret: "admin-secret-that-is-at-least-32-bytes-long",
  resendApiKey: "re_test_key",
  resendFrom: "Jyotisha <login@staging.jyotisha.chat>",
};

const database = { kind: "pool" } as unknown as Pool;

test("Better Auth model mappings match the identity migration", () => {
  const options = buildAuthOptions({
    surface: "user",
    config,
    database,
    emailSender: new FakeEmailOtpSender(),
  });

  assert.equal(options.database, database);
  assert.equal(options.user?.modelName, "users");
  assert.deepEqual(options.user?.fields, {
    emailVerified: "email_verified",
    createdAt: "created_at",
    updatedAt: "updated_at",
  });
  assert.equal(options.session?.modelName, "sessions");
  assert.deepEqual(options.session?.fields, {
    expiresAt: "expires_at",
    createdAt: "created_at",
    updatedAt: "updated_at",
    ipAddress: "ip_address",
    userAgent: "user_agent",
    userId: "user_id",
  });
  assert.equal(options.account?.modelName, "accounts");
  assert.equal(options.account?.fields?.accountId, "account_id");
  assert.equal(options.account?.fields?.providerId, "provider_id");
  assert.equal(options.account?.fields?.accessTokenExpiresAt, "access_token_expires_at");
  assert.equal(options.verification?.modelName, "verifications");
  assert.equal(options.verification?.fields?.expiresAt, "expires_at");
  assert.equal(options.rateLimit?.modelName, "otp_rate_limits");
  assert.equal(options.rateLimit?.storage, "database");
  assert.equal(options.advanced?.database?.generateId, "uuid");
});

test("OTP policy hashes values, rotates resends, and builds opaque idempotency keys", async () => {
  const sender = new FakeEmailOtpSender();
  const otpOptions = createEmailOtpOptions(sender, config.userSecret, false);

  assert.equal(otpOptions.otpLength, 6);
  assert.equal(otpOptions.expiresIn, 300);
  assert.equal(otpOptions.allowedAttempts, 3);
  assert.equal(otpOptions.resendStrategy, "rotate");
  assert.equal(otpOptions.storeOTP, "hashed");
  assert.deepEqual(otpOptions.rateLimit, { window: 60, max: 3 });
  assert.equal(otpOptions.disableSignUp, false);

  await otpOptions.sendVerificationOTP({
    email: "person@example.com",
    otp: "123456",
    type: "sign-in",
  });
  assert.equal(sender.messages.length, 1);
  assert.match(sender.messages[0].idempotencyKey, /^otp-[0-9a-f]{64}$/);
  assert.doesNotMatch(sender.messages[0].idempotencyKey, /123456|person/);
});

test("user and admin auth surfaces have host-only isolated cookies", () => {
  const authorizer: AdminUserAuthorizer = async () => true;
  const userOptions = buildAuthOptions({
    surface: "user",
    config,
    database,
    emailSender: new FakeEmailOtpSender(),
  });
  const adminOptions = buildAuthOptions({
    surface: "admin",
    config,
    database,
    emailSender: new FakeEmailOtpSender(),
    authorizeAdminUser: authorizer,
  });

  assert.equal(userOptions.baseURL, config.userOrigin);
  assert.equal(adminOptions.baseURL, config.adminOrigin);
  assert.equal(userOptions.secret, config.userSecret);
  assert.equal(adminOptions.secret, config.adminSecret);
  assert.equal(userOptions.advanced?.cookiePrefix, "jyotisha-user");
  assert.equal(adminOptions.advanced?.cookiePrefix, "jyotisha-admin");
  for (const options of [userOptions, adminOptions]) {
    const attributes = options.advanced?.defaultCookieAttributes;
    assert.equal(attributes?.secure, true);
    assert.equal(attributes?.httpOnly, true);
    assert.equal(attributes?.sameSite, "lax");
    assert.equal(attributes?.path, "/");
    assert.equal(attributes && "domain" in attributes, false);
    assert.equal(options.advanced?.crossSubDomainCookies, undefined);
  }
});

test("admin surface disables sign-up and rejects non-admin session creation", async () => {
  const checkedUserIds: string[] = [];
  const options = buildAuthOptions({
    surface: "admin",
    config,
    database,
    emailSender: new FakeEmailOtpSender(),
    authorizeAdminUser: async (userId) => {
      checkedUserIds.push(userId);
      return userId === "admin-user-id";
    },
  });
  const emailPlugin = options.plugins?.find(
    (plugin) => plugin.id === "email-otp",
  );
  assert.ok(emailPlugin);

  const before = options.databaseHooks?.session?.create?.before;
  assert.ok(before);
  const session = {
    id: "session-id",
    token: "session-token",
    userId: "ordinary-user-id",
    expiresAt: new Date(Date.now() + 60_000),
    createdAt: new Date(),
    updatedAt: new Date(),
  };
  await assert.rejects(
    before(session, null),
    /Administrator access required/,
  );
  assert.equal(
    await before({ ...session, userId: "admin-user-id" }, null),
    undefined,
  );
  assert.deepEqual(checkedUserIds, ["ordinary-user-id", "admin-user-id"]);

  const otpOptions = createEmailOtpOptions(
    new FakeEmailOtpSender(),
    config.adminSecret,
    true,
  );
  assert.equal(otpOptions.disableSignUp, true);
});

test("admin surface requires a server-side persisted-role authorizer", () => {
  assert.throws(
    () =>
      buildAuthOptions({
        surface: "admin",
        config,
        database,
        emailSender: new FakeEmailOtpSender(),
      }),
    /admin user authorizer is required/,
  );
});

test("identity pool forces the identity search path", async () => {
  const pool = createIdentityPool(config.databaseUrl);

  try {
    assert.equal(pool.options.connectionString, config.databaseUrl);
    assert.equal(pool.options.options, "-c search_path=identity,pg_catalog");
    assert.equal(pool.options.max, 10);
  } finally {
    await pool.end();
  }
});

test("database admin authorizer requires a current persisted admin role", async () => {
  const rowsByUser = new Map<string, Record<string, unknown>>([
    ["admin", { role: "user,admin", banned: false, ban_expires: null }],
    ["user", { role: "user", banned: false, ban_expires: null }],
    ["banned", { role: "admin", banned: true, ban_expires: null }],
    [
      "expired-ban",
      {
        role: "admin",
        banned: true,
        ban_expires: new Date(Date.now() - 60_000),
      },
    ],
  ]);
  const queries: Array<{ sql: string; values: unknown[] }> = [];
  const pool = {
    async query(sql: string, values: unknown[]) {
      queries.push({ sql, values });
      const row = rowsByUser.get(String(values[0]));
      return { rows: row ? [row] : [] };
    },
  } as unknown as Pool;
  const authorize = createDatabaseAdminAuthorizer(pool);

  assert.equal(await authorize("admin"), true);
  assert.equal(await authorize("user"), false);
  assert.equal(await authorize("banned"), false);
  assert.equal(await authorize("expired-ban"), true);
  assert.equal(await authorize("missing"), false);
  assert.equal(queries.length, 5);
  assert.match(queries[0].sql, /from identity\.users/);
  assert.deepEqual(queries[0].values, ["admin"]);
});
