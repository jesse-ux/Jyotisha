import assert from "node:assert/strict";
import test from "node:test";
import {
  parseBirthTimeProfile,
  parseCandidateResult,
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
    d4Sign: null,
    d9Sign: "Leo",
    d10Sign: "Virgo",
    d24Sign: null,
    d30Sign: null,
  });
});

test("rectification adapter rejects a malformed Python questionnaire", () => {
  assert.throws(() => parseRectificationQuestionnaire({
    questions: [{ id: "missing_prompt" }],
    candidate_scan: { samples: [] },
  }));
});

test("rectification adapter normalizes all evidence-domain Varga signs", () => {
  const questionnaire = parseRectificationQuestionnaire({
    questions: [],
    candidate_scan: {
      samples: [{
        ascendant: { sign: "Cancer" },
        varga_lagna: {
          D4: { sign: "Aries" },
          D9: { sign: "Leo" },
          D10: { sign: "Virgo" },
          D24: { sign: "Gemini" },
          D30: { sign: "Pisces" },
        },
      }],
    },
  });

  assert.deepEqual(questionnaire.samples[0], {
    ascendantSign: "Cancer",
    d4Sign: "Aries",
    d9Sign: "Leo",
    d10Sign: "Virgo",
    d24Sign: "Gemini",
    d30Sign: "Pisces",
  });
});

test("rectification adapter preserves scoring maps needed after the third answer", () => {
  const questionnaire = parseRectificationQuestionnaire({
    questions: [{
      id: "education_environment_shift",
      prompt: "是否有明显学业变化？",
      round: 1,
      options: [{ key: "A", label: "明确有" }],
      scoring_map: {
        A: { cluster: "early_candidate_cluster", points: 3 },
      },
    }],
    candidate_scan: { samples: [] },
  });

  assert.deepEqual(questionnaire.raw.questions, [{
    id: "education_environment_shift",
    prompt: "是否有明显学业变化？",
    round: 1,
    options: [{ key: "A", label: "明确有" }],
    scoring_map: {
      A: { cluster: "early_candidate_cluster", points: 3 },
    },
  }]);
});

test("rectification adapter normalizes scoring without elevating confidence", () => {
  const scoring = parseRectificationScoring({
    answered_count: 3,
    candidate_cluster_rankings: [
      { cluster: "middle_candidate_cluster", score: 5 },
    ],
    next_round: 2,
    next_round_questions: [{
      id: "health_crisis_or_low_period",
      prompt: "是否有明显健康或低谷阶段？",
      options: [{ key: "A", label: "明确有" }],
    }],
  });

  assert.equal(scoring.answeredCount, 3);
  assert.deepEqual(scoring.candidateClusterRankings, [
    { cluster: "middle_candidate_cluster", score: 5 },
  ]);
  assert.equal(scoring.nextRound, 2);
  assert.deepEqual(scoring.nextRoundQuestions, [{
    id: "health_crisis_or_low_period",
    prompt: "是否有明显健康或低谷阶段？",
    options: [{ key: "A", label: "明确有" }],
  }]);
});

test("rectification adapter normalizes an event-scored candidate result", () => {
  const result = parseCandidateResult({
    result_id: "1d8ee348-61a3-433d-8907-ff6d281b9992",
    confidence: "high",
    can_apply: true,
    winning_segment: {
      start_time: "14:22",
      end_time: "14:26",
      representative_time: "14:24",
      width_minutes: 5,
    },
    event_count: 4,
    domain_count: 3,
    top_score: 16,
    second_score: 10,
    margin_percent: 37.5,
    reasons: [],
    evidence: [{
      event_id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
      domain: "career",
      candidate_time: "14:24",
      rule_ids: ["vim_md_domain_house"],
      points: 4,
    }],
    algorithm_version: "birth-time-event-scoring-v1",
  });

  assert.equal(result.resultId, "1d8ee348-61a3-433d-8907-ff6d281b9992");
  assert.equal(result.winningSegment?.representativeTime, "14:24");
  assert.deepEqual(result.evidence[0]?.ruleIds, ["vim_md_domain_house"]);
});
