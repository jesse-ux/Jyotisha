import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  persistExistingChatSession,
  sessionMutationMenuVisible,
} from "../src/lib/chat-session-persistence.ts";

const sql = readFileSync(new URL(
  "../supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql",
  import.meta.url,
), "utf8");

test("chat sessions expose owner-only delete", () => {
  assert.match(sql, /create policy chat_sessions_delete_own[\s\S]*for delete[\s\S]*auth\.uid\(\).*user_id/i);
  assert.match(sql, /grant delete on table public\.chat_sessions to authenticated/i);
});

test("a late response cannot insert or resurrect a session deleted on another device", async () => {
  const inserts = 0;
  let updates = 0;
  await assert.rejects(
    persistExistingChatSession(async () => {
      updates += 1;
      return { found: false, error: null };
    }),
    /另一设备删除.*不会重新创建/,
  );
  assert.equal(updates, 1);
  assert.equal(inserts, 0);
});

test("an existing session update succeeds without a create fallback", async () => {
  let updates = 0;
  await persistExistingChatSession(async () => {
    updates += 1;
    return { found: true, error: null };
  });
  assert.equal(updates, 1);
});

test("session mutation menu closes and cannot act while a response is pending", () => {
  assert.equal(sessionMutationMenuVisible(true, true), false);
  assert.equal(sessionMutationMenuVisible(false, true), false);
  assert.equal(sessionMutationMenuVisible(true, false), true);
});
