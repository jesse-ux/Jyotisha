import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(
  new URL(
    "../supabase/migrations/20260721150000_align_conversational_finance_domain.sql",
    import.meta.url,
  ),
  "utf8",
);

test("durable rectification SQL accepts every application evidence domain", () => {
  for (const validator of [
    "conversational_rectification_valid_evidence_request(jsonb)",
    "conversational_rectification_valid_life_event_evidence(jsonb)",
    "conversational_rectification_valid_private_candidate(jsonb)",
  ]) {
    assert.match(migration, new RegExp(validator.replace(/[()]/g, "\\$&")));
  }
  assert.match(migration, /'education', 'finance', 'relocation'/);
  assert.match(migration, /birth_time_rectification_event_evidence_domain_check/);
});

test("durable public recap accepts and validates its optional domain", () => {
  assert.match(
    migration,
    /array\['id', 'summary', 'dateLabel', 'domain', 'isCorrection'\]/,
  );
  assert.match(migration, /item \? 'domain'/);
  assert.match(migration, /item ->> 'domain' not in/);
});
