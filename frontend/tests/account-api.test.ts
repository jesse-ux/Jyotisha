import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");

test("account API reads and returns the server-configured rectification price", () => {
  assert.match(source, /parseRectificationPriceCredits\(\s*process\.env\.RECTIFICATION_PRICE_CREDITS,?\s*\)/);
  assert.match(source, /rectificationPriceCredits/);
  assert.doesNotMatch(source, /RECTIFICATION_PRICE_CREDITS[^\n]*\?\?\s*["']1["']/);
});

test("account API projects only the minimum case state needed by the homepage", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(1\)/)?.[0] ?? "";

  assert.match(caseSelect, /id,journey_protocol,status,turn_version,revision_of_case_id,baseline_active_time,updated_at/);
  assert.doesNotMatch(caseSelect, /candidate_scan|event_evidence|validation_receipt|pending_consultation_question|journey_snapshot|turn_state/);
  assert.match(source, /caseId:/);
  assert.match(source, /journeyProtocol:/);
  assert.match(source, /turnVersion:/);
  assert.match(source, /preservesActiveTime:/);
});

test("account API scopes the service-role case lookup to the authenticated account", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(1\)/)?.[0] ?? "";

  assert.match(caseSelect, /\.eq\("user_id", user\.id\)/);
  assert.match(caseSelect, /\.eq\("journey_protocol", "conversational-evidence-v3"\)/);
  assert.match(caseSelect, /\.order\("updated_at", \{ ascending: false \}\)/);
});
