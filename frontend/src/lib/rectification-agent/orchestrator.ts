import { createHash, randomUUID } from "node:crypto";
import type { CandidateEngineResult, RectificationV4CandidateEngine } from "../rectification-v4/candidate-engine.ts";
import { buildCandidateClusters } from "../rectification-v4/candidate-clusters.ts";
import type { CandidateSnapshot, RectificationAnalysisTrace, RectificationV4Question } from "../rectification-v4/contracts.ts";
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
  vedAstroPostValidationSchema,
  validateRectificationDecision,
  type AgentRun,
  type CandidateFeatureSnapshot,
  type DiagnosticsSummary,
  type StoredPublicMessage,
  type ValidatedDecision,
  type VedAstroPostValidation,
} from "./contracts.ts";

function hash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function vedAstroCandidateTimes(snapshot: CandidateSnapshot): readonly [string, string] | null {
  const primary = snapshot.clusters[0]?.representativeTime;
  if (!primary) return null;
  const runnerUp = snapshot.clusters[1]?.representativeTime
    ?? [...snapshot.candidates].sort((left, right) => right.score - left.score).find((candidate) => candidate.time !== primary)?.time;
  return runnerUp && runnerUp !== primary ? [primary, runnerUp] : null;
}

function blockedVedAstroValidation(now: Date, blocker: string, candidateTimes: readonly [string, string] | null): VedAstroPostValidation {
  const safe = {
    contractVersion: "vedastro-post-validation-v1" as const,
    provider: "vedastro_official" as const,
    status: "blocked" as const,
    providerStatus: "unavailable",
    blockers: [blocker],
    primaryCandidateTime: candidateTimes?.[0] ?? null,
    runnerUpCandidateTime: candidateTimes?.[1] ?? null,
    eligibleEventCount: 0,
    selectedEventCount: 0,
    unsupportedEventCount: 0,
    candidateMetrics: [],
    minuteSensitiveValidation: { comparisonReady: false, discriminated: false, discriminatedLayers: [] },
    canConfirmExactMinute: false as const,
  };
  return vedAstroPostValidationSchema.parse({
    ...safe,
    validationHash: hash(safe),
    validatedAt: now.toISOString(),
  });
}

const analysisPhaseLabels = {
  extracting_evidence: "整理用户经历",
  scoring_candidates: "扫描候选分钟",
  checking_robustness: "检查候选稳定性",
  planning_question: "生成语义问题机会",
  reasoning: "选择下一步动作",
  rendering: "生成安全回复",
} as const;

const diagnosticLabels = {
  leave_one_event_out: "留一事件稳定性",
  leave_one_domain_out: "留一领域稳定性",
  date_sensitivity: "日期敏感性",
  neighbor_stability: "相邻分钟稳定性",
  candidate_split: "候选分裂诊断",
} as const;

type AnalysisPhase = keyof typeof analysisPhaseLabels;

export function publicRectificationTechniques(result: CandidateEngineResult | null): string[] {
  if (!result) return [];
  const techniques = new Set<string>();
  const add = (value: string) => {
    const normalized = value.toLocaleLowerCase();
    if (normalized.includes("vim")) techniques.add("Vimshottari Dasha");
    if (normalized.includes("narayana")) techniques.add("Narayana Dasha");
    if (normalized.includes("controlled_transit")) techniques.add("木星/土星受控行运");
    if (normalized.includes("ashtakavarga")) techniques.add("Ashtakavarga");
    if (normalized.includes("shadbala")) techniques.add("Shadbala 已验证分量");
    for (const layer of ["D2", "D4", "D9", "D10", "D11", "D24", "D30"] as const) {
      if (new RegExp(`(?:^|[^0-9])${layer}(?:$|[^0-9])`, "i").test(value)) techniques.add(layer);
    }
  };
  for (const candidate of Object.values(result.contributionMatrix)) {
    for (const contribution of Object.values(candidate)) {
      contribution.rule_ids.forEach(add);
      contribution.technique_layers.forEach(add);
    }
  }
  return [...techniques];
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
  publicMessage: StoredPublicMessage;
  nextQuestion: RectificationV4Question | null;
  agentRun: AgentRun;
  status: "awaiting_answer" | "range_ready" | "paused";
  phase: "collecting_evidence" | "complete";
}>> {
  const { claimed, now } = input;
  const stages: RectificationAnalysisTrace["stages"] = [];
  let activePhase: AnalysisPhase | null = null;
  let activePhaseStarted = 0;
  const finishPhase = (status: "completed" | "failed" = "completed") => {
    if (!activePhase) return;
    stages.push({
      phase: activePhase,
      label: analysisPhaseLabels[activePhase],
      status,
      durationMs: Math.max(0, Date.now() - activePhaseStarted),
    });
    activePhase = null;
  };
  const enterPhase = async (phase: AnalysisPhase) => {
    finishPhase();
    activePhase = phase;
    activePhaseStarted = Date.now();
    await input.onPhase?.(phase);
  };
  await enterPhase("extracting_evidence");
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
  let engineResult: CandidateEngineResult | null = null;
  const analysisToolCalls: RectificationAnalysisTrace["toolCalls"] = [];

  if (scoreable.length >= 3 && domains.size >= 2) {
    await enterPhase("scoring_candidates");
    const engineStarted = Date.now();
    const scored = await input.engine.score({ calculationSpec: claimed.case.calculationSpec, events: scoreable });
    engineResult = scored;
    analysisToolCalls.push({ category: "candidate_engine", label: "候选分钟扫描与稳定性诊断", outcome: "succeeded", durationMs: Date.now() - engineStarted });
    await enterPhase("checking_robustness");
    const clusters = buildCandidateClusters(scored.candidates);
    const robustness = {
      neighborSupportMinutes: scored.robustness.neighborSupportMinutes,
      leaveOneOutRetentionRate: scored.robustness.leaveOneOutRetentionRate,
      leaveOneDomainOutRetentionRate: scored.robustness.leaveOneDomainOutRetentionRate,
      dateSensitivityRetentionRate: scored.robustness.dateSensitivityRetentionRate,
      calculationSpecHashMatched: scored.calculationSpecHash === claimed.case.calculationSpecHash,
    };
    const gate = evaluateDecisionGate({
      clusters,
      robustness,
      scoreableEventCount: scoreable.length,
      scoreableDomains: [...domains],
      missingTechniqueLayers: scored.missingLayers,
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
      gateReasons: [...gate.reasons],
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

  if (snapshot?.canAcceptRange && diagnostics && claimed.case.deploymentMode === "v5_agent") {
    const candidateTimes = vedAstroCandidateTimes(snapshot);
    const validationStarted = Date.now();
    let externalValidation: VedAstroPostValidation;
    let outcome: "succeeded" | "failed" | "rejected";
    if (!candidateTimes) {
      externalValidation = blockedVedAstroValidation(now, "vedastro_runner_up_candidate_missing", null);
      outcome = "rejected";
    } else if (!input.engine.validateWithVedAstro) {
      externalValidation = blockedVedAstroValidation(now, "vedastro_validator_unavailable", candidateTimes);
      outcome = "failed";
    } else {
      try {
        externalValidation = await input.engine.validateWithVedAstro({
          calculationSpec: claimed.case.calculationSpec,
          events: scoreable,
          candidateTimes,
        });
        outcome = externalValidation.status === "pass" ? "succeeded" : "rejected";
      } catch {
        externalValidation = blockedVedAstroValidation(now, "vedastro_validation_failed", candidateTimes);
        outcome = "failed";
      }
    }
    diagnostics = diagnosticsSummarySchema.parse({ ...diagnostics, externalValidation });
    analysisToolCalls.push({
      category: "diagnostic",
      label: "VedAstro 事后校验",
      outcome,
      durationMs: Date.now() - validationStarted,
    });
    if (externalValidation.status !== "pass") {
      snapshot = {
        ...snapshot,
        canAcceptRange: false,
        gateReasons: [...new Set([
          ...snapshot.gateReasons,
          "vedastro_validation_not_passed",
          ...externalValidation.blockers,
        ])].slice(0, 20),
      };
    }
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

  await enterPhase("planning_question");
  const opportunities = buildQuestionOpportunities({
    caseId: claimed.case.id,
    events,
    turns: claimed.turns,
    snapshot,
    diagnostics,
    targetDisposition: reconciliation.targetDisposition,
    retryTargetEventIds: reconciliation.unansweredTargetEventId ? [reconciliation.unansweredTargetEventId] : [],
  });
  await enterPhase("reasoning");
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

  await enterPhase("rendering");
  const legacyProjection = projectLegacyV4Turn({
    events,
    newEvents: extracted,
    attemptedRefinementEventIds: claimed.attemptedRefinementEventIds,
    latestAnswer: claimed.turn.answer,
    snapshot,
  });
  const agentVisible = claimed.case.deploymentMode === "v5_agent";
  let rendererRealization: "model_validated" | "server_fallback" | null = null;
  let rendererFallbackReason: "model_unavailable" | "question_rejected" | "model_failed" | null = null;
  const renderedMessage = agentVisible
    ? await renderPublicTurn({
      caseValue: claimed.case,
      latestAnswer: claimed.turn.answer,
      acceptedEvents: extracted,
      pendingEvidence: reconciliation.pending,
      snapshot,
      previousSnapshot: claimed.case.latestSnapshot,
      validated: validatedDecision,
      onRealization: (outcome) => {
        rendererRealization = outcome.mode;
        rendererFallbackReason = outcome.reason;
      },
    })
    : legacyProjection.publicMessage;
  finishPhase();
  if (agentVisible && rendererRealization) {
    stages.push({
      phase: "rendering",
      label: rendererRealization === "model_validated"
        ? "自然语言问题已通过安全校验"
        : rendererFallbackReason === "question_rejected"
          ? "模型问题未通过安全校验，已使用服务器安全问题"
          : "模型回复不可用，已使用服务器安全问题",
      status: "completed",
      durationMs: null,
    });
  }
  for (const call of reasoned.toolCalls) {
    analysisToolCalls.push({
      category: "agent_diagnostic",
      label: call.diagnostic ? diagnosticLabels[call.diagnostic] : "只读诊断",
      outcome: call.outcome,
      durationMs: call.durationMs,
    });
  }
  const reasoningSummary = reasoned.mode === "agent" && !fallbackReason ? reasoned.reasoningSummary : null;
  const analysisTrace: RectificationAnalysisTrace = {
    status: claimed.case.deploymentMode === "v4_legacy" ? "legacy" : "completed",
    stages,
    toolCalls: analysisToolCalls,
    techniques: publicRectificationTechniques(engineResult),
    reasoningSummary,
    reasoningSource: reasoningSummary ? "provider_summary" : "none",
  };
  const publicMessage: StoredPublicMessage = { ...renderedMessage, analysisTrace };
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
