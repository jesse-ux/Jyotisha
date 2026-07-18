import assert from "node:assert/strict";
import test from "node:test";
import {
  parseBirthTimeProfile,
  parseCandidateDifferenceBuild,
  parseCandidateResult,
  parseDynamicChoiceScoring,
  parseRectificationQuestionnaire,
  parseRectificationScoring,
} from "../src/lib/birth-time-journey-adapters.ts";

const coordinates = {
  latitude: 31.2304,
  longitude: 121.4737,
  timezone_offset: 8,
} as const;

const apiPacket = {
  success: true,
  endpoint: "dynamic_rectification_opportunities",
  case_id: "case-1",
  scoring_version: "birth-time-choice-scoring-v2",
  current_range: { start_time: "05:30", end_time: "05:33" },
  opportunities: [{
    opportunity_id: "career-window",
    dimension_code: "career",
    neutral_context: "career",
    estimated_information_gain: 0.5,
    candidate_partition_fingerprint: "career-partitions-v2",
    fallback_prompt: "哪段经历更接近你的职业变化？",
    partitions: [{
      partition_id: "career-early",
      descriptor: "2014-01-01--2017-12-31",
      fallback_label: "2014—2017",
      candidate_scores: { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 },
    }, {
      partition_id: "career-late",
      descriptor: "2018-01-01--2021-12-31",
      fallback_label: "2018—2021",
      candidate_scores: { "05:30": 1, "05:31": 0, "05:32": 0, "05:33": 1 },
    }],
  }],
  asked_question_fingerprints: ["asked-1"],
  candidate_partition_fingerprints: ["partition-1"],
  recent_range_history: [{ start_time: "05:30", end_time: "05:33" }],
  candidate_model: {
    version: "birth-time-choice-scoring-v2",
    candidate_times: ["05:30", "05:31", "05:32", "05:33"],
  },
} as const;

const apiScore = {
  success: true,
  endpoint: "dynamic_rectification_score",
  result_id: "1d8ee348-61a3-433d-8907-ff6d281b9992",
  confidence: "low",
  can_apply: false,
  winning_segment: {
    start_time: "05:31",
    end_time: "05:32",
    representative_time: "05:31",
    width_minutes: 2,
  },
  event_count: 1,
  domain_count: 1,
  top_score: 0.5,
  second_score: 0,
  margin_percent: 50,
  reasons: ["insufficient_effective_evidence"],
  evidence: [],
  algorithm_version: "birth-time-choice-scoring-v2",
  evidence_mode: "dynamic_choice",
  effective_answer_count: 1,
  dimension_count: 1,
} as const;

test("difference packets keep candidate scores on the server-only internal shape", () => {
  const build = parseCandidateDifferenceBuild(apiPacket);

  assert.equal(build.scoringPartitions["career-window"]?.[0]?.candidateScores["05:31"], 1);
  assert.equal(build.packet.opportunities[0]?.estimatedInformationGain, 0.5);
  assert.deepEqual(build.candidateModel, apiPacket.candidate_model);
  assert.equal("candidateScores" in build.packet.opportunities[0]!.partitions[0]!, false);
});

test("difference packet parser rejects non-versioned or extra response fields", () => {
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    scoring_version: "birth-time-choice-scoring-v1",
  }));
  assert.throws(() => parseCandidateDifferenceBuild({ ...apiPacket, confidence: "high" }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{
      ...apiPacket.opportunities[0],
      partitions: [{
        ...apiPacket.opportunities[0].partitions[0],
        candidate_scores: { "not-a-time": 1 },
      }, apiPacket.opportunities[0].partitions[1]],
    }],
  }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{
      ...apiPacket.opportunities[0],
      partitions: [{
        ...apiPacket.opportunities[0].partitions[0],
        candidate_scores: {
          ...apiPacket.opportunities[0].partitions[0].candidate_scores,
          "05:34": 1,
        },
      }, apiPacket.opportunities[0].partitions[1]],
    }],
  }));
});

test("difference packet parser preserves an exact cross-midnight score range", () => {
  const parsed = parseCandidateDifferenceBuild({
    ...apiPacket,
    current_range: { start_time: "23:59", end_time: "00:00" },
    opportunities: [{
      ...apiPacket.opportunities[0],
      partitions: apiPacket.opportunities[0].partitions.map((partition) => ({
        ...partition,
        candidate_scores: { "23:59": 1, "00:00": 0 },
      })),
    }],
  });

  assert.deepEqual(parsed.packet.currentRange, { startTime: "23:59", endTime: "00:00" });
});

test("choice score parser rejects model-controlled confidence fields", () => {
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore,
    confidence: "high",
    effective_answer_count: 1,
    can_apply: true,
  }));
});

test("choice scores adapt into the existing guarded candidate shape", () => {
  const parsed = parseDynamicChoiceScoring(apiScore);

  assert.equal(parsed.candidate.eventCount, parsed.effectiveAnswerCount);
  assert.equal(parsed.candidate.domainCount, parsed.dimensionCount);
  assert.deepEqual(parsed.candidate.evidence, []);
  assert.equal(parsed.candidate.algorithmVersion, "birth-time-choice-scoring-v2");
});

test("choice score parser rejects count, evidence mode, evidence, and version mismatches", () => {
  assert.throws(() => parseDynamicChoiceScoring({ ...apiScore, event_count: 2 }));
  assert.throws(() => parseDynamicChoiceScoring({ ...apiScore, domain_count: 2 }));
  assert.throws(() => parseDynamicChoiceScoring({ ...apiScore, evidence_mode: "dated_event" }));
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore,
    evidence: [{
      event_id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
      domain: "career",
      candidate_time: "05:31",
      rule_ids: ["forged"],
      points: 1,
    }],
  }));
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore,
    algorithm_version: "birth-time-event-scoring-v1",
  }));
});

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

test("candidate compatibility result accepts ten effective items but not eleven", () => {
  const lowCandidate = {
    result_id: "1d8ee348-61a3-433d-8907-ff6d281b9992",
    confidence: "low",
    can_apply: false,
    winning_segment: null,
    event_count: 10,
    domain_count: 5,
    top_score: 0,
    second_score: 0,
    margin_percent: 0,
    reasons: ["safety_cap"],
    evidence: [],
    algorithm_version: "birth-time-choice-scoring-v2",
  } as const;

  assert.equal(parseCandidateResult(lowCandidate).eventCount, 10);
  assert.throws(() => parseCandidateResult({ ...lowCandidate, event_count: 11 }));
});
