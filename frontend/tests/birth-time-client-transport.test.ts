import assert from "node:assert/strict";
import test from "node:test";
import { postJson } from "../src/lib/birth-time-client-transport.ts";

test("non-json 502 returns a null payload instead of leaking WebKit syntax text", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response("bad gateway", { status: 502 });
  try {
    const result = await postJson({ url: "/x", body: "{}", retryLostResponse: false });
    assert.equal(result.response.status, 502);
    assert.equal(result.payload, null);
  } finally {
    globalThis.fetch = original;
  }
});

test("DOMException SyntaxError is classified as a lost response", async () => {
  const original = globalThis.fetch;
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    if (attempts === 1) throw new DOMException("pattern", "SyntaxError");
    return Response.json({ ok: true });
  };
  try {
    const result = await postJson({ url: "/x", body: "{}", retryLostResponse: true });
    assert.deepEqual(result.payload, { ok: true });
  } finally {
    globalThis.fetch = original;
  }
});
