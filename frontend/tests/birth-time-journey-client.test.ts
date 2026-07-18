import assert from "node:assert/strict";
import test from "node:test";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";
import {
  highConfirmationTurn,
  snapshot,
} from "./birth-time-journey-client-test-support.ts";

test("journey client parses the sanitized API response", () => {
  const parsed = parseJourneyResponse({
    caseId: highConfirmationTurn.caseId,
    snapshot,
    questionnaire: {
      questions: [{
        id: "education_environment_shift",
        prompt: "是否有明显学业变化？",
        options: [{ key: "A", label: "明确有" }],
      }],
      samples: [],
      raw: {},
    },
    scoring: null,
  });

  assert.equal(parsed.snapshot.route, "rectification");
  assert.equal(parsed.questionnaire?.questions[0]?.id, "education_environment_shift");
});

test("journey client preserves deterministic next rectification questions", () => {
  const parsed = parseJourneyResponse({
    caseId: highConfirmationTurn.caseId,
    snapshot: {
      ...snapshot,
      state: "candidate",
      assistantIntent: "present_saved_candidate_range",
    },
    questionnaire: {
      questions: [
        { id: "education_environment_shift", prompt: "是否有明显学业变化？" },
        { id: "residence_relocation_shift", prompt: "是否有明显居住变化？" },
        { id: "relationship_or_partner_entry", prompt: "是否有明显关系变化？" },
      ],
      samples: [],
      raw: {},
    },
    scoring: {
      answeredCount: 3,
      candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
      nextRound: 2,
      nextRoundQuestions: [{
        id: "health_crisis_or_low_period",
        prompt: "是否有明显健康或低谷阶段？",
        options: [{ key: "A", label: "明确有" }],
      }],
      raw: {},
    },
    answers: {
      education_environment_shift: "A",
      residence_relocation_shift: "A",
      relationship_or_partner_entry: "B",
    },
  });

  assert.equal(parsed.scoring?.nextRound, 2);
  assert.equal(
    parsed.scoring?.nextRoundQuestions[0]?.id,
    "health_crisis_or_low_period",
  );
});

test("journey client rejects an applied rectification result", () => {
  assert.throws(() => parseJourneyResponse({
    caseId: highConfirmationTurn.caseId,
    snapshot: { ...snapshot, canApply: true, activeTime: "14:24" },
    questionnaire: null,
    scoring: null,
  }));
});

test("journey client accepts only a guarded high-confidence confirmation", () => {
  const parsed = parseJourneyResponse({
    ...highConfirmationTurn,
    turnVersion: undefined,
  });

  assert.equal(parsed.snapshot.state, "confirming");
  assert.equal(
    parsed.candidateResult?.winningSegment?.representativeTime,
    "14:24",
  );
  assert.throws(() => parseJourneyResponse({
    ...parsed,
    turnVersion: undefined,
    snapshot: { ...parsed.snapshot, state: "candidate", input: "candidate_actions" },
  }));
});

test("client rejects a nonterminal turn without nextAction", () => {
  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    nextAction: undefined,
  }));
});

test("client derives Agent permission without exposing legacy canApply", () => {
  const parsed = parseJourneyResponse(highConfirmationTurn);

  assert.equal(parsed.permissions.canConfirmCandidate, true);
  assert.equal("canApply" in parsed.permissions, false);
});

test("versioned client responses require every response field", () => {
  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    answers: undefined,
  }));
});

test("client preserves every candidate varga sign", () => {
  const sample = {
    ascendantSign: "Aries",
    d4Sign: "Taurus",
    d9Sign: "Gemini",
    d10Sign: "Cancer",
    d24Sign: "Leo",
    d30Sign: "Virgo",
  };
  const parsed = parseJourneyResponse({
    ...highConfirmationTurn,
    questionnaire: { questions: [], samples: [sample], raw: {} },
  });

  assert.deepEqual(parsed.questionnaire?.samples[0], sample);
});

test("versioned response parsing returns a readonly public boundary", () => {
  const parsed = parseJourneyResponse(highConfirmationTurn);

  assert.equal(Object.isFrozen(parsed), true);
  assert.equal(Object.isFrozen(parsed.candidateResult), true);
});
