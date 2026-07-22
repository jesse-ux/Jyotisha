import assert from "node:assert/strict";
import test from "node:test";

import { FakeEmailOtpSender } from "../src/modules/identity/email/fake-email-otp-sender.ts";
import { ResendEmailOtpSender } from "../src/modules/identity/email/resend-email-otp-sender.ts";
import type { EmailOtpMessage } from "../src/modules/identity/contracts.ts";

const message: EmailOtpMessage = {
  email: "person@example.com",
  otp: "123456",
  type: "sign-in",
  idempotencyKey: "otp-request-018f4e6d",
};

test("fake OTP sender records messages without network access", async () => {
  const sender = new FakeEmailOtpSender();

  await sender.send(message);

  assert.deepEqual(sender.messages, [message]);
  assert.notEqual(sender.messages[0], message);
});

test("Resend OTP sender emits an idempotent authenticated request", async () => {
  const requests: Array<{ input: string | URL | Request; init?: RequestInit }> = [];
  const fetchImpl: typeof fetch = async (input, init) => {
    requests.push({ input, init });
    return Response.json({ id: "email_123" }, { status: 200 });
  };
  const sender = new ResendEmailOtpSender({
    apiKey: "re_test_secret_value",
    from: "Jyotisha <login@staging.jyotisha.chat>",
    fetchImpl,
  });

  await sender.send(message);

  assert.equal(requests.length, 1);
  assert.equal(requests[0].input, "https://api.resend.com/emails");
  assert.equal(requests[0].init?.method, "POST");
  const headers = new Headers(requests[0].init?.headers);
  assert.equal(headers.get("authorization"), "Bearer re_test_secret_value");
  assert.equal(headers.get("content-type"), "application/json");
  assert.equal(headers.get("idempotency-key"), message.idempotencyKey);
  assert.equal(headers.get("user-agent"), "jyotisha-identity/1.0");

  const body = JSON.parse(String(requests[0].init?.body)) as Record<
    string,
    unknown
  >;
  assert.equal(body.from, "Jyotisha <login@staging.jyotisha.chat>");
  assert.deepEqual(body.to, [message.email]);
  assert.equal(body.subject, "Your Jyotisha sign-in code");
  assert.match(String(body.text), /123456/);
  assert.match(String(body.html), /123456/);
});

test("Resend OTP sender escapes template values", async () => {
  let body = "";
  const sender = new ResendEmailOtpSender({
    apiKey: "re_test_secret_value",
    from: "Jyotisha <login@staging.jyotisha.chat>",
    fetchImpl: async (_input, init) => {
      body = String(init?.body);
      return Response.json({ id: "email_123" });
    },
  });

  await sender.send({ ...message, otp: "<script>alert(1)</script>" });

  const parsed = JSON.parse(body) as { html: string };
  assert.doesNotMatch(parsed.html, /<script>/);
  assert.match(parsed.html, /&lt;script&gt;/);
});

test("Resend errors exclude secrets, OTPs, recipients, and provider bodies", async () => {
  const apiKey = "re_secret_should_not_leak";
  const rawProviderError = "provider diagnostic should not leak";
  const sender = new ResendEmailOtpSender({
    apiKey,
    from: "Jyotisha <login@staging.jyotisha.chat>",
    fetchImpl: async () =>
      new Response(rawProviderError, {
        status: 429,
        statusText: "Too Many Requests",
      }),
  });

  await assert.rejects(sender.send(message), (error: unknown) => {
    assert.ok(error instanceof Error);
    assert.equal(error.message, "OTP email delivery failed");
    assert.doesNotMatch(error.message, new RegExp(apiKey));
    assert.doesNotMatch(error.message, new RegExp(message.otp));
    assert.doesNotMatch(error.message, new RegExp(message.email));
    assert.doesNotMatch(error.message, new RegExp(rawProviderError));
    return true;
  });
});

test("network errors use the same safe delivery error", async () => {
  const sender = new ResendEmailOtpSender({
    apiKey: "re_test_secret_value",
    from: "Jyotisha <login@staging.jyotisha.chat>",
    fetchImpl: async () => {
      throw new Error("socket includes recipient person@example.com");
    },
  });

  await assert.rejects(
    sender.send(message),
    new Error("OTP email delivery failed"),
  );
});
