import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { createSelfHostedOtpActions } from "../src/modules/identity/client.ts";

test("login page selects the auth provider from server-only validated config", () => {
  const page = readFileSync(
    new URL("../src/app/login/page.tsx", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(page, /["']use client["']/);
  assert.match(page, /readIdentityConfig\(process\.env\)/);
  assert.match(page, /provider=\{config\.provider\}/);
  assert.doesNotMatch(page, /NEXT_PUBLIC_AUTH_PROVIDER/);
});

test("self-hosted OTP actions call Better Auth without browser token storage", async () => {
  const calls: Array<{ operation: string; input: Record<string, string> }> = [];
  const actions = createSelfHostedOtpActions({
    emailOtp: {
      async sendVerificationOtp(input) {
        calls.push({ operation: "send", input });
        return { data: { success: true }, error: null };
      },
    },
    signIn: {
      async emailOtp(input) {
        calls.push({ operation: "verify", input });
        return { data: { user: { id: "user-id" } }, error: null };
      },
    },
  });

  await actions.send(" Person@Example.com ");
  await actions.verify(" Person@Example.com ", "123456");

  assert.deepEqual(calls, [
    {
      operation: "send",
      input: { email: "person@example.com", type: "sign-in" },
    },
    {
      operation: "verify",
      input: { email: "person@example.com", otp: "123456" },
    },
  ]);
  const clientSource = readFileSync(
    new URL("../src/modules/identity/client.ts", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(clientSource, /localStorage|sessionStorage/);
});

test("self-hosted OTP actions expose generic enumeration-safe errors", async () => {
  const actions = createSelfHostedOtpActions({
    emailOtp: {
      async sendVerificationOtp() {
        return {
          data: null,
          error: { message: "database says account does not exist" },
        };
      },
    },
    signIn: {
      async emailOtp() {
        return {
          data: null,
          error: { message: "internal OTP hash 123456 mismatch" },
        };
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
});
