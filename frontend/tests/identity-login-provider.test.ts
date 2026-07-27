import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { createSelfHostedAuthActions } from "../src/modules/identity/client.ts";

test("login page selects the auth provider and limits passwords to the user surface", () => {
  const page = readFileSync(
    new URL("../src/app/login/page.tsx", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(page, /["']use client["']/);
  assert.match(page, /export const dynamic = "force-dynamic"/);
  assert.match(page, /readIdentityConfig\(process\.env\)/);
  assert.match(page, /isSelfHostedIdentityEnabled\(process\.env\)/);
  assert.match(page, /resolveIdentitySurface/);
  assert.match(page, /surface === "admin"/);
  assert.match(
    page,
    /passwordEnabled = provider === "self-hosted" && surface === "user"/,
  );
  assert.match(page, /passwordEnabled=\{passwordEnabled\}/);
  assert.doesNotMatch(page, /NEXT_PUBLIC_AUTH_PROVIDER/);
});

test("self-hosted auth actions call Better Auth without browser token storage", async () => {
  const calls: Array<{ operation: string; input?: Record<string, string> }> = [];
  const fetchCalls: Array<{ path: string; method: string; body: string }> = [];
  const actions = createSelfHostedAuthActions(
    {
      emailOtp: {
        async sendVerificationOtp(input) {
          calls.push({ operation: "send", input });
          return { data: { success: true }, error: null };
        },
        async requestPasswordReset(input) {
          calls.push({ operation: "request-reset", input });
          return { data: { success: true }, error: null };
        },
        async resetPassword(input) {
          calls.push({ operation: "reset", input });
          return { data: { success: true }, error: null };
        },
      },
      signIn: {
        async emailOtp(input) {
          calls.push({ operation: "verify", input });
          return { data: { user: { id: "user-id" } }, error: null };
        },
        async email(input) {
          calls.push({ operation: "password", input });
          return { data: { user: { id: "user-id" } }, error: null };
        },
      },
    },
    async (input, init) => {
      fetchCalls.push({
        path: String(input),
        method: init?.method ?? "GET",
        body: typeof init?.body === "string" ? init.body : "",
      });
      return Response.json(
        init?.method === "POST" ? { ok: true } : { hasPassword: false },
      );
    },
  );

  await actions.send(" Person@Example.com ");
  await actions.verify(" Person@Example.com ", "123456");
  await actions.signInWithPassword(" Person@Example.com ", "password-1");
  await actions.requestPasswordReset(" Person@Example.com ");
  await actions.resetPassword(
    " Person@Example.com ",
    "654321",
    "password-2",
  );
  assert.equal(await actions.hasPassword(), false);
  await actions.setPassword("password-3");

  assert.deepEqual(calls, [
    {
      operation: "send",
      input: { email: "person@example.com", type: "sign-in" },
    },
    {
      operation: "verify",
      input: { email: "person@example.com", otp: "123456" },
    },
    {
      operation: "password",
      input: { email: "person@example.com", password: "password-1" },
    },
    {
      operation: "request-reset",
      input: { email: "person@example.com" },
    },
    {
      operation: "reset",
      input: {
        email: "person@example.com",
        otp: "654321",
        password: "password-2",
      },
    },
  ]);
  assert.deepEqual(fetchCalls, [
    { path: "/api/account/password", method: "GET", body: "" },
    {
      path: "/api/account/password",
      method: "POST",
      body: JSON.stringify({ newPassword: "password-3" }),
    },
  ]);

  const clientSource = readFileSync(
    new URL("../src/modules/identity/client.ts", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(clientSource, /localStorage|sessionStorage/);
});

test("self-hosted auth actions expose generic enumeration-safe errors", async () => {
  const failed = { data: null, error: { message: "internal account detail" } };
  const actions = createSelfHostedAuthActions({
    emailOtp: {
      async sendVerificationOtp() {
        return failed;
      },
      async requestPasswordReset() {
        return failed;
      },
      async resetPassword() {
        return failed;
      },
    },
    signIn: {
      async emailOtp() {
        return failed;
      },
      async email() {
        return failed;
      },
    },
  });

  await assert.rejects(
    actions.send("missing@example.com"),
    new Error("暂时无法发送验证码，请稍后再试"),
  );
  await assert.rejects(
    actions.verify("missing@example.com", "123456"),
    new Error("验证码错误或已过期，请重新获取"),
  );
  await assert.rejects(
    actions.signInWithPassword("missing@example.com", "password"),
    new Error("邮箱或密码错误"),
  );
  await assert.rejects(
    actions.requestPasswordReset("missing@example.com"),
    new Error("暂时无法发送验证码，请稍后再试"),
  );
  await assert.rejects(
    actions.resetPassword("missing@example.com", "123456", "password"),
    new Error("验证码错误或已过期，请重新获取"),
  );
});

test("login UI preserves accessible OTP, password, registration, and reset inputs", () => {
  const component = readFileSync(
    new URL("../src/components/email-otp-login.tsx", import.meta.url),
    "utf8",
  );
  for (const label of ["验证码登录", "密码登录", "注册账号", "忘记密码"]) {
    assert.match(component, new RegExp(label));
  }
  for (const autocomplete of [
    "email",
    "current-password",
    "new-password",
    "one-time-code",
  ]) {
    assert.match(component, new RegExp(`autoComplete="${autocomplete}"`));
  }
  assert.match(component, /role="alert"/);
  assert.match(component, /role="status"/);

  const route = readFileSync(
    new URL("../src/app/api/account/password/route.ts", import.meta.url),
    "utf8",
  );
  assert.match(route, /services\.user\.api\.getSession/);
  assert.match(route, /services\.user\.api\.setPassword/);
  assert.match(route, /provider_id = 'credential'/);
  assert.doesNotMatch(route, /update\s+identity\.accounts/i);
});
