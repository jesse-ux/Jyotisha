import { createHash } from "node:crypto";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationTurn,
} from "./contracts.ts";
import { ConversationalRectificationError } from "./errors.ts";
import { extractLifeEventEvidence } from "./evidence-extractor.ts";
import {
  declaredBirthInputSchema,
  privateCandidateSchema,
  validationReceiptSchema,
  type DeclaredBirthInput,
  type LifeEventEvidence,
  type PrivateCandidate,
  type ValidationReceipt,
} from "./persistence-contracts.ts";
import {
  generateRectificationNarrative,
  type RectificationNarrativeGenerator,
  type RectificationNarrativeResult,
} from "./narrative-agent.ts";
import {
  projectRectificationTechnicalPacket,
  type RectificationEvidenceDomain,
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";
import {
  convergenceNotes,
  MINIMUM_SCOREABLE_EVENTS,
  nextPlateauCount,
  rangeCompletionCopy,
  rangeCompletionReason,
  type RangeCompletionReason,
} from "./convergence.ts";
import type { ConversationalRectificationBilling } from "./billing.ts";
import {
  projectLegacyCaseForConversationalImport,
  type LegacyConversationalImportSource,
} from "./legacy-import.ts";
import type {
  ConversationalRectificationStore,
  LifeEventEvidenceInput,
  LoadedConversationalRectificationCase,
  PrivateCandidateInput,
  StoredConversationalRectificationCase,
} from "./store.ts";

type CommandOf<Type extends ConversationalRectificationCommand["type"]> = Extract<
  ConversationalRectificationCommand,
  { readonly type: Type }
>;

export type ComputedConversationalRectificationPacket = Readonly<{
  packet: RectificationTechnicalPacket;
  resultId: string | null;
}>;

export type ConversationalRectificationProfile = Readonly<{
  declaredBirthInput: unknown;
  revisionOfCaseId: string | null;
  legacyCaseId?: string | null;
}>;

export type ConversationalRectificationPacketBuildInput = Readonly<{
  userId: string;
  caseId: string;
  asOfDate: string;
  declaredBirthInput: DeclaredBirthInput;
  privateCandidate: PrivateCandidateInput | null;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
  preserveCandidateRange?: true;
}>;

export type ConversationalRectificationServicePorts = Readonly<{
  store: Pick<ConversationalRectificationStore,
    "createCaseWithFirstTurn" | "loadCase" | "loadActionReceipt" | "saveTurn" | "pause" | "abandon" | "confirm">
    & Partial<Pick<ConversationalRectificationStore, "importLegacy">>;
  billing: Pick<ConversationalRectificationBilling, "reserve" | "complete" | "release">;
  rectificationPriceCredits: number;
  allowNewCaseCreation?: boolean;
  loadDeclaredProfile(userId: string): Promise<ConversationalRectificationProfile>;
  loadLegacyCase?(
    userId: string,
    legacyCaseId: string,
  ): Promise<LegacyConversationalImportSource | null>;
  buildTechnicalPacket(
    input: ConversationalRectificationPacketBuildInput,
  ): Promise<ComputedConversationalRectificationPacket>;
  narrativeGenerator: RectificationNarrativeGenerator;
  asOfDate(): string;
}>;

export type ConversationalRectificationService = Readonly<{
  importLegacyCase(
    userId: string,
    legacyCaseId: string,
    actionId: string,
    pendingConsultationQuestion?: string | null,
  ): Promise<ConversationalRectificationTurn>;
  start(userId: string, command: CommandOf<"start">): Promise<ConversationalRectificationTurn>;
  resume(userId: string, command: CommandOf<"resume">): Promise<ConversationalRectificationTurn>;
  answer(userId: string, command: CommandOf<"answer">): Promise<ConversationalRectificationTurn>;
  pause(userId: string, command: CommandOf<"pause">): Promise<ConversationalRectificationTurn>;
  abandon(userId: string, command: CommandOf<"abandon">): Promise<ConversationalRectificationTurn>;
  confirm(userId: string, command: CommandOf<"confirm">): Promise<ConversationalRectificationTurn>;
}>;

export type ConversationalRectificationTelemetryOutcome = Readonly<{
  billingState: "not_applicable" | "charged" | "released" | "migration_waived" | "unchanged" | "unknown";
  caseStatus: ConversationalRectificationTurn["status"] | null;
}>;

const telemetryOutcomes = new WeakMap<
  ConversationalRectificationService,
  () => ConversationalRectificationTelemetryOutcome
>();

export function conversationalRectificationTelemetryOutcome(
  service: ConversationalRectificationService,
): ConversationalRectificationTelemetryOutcome | null {
  return telemetryOutcomes.get(service)?.() ?? null;
}

const transitionValidatorVersion = "conversational-rectification-orchestrator-v1";
const explicitDirectionChangePattern = /(?:都不符合|都不是|不符合|换(?:个|一)?(?:方向|领域)|其他方向|别的方向|不想(?:谈|说|回答)|拒绝回答)/;
const genericUncertaintyPattern = /(?:不知道|不确定)/;

export function evidencePredatesBirthDate(
  evidence: Pick<LifeEventEvidence, "dateValue" | "datePrecision">,
  birthDate: string,
): boolean {
  if (!evidence.dateValue) return false;
  const boundary = evidence.datePrecision === "year"
    ? birthDate.slice(0, 4)
    : evidence.datePrecision === "month"
      ? birthDate.slice(0, 7)
      : evidence.datePrecision === "day"
        ? birthDate
        : null;
  return boundary !== null && evidence.dateValue < boundary;
}

function evidenceForDeclaredBirthDate(
  evidence: readonly LifeEventEvidence[],
  birthDate: string,
): readonly LifeEventEvidence[] {
  return evidence.map((item) => item.scoreable === true
    && evidencePredatesBirthDate(item, birthDate)
    ? { ...item, extractionStatus: "needs_clarification" as const, scoreable: false }
    : item);
}

function safeFailure(error: unknown): ConversationalRectificationError {
  return error instanceof ConversationalRectificationError
    ? error
    : new ConversationalRectificationError("service_unavailable");
}

function parseCommand<Type extends ConversationalRectificationCommand["type"]>(
  type: Type,
  value: unknown,
): CommandOf<Type> {
  const parsed = conversationalRectificationCommandSchema.safeParse(value);
  if (!parsed.success || parsed.data.type !== type) {
    throw new ConversationalRectificationError("invalid_command");
  }
  return parsed.data as CommandOf<Type>;
}

type MutableCommand = Extract<ConversationalRectificationCommand, {
  readonly type: "answer" | "pause" | "abandon" | "confirm";
}>;

function commandFingerprint(command: MutableCommand): string {
  const identity = command.type === "answer"
    ? [command.type, command.caseId, command.actionId, command.turnVersion,
        command.domain ?? null, command.answer, command.correctsEvidenceId ?? null]
    : command.type === "confirm"
      ? [command.type, command.caseId, command.actionId, command.turnVersion, command.time]
      : [command.type, command.caseId, command.actionId, command.turnVersion];
  return createHash("sha256").update(JSON.stringify(identity), "utf8").digest("hex");
}

function visibleEvidenceSummary(value: string): string {
  const cleaned = value.replace(/(?:发生时间|事件详情)\s*[:：]\s*/g, "").trim();
  return cleaned || value;
}

function publicTurn(value: StoredConversationalRectificationCase): ConversationalRectificationTurn {
  const parsed = conversationalRectificationTurnSchema.safeParse(value.latestTurn);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  const evidenceDomains = new Map(
    effectiveLifeEventEvidence(value.eventEvidence ?? []).map((item) => [item.id, item.domain]),
  );
  return {
    ...parsed.data,
    evidenceRecap: parsed.data.evidenceRecap.map((item) => ({
      ...item,
      summary: visibleEvidenceSummary(item.summary),
      ...(item.domain ? {} : evidenceDomains.get(item.id)
        ? { domain: evidenceDomains.get(item.id) }
        : {}),
    })),
  };
}

function transitionReceipt(modelId = "deterministic-rectification-transition"): ValidationReceipt {
  return validationReceiptSchema.parse({
    modelId,
    schemaValidated: true,
    validatorVersion: transitionValidatorVersion,
    retryCount: 0,
    fallbackUsed: false,
    issues: [],
  });
}

function latestReceipt(value: LoadedConversationalRectificationCase): ValidationReceipt {
  const receipt = value.validationReceipts.at(-1);
  const parsed = validationReceiptSchema.safeParse(receipt);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  return parsed.data;
}

export function effectiveLifeEventEvidence<
  Evidence extends Readonly<{
    id: string;
    correctsEvidenceIds?: readonly string[];
  }>,
>(evidence: ReadonlyArray<Evidence>): ReadonlyArray<Evidence> {
  const correctedIds = new Set<string>();
  for (const item of evidence) {
    for (const correctedId of item.correctsEvidenceIds ?? []) correctedIds.add(correctedId);
  }
  return evidence.filter((item) => !correctedIds.has(item.id));
}

function evidenceRecap(evidence: ReadonlyArray<LifeEventEvidenceInput>) {
  return effectiveLifeEventEvidence(evidence).slice(-20).map((item) => ({
    id: item.id,
    summary: visibleEvidenceSummary(item.eventSummary),
    dateLabel: item.dateValue
      ? item.scoreable === false && item.extractionStatus !== "needs_clarification"
        ? `${item.dateValue}（未来，仅作背景）`
        : item.dateValue
      : "日期待补充",
    domain: item.domain,
    ...((item.correctsEvidenceIds?.length ?? 0) > 0 ? { isCorrection: true } : {}),
  }));
}

function narrativeConversationContext(input: Readonly<{
  latestUserText: string;
  allEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  newEvidence: ReadonlyArray<LifeEventEvidenceInput>;
}>) {
  const activeEvidence = effectiveLifeEventEvidence(input.allEvidence);
  const activeIds = new Set(activeEvidence.map((item) => item.id));
  return {
    latestUserText: input.latestUserText.trim().slice(0, 4_000),
    latestEvidence: evidenceRecap(input.newEvidence).map((item) => ({
      dateLabel: item.dateLabel,
      summary: item.summary,
      domain: item.domain,
    })),
    eventLedger: input.allEvidence.slice(-40).map((item) => ({
      id: item.id,
      rawText: item.rawText,
      dateLabel: item.dateValue ?? "日期待补充",
      summary: visibleEvidenceSummary(item.eventSummary),
      domain: item.domain,
      extractionStatus: item.extractionStatus,
      active: activeIds.has(item.id),
      correctsEvidenceIds: [...(item.correctsEvidenceIds ?? [])],
    })),
    unresolvedEvidence: activeEvidence
      .filter((item) => item.extractionStatus === "needs_clarification")
      .slice(-20)
      .map((item) => ({
        id: item.id,
        rawText: item.rawText,
        summary: visibleEvidenceSummary(item.eventSummary),
        domain: item.domain,
        dateLabel: item.dateValue ?? "日期待补充",
      })),
  };
}

const progressDomainLabels = {
  career: "事业",
  education: "学业",
  finance: "财务",
  health_pressure: "健康与重大压力",
  relocation: "搬迁",
  relationship: "重要关系",
  family: "家庭",
  other: "其他关键经历",
} as const satisfies Readonly<Record<RectificationEvidenceDomain, string>>;

function evidenceProgressNarrative(input: Readonly<{
  previousCandidate: PrivateCandidateInput;
  packet: RectificationTechnicalPacket;
  newEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  allEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  scoreableEventCount: number;
  willContinue: boolean;
  authoredNarrative?: string | null;
}>): string {
  const recorded = evidenceRecap(input.newEvidence);
  const acknowledgement = recorded.length === 0
    ? "这段经历已经保存。"
    : `已记录：${recorded.map((item) => `${item.dateLabel} · ${item.summary}`).join("；")}。`;
  const previousStart = input.previousCandidate.rangeStart;
  const previousEnd = input.previousCandidate.rangeEnd;
  const nextStart = input.packet.candidate.range.startTime;
  const nextEnd = input.packet.candidate.range.endTime;
  const rangeChanged = previousStart !== nextStart || previousEnd !== nextEnd;
  const progress = input.scoreableEventCount < MINIMUM_SCOREABLE_EVENTS
    ? `当前累计 ${input.scoreableEventCount} 条可评分经历；系统至少需要 ${MINIMUM_SCOREABLE_EVENTS} 条时间明确的经历才开始事件排序，所以本轮候选范围暂时保持 ${nextStart}–${nextEnd}。`
    : rangeChanged
      ? `候选范围已从 ${previousStart ?? "原范围"}–${previousEnd ?? "原范围"} 更新为 ${nextStart}–${nextEnd}。`
      : `本轮已纳入 ${input.scoreableEventCount} 条可评分经历，但候选范围暂未稳定缩小；这不是提交失败。`;
  const suggested = nextEvidenceDomains(input.packet, input.allEvidence)
    .map((item) => progressDomainLabels[item.domain]);
  const nextStep = input.willContinue && suggested.length > 0
    ? `下一步：请优先补充一件${suggested.join("或")}领域已经发生的事件，并选择大致年月。`
    : "";
  const differenceBasis = input.packet.suggestedDomains.length > 0
    ? `本轮区分重点：${input.packet.suggestedDomains.slice(0, 2)
      .map((item) => `${progressDomainLabels[item.domain]}事件用于比较 ${item.layer}`)
      .join("；")}。`
    : "";
  const authored = input.authoredNarrative?.trim();
  if (authored) return authored.slice(0, 12_000);
  return [acknowledgement, authored, progress, nextStep, differenceBasis]
    .filter(Boolean)
    .join("\n")
    .slice(0, 12_000);
}

function unansweredEvidenceDomains(
  packet: RectificationTechnicalPacket,
  evidence: ReadonlyArray<LifeEventEvidenceInput>,
) {
  const answeredDomains = new Set(effectiveLifeEventEvidence(evidence)
    .filter((item) => item.extractionStatus !== "needs_clarification")
    .map((item) => item.domain));
  return packet.suggestedDomains.filter((item) => !answeredDomains.has(item.domain));
}

function nextEvidenceDomains(
  packet: RectificationTechnicalPacket,
  evidence: ReadonlyArray<LifeEventEvidenceInput>,
) {
  const unanswered = unansweredEvidenceDomains(packet, evidence);
  return (unanswered.length > 0 ? unanswered : packet.suggestedDomains).slice(0, 2);
}

function evidenceRequestForProgress(input: Readonly<{
  packet: RectificationTechnicalPacket;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
  willContinue: boolean;
}>): RectificationNarrativeResult["output"]["evidenceRequest"] {
  if (!input.willContinue) return null;
  const suggested = nextEvidenceDomains(input.packet, input.evidence);
  if (suggested.length === 0) return null;
  const labels = suggested.map((item) => progressDomainLabels[item.domain]);
  return {
    domains: suggested.map((item) => item.domain),
    datePrecision: "month_preferred",
    prompt: `请说一件${labels.join("或")}方面已经发生的事，尽量写明哪一年、哪一月以及发生了什么。`,
  };
}

function exactTechnicalReceipt(packet: RectificationTechnicalPacket) {
  const projected = projectRectificationTechnicalPacket(packet);
  return {
    calculationVersion: projected.technicalReceipt.calculationVersion,
    stableLayers: projected.technicalReceipt.stableLayers,
    sensitiveLayers: projected.technicalReceipt.sensitiveLayers,
    candidateDifferenceRefs: projected.technicalReceipt.candidateDifferenceRefs,
  };
}

function actionsFor(status: "active" | "confirming") {
  if (status === "confirming") {
    return ["answer", "pause", "abandon", "confirm"] as const;
  }
  return ["answer", "pause", "abandon"] as const;
}

function confirmationGatedPacket(
  packet: RectificationTechnicalPacket,
  scoreableEventCount: number,
): RectificationTechnicalPacket {
  if (packet.candidate.status !== "ready_for_confirmation"
    || scoreableEventCount >= MINIMUM_SCOREABLE_EVENTS) return packet;
  return {
    ...packet,
    candidate: { ...packet.candidate, status: "pending_validation" },
    useBoundary: `当前候选仍需至少 ${MINIMUM_SCOREABLE_EVENTS} 条时间明确、可评分的真实经历验证，不能作为已经校正完成的出生分钟。`,
  };
}

function turnFromNarrative(input: {
  readonly caseId: string;
  readonly turnVersion: number;
  readonly pendingConsultationQuestion: string | null;
  readonly packet: RectificationTechnicalPacket;
  readonly narrative: RectificationNarrativeResult;
  readonly evidence: ReadonlyArray<LifeEventEvidenceInput>;
}): ConversationalRectificationTurn {
  const projected = projectRectificationTechnicalPacket(input.packet);
  const status = projected.candidate.status === "ready_for_confirmation" ? "confirming" : "active";
  const evidenceRequest = input.narrative.output.evidenceRequest
    ? {
        domains: input.narrative.output.evidenceRequest.domains,
        datePrecision: input.narrative.output.evidenceRequest.datePrecision,
        freeTextAllowed: true as const,
      }
    : null;
  const candidate = {
    status: projected.candidate.status,
    representativeTime: projected.candidate.representativeTime,
    rangeStart: projected.candidate.rangeStart,
    rangeEnd: projected.candidate.rangeEnd,
  };
  const parsed = conversationalRectificationTurnSchema.safeParse({
    caseId: input.caseId,
    journeyProtocol: "conversational-evidence-v3",
    status,
    turnVersion: input.turnVersion,
    narrative: input.narrative.narrative,
    candidate,
    technicalReceipt: exactTechnicalReceipt(input.packet),
    evidenceRequest,
    evidenceRecap: evidenceRecap(input.evidence),
    actions: actionsFor(status),
    pendingConsultationQuestion: input.pendingConsultationQuestion,
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return parsed.data;
}

function privateCandidateFromPacket(input: {
  readonly packet: RectificationTechnicalPacket;
  readonly resultId: string | null;
  readonly iteration: number;
  readonly forceCollecting?: boolean;
  readonly notes?: readonly string[];
}): PrivateCandidate {
  const packet = input.packet;
  const parsed = privateCandidateSchema.safeParse({
    resultId: input.resultId,
    representativeTime: packet.candidate.representativeTime,
    rangeStart: packet.candidate.range.startTime,
    rangeEnd: packet.candidate.range.endTime,
    calculationVersion: packet.calculationVersion,
    candidateWeights: Object.entries(packet.candidateWeights)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([, weight]) => weight),
    candidateModelRefs: packet.candidateModelRefs,
    d1Stability: packet.d1Stability,
    boundaryDistanceMinutes: packet.boundaryDistanceMinutes,
    supportedSensitiveLayers: packet.supportedSensitiveLayers,
    scoredHistoricalEvidence: packet.scoredHistoricalEvidence,
    suggestedDomains: packet.suggestedDomains.map((item) => item.domain),
    futureWindows: packet.futureWindows,
    workingState: {
      phase: input.forceCollecting
        ? "collecting_evidence"
        : packet.candidate.status === "ready_for_confirmation" ? "ready" : "collecting_evidence",
      iteration: input.iteration,
      notes: [...(input.notes ?? [])],
    },
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return parsed.data;
}

function completedRangeTurn(
  turn: ConversationalRectificationTurn,
  reason: RangeCompletionReason,
): ConversationalRectificationTurn {
  const suffix = `${rangeCompletionCopy(reason)} 当前证据没有收敛到可确认分钟，因此本次不计费，已退回暂扣点数。候选范围仅作记录，代表时间不会替换当前排盘时间。`;
  const parsed = conversationalRectificationTurnSchema.safeParse({
    ...turn,
    status: "completed",
    narrative: boundedNarrative(turn.narrative, suffix),
    candidate: { ...turn.candidate, status: "pending_validation" },
    evidenceRequest: null,
    actions: turn.pendingConsultationQuestion ? ["continue_original_question"] : [],
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return parsed.data;
}

function changedTurn(input: {
  readonly current: LoadedConversationalRectificationCase;
  readonly status: "paused" | "abandoned" | "completed";
  readonly narrative: string;
  readonly receipt?: ValidationReceipt;
}): { readonly turn: ConversationalRectificationTurn; readonly receipt: ValidationReceipt } {
  const current = input.current.latestTurn;
  const actions = input.status === "paused"
    ? ["answer", "abandon"]
    : input.status === "completed" && current.pendingConsultationQuestion
      ? ["continue_original_question"]
      : [];
  const candidate = input.status === "completed"
    ? { ...current.candidate, status: "confirmed" as const }
    : current.candidate;
  const parsed = conversationalRectificationTurnSchema.safeParse({
    ...current,
    status: input.status,
    turnVersion: input.current.turnVersion + 1,
    narrative: input.narrative,
    candidate,
    evidenceRequest: input.status === "completed" ? null : current.evidenceRequest,
    actions,
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return { turn: parsed.data, receipt: input.receipt ?? transitionReceipt() };
}

function boundedNarrative(previous: string, suffix: string): string {
  const room = Math.max(1, 12_000 - suffix.length - 2);
  return `${previous.slice(0, room)}\n\n${suffix}`.slice(0, 12_000);
}

function midpointOfRange(range: Readonly<{ startTime: string; endTime: string }>): string {
  const minute = (value: string) => {
    const [hour = 0, part = 0] = value.split(":").map(Number);
    return hour * 60 + part;
  };
  const clock = (value: number) => {
    const normalized = ((value % 1_440) + 1_440) % 1_440;
    return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
  };
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  if (end < start) end += 1_440;
  return clock(Math.round((start + end) / 2));
}

function domainsForClarification(
  current: ConversationalRectificationTurn,
  hint: RectificationEvidenceDomain | undefined,
): readonly RectificationEvidenceDomain[] {
  const values = [
    hint,
    ...(current.evidenceRequest?.domains ?? []),
    "career" as const,
    "relationship" as const,
  ].filter((value): value is RectificationEvidenceDomain => Boolean(value));
  return [...new Set(values)].slice(0, 4).length >= 2
    ? [...new Set(values)].slice(0, 4)
    : ["career", "relationship"];
}

type CorrectionResetReason =
  | "needs_clarification"
  | "non_scoreable"
  | "direction_change"
  | "validation_fallback";

function nonScoringTurn(input: {
  readonly current: LoadedConversationalRectificationCase;
  readonly newEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  readonly domain?: RectificationEvidenceDomain;
  readonly directionChange: boolean;
  readonly correctionReset?: Readonly<{
    packet: RectificationTechnicalPacket;
    reason: CorrectionResetReason;
  }>;
}): { readonly turn: ConversationalRectificationTurn; readonly receipt: ValidationReceipt } {
  const allEvidence = [...input.current.eventEvidence, ...input.newEvidence];
  const hasFuture = input.newEvidence.some((item) => item.extractionStatus !== "needs_clarification"
    && item.scoreable === false && item.dateValue !== null);
  const latestIncomplete = input.newEvidence
    .filter((item) => item.extractionStatus === "needs_clarification")
    .at(-1);
  const clarificationNarrative = latestIncomplete?.dateValue === null
    && latestIncomplete.eventSummary !== "事件内容待补充"
    ? `你提到“${visibleEvidenceSummary(latestIncomplete.eventSummary)}”，具体内容我已经记下了。它大致是什么年月？只记得年份也可以。`
    : latestIncomplete?.dateValue
      && latestIncomplete.eventSummary === "事件内容待补充"
      ? `我已经记下 ${latestIncomplete.dateValue} 这个时间。那时具体发生了什么重要事情？`
      : null;
  const correctionNarrative = input.correctionReset?.reason === "validation_fallback"
    ? "这条更正已保存，原记录已经停止参与候选评分，候选范围也已重新计算。为避免只凭一次修订直接确认出生分钟，本轮先保持待验证；请继续补充另一件已经发生的真实经历。"
    : input.correctionReset?.reason === "direction_change"
      ? "这条更正已保存，原记录已经停止参与候选评分。我们会从声明范围重新开始核对，你可以换一个真实事件方向并尽量写明年月；本轮不会沿用旧候选推进确认。"
      : input.correctionReset?.reason === "non_scoreable"
        ? "这条更正已保存，原记录已经停止参与候选评分。更正后的内容目前不能作为已经发生的评分证据，候选已从声明范围重新计算；请再补充一件已发生并带有年月的事件。"
        : "这条更正已保存，原记录已经停止参与候选评分。更正后的事件时间还不够清楚，候选已从声明范围重新计算；请补充大约年份、月份和发生了什么。";
  const narrative = input.correctionReset
    ? correctionNarrative
    : input.directionChange
      ? "好的，我们不沿用不符合你的方向。你可以自由描述另一件已经发生的生活变化，尽量写明年月；我会根据事实继续，而不是让你选择宽泛年份。"
      : hasFuture
        ? "已保存这段描述。未来事件只能作为背景，不能用于校正评分；请再说一件已经发生的事件，并尽量写明年月。"
        : clarificationNarrative
          ?? "我已保存你的原话，但还缺少可用于区分候选的明确时间。请用自己的话补充这件已经发生的事大约是哪一年、哪一月；不需要选择固定答案。";
  const status = input.correctionReset
    ? "active" as const
    : input.current.status === "confirming" ? "confirming" as const : "active" as const;
  const actions = actionsFor(status);
  const evidenceRequest = status === "confirming" && input.current.latestTurn.evidenceRequest === null
    ? null
    : {
        domains: domainsForClarification(input.current.latestTurn, input.domain),
        datePrecision: "month_preferred" as const,
        freeTextAllowed: true as const,
      };
  const parsed = conversationalRectificationTurnSchema.safeParse({
    ...input.current.latestTurn,
    status,
    turnVersion: input.current.turnVersion + 1,
    narrative,
    evidenceRequest,
    evidenceRecap: evidenceRecap(allEvidence),
    actions,
    ...(input.correctionReset ? {
      candidate: {
        ...projectRectificationTechnicalPacket(input.correctionReset.packet).candidate,
        status: "pending_validation" as const,
      },
      technicalReceipt: exactTechnicalReceipt(input.correctionReset.packet),
    } : {}),
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return {
    turn: parsed.data,
    receipt: transitionReceipt("deterministic-evidence-clarification"),
  };
}

function requireLoaded(
  value: LoadedConversationalRectificationCase | null,
): LoadedConversationalRectificationCase {
  if (!value) throw new ConversationalRectificationError("case_not_found");
  return value;
}

function requireExactVersion(current: LoadedConversationalRectificationCase, expected: number) {
  if (current.turnVersion !== expected) throw new ConversationalRectificationError("stale_turn");
}

function requireMutable(current: LoadedConversationalRectificationCase) {
  if (!(["active", "paused", "confirming"] as const).includes(
    current.status as "active" | "paused" | "confirming",
  )) {
    throw new ConversationalRectificationError("invalid_transition");
  }
}

export function createConversationalRectificationService(
  ports: ConversationalRectificationServicePorts,
): ConversationalRectificationService {
  let lastTelemetryOutcome: ConversationalRectificationTelemetryOutcome = {
    billingState: "not_applicable",
    caseStatus: null,
  };
  function resetTelemetryOutcome() {
    lastTelemetryOutcome = { billingState: "not_applicable", caseStatus: null };
  }
  function observeCase(
    value: LoadedConversationalRectificationCase | StoredConversationalRectificationCase,
    billingState: ConversationalRectificationTelemetryOutcome["billingState"] = "unchanged",
  ) {
    lastTelemetryOutcome = { billingState, caseStatus: publicTurn(value).status };
  }

  async function load(userId: string, caseId: string) {
    try {
      const current = requireLoaded(await ports.store.loadCase({ userId, caseId }));
      observeCase(current);
      return current;
    } catch (error) {
      throw safeFailure(error);
    }
  }

  async function replayMutation(
    userId: string,
    command: MutableCommand,
    actionKind: "save_turn" | "pause" | "abandon" | "confirm",
    fingerprint: string,
  ): Promise<ConversationalRectificationTurn | null> {
    try {
      const receipt = await ports.store.loadActionReceipt({
        userId,
        caseId: command.caseId,
        expectedVersion: command.turnVersion,
        actionId: command.actionId,
        actionKind,
        commandFingerprint: fingerprint,
      });
      if (!receipt) return null;
      observeCase(receipt);
      return publicTurn(receipt);
    } catch (error) {
      throw safeFailure(error);
    }
  }

  async function importLegacyCase(
    userId: string,
    legacyCaseId: string,
    actionId: string,
    pendingConsultationQuestion: string | null = null,
  ): Promise<ConversationalRectificationTurn> {
    resetTelemetryOutcome();
    const importer = ports.store.importLegacy;
    const loadLegacy = ports.loadLegacyCase;
    if (!importer || !loadLegacy) {
      throw new ConversationalRectificationError("service_unavailable");
    }

    try {
      const existingByAction = await ports.store.loadCase({ userId, caseId: actionId });
      if (existingByAction) {
        observeCase(existingByAction);
        if (existingByAction.importedFromCaseId !== legacyCaseId
          || existingByAction.billingState !== "migration_waived"
          || existingByAction.pendingConsultationQuestion !== pendingConsultationQuestion) {
          throw new ConversationalRectificationError("action_conflict");
        }
        return publicTurn(existingByAction);
      }
      const current = await ports.store.loadCase({ userId });
      if (current?.importedFromCaseId === legacyCaseId
        && current.billingState === "migration_waived"
        && current.pendingConsultationQuestion === pendingConsultationQuestion) {
        observeCase(current);
        return publicTurn(current);
      }
      if (current?.importedFromCaseId === legacyCaseId
        && current.billingState === "migration_waived") {
        throw new ConversationalRectificationError("action_conflict");
      }
      if (ports.allowNewCaseCreation === false) {
        throw new ConversationalRectificationError("service_unavailable");
      }

      const legacy = await loadLegacy(userId, legacyCaseId);
      if (!legacy) throw new ConversationalRectificationError("case_not_found");
      const projected = projectLegacyCaseForConversationalImport({
        source: legacy,
        asOfDate: ports.asOfDate(),
        expectedUserId: userId,
      });
      const rangeSeed = privateCandidateSchema.parse({
        resultId: null,
        representativeTime: midpointOfRange(projected.currentRange),
        rangeStart: projected.currentRange.startTime,
        rangeEnd: projected.currentRange.endTime,
        calculationVersion: "legacy-import-range-v1",
        workingState: { phase: "collecting_evidence", iteration: 0, notes: [] },
      });
      const computed = await ports.buildTechnicalPacket({
        userId,
        caseId: actionId,
        asOfDate: ports.asOfDate(),
        declaredBirthInput: projected.declaredBirthInput,
        privateCandidate: rangeSeed,
        evidence: projected.evidence,
        preserveCandidateRange: true,
      });
      const gatedPacket = confirmationGatedPacket(computed.packet, 0);
      const narrative = await generateRectificationNarrative({
        phase: "first",
        packet: gatedPacket,
        generator: ports.narrativeGenerator,
      });
      const privateCandidate = privateCandidateFromPacket({
        packet: gatedPacket,
        resultId: null,
        iteration: 0,
        forceCollecting: true,
      });
      const firstTurn = turnFromNarrative({
        caseId: actionId,
        turnVersion: 0,
        pendingConsultationQuestion,
        packet: gatedPacket,
        narrative,
        evidence: projected.evidence,
      });
      const imported = await importer.call(ports.store, {
        userId,
        caseId: actionId,
        expectedVersion: projected.expectedVersion,
        actionId,
        legacyCaseId,
        price: ports.rectificationPriceCredits,
        pendingConsultationQuestion,
        declaredBirthInput: projected.declaredBirthInput,
        evidence: projected.evidence,
        firstTurn,
        validationReceipt: narrative.validationReceipt,
        privateCandidate,
      });
      observeCase(imported, "migration_waived");
      return publicTurn(imported);
    } catch (error) {
      if (error instanceof ConversationalRectificationError
        && error.code === "action_conflict") {
        try {
          const winner = await ports.store.loadCase({ userId });
          if (winner?.importedFromCaseId === legacyCaseId
            && winner.billingState === "migration_waived"
            && winner.pendingConsultationQuestion === pendingConsultationQuestion) {
            observeCase(winner);
            return publicTurn(winner);
          }
        } catch {
          // Preserve the original stable conflict below.
        }
      }
      throw safeFailure(error);
    }
  }

  function extractedEvidence(command: CommandOf<"answer">): readonly LifeEventEvidence[] {
    let extracted: readonly LifeEventEvidence[];
    try {
      extracted = extractLifeEventEvidence({
        rawText: command.answer,
        sourceTurnId: command.actionId,
        asOfDate: ports.asOfDate(),
        correctsEvidenceId: command.correctsEvidenceId,
      }).map((item) => ({
        ...item,
        correctsEvidenceIds: [...item.correctsEvidenceIds],
        domain: item.domain === "other" && command.domain && command.domain !== "other"
          ? command.domain
          : item.domain,
      }));
    } catch {
      throw new ConversationalRectificationError("invalid_command");
    }
    if (extracted.length > 20) throw new ConversationalRectificationError("invalid_command");
    if (command.correctsEvidenceId && extracted.length !== 1) {
      throw new ConversationalRectificationError("invalid_command");
    }
    return extracted;
  }

  function completeLatestClarification(input: Readonly<{
    command: CommandOf<"answer">;
    current: LoadedConversationalRectificationCase;
    extracted: readonly LifeEventEvidence[];
  }>): readonly LifeEventEvidence[] {
    if (input.command.correctsEvidenceId || input.extracted.length !== 1) return input.extracted;
    const pending = effectiveLifeEventEvidence(input.current.eventEvidence)
      .filter((item) => item.extractionStatus === "needs_clarification")
      .at(-1);
    const supplied = input.extracted[0];
    if (!pending || !supplied) return input.extracted;

    const pendingHasSummary = pending.eventSummary !== "事件内容待补充";
    const suppliedHasSummary = supplied.eventSummary !== "事件内容待补充";
    const fillsMissingDate = pending.dateValue === null
      && supplied.dateValue !== null
      && pendingHasSummary
      && !suppliedHasSummary;
    const fillsMissingSummary = pending.dateValue !== null
      && supplied.dateValue === null
      && !pendingHasSummary
      && suppliedHasSummary;
    if (!fillsMissingDate && !fillsMissingSummary) return input.extracted;

    const dateValue = supplied.dateValue ?? pending.dateValue;
    const summary = suppliedHasSummary ? supplied.eventSummary : pending.eventSummary;
    if (!dateValue || summary === "事件内容待补充") return input.extracted;
    const merged = extractLifeEventEvidence({
      rawText: `${dateValue} ${summary}`,
      sourceTurnId: input.command.actionId,
      asOfDate: ports.asOfDate(),
      correctsEvidenceId: pending.id,
    });
    if (merged.length !== 1) return input.extracted;
    return merged.map((item) => ({
      ...item,
      rawText: `${pending.rawText}\n补充：${input.command.answer}`,
      domain: pending.domain === "other" ? item.domain : pending.domain,
      correctsEvidenceIds: [...item.correctsEvidenceIds],
    }));
  }

  const service: ConversationalRectificationService = Object.freeze({
    importLegacyCase,
    async start(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("start", rawCommand);
      let profile: ConversationalRectificationProfile;
      try {
        profile = await ports.loadDeclaredProfile(userId);
      } catch (error) {
        throw safeFailure(error);
      }
      const declared = declaredBirthInputSchema.safeParse(profile.declaredBirthInput);
      if (!declared.success) throw new ConversationalRectificationError("profile_incomplete");

      if (profile.legacyCaseId) {
        return importLegacyCase(
          userId,
          profile.legacyCaseId,
          command.actionId,
          command.pendingConsultationQuestion ?? null,
        );
      }

      let price: number;
      try {
        price = ports.rectificationPriceCredits;
      } catch {
        throw new ConversationalRectificationError("service_unavailable");
      }
      if (!Number.isSafeInteger(price) || price < 1 || price > 1_000_000) {
        throw new ConversationalRectificationError("service_unavailable");
      }

      const caseId = command.actionId;
      let existing: LoadedConversationalRectificationCase | null;
      try {
        existing = await ports.store.loadCase({ userId, caseId });
      } catch (error) {
        throw safeFailure(error);
      }
      if (existing) {
        observeCase(existing);
        if (existing.pendingConsultationQuestion !== (command.pendingConsultationQuestion ?? null)) {
          throw new ConversationalRectificationError("action_conflict");
        }
        if (existing.billingState === "reserved") {
          try {
            await ports.billing.complete({
              userId,
              caseId,
              expectedVersion: 0,
              actionId: command.actionId,
            });
            observeCase(existing, "charged");
          } catch (error) {
            try {
              await ports.billing.release({
                userId,
                caseId,
                expectedVersion: 0,
                actionId: command.actionId,
                price,
              });
              observeCase(existing, "released");
            } catch {
              throw new ConversationalRectificationError("billing_failed");
            }
            throw safeFailure(error);
          }
        } else if (existing.billingState !== "charged"
          && existing.billingState !== "migration_waived") {
          throw new ConversationalRectificationError("billing_failed");
        }
        return publicTurn(existing);
      }
      if (ports.allowNewCaseCreation === false) {
        throw new ConversationalRectificationError("service_unavailable");
      }

      let reserved = false;
      try {
        const reservation = await ports.billing.reserve({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
          price,
        });
        reserved = reservation.billingState === "reserved";
        if (reserved) lastTelemetryOutcome = { billingState: "unknown", caseStatus: null };
        const computed = await ports.buildTechnicalPacket({
          userId,
          caseId,
          asOfDate: ports.asOfDate(),
          declaredBirthInput: declared.data,
          privateCandidate: null,
          evidence: [],
        });
        const gatedPacket = confirmationGatedPacket(computed.packet, 0);
        const narrative = await generateRectificationNarrative({
          phase: "first",
          packet: gatedPacket,
          generator: ports.narrativeGenerator,
        });
        const privateCandidate = privateCandidateFromPacket({
          packet: gatedPacket,
          resultId: null,
          iteration: 0,
          forceCollecting: true,
        });
        const firstTurn = turnFromNarrative({
          caseId,
          turnVersion: 0,
          pendingConsultationQuestion: command.pendingConsultationQuestion ?? null,
          packet: gatedPacket,
          narrative,
          evidence: [],
        });
        const created = await ports.store.createCaseWithFirstTurn({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
          revisionOfCaseId: profile.revisionOfCaseId,
          pendingConsultationQuestion: command.pendingConsultationQuestion ?? null,
          declaredBirthInput: declared.data,
          firstTurn,
          validationReceipt: narrative.validationReceipt,
          privateCandidate,
        });
        observeCase(created, "unknown");
        await ports.billing.complete({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
        });
        observeCase(created, "charged");
        return publicTurn(created);
      } catch (error) {
        if (reserved) {
          try {
            await ports.billing.release({
              userId,
              caseId,
              expectedVersion: 0,
              actionId: command.actionId,
              price,
            });
            lastTelemetryOutcome = {
              billingState: "released",
              caseStatus: lastTelemetryOutcome.caseStatus,
            };
          } catch {
            throw new ConversationalRectificationError("billing_failed");
          }
        }
        throw safeFailure(error);
      }
    },

    async resume(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("resume", rawCommand);
      const current = await load(userId, command.caseId);
      return publicTurn(current);
    },

    async answer(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("answer", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "save_turn", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      requireMutable(current);
      const evidence = evidenceForDeclaredBirthDate(
        completeLatestClarification({
          command,
          current,
          extracted: extractedEvidence(command),
        }),
        current.declaredBirthInput.birthDate,
      );

      if (current.turnVersion === command.turnVersion + 1) {
        try {
          const replayed = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            evidence,
            validationReceipt: latestReceipt(current),
            privateCandidate: current.privateCandidate,
          });
          return publicTurn(replayed);
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);

      if (command.correctsEvidenceId
        && !effectiveLifeEventEvidence(current.eventEvidence)
          .some((item) => item.id === command.correctsEvidenceId)) {
        throw new ConversationalRectificationError("action_conflict");
      }

      const scoreableEvidence = evidence.filter((item) => item.scoreable === true
        && item.extractionStatus !== "needs_clarification");
      const explicitDirectionChange = explicitDirectionChangePattern.test(command.answer);
      const directionChange = explicitDirectionChange
        || (scoreableEvidence.length === 0 && genericUncertaintyPattern.test(command.answer));
      const allScoreable = effectiveLifeEventEvidence([...current.eventEvidence, ...evidence])
        .filter((item) => item.scoreable === true
          && item.extractionStatus !== "needs_clarification"
          && !evidencePredatesBirthDate(item, current.declaredBirthInput.birthDate));

      if (command.correctsEvidenceId) {
        try {
          const computed = await ports.buildTechnicalPacket({
            userId,
            caseId: command.caseId,
            asOfDate: ports.asOfDate(),
            declaredBirthInput: current.declaredBirthInput,
            // A correction invalidates any range narrowed by the retired fact.
            // Rebuild from the user's declared/baseline range so eliminated
            // minutes can re-enter the deterministic scan.
            privateCandidate: null,
            evidence: allScoreable,
          });
          const gatedPacket = confirmationGatedPacket(
            computed.packet,
            allScoreable.length,
          );
          const replacement = evidence[0];
          if (!replacement) throw new ConversationalRectificationError("invalid_command");
          const resetReason: CorrectionResetReason | null = directionChange
            ? "direction_change"
            : replacement.extractionStatus === "needs_clarification"
              ? "needs_clarification"
              : replacement.scoreable !== true ? "non_scoreable" : null;
          if (resetReason) {
            const next = nonScoringTurn({
              current,
              newEvidence: evidence,
              domain: command.domain,
              directionChange: false,
              correctionReset: { packet: computed.packet, reason: resetReason },
            });
            const privateCandidate = privateCandidateFromPacket({
              packet: gatedPacket,
              resultId: null,
              iteration: (current.privateCandidate.workingState?.iteration ?? 0) + 1,
              forceCollecting: true,
            });
            const saved = await ports.store.saveTurn({
              userId,
              caseId: command.caseId,
              expectedVersion: command.turnVersion,
              actionId: command.actionId,
              commandFingerprint: fingerprint,
              turn: next.turn,
              evidence,
              validationReceipt: next.receipt,
              privateCandidate,
            });
            return publicTurn(saved);
          }

          const phase = gatedPacket.candidate.status === "ready_for_confirmation"
            ? "final" as const
            : "intermediate" as const;
          const narrative = await generateRectificationNarrative({
            phase,
            packet: gatedPacket,
            generator: ports.narrativeGenerator,
            context: narrativeConversationContext({
              latestUserText: command.answer,
              allEvidence: [...current.eventEvidence, ...evidence],
              newEvidence: evidence,
            }),
          });
          if (narrative.fallbackUsed) {
            const next = nonScoringTurn({
              current,
              newEvidence: evidence,
              domain: command.domain,
              directionChange: false,
              correctionReset: {
                packet: gatedPacket,
                reason: "validation_fallback",
              },
            });
            const privateCandidate = privateCandidateFromPacket({
              packet: gatedPacket,
              resultId: null,
              iteration: (current.privateCandidate.workingState?.iteration ?? 0) + 1,
              forceCollecting: true,
            });
            const saved = await ports.store.saveTurn({
              userId,
              caseId: command.caseId,
              expectedVersion: command.turnVersion,
              actionId: command.actionId,
              commandFingerprint: fingerprint,
              turn: next.turn,
              evidence,
              validationReceipt: narrative.validationReceipt,
              privateCandidate,
            });
            return publicTurn(saved);
          }
          const privateCandidate = privateCandidateFromPacket({
            packet: gatedPacket,
            resultId: gatedPacket.candidate.status === "ready_for_confirmation"
              ? computed.resultId
              : null,
            iteration: (current.privateCandidate.workingState?.iteration ?? 0) + 1,
            forceCollecting: gatedPacket.candidate.status !== "ready_for_confirmation",
          });
          const turn = turnFromNarrative({
            caseId: command.caseId,
            turnVersion: command.turnVersion + 1,
            pendingConsultationQuestion: current.pendingConsultationQuestion,
            packet: gatedPacket,
            narrative,
            evidence: [...current.eventEvidence, ...evidence],
          });
          const saved = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn,
            evidence,
            validationReceipt: narrative.validationReceipt,
            privateCandidate,
          });
          return publicTurn(saved);
        } catch (error) {
          throw safeFailure(error);
        }
      }
      if (directionChange || scoreableEvidence.length === 0) {
        const next = nonScoringTurn({
          current,
          newEvidence: evidence,
          domain: command.domain,
          directionChange,
        });
        try {
          const saved = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: next.turn,
            evidence,
            validationReceipt: next.receipt,
            privateCandidate: current.privateCandidate,
          });
          return publicTurn(saved);
        } catch (error) {
          throw safeFailure(error);
        }
      }

      try {
        const computed = await ports.buildTechnicalPacket({
          userId,
          caseId: command.caseId,
          asOfDate: ports.asOfDate(),
          declaredBirthInput: current.declaredBirthInput,
          privateCandidate: current.privateCandidate,
          evidence: allScoreable,
        });
        const gatedPacket = confirmationGatedPacket(
          computed.packet,
          allScoreable.length,
        );
        const phase = gatedPacket.candidate.status === "ready_for_confirmation"
          ? "final" as const
          : "intermediate" as const;
        const narrative = await generateRectificationNarrative({
          phase,
          packet: gatedPacket,
          generator: ports.narrativeGenerator,
          context: narrativeConversationContext({
            latestUserText: command.answer,
            allEvidence: [...current.eventEvidence, ...evidence],
            newEvidence: evidence,
          }),
        });
        const plateauCount = nextPlateauCount(current.privateCandidate, gatedPacket);
        const completionReason = rangeCompletionReason({
          packet: gatedPacket,
          scoreableEventCount: allScoreable.length,
          plateauCount,
          unansweredSuggestedDomainCount: unansweredEvidenceDomains(
            gatedPacket,
            [...current.eventEvidence, ...evidence],
          ).length,
        });
        const narrativeWithProgress = {
          ...narrative,
          narrative: evidenceProgressNarrative({
            previousCandidate: current.privateCandidate,
            packet: gatedPacket,
            newEvidence: evidence,
            allEvidence: [...current.eventEvidence, ...evidence],
            scoreableEventCount: allScoreable.length,
            willContinue: completionReason === null
              && gatedPacket.candidate.status !== "ready_for_confirmation",
            authoredNarrative: narrative.fallbackUsed ? null : narrative.narrative,
          }),
          output: {
            ...narrative.output,
            evidenceRequest: evidenceRequestForProgress({
              packet: gatedPacket,
              evidence: [...current.eventEvidence, ...evidence],
              willContinue: completionReason === null
                && gatedPacket.candidate.status !== "ready_for_confirmation",
            }),
          },
        } satisfies RectificationNarrativeResult;
        const privateCandidate = privateCandidateFromPacket({
          packet: gatedPacket,
          resultId: gatedPacket.candidate.status === "ready_for_confirmation"
            ? computed.resultId
            : null,
          iteration: (current.privateCandidate.workingState?.iteration ?? 0) + 1,
          notes: convergenceNotes(current.privateCandidate, plateauCount),
          forceCollecting: gatedPacket.candidate.status !== "ready_for_confirmation",
        });
        const narratedTurn = turnFromNarrative({
          caseId: command.caseId,
          turnVersion: command.turnVersion + 1,
          pendingConsultationQuestion: current.pendingConsultationQuestion,
          packet: gatedPacket,
          narrative: narrativeWithProgress,
          evidence: [...current.eventEvidence, ...evidence],
        });
        const turn = completionReason
          ? completedRangeTurn(narratedTurn, completionReason)
          : narratedTurn;
        const saved = await ports.store.saveTurn({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn,
          evidence,
          validationReceipt: narrative.validationReceipt,
          privateCandidate,
        });
        return publicTurn(saved);
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async pause(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("pause", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "pause", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "paused") {
        try {
          const replayed = await ports.store.pause({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          });
          return publicTurn(replayed);
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      if (current.status !== "active" && current.status !== "confirming") {
        throw new ConversationalRectificationError("invalid_transition");
      }
      const next = changedTurn({
        current,
        status: "paused",
        narrative: boundedNarrative(current.latestTurn.narrative, "校正已暂停，现有证据和候选已保存；继续时不会重复扣点。"),
      });
      try {
        return publicTurn(await ports.store.pause({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async abandon(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("abandon", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "abandon", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "abandoned") {
        try {
          return publicTurn(await ports.store.abandon({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          }));
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      requireMutable(current);
      const next = changedTurn({
        current,
        status: "abandoned",
        narrative: boundedNarrative(current.latestTurn.narrative, "本次校正已放弃；再次校正期间原有确认时间始终没有被替换。"),
      });
      try {
        return publicTurn(await ports.store.abandon({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async confirm(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("confirm", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "confirm", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "completed") {
        const resultId = current.privateCandidate.resultId;
        if (!resultId) throw new ConversationalRectificationError("candidate_changed");
        try {
          return publicTurn(await ports.store.confirm({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            resultId,
            time: command.time,
            calculationVersion: current.privateCandidate.calculationVersion,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          }));
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      const resultId = current.privateCandidate.resultId;
      if (current.status !== "confirming"
        || current.latestTurn.candidate.status !== "ready_for_confirmation"
        || !resultId
        || current.privateCandidate.representativeTime !== command.time
        || current.latestTurn.candidate.representativeTime !== command.time) {
        throw new ConversationalRectificationError("candidate_changed");
      }
      const next = changedTurn({
        current,
        status: "completed",
        narrative: boundedNarrative(
          current.latestTurn.narrative,
          current.pendingConsultationQuestion
            ? "你已明确确认这个候选时间。现在可以使用新确认时间继续回答原问题。"
            : "你已明确确认这个候选时间，账户当前排盘时间已原子更新。",
        ),
      });
      try {
        return publicTurn(await ports.store.confirm({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          resultId,
          time: command.time,
          calculationVersion: current.privateCandidate.calculationVersion,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },
  });
  telemetryOutcomes.set(service, () => lastTelemetryOutcome);
  return service;
}
