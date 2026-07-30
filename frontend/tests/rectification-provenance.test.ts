import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { calculationSpecSchema, lifeEventRevisionSchema, reviseEventRequestSchema, type CalculationSpec, type LifeEventRevision } from "../src/lib/rectification-v4/contracts.ts";
import { createRectificationV4CandidateEngine } from "../src/lib/rectification-v4/candidate-engine.ts";
import { calculationSpecHash, evidenceSetHash } from "../src/lib/rectification-v4/fingerprints.ts";
import { rectificationEventRevisionFromRow } from "../src/lib/rectification-v4/supabase-store.ts";

const legacySpec: CalculationSpec = {
  version: "rectification-calculation-spec-v4", birthDate: "1990-01-02",
  candidateRange: { start: "05:00", end: "06:00" }, latitude: 25.033, longitude: 121.5654,
  timezoneOffsetHours: 8, ayanamsa: "lahiri", nodeMode: "mean", minuteStep: 1,
};
const baseEvent: LifeEventRevision = {
  id: "00000000-0000-4000-8000-000000000001", eventId: "00000000-0000-4000-8000-000000000002", revision: 1,
  domain: "career", eventKind: "career_change", subject: "self", relatedPerson: null,
  summary: "工作变动", rawText: "2020年工作变动", dateRange: { start: "2020-01-01", end: "2020-12-31", precision: "year", label: "2020" },
  scoreability: "scoreable", supersedesRevisionId: null, createdAt: "2026-07-30T00:00:00.000Z",
};

test("legacy provenance stays absent and legacy hashes stay unchanged", () => {
  const spec = calculationSpecSchema.parse(legacySpec);
  const event = lifeEventRevisionSchema.parse(baseEvent);
  assert.equal(Object.hasOwn(spec, "birthTimeSource"), false);
  assert.equal(Object.hasOwn(event, "dateSource"), false);
  assert.equal(calculationSpecHash(spec), "b50754817fd516b4bb089ee85f9ebb4c8fa2a148e9cdfa5c6bf694e979b216fe");
  assert.equal(evidenceSetHash([event]), "9086797178bfcaf2f5d23f309eacf49ddab4e75e2aefa120b111dbc31a7382f5");
});

test("enriched calculation spec and evidence provenance hash deterministically", () => {
  const enriched = calculationSpecSchema.parse({ ...legacySpec, birthTimeSource: "family_exact", timezoneId: "Asia/Taipei", timezoneSource: "iana_historical", localTimeStatus: "resolved" });
  assert.equal(calculationSpecHash(enriched), "fa4afe79228bedebd809c7b3c9d9d32a428f7066e3e1fd1813e44b317bd38e66");
  assert.notEqual(evidenceSetHash([{ ...baseEvent, dateSource: null }]), evidenceSetHash([baseEvent]));
  assert.equal(evidenceSetHash([{ ...baseEvent, dateSource: "user_reported", dateReliability: "medium" }]), evidenceSetHash([{ ...baseEvent, dateReliability: "medium", dateSource: "user_reported" }]));
});

test("revision requests and Supabase rows preserve missing versus explicit null", () => {
  const request = reviseEventRequestSchema.parse({
    actionId: "00000000-0000-4000-8000-000000000003", expectedCaseVersion: 1,
    domain: "career", eventKind: "career_change", subject: "self", relatedPerson: null,
    summary: "工作变动", rawText: "2020年工作变动", dateRange: baseEvent.dateRange, dateSource: null,
  });
  assert.equal(Object.hasOwn(request, "dateSource"), true);
  const row = {
    id: baseEvent.id, event_id: baseEvent.eventId, revision: 1, domain: "career", event_kind: "career_change",
    subject: "self", related_person: null, summary: baseEvent.summary, raw_text: baseEvent.rawText,
    date_start: "2020-01-01", date_end: "2020-12-31", date_precision: "year", date_label: "2020",
    scoreability: "scoreable", supersedes_revision_id: null, created_at: baseEvent.createdAt,
  };
  assert.equal(Object.hasOwn(rectificationEventRevisionFromRow(row), "dateSource"), false);
  const enriched = rectificationEventRevisionFromRow({ ...row, date_provenance: { dateSource: null, dateReliability: "medium" } });
  assert.equal(Object.hasOwn(enriched, "dateSource"), true);
  assert.equal(enriched.dateSource, null);
  assert.equal(enriched.dateReliability, "medium");
});

test("forward-only migration persists provenance in both RPCs and retains completed replay", () => {
  const sql = readFileSync(new URL("../supabase/migrations/20260730010000_rectification_provenance.sql", import.meta.url), "utf8");
  assert.match(sql, /add column if not exists date_provenance jsonb/);
  assert.equal((sql.match(/where entry\.key in \('dateSource'/g) ?? []).length, 2);
  assert.match(sql, /create or replace function public\.revise_birth_time_rectification_v4_event/);
  assert.match(sql, /create or replace function public\.complete_birth_time_rectification_v5_job/);
  assert.match(sql, /if v_job\.status = 'completed'[\s\S]*rectification_v5_replay_payload_mismatch[\s\S]*return v_case\.id/);
  assert.doesNotMatch(sql, /update public\.birth_time_rectification_v4_event_revisions/i);
});

test("candidate engine forwards present provenance without inventing missing fields", async () => {
  let body: Record<string, unknown> | null = null;
  const engine = createRectificationV4CandidateEngine({
    apiBase: "http://example.test",
    fetchImpl: async (_input, init) => {
      body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      throw new Error("captured");
    },
  });
  await assert.rejects(engine.score({
    calculationSpec: { ...legacySpec, birthTimeSource: "family_exact", timezoneId: "Asia/Taipei", localTimeStatus: null },
    events: [{ ...baseEvent, dateSource: "user_reported", dateReliability: null }],
  }), /captured/);
  const captured = body as unknown as Record<string, unknown>;
  assert.equal(captured.birth_time_source, "family_exact");
  assert.equal(captured.timezone_id, "Asia/Taipei");
  assert.equal(Object.hasOwn(captured, "timezone_source"), false);
  assert.equal(captured.local_time_status, null);
  const event = (captured.events as Record<string, unknown>[])[0];
  assert.equal(event.date_source, "user_reported");
  assert.equal(event.date_reliability, null);
  assert.equal(Object.hasOwn(event, "date_corroboration"), false);
});

test("candidate engine sends only the selected pair and persists a safe VedAstro projection", async () => {
  let body: Record<string, unknown> | null = null;
  const engine = createRectificationV4CandidateEngine({
    apiBase: "http://example.test",
    fetchImpl: async (input, init) => {
      assert.equal(String(input), "http://example.test/api/rectification/v5/vedastro-validate");
      body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      return new Response(JSON.stringify({
        status: "pass",
        passed: true,
        can_confirm_exact_minute: false,
        candidate_times: { primary: "05:13", runner_up: "05:14" },
        blockers: [],
        minute_sensitive_validation: {
          comparison_ready: true,
          discriminated: true,
          discriminated_layers: ["D9"],
          raw_response: { secret: true },
        },
        event_validation: {
          eligible_event_count: 1,
          supported_event_count: 1,
          unsupported_events: [{ event_id: "private", summary: "must not persist" }],
          candidates: [
            { role: "primary", metric: { requested_event_count: 1, successful_event_count: 1, matched_event_count: 1, event_hit_count: 2, signal_lift: 3 }, events: [{ raw_response: "secret" }] },
            { role: "runner_up", metric: { requested_event_count: 1, successful_event_count: 1, matched_event_count: 1, event_hit_count: 1, signal_lift: 1 } },
          ],
        },
        raw_request: { api_key: "secret" },
      }), { status: 200, headers: { "content-type": "application/json" } });
    },
  });
  assert.ok(engine.validateWithVedAstro);
  const validation = await engine.validateWithVedAstro({
    calculationSpec: legacySpec,
    events: [baseEvent],
    candidateTimes: ["05:13", "05:14"],
  });
  const captured = body as unknown as Record<string, unknown>;
  assert.deepEqual(captured.candidate_times, ["05:13", "05:14"]);
  assert.equal(validation.status, "pass");
  assert.equal(validation.canConfirmExactMinute, false);
  assert.deepEqual(validation.minuteSensitiveValidation.discriminatedLayers, ["D9"]);
  const serialized = JSON.stringify(validation);
  assert.doesNotMatch(serialized, /raw_request|raw_response|api_key|must not persist|secret/);
});
