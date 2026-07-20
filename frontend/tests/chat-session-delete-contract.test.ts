import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const sql = readFileSync(new URL(
  "../supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql",
  import.meta.url,
), "utf8");

test("chat sessions expose owner-only delete", () => {
  assert.match(sql, /create policy chat_sessions_delete_own[\s\S]*for delete[\s\S]*auth\.uid\(\).*user_id/i);
  assert.match(sql, /grant delete on table public\.chat_sessions to authenticated/i);
});
