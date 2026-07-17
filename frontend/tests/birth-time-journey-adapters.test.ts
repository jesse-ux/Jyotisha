import assert from "node:assert/strict";
import test from "node:test";
import {
  parseBirthTimeProfile,
  parseRectificationQuestionnaire,
  parseRectificationScoring,
} from "../src/lib/birth-time-journey-adapters.ts";

const coordinates = {
  latitude: 31.2304,
  longitude: 121.4737,
  timezone_offset: 8,
} as const;

test("birth time profile adapter parses an exact hospital declaration", () => {
  const assessment = parseBirthTimeProfile({
    birth_date: "1993-04-17",
    reported_birth_time: "08:16:00",
    birth_time_source: "hospital_record",
    uncertainty_before_minutes: 2,
    uncertainty_after_minutes: 2,
    ...coordinates,
  });

  assert.equal(assessment.source, "hospital_record");
  if (assessment.source === "hospital_record") {
    assert.equal(assessment.reportedTime, "08:16");
    assert.equal(assessment.location.lon, 121.4737);
  }
});

test("birth time profile adapter parses a period without inventing a time", () => {
  const assessment = parseBirthTimeProfile({
    birth_date: "1993-04-17",
    reported_birth_time: null,
    birth_time_source: "period_only",
    birth_time_period: "evening",
    ...coordinates,
  });

  assert.equal(assessment.source, "period_only");
  assert.equal("reportedTime" in assessment, false);
});

test("birth time profile adapter rejects missing location coordinates", () => {
  assert.throws(() => parseBirthTimeProfile({
    birth_date: "1993-04-17",
    reported_birth_time: "08:16:00",
    birth_time_source: "hospital_record",
    uncertainty_before_minutes: 2,
    uncertainty_after_minutes: 2,
  }));
});

test("rectification adapter normalizes Python questionnaire samples and options", () => {
  const questionnaire = parseRectificationQuestionnaire({
    questions: [{
      id: "education_environment_shift",
      prompt: "是否有明显学业变化？",
      options: [
        { key: "A", label: "明确有" },
        { key: "D", label: "不记得" },
      ],
    }],
    candidate_scan: {
      samples: [{
        ascendant: { sign: "Cancer" },
        varga_lagna: {
          D9: { sign: "Leo" },
          D10: { sign: "Virgo" },
        },
      }],
    },
  });

  assert.deepEqual(questionnaire.questions[0]?.options, [
    { key: "A", label: "明确有" },
    { key: "D", label: "不记得" },
  ]);
  assert.deepEqual(questionnaire.samples[0], {
    ascendantSign: "Cancer",
    d9Sign: "Leo",
    d10Sign: "Virgo",
  });
});

test("rectification adapter rejects a malformed Python questionnaire", () => {
  assert.throws(() => parseRectificationQuestionnaire({
    questions: [{ id: "missing_prompt" }],
    candidate_scan: { samples: [] },
  }));
});

test("rectification adapter normalizes scoring without elevating confidence", () => {
  const scoring = parseRectificationScoring({
    answered_count: 3,
    candidate_cluster_rankings: [
      { cluster: "middle_candidate_cluster", score: 5 },
    ],
    next_round: 2,
  });

  assert.equal(scoring.answeredCount, 3);
  assert.deepEqual(scoring.candidateClusterRankings, [
    { cluster: "middle_candidate_cluster", score: 5 },
  ]);
  assert.equal(scoring.raw.next_round, 2);
});
