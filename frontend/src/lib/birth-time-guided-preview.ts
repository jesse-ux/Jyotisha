import { parseJourneyResponse } from "./birth-time-journey-client.ts";
import type { JourneyClientResponse } from "./birth-time-journey-client.ts";
import { dynamicBirthTimePreview } from "./birth-time-dynamic-preview.ts";

const caseId = "7299894c-10a8-4b45-91d1-339007282c50";
const resultId = "345087cc-7e7f-4b37-90e5-f0c0a6e5b7a7";
const jobId = "5da741ba-4713-4c27-9cf4-a85e52dc4658";
const draftId = "1c10e4d8-d70b-43c2-9766-14c152f37593";

const question = {
  questionId: "education_entry",
  phase: "baseline",
  domain: "education",
  requestedPrecision: ["year"],
  allowUnknown: true,
  purposeCode: "baseline_education",
  plannerVersion: "birth-time-question-planner-v1",
};

const candidate = {
  resultId,
  confidence: "medium",
  canApply: false,
  winningSegment: {
    startTime: "05:18",
    endTime: "05:24",
    representativeTime: "05:21",
    widthMinutes: 7,
  },
  eventCount: 4,
  domainCount: 3,
  topScore: 14.4,
  secondScore: 12.1,
  marginPercent: 15.97,
  reasons: [],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
};

function response(overrides: Readonly<Record<string, unknown>> = {}): JourneyClientResponse {
  return parseJourneyResponse({
    caseId,
    snapshot: {
      state: "rectifying",
      assistantIntent: "start_standard_rectification",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: null,
    scoring: null,
    answers: {},
    lifeEvents: [],
    candidateResult: null,
    turnVersion: 1,
    nextAction: { kind: "ask_baseline_evidence", question },
    progress: {
      phase: "baseline",
      baselineDomainCount: 0,
      confirmedEvidenceCount: 0,
      adaptiveRound: 0,
      maxAdaptiveRounds: 3,
    },
    permissions: { canConfirmCandidate: false },
    evidenceDraft: null,
    ...overrides,
  });
}

const modes = new Set([
  "birth-time-rectification",
  "birth-time-rectification-candidate",
  "birth-time-rectification-events",
  "birth-time-rectification-result",
  "birth-time-rectification-confirmation",
  "birth-time-rectification-draft",
  "birth-time-rectification-score-pending",
  "birth-time-rectification-retry",
  "birth-time-rectification-adaptive",
  "birth-time-rectification-low",
  "birth-time-rectification-saved",
  "birth-time-rectification-ready",
]);

export function isGuidedBirthTimePreview(mode: string): boolean {
  return modes.has(mode);
}

export function guidedBirthTimePreview(mode: string): JourneyClientResponse {
  if (mode === "birth-time-rectification") return dynamicBirthTimePreview();
  if (mode === "birth-time-rectification-draft" || mode === "birth-time-rectification-events") {
    return response({
      snapshot: { ...response().snapshot, input: "life_events", assistantIntent: "collect_dated_life_events" },
      turnVersion: 2,
      nextAction: { kind: "review_evidence_draft", draftId },
      progress: { ...response().progress, phase: "review" },
      evidenceDraft: {
        draftId,
        questionId: question.questionId,
        domain: "education",
        precision: "year",
        date: "2008",
        status: "draft",
        needsReview: false,
      },
    });
  }
  if (mode === "birth-time-rectification-score-pending" || mode === "birth-time-rectification-candidate") {
    return response({
      turnVersion: 3,
      nextAction: { kind: "score_pending", jobId },
      progress: { ...response().progress, phase: "scoring", baselineDomainCount: 3, confirmedEvidenceCount: 3 },
    });
  }
  if (mode === "birth-time-rectification-retry") {
    return response({
      turnVersion: 4,
      nextAction: { kind: "retry_scoring", jobId },
      progress: { ...response().progress, phase: "scoring", baselineDomainCount: 3, confirmedEvidenceCount: 3 },
    });
  }
  if (mode === "birth-time-rectification-adaptive") {
    return response({
      snapshot: { ...response().snapshot, confidence: "low" },
      candidateResult: { ...candidate, confidence: "low", canApply: false },
      turnVersion: 5,
      nextAction: {
        kind: "ask_adaptive_evidence",
        question: {
          ...question,
          questionId: "relationship_entry",
          phase: "adaptive",
          domain: "relationship",
          purposeCode: "adaptive_relationship",
        },
      },
      progress: { ...response().progress, phase: "adaptive", baselineDomainCount: 3, confirmedEvidenceCount: 3, adaptiveRound: 1 },
    });
  }
  if (mode === "birth-time-rectification-low") {
    return response({
      snapshot: { ...response().snapshot, state: "candidate", input: "candidate_actions", confidence: "low", assistantIntent: "explain_event_evidence_insufficient" },
      candidateResult: { ...candidate, confidence: "low", canApply: false },
      turnVersion: 6,
      nextAction: { kind: "present_low_result", resultId },
      progress: { ...response().progress, phase: "result", baselineDomainCount: 3, confirmedEvidenceCount: 4, adaptiveRound: 3 },
    });
  }
  const candidateSnapshot = {
    ...response().snapshot,
    state: "candidate",
    assistantIntent: "present_candidate_result",
    input: "candidate_actions",
    confidence: "medium",
  };
  const resultTurn = {
    snapshot: candidateSnapshot,
    candidateResult: candidate,
    turnVersion: 5,
    nextAction: { kind: "present_medium_result", resultId },
    progress: { ...response().progress, phase: "result", baselineDomainCount: 3, confirmedEvidenceCount: 4 },
  };
  if (mode === "birth-time-rectification-result") return response(resultTurn);
  if (mode === "birth-time-rectification-saved") {
    return response({ ...resultTurn, turnVersion: 6, nextAction: { kind: "candidate_saved", resultId } });
  }
  if (mode === "birth-time-rectification-confirmation") {
    const high = {
      ...candidate,
      confidence: "high",
      canApply: true,
      winningSegment: { ...candidate.winningSegment, widthMinutes: 5 },
      marginPercent: 24,
    };
    return response({
      ...resultTurn,
      snapshot: { ...candidateSnapshot, state: "confirming", input: "candidate_confirmation", confidence: "high", canApply: true, assistantIntent: "confirm_candidate_time" },
      candidateResult: high,
      nextAction: { kind: "request_candidate_confirmation", resultId },
      permissions: { canConfirmCandidate: true },
    });
  }
  if (mode === "birth-time-rectification-ready") {
    const high = {
      ...candidate,
      confidence: "high",
      canApply: true,
      winningSegment: { ...candidate.winningSegment, widthMinutes: 5 },
      marginPercent: 24,
    };
    return response({
      ...resultTurn,
      snapshot: { ...candidateSnapshot, state: "ready", input: "none", route: "direct_chart", confidence: "high", activeTime: "05:21", assistantIntent: "confirmed_candidate_time" },
      candidateResult: high,
      nextAction: { kind: "ready", activeTime: "05:21" },
      progress: { ...response().progress, phase: "ready", baselineDomainCount: 3, confirmedEvidenceCount: 4 },
    });
  }
  return response();
}

export const previewRectificationJourney = guidedBirthTimePreview("birth-time-rectification");
