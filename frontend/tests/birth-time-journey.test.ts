import assert from "node:assert/strict";
import test from "node:test";
import {
  assessBirthTime,
  birthTimeAssessmentSchema,
  candidateResultSchema,
  journeySnapshotSchema,
  withCandidateResult,
  withConfirmedCandidate,
  withRectificationScoring,
} from "../src/lib/birth-time-journey.ts";

const location = { lat: 31.2304, lon: 121.4737, tz: 8 } as const;

test("birth time journey sends a stable hospital record directly to charting", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "hospital_record",
    reportedTime: "08:16",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
    location,
  });

  const snapshot = assessBirthTime(assessment, { kind: "stable" });

  assert.equal(snapshot.state, "ready");
  assert.equal(snapshot.route, "direct_chart");
  assert.equal(snapshot.canApply, true);
  assert.equal(snapshot.activeTime, "08:16");
  assert.equal(snapshot.assistantIntent, "confirm_stable_record");
  assert.equal(journeySnapshotSchema.safeParse(snapshot).success, true);
});

test("birth time journey fails a sensitive hospital record closed into rectification", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "hospital_record",
    reportedTime: "08:16",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
    location,
  });

  const snapshot = assessBirthTime(assessment, { kind: "sensitive" });

  assert.equal(snapshot.state, "rectifying");
  assert.equal(snapshot.route, "rectification");
  assert.equal(snapshot.canApply, false);
  assert.equal(snapshot.activeTime, null);
  assert.equal(snapshot.assistantIntent, "explain_sensitive_boundary");
});

test("birth time journey fails a scanner outage closed into rectification", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "hospital_record",
    reportedTime: "08:16",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
    location,
  });

  const snapshot = assessBirthTime(assessment, { kind: "unavailable" });

  assert.equal(snapshot.route, "rectification");
  assert.equal(snapshot.canApply, false);
  assert.equal(snapshot.assistantIntent, "explain_assessment_unavailable");
});

test("birth time journey routes family and approximate declarations to rectification", () => {
  const family = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "family_exact",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 10,
    uncertaintyAfterMinutes: 10,
    location,
  });
  const approximate = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "approximate",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    location,
  });

  assert.equal(assessBirthTime(family, { kind: "sensitive" }).assistantIntent, "start_light_rectification");
  assert.equal(assessBirthTime(approximate, { kind: "sensitive" }).assistantIntent, "start_standard_rectification");
});

test("birth time journey accepts period-only and unknown declarations without inventing a clock time", () => {
  const period = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "period_only",
    period: "evening",
    location,
  });
  const unknown = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "unknown",
    clue: "家人只记得天黑以后",
    location,
  });

  const periodSnapshot = assessBirthTime(period, { kind: "not_required" });
  const unknownSnapshot = assessBirthTime(unknown, { kind: "not_required" });

  assert.equal(periodSnapshot.reportedRange.label, "18:00—22:59");
  assert.equal(periodSnapshot.activeTime, null);
  assert.equal(periodSnapshot.assistantIntent, "start_period_rectification");
  assert.equal(unknownSnapshot.reportedRange.label, "全天待确认");
  assert.equal(unknownSnapshot.assistantIntent, "collect_time_clues");
});

test("birth time assessment rejects source-specific missing or invalid fields", () => {
  const missingTime = birthTimeAssessmentSchema.safeParse({
    date: "1993-04-17",
    source: "hospital_record",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
    location,
  });
  const invalidFamilyRange = birthTimeAssessmentSchema.safeParse({
    date: "1993-04-17",
    source: "family_exact",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    location,
  });

  assert.equal(missingTime.success, false);
  assert.equal(invalidFamilyRange.success, false);
});

test("rectification scoring can save a candidate but never apply an exact minute", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "approximate",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    location,
  });
  const initial = assessBirthTime(assessment, { kind: "sensitive" });

  const scored = withRectificationScoring(initial, {
    answeredCount: 3,
    candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
  });

  assert.equal(scored.state, "candidate");
  assert.equal(scored.canApply, false);
  assert.equal(scored.activeTime, null);
  assert.equal(scored.assistantIntent, "present_saved_candidate_range");
});

test("the completed questionnaire deterministically requests dated life events", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "period_only",
    period: "early_morning",
    location,
  });
  const initial = assessBirthTime(assessment, { kind: "not_required" });

  const completed = withRectificationScoring(initial, {
    answeredCount: 8,
    candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
    nextRound: null,
    nextRoundQuestions: [],
  });

  assert.equal(completed.state, "rectifying");
  assert.equal(completed.input, "life_events");
  assert.equal(completed.assistantIntent, "collect_dated_life_events");
  assert.equal(completed.canApply, false);
  assert.equal(completed.activeTime, null);
});

test("candidate confidence deterministically selects the next action", () => {
  const assessment = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "approximate",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    location,
  });
  const eventSnapshot = withRectificationScoring(
    assessBirthTime(assessment, { kind: "sensitive" }),
    {
      answeredCount: 8,
      candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
      nextRound: null,
      nextRoundQuestions: [],
    },
  );
  const base = {
    resultId: "1d8ee348-61a3-433d-8907-ff6d281b9992",
    winningSegment: {
      startTime: "14:22",
      endTime: "14:26",
      representativeTime: "14:24",
      widthMinutes: 5,
    },
    eventCount: 4,
    domainCount: 3,
    topScore: 16,
    secondScore: 10,
    marginPercent: 37.5,
    reasons: [],
    evidence: [],
    algorithmVersion: "birth-time-event-scoring-v1",
  } as const;

  const low = withCandidateResult(eventSnapshot, candidateResultSchema.parse({
    ...base,
    confidence: "low",
    canApply: false,
  }));
  const medium = withCandidateResult(eventSnapshot, candidateResultSchema.parse({
    ...base,
    confidence: "medium",
    canApply: false,
  }));
  const highResult = candidateResultSchema.parse({
    ...base,
    confidence: "high",
    canApply: true,
  });
  const high = withCandidateResult(eventSnapshot, highResult);

  assert.deepEqual(
    [low.input, medium.input, high.input],
    ["life_events", "candidate_actions", "candidate_confirmation"],
  );
  assert.deepEqual([low.canApply, medium.canApply, high.canApply], [false, false, true]);
  assert.equal(high.state, "confirming");

  const ready = withConfirmedCandidate(high, highResult, "14:24");
  assert.equal(ready.state, "ready");
  assert.equal(ready.route, "direct_chart");
  assert.equal(ready.activeTime, "14:24");
  assert.equal(ready.canApply, false);
});
