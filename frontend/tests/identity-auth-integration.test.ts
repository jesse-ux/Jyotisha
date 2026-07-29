import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { toNextJsHandler } from "better-auth/next-js";

import {
  createIdentityAuthServices,
  createIdentityPool,
} from "../src/modules/identity/auth.ts";
import type { SelfHostedIdentityConfig } from "../src/modules/identity/config.ts";
import { FakeEmailOtpSender } from "../src/modules/identity/email/fake-email-otp-sender.ts";
import { createHostIsolatedAuthHandlers } from "../src/modules/identity/host.ts";
import {
  GET as getPasswordStatus,
  POST as setAccountPassword,
} from "../src/app/api/account/password/route.ts";
import { startPostgresFixture } from "./helpers/postgres-fixture.ts";

const runnerPath = fileURLToPath(
  new URL("../scripts/db-migrate.mjs", import.meta.url),
);
const migrationsDirectory = fileURLToPath(
  new URL("../db/migrations", import.meta.url),
);
const userHost = "staging.jyotisha.chat";
const adminHost = "admin.staging.jyotisha.chat";

function request(
  host: string,
  path: string,
  body?: Record<string, unknown>,
  cookie?: string,
): Request {
  const headers: Record<string, string> = {
    host,
    origin: `https://${host}`,
  };
  if (body) headers["content-type"] = "application/json";
  if (cookie) headers.cookie = cookie;
  return new Request(`https://${host}${path}`, {
    method: body ? "POST" : "GET",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

function sessionCookie(response: Response): string {
  return (response.headers.get("set-cookie") ?? "").split(";", 1)[0];
}

const envKeys = [
  "AUTH_PROVIDER",
  "SELF_HOSTED_IDENTITY_ENABLED",
  "IDENTITY_DATABASE_URL",
  "AUTH_USER_ORIGIN",
  "AUTH_ADMIN_ORIGIN",
  "BETTER_AUTH_USER_SECRET",
  "BETTER_AUTH_ADMIN_SECRET",
  "RESEND_API_KEY",
  "RESEND_FROM_EMAIL",
] as const;

test("Better Auth supports user OTP/password flows and password-only admin login", async () => {
  const fixture = startPostgresFixture();
  const migration = spawnSync(process.execPath, [runnerPath], {
    encoding: "utf8",
    env: {
      ...process.env,
      MIGRATIONS_DIRECTORY: migrationsDirectory,
      SCHEMA_DATABASE_URL: fixture.connectionUrl(
        "schema_owner",
        "schema-owner-test-password",
      ),
    },
  });
  assert.equal(migration.status, 0, migration.stderr);

  const config: SelfHostedIdentityConfig = {
    provider: "self-hosted",
    databaseUrl: fixture.connectionUrl(
      "identity_runtime",
      "identity-runtime-test-password",
    ),
    userOrigin: `https://${userHost}`,
    adminOrigin: `https://${adminHost}`,
    userSecret: "user-secret-that-is-at-least-32-bytes-long",
    adminSecret: "admin-secret-that-is-at-least-32-bytes-long",
    resendApiKey: "re_test",
    resendFrom: "Jyotisha <login@staging.jyotisha.chat>",
  };
  const previousEnv = new Map(
    envKeys.map((key) => [key, process.env[key]] as const),
  );
  Object.assign(process.env, {
    AUTH_PROVIDER: "self-hosted",
    SELF_HOSTED_IDENTITY_ENABLED: "true",
    IDENTITY_DATABASE_URL: config.databaseUrl,
    AUTH_USER_ORIGIN: config.userOrigin,
    AUTH_ADMIN_ORIGIN: config.adminOrigin,
    BETTER_AUTH_USER_SECRET: config.userSecret,
    BETTER_AUTH_ADMIN_SECRET: config.adminSecret,
    RESEND_API_KEY: config.resendApiKey,
    RESEND_FROM_EMAIL: config.resendFrom,
  });

  const identityGlobal = globalThis as typeof globalThis & {
    jyotishaIdentityAuth?: ReturnType<typeof createIdentityAuthServices>;
  };
  delete identityGlobal.jyotishaIdentityAuth;

  const sender = new FakeEmailOtpSender();
  const pool = createIdentityPool(config.databaseUrl);
  const services = createIdentityAuthServices(config, {
    pool,
    emailSender: sender,
  });
  const handlers = createHostIsolatedAuthHandlers(config, {
    user: toNextJsHandler(services.user),
    admin: toNextJsHandler(services.admin),
  });

  async function otpSignIn(email: string): Promise<string> {
    const send = await handlers.POST(
      request(userHost, "/api/auth/email-otp/send-verification-otp", {
        email,
        type: "sign-in",
      }),
    );
    assert.equal(send.status, 200);
    const message = sender.messages.at(-1);
    assert.equal(message?.email, email);
    assert.equal(message?.type, "sign-in");

    const signIn = await handlers.POST(
      request(userHost, "/api/auth/sign-in/email-otp", {
        email,
        otp: message?.otp,
      }),
    );
    assert.equal(signIn.status, 200);
    const cookie = sessionCookie(signIn);
    assert.match(cookie, /^(?:__Secure-)?jyotisha-user\.session_token=/);
    return cookie;
  }

  async function passwordSignIn(
    email: string,
    password: string,
  ): Promise<Response> {
    return handlers.POST(
      request(userHost, "/api/auth/sign-in/email", { email, password }),
    );
  }

  try {
    const unauthenticatedSet = await setAccountPassword(
      request(userHost, "/api/account/password", {
        newPassword: "not-authorized",
      }),
    );
    assert.equal(unauthenticatedSet.status, 401);

    const newEmail = "new-user@example.com";
    const firstPassword = "first-password";
    const resetPassword = "reset-password";
    const newUserOtpCookie = await otpSignIn(newEmail);

    const initialStatus = await getPasswordStatus(
      request(userHost, "/api/account/password", undefined, newUserOtpCookie),
    );
    assert.equal(initialStatus.status, 200);
    assert.deepEqual(await initialStatus.json(), { hasPassword: false });

    const firstSet = await setAccountPassword(
      request(
        userHost,
        "/api/account/password",
        { newPassword: firstPassword },
        newUserOtpCookie,
      ),
    );
    assert.equal(firstSet.status, 200);

    const secondSet = await setAccountPassword(
      request(
        userHost,
        "/api/account/password",
        { newPassword: "must-not-overwrite" },
        newUserOtpCookie,
      ),
    );
    assert.equal(secondSet.status, 409);

    const storedHash = fixture.psql(
      "select password from identity.accounts where provider_id = 'credential' and user_id = (select id from identity.users where email = 'new-user@example.com')",
    );
    assert.notEqual(storedHash, firstPassword);
    assert.match(storedHash, /^[0-9a-f]{32}:[0-9a-f]{128}$/);

    const passwordLogin = await passwordSignIn(newEmail, firstPassword);
    assert.equal(passwordLogin.status, 200);
    const passwordCookie = sessionCookie(passwordLogin);
    assert.match(passwordCookie, /^(?:__Secure-)?jyotisha-user\.session_token=/);

    const wrongPassword = await passwordSignIn(newEmail, "wrong-password");
    assert.notEqual(wrongPassword.status, 200);
    assert.equal(wrongPassword.headers.has("set-cookie"), false);

    const otpLoginCookie = await otpSignIn(newEmail);
    assert.match(otpLoginCookie, /^(?:__Secure-)?jyotisha-user\.session_token=/);

    const oldOtpEmail = "otp-only@example.com";
    const firstOldOtpCookie = await otpSignIn(oldOtpEmail);
    const signOut = await handlers.POST(
      request(
        userHost,
        "/api/auth/sign-out",
        {},
        firstOldOtpCookie,
      ),
    );
    assert.equal(signOut.status, 200);
    const returningOldOtpCookie = await otpSignIn(oldOtpEmail);
    const oldOtpStatus = await getPasswordStatus(
      request(
        userHost,
        "/api/account/password",
        undefined,
        returningOldOtpCookie,
      ),
    );
    assert.deepEqual(await oldOtpStatus.json(), { hasPassword: false });
    const oldOtpSet = await setAccountPassword(
      request(
        userHost,
        "/api/account/password",
        { newPassword: "old-user-password" },
        returningOldOtpCookie,
      ),
    );
    assert.equal(oldOtpSet.status, 200);
    assert.equal(
      (await passwordSignIn(oldOtpEmail, "old-user-password")).status,
      200,
    );

    const unknownResetMessageCount = sender.messages.length;
    const unknownReset = await handlers.POST(
      request(userHost, "/api/auth/email-otp/request-password-reset", {
        email: "missing@example.com",
      }),
    );
    assert.equal(unknownReset.status, 200);
    assert.equal(sender.messages.length, unknownResetMessageCount);

    const resetRequest = await handlers.POST(
      request(userHost, "/api/auth/email-otp/request-password-reset", {
        email: newEmail,
      }),
    );
    assert.equal(resetRequest.status, 200);
    const resetMessage = sender.messages.at(-1);
    assert.equal(resetMessage?.type, "forget-password");

    const reset = await handlers.POST(
      request(userHost, "/api/auth/email-otp/reset-password", {
        email: newEmail,
        otp: resetMessage?.otp,
        password: resetPassword,
      }),
    );
    assert.equal(reset.status, 200);

    const newUserId = fixture.psql(
      "select id from identity.users where email = 'new-user@example.com'",
    );
    assert.equal(
      fixture.psql(
        `select count(*) from identity.sessions where user_id = '${newUserId}'`,
      ),
      "0",
    );
    for (const cookie of [newUserOtpCookie, passwordCookie, otpLoginCookie]) {
      assert.equal(
        await services.user.api.getSession({
          headers: new Headers({ cookie }),
        }),
        null,
      );
    }

    const oldPasswordAfterReset = await passwordSignIn(newEmail, firstPassword);
    assert.notEqual(oldPasswordAfterReset.status, 200);
    assert.equal(oldPasswordAfterReset.headers.has("set-cookie"), false);
    const newPasswordAfterReset = await passwordSignIn(newEmail, resetPassword);
    assert.equal(newPasswordAfterReset.status, 200);
    assert.match(
      sessionCookie(newPasswordAfterReset),
      /^(?:__Secure-)?jyotisha-user\.session_token=/,
    );

    const nonAdminPasswordLogin = await handlers.POST(
      request(adminHost, "/api/auth/sign-in/email", {
        email: newEmail,
        password: resetPassword,
      }),
    );
    assert.notEqual(nonAdminPasswordLogin.status, 200);
    assert.equal(nonAdminPasswordLogin.headers.has("set-cookie"), false);

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      "update identity.users set role = 'user,admin' where email = 'new-user@example.com'",
    );
    const adminPasswordLogin = await handlers.POST(
      request(adminHost, "/api/auth/sign-in/email", {
        email: newEmail,
        password: resetPassword,
      }),
    );
    assert.equal(adminPasswordLogin.status, 200);
    assert.match(
      sessionCookie(adminPasswordLogin),
      /^(?:__Secure-)?jyotisha-admin\.session_token=/,
    );

    const sentMessageCount = sender.messages.length;
    const adminSend = await handlers.POST(
      request(adminHost, "/api/auth/email-otp/send-verification-otp", {
        email: newEmail,
        type: "sign-in",
      }),
    );
    assert.notEqual(adminSend.status, 200);
    assert.equal(sender.messages.length, sentMessageCount);

    const adminPasswordRoute = await setAccountPassword(
      request(
        adminHost,
        "/api/account/password",
        { newPassword: "admin-must-not-set-password" },
        sessionCookie(adminPasswordLogin),
      ),
    );
    assert.equal(adminPasswordRoute.status, 401);
  } finally {
    const globalServices = (globalThis as typeof identityGlobal).jyotishaIdentityAuth;
    if (globalServices) {
      await globalServices.pool.end();
      delete identityGlobal.jyotishaIdentityAuth;
    }
    await pool.end();
    fixture.stop();
    for (const key of envKeys) {
      const value = previousEnv.get(key);
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});
