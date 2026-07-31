import { createHash, randomUUID } from "node:crypto";
import type { CandidateEngineResult, RectificationV4CandidateEngine } from "../rectification-v4/candidate-engine.ts";
import { buildCandidateClusters } from "../rectification-v4/candidate-clusters.ts";
import type { CandidateSnapshot, RectificationAnalysisTrace, RectificationV4Question } from "../rectification-v4/contracts.ts";
import { evaluateDecisionGate } from "../rectification-v4/decision-gate.ts";
import { reconcileV4Evidence, stageAgentEvidenceProposals, type ReconciledV4Evidence, type TargetDisposition } from "../rectification-v4/extraction.ts";
import { buildRectificationCaseDossier, runRectificationDirector, type RectificationDirectorGenerator } from "./director-agent.ts";
import { candidateUpdateFor } from "./renderer-agent.ts";
import { extractEventWithModel } from "./event-extractor-agent.ts";
import { evidenceSetHash } from "../rectification-v4/fingerprints.ts";
import { latestEventRevisions, scoreableEvents } from "../rectification-v4/evidence-ledger.ts";
import { projectLegacyV4Turn } from "../rectification-v4/legacy-projector.ts";
import type { ClaimedRectificationV4Job } from "../rectification-v4/store.ts";
import { deterministicDecision } from "./fallback-policy.ts";
import { buildQuestionOpportunities } from "./opportunity-builder.ts";
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
  extracting_evidence: "整理并验证事件提议",
  scoring_candidates: "重算候选评分",
  checking_robustness: "验证候选稳定性",
  planning_question: "准备 Director 完整档案",
  reasoning: "Director 选择访谈焦点",
  rendering: "验证并保存公开回复",
} as const;

const diagnosticLabels = {
  leave_one_event_out: "留一事件稳定性",
  leave_one_domain_out: "留一领域稳定性",
  date_sensitivity: "日期敏感性",
  neighbor_stability: "相邻分钟稳定性",
  candidate_split: "候选分裂诊断",
} as const;

type AnalysisPhase = keyof typeof analysisPhaseLabels;

const closedTargetDispositions = new Set<TargetDisposition>(["unknown", "declined", "direction_change"]);

export function composeRectificationPublicTurn(message: Pick<StoredPublicMessage, "acknowledgement" | "evidenceExplanation" | "candidateUpdate" | "limitation" | "question">): string {
  const question = message.question?.trim() ?? "";
  const context = [message.acknowledgement, message.evidenceExplanation, message.candidateUpdate, message.limitation].filter((part): part is string => Boolean(part?.trim())).join("\n\n");
  if (!question) return context.slice(0, 1_000);
  const availableContext = Math.max(0, 1_000 - question.length - 2);
  const prefix = context.slice(0, availableContext).trim();
  return prefix ? `${prefix}\n\n${question}` : question;
}

export function mergeDirectorReconciliation(input: Readonly<{
  server: ReconciledV4Evidence;
  staged: ReconciledV4Evidence;
  proposedDisposition: TargetDisposition;
  currentTargetEventId: string | null;
}>): ReconciledV4Evidence {
  if (closedTargetDispositions.has(input.server.targetDisposition)) {
    return { ...input.staged, pending: [], unansweredTargetEventId: null, targetDisposition: input.server.targetDisposition };
  }
  const revisedCurrentTarget = Boolean(input.currentTargetEventId && input.staged.revisions.some((event) => event.eventId === input.currentTargetEventId));
  const addedOtherEvent = input.staged.revisions.some((event) => event.eventId !== input.currentTargetEventId);
  const valid = input.proposedDisposition !== "resolved" && input.proposedDisposition !== "answered_other_event"
    || input.proposedDisposition === "resolved" && revisedCurrentTarget
    || input.proposedDisposition === "answered_other_event" && addedOtherEvent;
  return valid ? { ...input.staged, targetDisposition: input.proposedDisposition } : input.staged;
}

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
  generateDirectorPlan?: RectificationDirectorGenerator;
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
  const provisionalDisposition = claimed.turn.questionTargetEventId ? "unresolved" as const : "not_applicable" as const;
  const provisionalDiagnostics = diagnosticsSummarySchema.parse({
    id: randomUUID(), caseId: claimed.case.id, snapshotId: claimed.case.latestSnapshot?.id ?? randomUUID(),
    primaryClusterRetentionRate: 0, leaveOneEventOutRetentionRate: 0, leaveOneDomainOutRetentionRate: 0,
    dateSensitivityRetentionRate: 0, neighborSupportMinutes: 0, primarySecondaryMarginPercent: 0,
    clusterMassRatio: 0, unstableEventIds: [], mostDiscriminatingLayers: [], eventDateSensitivity: [],
    candidateSplits: [], calculationHash: hash(claimed.events), createdAt: now.toISOString(),
  });
  let evidenceDirector: Awaited<ReturnType<typeof runRectificationDirector>> | null = null;
  let reconciliation;
  if (claimed.case.deploymentMode !== "v4_legacy" && claimed.turn.answer) {
    const dossier = buildRectificationCaseDossier({
      caseValue: claimed.case, turns: claimed.turns, events: claimed.events, pendingEvidence: claimed.pendingEvidence, snapshot: claimed.case.latestSnapshot,
      previousSnapshot: claimed.case.latestSnapshot, diagnostics: null, targetDisposition: provisionalDisposition,
      currentTargetEventId: claimed.turn.questionTargetEventId,
    });
    evidenceDirector = await runRectificationDirector({
      caseValue: claimed.case, dossier, latestAnswer: claimed.turn.answer, phase: "evidence", diagnostics: provisionalDiagnostics, generatePlan: input.generateDirectorPlan,
    });
    const serverReconciliation = reconcileV4Evidence({ caseId: claimed.case.id, answer: claimed.turn.answer, sourceTurnId: claimed.turn.id, asOfDate, existing: claimed.events, targetEventId: claimed.turn.questionTargetEventId, now });
    reconciliation = claimed.case.deploymentMode === "v5_agent" && evidenceDirector.mode === "agent" && evidenceDirector.plan.evidenceProposals.length
      ? stageAgentEvidenceProposals({ caseId: claimed.case.id, rawText: claimed.turn.answer, sourceTurnId: claimed.turn.id, asOfDate, existing: claimed.events, proposals: evidenceDirector.plan.evidenceProposals, now })
      : serverReconciliation;
    if (claimed.case.deploymentMode === "v5_agent" && evidenceDirector.mode === "agent") {
      reconciliation = mergeDirectorReconciliation({
        server: serverReconciliation,
        staged: reconciliation,
        proposedDisposition: evidenceDirector.plan.targetDisposition,
        currentTargetEventId: claimed.turn.questionTargetEventId,
      });
    }
  } else {
    reconciliation = claimed.turn.answer ? reconcileV4Evidence({
      caseId: claimed.case.id, answer: claimed.turn.answer, sourceTurnId: claimed.turn.id, asOfDate,
      existing: claimed.events, targetEventId: claimed.turn.questionTargetEventId, now,
    }) : { revisions: [], pending: [], unansweredTargetEventId: null, targetDisposition: "not_applicable" as const };
  }
  const needsAssistance = claimed.case.deploymentMode === "v4_legacy" && (
    reconciliation.pending.some((event) => event.reasonCode === "event_unparsed")
    || reconciliation.revisions.some((event) => event.scoreability === "pending_review" || event.scoreability === "unsupported")
  );
  if (needsAssistance) {
    const assisted = await extractEventWithModel({ rawText: claimed.turn.answer, sourceTurnId: claimed.turn.id, asOfDate, modelId: claimed.case.orchestrationModelId });
    if (assisted) reconciliation = reconcileV4Evidence({ caseId: claimed.case.id, answer: claimed.turn.answer, sourceTurnId: claimed.turn.id, asOfDate, existing: claimed.events, targetEventId: claimed.turn.questionTargetEventId, assistedEvidence: [assisted], now });
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

  if (claimed.case.deploymentMode !== "v4_legacy") {
    await enterPhase("planning_question");
    const newlyCreatedBroadDateEvent = [...extracted].reverse().find((event) => event.revision === 1
      && event.scoreability === "scoreable"
      && (event.dateRange.precision === "year" || event.dateRange.precision === "quarter"));
    const planningTargetEventId = reconciliation.unansweredTargetEventId ?? newlyCreatedBroadDateEvent?.eventId ?? null;
    const planningTargetDisposition = planningTargetEventId && reconciliation.targetDisposition === "not_applicable"
      ? "unresolved" as const
      : reconciliation.targetDisposition;
    const dossier = buildRectificationCaseDossier({
      caseValue: claimed.case, turns: claimed.turns, events, pendingEvidence: [...claimed.pendingEvidence, ...reconciliation.pending],
      snapshot, previousSnapshot: claimed.case.latestSnapshot, diagnostics,
      targetDisposition: planningTargetDisposition, currentTargetEventId: planningTargetEventId,
    });
    await enterPhase("reasoning");
    const directed = await runRectificationDirector({
      caseValue: claimed.case, dossier, latestAnswer: claimed.turn.answer, phase: "final", diagnostics: safeDiagnostics, generatePlan: input.generateDirectorPlan,
    });
    const plan = directed.plan;
    const action = plan.action;
    if (action.type === "request_diagnostic" || action.type === "request_tool") {
      throw new Error("rectification_director_tool_loop_incomplete");
    }
    const decision = action.type === "ask_question"
      ? { action: "ask_question" as const, focus: action.focus, question: action.question }
      : action.type === "offer_candidate_range"
        ? { action: "offer_candidate_range" as const, snapshotId: action.snapshotId }
        : { action: "stop_low_confidence" as const, reasonCodes: action.reasonCodes };
    const validatedDecision: ValidatedDecision = {
      decision,
      mode: directed.mode,
      validationIssues: directed.fallbackReason ? [directed.fallbackReason] : [],
      selectedOpportunity: null,
    };
    await enterPhase("rendering");
    finishPhase();
    for (const call of directed.toolCalls) analysisToolCalls.push({
      category: "agent_diagnostic",
      label: call.diagnostic ? diagnosticLabels[call.diagnostic] : ({ case_read: "读取案件档案", candidate_scan: "读取候选扫描", evidence_gap: "检查证据缺口" } as Record<string, string>)[call.tool] ?? "只读诊断",
      outcome: call.outcome, durationMs: call.durationMs,
    });
    const publicMessage: StoredPublicMessage = {
      acknowledgement: plan.publicReply.acknowledgement,
      evidenceExplanation: plan.publicReply.evidenceExplanation,
      candidateUpdate: candidateUpdateFor({ snapshot, previousSnapshot: claimed.case.latestSnapshot, decisionAction: decision.action }),
      limitation: plan.publicReply.limitation,
      question: action.type === "ask_question" ? action.question : null,
      analysisTrace: {
        status: "completed", stages, toolCalls: analysisToolCalls, techniques: publicRectificationTechniques(engineResult),
        reasoningSummary: null, reasoningSource: "none",
      },
    };
    const targetEvent = action.type === "ask_question" && action.focus.targetEventId
      ? events.find((event) => event.eventId === action.focus.targetEventId) ?? null
      : null;
    const nextQuestion: RectificationV4Question | null = action.type === "ask_question" ? {
      id: randomUUID(),
      domain: action.focus.domain ?? targetEvent?.domain ?? "other",
      targetEventId: action.focus.targetEventId,
      prompt: composeRectificationPublicTurn(publicMessage),
      recallCost: "medium",
      reason: action.focus.rationaleCodes.join(",").slice(0, 240) || "agent_directed_focus",
    } : null;
    const status = action.type === "offer_candidate_range" ? "range_ready" as const
      : action.type === "stop_low_confidence" ? "paused" as const
        : "awaiting_answer" as const;
    const totalInput = [evidenceDirector?.inputTokenCount, directed.inputTokenCount].filter((value): value is number => value !== null && value !== undefined).reduce((sum, value) => sum + value, 0);
    const totalOutput = [evidenceDirector?.outputTokenCount, directed.outputTokenCount].filter((value): value is number => value !== null && value !== undefined).reduce((sum, value) => sum + value, 0);
    const fallbackReason = [evidenceDirector?.fallbackReason, directed.fallbackReason].filter(Boolean).join(";").slice(0, 240) || null;
    const agentRun: AgentRun = {
      id: randomUUID(), caseId: claimed.case.id, jobId: claimed.job.id, caseVersion: claimed.case.version,
      modelId: claimed.case.orchestrationModelId, skillVersion: claimed.case.skillVersion, promptVersion: claimed.case.promptVersion,
      deploymentMode: claimed.case.deploymentMode, deploymentSha: process.env.DEPLOYMENT_SHA?.trim() || null,
      decision, validatedDecision, toolCalls: [...directed.toolCalls], fallbackReason,
      inputTokenCount: totalInput || null, outputTokenCount: totalOutput || null,
      latencyMs: Math.min(300_000, (evidenceDirector?.latencyMs ?? 0) + directed.latencyMs), createdAt: now.toISOString(),
    };
    if (claimed.case.deploymentMode === "v5_shadow") {
      const legacy = projectLegacyV4Turn({
        events,
        newEvents: extracted,
        attemptedRefinementEventIds: claimed.attemptedRefinementEventIds,
        latestAnswer: claimed.turn.answer,
        snapshot,
      });
      return {
        newEventRevisions: extracted, pendingEvidence: [...reconciliation.pending], snapshot, diagnostics, featureSnapshot,
        validatedDecision, publicMessage: { ...legacy.publicMessage, analysisTrace: publicMessage.analysisTrace },
        nextQuestion: legacy.nextQuestion, agentRun, status: legacy.status, phase: legacy.phase,
      };
    }
    return {
      newEventRevisions: extracted, pendingEvidence: [...reconciliation.pending], snapshot, diagnostics, featureSnapshot,
      validatedDecision, publicMessage, nextQuestion, agentRun, status,
      phase: status === "awaiting_answer" ? "collecting_evidence" as const : "complete" as const,
    };
  }

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
  const selectedOpportunity = finalDecision.action === "ask_question" && "opportunityId" in finalDecision
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
  const renderedMessage = legacyProjection.publicMessage;
  finishPhase();
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
    status: "legacy",
    stages,
    toolCalls: analysisToolCalls,
    techniques: publicRectificationTechniques(engineResult),
    reasoningSummary,
    reasoningSource: reasoningSummary ? "provider_summary" : "none",
  };
  const publicMessage: StoredPublicMessage = { ...renderedMessage, analysisTrace };
  const nextQuestion = legacyProjection.nextQuestion;
  const status = legacyProjection.status;
  const phase = legacyProjection.phase;

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
