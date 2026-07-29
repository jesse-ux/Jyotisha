import { createHash, randomUUID } from "node:crypto";
import type { RectificationV4CandidateEngine } from "../rectification-v4/candidate-engine.ts";
import { buildCandidateClusters } from "../rectification-v4/candidate-clusters.ts";
import type { CandidateSnapshot, RectificationV4Question } from "../rectification-v4/contracts.ts";
import { evaluateDecisionGate } from "../rectification-v4/decision-gate.ts";
import { reconcileV4Evidence } from "../rectification-v4/extraction.ts";
import { extractEventWithModel } from "./event-extractor-agent.ts";
import { evidenceSetHash } from "../rectification-v4/fingerprints.ts";
import { latestEventRevisions, scoreableEvents } from "../rectification-v4/evidence-ledger.ts";
import { projectLegacyV4Turn } from "../rectification-v4/legacy-projector.ts";
import type { ClaimedRectificationV4Job } from "../rectification-v4/store.ts";
import { deterministicDecision } from "./fallback-policy.ts";
import { buildQuestionOpportunities } from "./opportunity-builder.ts";
import { renderPublicTurn } from "./renderer-agent.ts";
import { runBoundedReasoner } from "./reasoner-agent.ts";
import { recordRectificationAgentTelemetry } from "./telemetry.ts";
import {
  candidateFeatureSnapshotSchema,
  diagnosticsSummarySchema,
  validateRectificationDecision,
  type AgentRun,
  type CandidateFeatureSnapshot,
  type DiagnosticsSummary,
  type PublicMessage,
  type ValidatedDecision,
} from "./contracts.ts";

function hash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

export async function processRectificationAgentTurn(input: Readonly<{
  claimed: ClaimedRectificationV4Job;
  engine: RectificationV4CandidateEngine;
  now: Date;
  onPhase?: (phase: "extracting_evidence" | "scoring_candidates" | "checking_robustness" | "planning_question" | "reasoning" | "rendering") => Promise<void>;
}>): Promise<Readonly<{
  newEventRevisions: ClaimedRectificationV4Job["events"];
  pendingEvidence: import("../rectification-v4/contracts.ts").PendingEvidence[];
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
  featureSnapshot: CandidateFeatureSnapshot | null;
  validatedDecision: ValidatedDecision;
  publicMessage: PublicMessage;
  nextQuestion: RectificationV4Question | null;
  agentRun: AgentRun;
  status: "awaiting_answer" | "range_ready" | "paused";
  phase: "collecting_evidence" | "complete";
}>> {
  const { claimed, now } = input;
  await input.onPhase?.("extracting_evidence");
  const asOfDate = now.toISOString().slice(0, 10);
  let reconciliation = claimed.turn.answer ? reconcileV4Evidence({
    caseId: claimed.case.id,
    answer: claimed.turn.answer,
    sourceTurnId: claimed.turn.id,
    asOfDate,
    existing: claimed.events,
    targetEventId: claimed.turn.questionTargetEventId,
    now,
  }) : { revisions: [], pending: [], unansweredTargetEventId: null, targetDisposition: "not_applicable" as const };
  const needsAssistance = claimed.case.deploymentMode !== "v4_legacy" && (
    reconciliation.pending.some((event) => event.reasonCode === "event_unparsed")
    || reconciliation.revisions.some((event) => event.scoreability === "pending_review" || event.scoreability === "unsupported")
  );
  if (needsAssistance) {
    const assisted = await extractEventWithModel({
      rawText: claimed.turn.answer,
      sourceTurnId: claimed.turn.id,
      asOfDate,
      modelId: claimed.case.orchestrationModelId,
    });
    if (assisted) reconciliation = reconcileV4Evidence({
      caseId: claimed.case.id,
      answer: claimed.turn.answer,
      sourceTurnId: claimed.turn.id,
      asOfDate,
      existing: claimed.events,
      targetEventId: claimed.turn.questionTargetEventId,
      assistedEvidence: [assisted],
      now,
    });
  }
  const extracted = reconciliation.revisions;
  const events = latestEventRevisions([...claimed.events, ...extracted]);
  const scoreable = scoreableEvents(events);
  const domains = new Set(scoreable.map((event) => event.domain));
  let snapshot: CandidateSnapshot | null = null;
  let diagnostics: DiagnosticsSummary | null = null;
  let featureSnapshot: CandidateFeatureSnapshot | null = null;

  if (scoreable.length >= 3 && domains.size >= 2) {
    await input.onPhase?.("scoring_candidates");
    const scored = await input.engine.score({ calculationSpec: claimed.case.calculationSpec, events: scoreable });
    await input.onPhase?.("checking_robustness");
    const clusters = buildCandidateClusters(scored.candidates);
    const robustness = {
      neighborSupportMinutes: scored.robustness.neighborSupportMinutes,
      leaveOneOutRetentionRate: scored.robustness.leaveOneOutRetentionRate,
      dateSensitivityRetentionRate: scored.robustness.dateSensitivityRetentionRate,
      calculationSpecHashMatched: scored.calculationSpecHash === claimed.case.calculationSpecHash,
    };
    const gate = evaluateDecisionGate({
      clusters,
      robustness,
      scoreableEventCount: scoreable.length,
      scoreableDomainCount: domains.size,
    });
    snapshot = {
      id: scored.resultId,
      caseId: claimed.case.id,
      caseVersion: claimed.case.version,
      evidenceSetHash: evidenceSetHash(events),
      calculationSpecHash: claimed.case.calculationSpecHash,
      algorithmVersion: scored.featureSnapshot.algorithm_version,
      candidates: [...scored.candidates],
      clusters: [...clusters],
      robustness,
      canConfirmExactMinute: false,
      canAcceptRange: gate.canAcceptRange,
      gateReasons: [...gate.reasons, ...scored.missingLayers.map((layer) => `missing_layer:${layer}`)],
      createdAt: now.toISOString(),
    };
    diagnostics = diagnosticsSummarySchema.parse({
      id: randomUUID(),
      caseId: claimed.case.id,
      snapshotId: snapshot.id,
      primaryClusterRetentionRate: scored.diagnostics.primary_cluster_retention_rate,
      leaveOneEventOutRetentionRate: scored.diagnostics.leave_one_event_out_retention_rate,
      leaveOneDomainOutRetentionRate: scored.diagnostics.leave_one_domain_out_retention_rate,
      dateSensitivityRetentionRate: scored.diagnostics.date_sensitivity_retention_rate,
      neighborSupportMinutes: scored.diagnostics.neighbor_support_minutes,
      primarySecondaryMarginPercent: scored.diagnostics.primary_secondary_margin_percent,
      clusterMassRatio: scored.diagnostics.cluster_mass_ratio,
      unstableEventIds: scored.diagnostics.unstable_event_ids,
      mostDiscriminatingLayers: scored.diagnostics.most_discriminating_layers,
      eventDateSensitivity: scored.diagnostics.event_date_sensitivity.map((item) => ({
        eventId: item.event_id,
        declaredDateRange: item.declared_date_range,
        sampleDates: item.sample_dates,
        winnerRetentionRate: item.winner_retention_rate,
        scoreVariance: item.score_variance,
        candidateClusterRetentionRate: item.candidate_cluster_retention_rate,
      })),
      candidateSplits: scored.diagnostics.candidate_splits.map((item) => ({
        leftCluster: item.left_cluster,
        rightCluster: item.right_cluster,
        techniqueLayers: item.technique_layers,
        eventIds: item.event_ids,
      })),
      calculationHash: hash(scored.diagnostics),
      createdAt: now.toISOString(),
    });
    featureSnapshot = candidateFeatureSnapshotSchema.parse({
      id: randomUUID(),
      caseId: claimed.case.id,
      calculationSpecHash: scored.featureSnapshot.calculation_spec_hash,
      algorithmVersion: scored.featureSnapshot.algorithm_version,
      candidateCount: scored.featureSnapshot.candidate_count,
      featureHash: scored.featureSnapshot.feature_hash,
      features: scored.featureSnapshot.features.map((item) => ({
        time: item.time,
        ascendantDegree: item.ascendant_degree,
        ascendantSignIndex: item.ascendant_sign_index,
        vargaAscendants: item.varga_ascendants,
        arudhaSigns: item.arudha_signs,
        availableLayers: item.available_layers,
        blockedLayers: item.blocked_layers,
        fingerprints: item.fingerprints,
      })),
      createdAt: now.toISOString(),
    });
  }

  const safeDiagnostics = diagnostics ?? diagnosticsSummarySchema.parse({
    id: randomUUID(),
    caseId: claimed.case.id,
    snapshotId: randomUUID(),
    primaryClusterRetentionRate: 0,
    leaveOneEventOutRetentionRate: 0,
    leaveOneDomainOutRetentionRate: 0,
    dateSensitivityRetentionRate: 0,
    neighborSupportMinutes: 0,
    primarySecondaryMarginPercent: 0,
    clusterMassRatio: 0,
    unstableEventIds: [],
    mostDiscriminatingLayers: [],
    eventDateSensitivity: [],
    candidateSplits: [],
    calculationHash: hash(events),
    createdAt: now.toISOString(),
  });

  await input.onPhase?.("planning_question");
  const opportunities = buildQuestionOpportunities({
    caseId: claimed.case.id,
    events,
    turns: claimed.turns,
    snapshot,
    diagnostics,
    targetDisposition: reconciliation.targetDisposition,
    retryTargetEventIds: reconciliation.unansweredTargetEventId ? [reconciliation.unansweredTargetEventId] : [],
  });
  await input.onPhase?.("reasoning");
  const reasoned = await runBoundedReasoner({
    caseValue: claimed.case,
    snapshot,
    diagnostics: safeDiagnostics,
    opportunities,
    recentTurns: claimed.turns,
    recentEvents: events,
    currentTarget: claimed.turn.questionTargetEventId
      ? events.find((event) => event.eventId === claimed.turn.questionTargetEventId) ?? null
      : null,
    targetDisposition: reconciliation.targetDisposition,
    pendingEvidence: reconciliation.pending,
    candidateRangeChanged: claimed.case.latestSnapshot?.clusters[0]?.startTime !== snapshot?.clusters[0]?.startTime
      || claimed.case.latestSnapshot?.clusters[0]?.endTime !== snapshot?.clusters[0]?.endTime,
    enabled: claimed.case.deploymentMode !== "v4_legacy",
  });
  const rawDecision = reasoned.decision;
  let validation = validateRectificationDecision({
    decision: rawDecision,
    caseId: claimed.case.id,
    snapshotId: snapshot?.id ?? null,
    opportunities,
    diagnostics: safeDiagnostics,
    candidateRangeOfferAllowed: snapshot?.canAcceptRange ?? false,
    toolCallCount: reasoned.toolCalls.length,
    maxToolCalls: 1,
  });
  let fallbackReason = reasoned.fallbackReason;
  if (!validation.decision) {
    recordRectificationAgentTelemetry({
      caseId: claimed.case.id, phase: "fallback", outcome: "rejected",
      modelId: claimed.case.orchestrationModelId, toolName: null,
      decisionAction: rawDecision.action, durationMs: reasoned.latencyMs,
      errorCode: "policy_validator_rejected", deploymentSha: process.env.DEPLOYMENT_SHA?.trim() || null,
    });
    validation = validateRectificationDecision({
      decision: deterministicDecision({ snapshot, diagnostics, opportunities }),
      caseId: claimed.case.id,
      snapshotId: snapshot?.id ?? null,
      opportunities,
      diagnostics: safeDiagnostics,
      candidateRangeOfferAllowed: snapshot?.canAcceptRange ?? false,
    });
    fallbackReason = `validator_rejected:${validation.issues.join(",") || "unknown"}`;
  }
  const finalDecision = validation.decision;
  if (!finalDecision) throw new Error("rectification_v5_fallback_validation_failed");
  const selectedOpportunity = finalDecision.action === "ask_question"
    ? opportunities.find((item) => item.opportunityId === finalDecision.opportunityId) ?? null
    : null;
  const validatedDecision: ValidatedDecision = {
    decision: finalDecision,
    mode: fallbackReason ? "deterministic_fallback" : reasoned.mode,
    validationIssues: [...validation.issues],
    selectedOpportunity,
  };

  await input.onPhase?.("rendering");
  const legacyProjection = projectLegacyV4Turn({
    events,
    newEvents: extracted,
    attemptedRefinementEventIds: claimed.attemptedRefinementEventIds,
    latestAnswer: claimed.turn.answer,
    snapshot,
  });
  const agentVisible = claimed.case.deploymentMode === "v5_agent";
  const publicMessage = agentVisible
    ? await renderPublicTurn({
      caseValue: claimed.case,
      latestAnswer: claimed.turn.answer,
      acceptedEvents: extracted,
      pendingEvidence: reconciliation.pending,
      snapshot,
      previousSnapshot: claimed.case.latestSnapshot,
      validated: validatedDecision,
    })
    : legacyProjection.publicMessage;
  const nextQuestion = agentVisible && selectedOpportunity ? {
    id: randomUUID(),
    domain: selectedOpportunity.domain,
    targetEventId: selectedOpportunity.targetEventId,
    prompt: publicMessage.question ?? selectedOpportunity.fallbackPrompt,
    recallCost: selectedOpportunity.privacyCost >= .2
      ? "high" as const
      : selectedOpportunity.recallEase < .6
        ? "medium" as const
        : "low" as const,
    reason: selectedOpportunity.reason,
  } : agentVisible ? null : legacyProjection.nextQuestion;
  const status = agentVisible
    ? finalDecision.action === "offer_candidate_range"
      ? "range_ready" as const
      : finalDecision.action === "stop_low_confidence"
        ? "paused" as const
        : "awaiting_answer" as const
    : legacyProjection.status;
  const phase = agentVisible
    ? status === "awaiting_answer" ? "collecting_evidence" as const : "complete" as const
    : legacyProjection.phase;

  const agentRun: AgentRun = {
    id: randomUUID(),
    caseId: claimed.case.id,
    jobId: claimed.job.id,
    caseVersion: claimed.case.version,
    modelId: claimed.case.orchestrationModelId,
    skillVersion: claimed.case.skillVersion,
    promptVersion: claimed.case.promptVersion,
    deploymentMode: claimed.case.deploymentMode,
    deploymentSha: process.env.DEPLOYMENT_SHA?.trim() || null,
    decision: rawDecision,
    validatedDecision,
    toolCalls: [...reasoned.toolCalls],
    fallbackReason,
    inputTokenCount: reasoned.inputTokenCount,
    outputTokenCount: reasoned.outputTokenCount,
    latencyMs: reasoned.latencyMs,
    createdAt: now.toISOString(),
  };
  return {
    newEventRevisions: extracted,
    pendingEvidence: [...reconciliation.pending],
    snapshot,
    diagnostics,
    featureSnapshot,
    validatedDecision,
    publicMessage,
    nextQuestion,
    agentRun,
    status,
    phase,
  };
}
