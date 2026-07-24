import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const financeMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260721150000_align_conversational_finance_domain.sql",
    import.meta.url,
  ),
  "utf8",
);
const healthPressureMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260722170000_align_conversational_health_pressure_domain.sql",
    import.meta.url,
  ),
  "utf8",
);
const requestCardinalityMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260722180000_align_conversational_evidence_request_cardinality.sql",
    import.meta.url,
  ),
  "utf8",
);
const followUpMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260723030000_align_conversational_follow_up_request.sql",
    import.meta.url,
  ),
  "utf8",
);
const assistantOnlyRegenerateMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260724030000_allow_assistant_only_rectification_regenerate.sql",
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
    assert.match(financeMigration, new RegExp(validator.replace(/[()]/g, "\\$&")));
  }
  assert.match(financeMigration, /'education', 'finance', 'relocation'/);
  assert.match(financeMigration, /birth_time_rectification_event_evidence_domain_check/);
});

test("durable public recap accepts and validates its optional domain", () => {
  assert.match(
    financeMigration,
    /array\['id', 'summary', 'dateLabel', 'domain', 'isCorrection'\]/,
  );
  assert.match(financeMigration, /item \? 'domain'/);
  assert.match(financeMigration, /item ->> 'domain' not in/);
});

test("durable public turns accept health pressure follow-up requests", () => {
  for (const validator of [
    "conversational_rectification_valid_evidence_request(jsonb)",
    "conversational_rectification_valid_evidence_recap(jsonb)",
    "conversational_rectification_valid_life_event_evidence(jsonb)",
    "conversational_rectification_valid_private_candidate(jsonb)",
  ]) {
    assert.match(
      healthPressureMigration,
      new RegExp(validator.replace(/[()]/g, "\\$&")),
    );
  }
  assert.match(healthPressureMigration, /'finance'', ''health_pressure'', ''relocation'/);
  assert.match(
    healthPressureMigration,
    /'finance', 'health_pressure', 'relocation'/,
  );
  assert.match(healthPressureMigration, /birth_time_rectification_event_evidence_domain_check/);
});

test("durable evidence requests allow one focused follow-up domain", () => {
  assert.match(
    requestCardinalityMigration,
    /conversational_rectification_valid_evidence_request\(jsonb\)/,
  );
  assert.match(requestCardinalityMigration, /'between 2 and 4'/);
  assert.match(requestCardinalityMigration, /'between 1 and 4'/);
});

test("durable evidence requests accept bounded follow-up targeting", () => {
  assert.match(
    followUpMigration,
    /array\['domains', 'datePrecision', 'freeTextAllowed', 'followUp'\]/,
  );
  assert.match(followUpMigration, /array\['kind', 'evidenceId'\]/);
  assert.match(
    followUpMigration,
    /'new_event', 'event_date', 'event_detail'/,
  );
  assert.match(followUpMigration, /valid_uuid_text/);
});

test("durable regenerate turns may persist an assistant-only replacement", () => {
  assert.match(assistantOnlyRegenerateMigration, /p_user_message is not null and/);
  assert.match(assistantOnlyRegenerateMigration, /v_saved_user_message is distinct from p_user_message/);
  assert.doesNotMatch(
    assistantOnlyRegenerateMigration,
    /if p_user_message is null\s+or/,
  );
});
