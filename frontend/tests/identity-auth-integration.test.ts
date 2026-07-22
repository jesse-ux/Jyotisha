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
import { startPostgresFixture } from "./helpers/postgres-fixture.ts";

const runnerPath = fileURLToPath(
  new URL("../scripts/db-migrate.mjs", import.meta.url),
);
const migrationsDirectory = fileURLToPath(
  new URL("../db/migrations", import.meta.url),
);

function request(
  host: string,
  path: string,
  body: Record<string, unknown>,
): Request {
  return new Request(`https://${host}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      host,
      origin: `https://${host}`,
    },
    body: JSON.stringify(body),
  });
}

test("Better Auth completes OTP sign-in against the migrated identity schema with isolated cookies", async () => {
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
    userOrigin: "https://staging.jyotisha.chat",
    adminOrigin: "https://admin.staging.jyotisha.chat",
    userSecret: "user-secret-that-is-at-least-32-bytes-long",
    adminSecret: "admin-secret-that-is-at-least-32-bytes-long",
    resendApiKey: "re_test",
    resendFrom: "Jyotisha <login@staging.jyotisha.chat>",
  };
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

  try {
    const userSend = await handlers.POST(
      request(
        "staging.jyotisha.chat",
        "/api/auth/email-otp/send-verification-otp",
        { email: "person@example.com", type: "sign-in" },
      ),
    );
    assert.equal(userSend.status, 200, await userSend.text());
    assert.equal(sender.messages.length, 1);

    const userSignIn = await handlers.POST(
      request("staging.jyotisha.chat", "/api/auth/sign-in/email-otp", {
        email: "person@example.com",
        otp: sender.messages[0].otp,
      }),
    );
    const userCookie = userSignIn.headers.get("set-cookie") ?? "";
    assert.equal(userSignIn.status, 200, await userSignIn.text());
    assert.match(userCookie, /jyotisha-user\.session_token=/);
    assert.doesNotMatch(userCookie, /jyotisha-admin/);
    assert.match(userCookie, /HttpOnly/i);
    assert.match(userCookie, /Secure/i);
    assert.match(userCookie, /SameSite=Lax/i);
    assert.doesNotMatch(userCookie, /Domain=/i);
    assert.equal(fixture.psql("select count(*) from identity.users"), "1");
    assert.equal(fixture.psql("select count(*) from identity.sessions"), "1");

    const adminSend = await handlers.POST(
      request(
        "admin.staging.jyotisha.chat",
        "/api/auth/email-otp/send-verification-otp",
        { email: "person@example.com", type: "sign-in" },
      ),
    );
    assert.equal(adminSend.status, 200, await adminSend.text());
    const deniedAdminSignIn = await handlers.POST(
      request(
        "admin.staging.jyotisha.chat",
        "/api/auth/sign-in/email-otp",
        { email: "person@example.com", otp: sender.messages[1].otp },
      ),
    );
    assert.equal(deniedAdminSignIn.status, 403);
    assert.equal(deniedAdminSignIn.headers.has("set-cookie"), false);
    assert.equal(fixture.psql("select count(*) from identity.sessions"), "1");

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      "update identity.users set role = 'user,admin' where email = 'person@example.com'",
    );
    const promotedSend = await handlers.POST(
      request(
        "admin.staging.jyotisha.chat",
        "/api/auth/email-otp/send-verification-otp",
        { email: "person@example.com", type: "sign-in" },
      ),
    );
    assert.equal(promotedSend.status, 200, await promotedSend.text());
    const adminSignIn = await handlers.POST(
      request(
        "admin.staging.jyotisha.chat",
        "/api/auth/sign-in/email-otp",
        { email: "person@example.com", otp: sender.messages[2].otp },
      ),
    );
    const adminCookie = adminSignIn.headers.get("set-cookie") ?? "";
    assert.equal(adminSignIn.status, 200, await adminSignIn.text());
    assert.match(adminCookie, /jyotisha-admin\.session_token=/);
    assert.doesNotMatch(adminCookie, /jyotisha-user/);
    assert.doesNotMatch(adminCookie, /Domain=/i);
    assert.equal(fixture.psql("select count(*) from identity.sessions"), "2");
  } finally {
    await pool.end();
    fixture.stop();
  }
});
