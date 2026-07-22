import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { writeChatSession, type ChatSessionWrite } from "../src/lib/chat-session-write-contract.ts";

const sessionId = "11111111-1111-4111-8111-111111111111";
const values = {
  title: "事业方向",
  theme: "career",
  model_id: "gpt-test",
  messages: [{ role: "user", text: "你好" }],
  session_type: "consultation",
  rectification_case_id: null,
  updated_at: "2026-07-22T00:00:00.000Z",
} satisfies ChatSessionWrite;

test("chat session writes use same-origin API instead of browser-to-Supabase requests", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  await writeChatSession(sessionId, values, "update", async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ ok: true });
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0]?.url, `/api/sessions/${sessionId}`);
  assert.equal(calls[0]?.init?.method, "PATCH");
  assert.equal(calls[0]?.init?.credentials, "same-origin");
});

test("transient Load failed is retried and never exposed as raw browser copy", async () => {
  let attempts = 0;
  await assert.rejects(
    writeChatSession(sessionId, values, "update", async () => {
      attempts += 1;
      throw new TypeError("Load failed");
    }),
    (error: unknown) => error instanceof Error
      && error.message === "网络暂时不可用，云端记录尚未更新",
  );
  assert.equal(attempts, 2);
});

test("owner or validation failures are not retried", async () => {
  let attempts = 0;
  await assert.rejects(
    writeChatSession(sessionId, values, "update", async () => {
      attempts += 1;
      return Response.json({ error: "聊天记录不存在或已被删除" }, { status: 404 });
    }),
    /聊天记录不存在或已被删除/,
  );
  assert.equal(attempts, 1);
});

test("session API owns create and update while answer UI keeps sync failures out of reply errors", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const collectionRoute = readFileSync(new URL("../src/app/api/sessions/route.ts", import.meta.url), "utf8");
  const itemRoute = readFileSync(new URL("../src/app/api/sessions/[id]/route.ts", import.meta.url), "utf8");

  assert.match(page, /writeChatSession\(session\.id, values, mode\)/);
  assert.doesNotMatch(page, /云端同步失败.*回答仍保留在当前页面/);
  assert.match(collectionRoute, /export async function POST/);
  assert.match(itemRoute, /export async function PATCH/);
  assert.match(itemRoute, /\.eq\("user_id", user\.id\)/);
});
