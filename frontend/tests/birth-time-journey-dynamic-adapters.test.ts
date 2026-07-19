import assert from "node:assert/strict";
import test from "node:test";
import {
  parseCandidateDifferenceBuild,
  parseDynamicChoiceScoring,
} from "../src/lib/birth-time-journey-dynamic-adapters.ts";

const scores = { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 } as const;
const inverseScores = { "05:30": 1, "05:31": 0, "05:32": 0, "05:33": 1 } as const;
const firstPartition = {
  partition_id: "career-early",
  descriptor: "2014-01-01--2017-12-31",
  fallback_label: "2014—2017",
  candidate_scores: scores,
} as const;
const secondPartition = {
  partition_id: "career-late",
  descriptor: "2018-01-01--2021-12-31",
  fallback_label: "2018—2021",
  candidate_scores: inverseScores,
} as const;
const opportunity = {
  opportunity_id: "career-window",
  dimension_code: "career",
  neutral_context: "career",
  estimated_information_gain: 0.5,
  candidate_partition_fingerprint: "career-partitions-v2",
  fallback_prompt: "哪段经历更接近你的职业变化？",
  partitions: [firstPartition, secondPartition],
} as const;
const apiPacket = {
  success: true,
  endpoint: "dynamic_rectification_opportunities",
  case_id: "case-1",
  scoring_version: "birth-time-choice-scoring-v2",
  current_range: { start_time: "05:30", end_time: "05:33" },
  opportunities: [opportunity],
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

test("difference packets separate public copy from private score vectors", () => {
  const build = parseCandidateDifferenceBuild(apiPacket);
  const mappedOpportunity = build.packet.opportunities[0];
  const mappedPartition = mappedOpportunity?.partitions[0];
  const privatePartition = build.scoringPartitions["career-window"]?.[0];

  assert.equal(mappedOpportunity?.opportunityId, "career-window");
  assert.equal(mappedOpportunity?.estimatedInformationGain, 0.5);
  assert.equal(mappedPartition?.partitionId, "career-early");
  assert.equal(mappedPartition && "candidateScores" in mappedPartition, false);
  assert.equal(privatePartition?.candidateScores["05:31"], 1);
  assert.deepEqual(build.candidateModel, {
    version: "birth-time-choice-scoring-v2",
    candidate_times: ["05:30", "05:31", "05:32", "05:33"],
  });
});

test("difference packets enforce the public prompt limit at the API boundary", () => {
  const withPrompt = (length: number) => ({
    ...apiPacket,
    opportunities: [{
      ...apiPacket.opportunities[0],
      fallback_prompt: `${"问".repeat(length - 1)}？`,
    }],
  });

  assert.equal(parseCandidateDifferenceBuild(withPrompt(120)).packet.opportunities[0]?.fallbackPrompt.length, 120);
  assert.throws(() => parseCandidateDifferenceBuild(withPrompt(121)));
});

test("difference packets reject wrong versions, extra fields, and invalid score keys", () => {
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket, scoring_version: "birth-time-choice-scoring-v1",
  }));
  assert.throws(() => parseCandidateDifferenceBuild({ ...apiPacket, confidence: "high" }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket, opportunities: [{ ...opportunity, model_controlled: true }],
  }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{ ...opportunity, partitions: [{ ...firstPartition, model_controlled: true }, secondPartition] }],
  }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{
      ...opportunity,
      partitions: [{ ...firstPartition, candidate_scores: { "not-a-time": 1 } }, secondPartition],
    }],
  }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{
      ...opportunity,
      partitions: [{ ...firstPartition, candidate_scores: { ...scores, "05:34": 1 } }, secondPartition],
    }],
  }));
});

test("difference packets reject duplicate opportunity and partition identifiers", () => {
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [opportunity, opportunity],
  }));
  assert.throws(() => parseCandidateDifferenceBuild({
    ...apiPacket,
    opportunities: [{
      ...opportunity,
      partitions: [firstPartition, { ...secondPartition, partition_id: firstPartition.partition_id }],
    }],
  }));
});

test("difference packets preserve an exact cross-midnight score range", () => {
  const parsed = parseCandidateDifferenceBuild({
    ...apiPacket,
    current_range: { start_time: "23:59", end_time: "00:00" },
    opportunities: [{
      ...opportunity,
      partitions: opportunity.partitions.map((partition) => ({
        ...partition,
        candidate_scores: { "23:59": 1, "00:00": 0 },
      })),
    }],
  });
  assert.deepEqual(parsed.packet.currentRange, { startTime: "23:59", endTime: "00:00" });
});

test("dynamic scores reject model-controlled gates and all nested extra fields", () => {
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore, confidence: "high", can_apply: true, effective_answer_count: 1,
  }));
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore,
    winning_segment: { ...apiScore.winning_segment, model_controlled: "accepted" },
  }));
});

test("dynamic scores require exact counts, mode, empty evidence, and v2", () => {
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
    ...apiScore, algorithm_version: "birth-time-event-scoring-v1",
  }));
});

test("dynamic scores map independent engine values into guarded candidates", () => {
  const parsed = parseDynamicChoiceScoring(apiScore);
  assert.equal(parsed.effectiveAnswerCount, 1);
  assert.equal(parsed.dimensionCount, 1);
  assert.equal(parsed.candidate.eventCount, 1);
  assert.equal(parsed.candidate.domainCount, 1);
  assert.equal(parsed.candidate.winningSegment?.representativeTime, "05:31");
  assert.deepEqual(parsed.candidate.evidence, []);
  assert.equal(parsed.candidate.algorithmVersion, "birth-time-choice-scoring-v2");
});
