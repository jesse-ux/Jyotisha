import assert from "node:assert/strict";
import test from "node:test";

import type { SelfHostedIdentityConfig } from "../src/modules/identity/config.ts";
import {
  createHostIsolatedAuthHandlers,
  resolveIdentitySurface,
} from "../src/modules/identity/host.ts";

const config: SelfHostedIdentityConfig = {
  provider: "self-hosted",
  databaseUrl: "postgresql://identity_runtime:test@postgres:5432/jyotisha",
  userOrigin: "https://staging.jyotisha.chat",
  adminOrigin: "https://admin.staging.jyotisha.chat",
  userSecret: "user-secret-that-is-at-least-32-bytes-long",
  adminSecret: "admin-secret-that-is-at-least-32-bytes-long",
  resendApiKey: "re_test",
  resendFrom: "Jyotisha <login@staging.jyotisha.chat>",
};

test("identity surface matching is exact, case-insensitive, and port-normalized", () => {
  assert.equal(resolveIdentitySurface("staging.jyotisha.chat", config), "user");
  assert.equal(resolveIdentitySurface("STAGING.JYOTISHA.CHAT:443", config), "user");
  assert.equal(
    resolveIdentitySurface("admin.staging.jyotisha.chat", config),
    "admin",
  );

  for (const host of [
    null,
    "",
    "evil-staging.jyotisha.chat",
    "staging.jyotisha.chat.evil.example",
    "staging.jyotisha.chat,evil.example",
    "staging.jyotisha.chat/path",
    "user@staging.jyotisha.chat",
    " staging.jyotisha.chat",
  ]) {
    assert.equal(resolveIdentitySurface(host, config), null, String(host));
  }
});

test("auth route dispatches only to the exact matching host", async () => {
  const calls: string[] = [];
  const handlers = createHostIsolatedAuthHandlers(config, {
    user: {
      GET: async () => {
        calls.push("user:get");
        return new Response("user");
      },
      POST: async () => {
        calls.push("user:post");
        return new Response("user");
      },
    },
    admin: {
      GET: async () => {
        calls.push("admin:get");
        return new Response("admin");
      },
      POST: async () => {
        calls.push("admin:post");
        return new Response("admin");
      },
    },
  });

  const userResponse = await handlers.POST(
    new Request("https://internal/api/auth/email-otp/send-verification-otp", {
      method: "POST",
      headers: { host: "staging.jyotisha.chat" },
    }),
  );
  assert.equal(await userResponse.text(), "user");

  const adminResponse = await handlers.GET(
    new Request("https://internal/api/auth/get-session", {
      headers: { host: "admin.staging.jyotisha.chat" },
    }),
  );
  assert.equal(await adminResponse.text(), "admin");
  assert.deepEqual(calls, ["user:post", "admin:get"]);
});

test("unknown hosts fail closed before an auth handler reads cookies", async () => {
  let calls = 0;
  const handler = async () => {
    calls += 1;
    return new Response("unexpected");
  };
  const handlers = createHostIsolatedAuthHandlers(config, {
    user: { GET: handler, POST: handler },
    admin: { GET: handler, POST: handler },
  });

  const response = await handlers.GET(
    new Request("https://internal/api/auth/get-session", {
      headers: {
        host: "staging.jyotisha.chat.evil.example",
        cookie: "jyotisha-admin.session_token=attacker-controlled",
      },
    }),
  );

  assert.equal(response.status, 421);
  assert.equal(calls, 0);
  assert.equal(response.headers.has("set-cookie"), false);
});

test("user host cannot reach Better Auth admin endpoints", async () => {
  let calls = 0;
  const handler = async () => {
    calls += 1;
    return new Response("unexpected");
  };
  const handlers = createHostIsolatedAuthHandlers(config, {
    user: { GET: handler, POST: handler },
    admin: { GET: handler, POST: handler },
  });

  const response = await handlers.POST(
    new Request("https://internal/api/auth/admin/set-role", {
      method: "POST",
      headers: { host: "staging.jyotisha.chat" },
    }),
  );

  assert.equal(response.status, 404);
  assert.equal(calls, 0);
});
