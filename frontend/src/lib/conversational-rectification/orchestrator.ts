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
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";
import {
  convergenceNotes,
  MINIMUM_SCOREABLE_EVENTS,
  nextPlateauCount,
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
  regenerate(userId: string, command: CommandOf<"regenerate">): Promise<ConversationalRectificationTurn>;
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
const contextualRelativeMonthPattern = /(?:来年|次年|第二年|翌年|同年|当年|那年)\s*(\d{1,2})\s*月份?/;
const contextualBareMonthDayPattern = /^\s*(\d{1,2})\s*月\s*(\d{1,2})\s*(?:日|号)\s*[。.]?\s*$/;
const contextualBareDayPattern = /^\s*(\d{1,2})\s*(?:日|号)\s*[。.]?\s*$/;

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

function evidencePostdatesAsOfDate(
  evidence: Pick<LifeEventEvidence, "dateValue" | "datePrecision">,
  asOfDate: string,
): boolean {
  if (!evidence.dateValue) return false;
  const boundary = evidence.datePrecision === "year"
    ? asOfDate.slice(0, 4)
    : evidence.datePrecision === "month"
      ? asOfDate.slice(0, 7)
      : evidence.datePrecision === "day"
        ? asOfDate
        : null;
  return boundary !== null && evidence.dateValue > boundary;
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
  readonly type: "answer" | "regenerate" | "pause" | "abandon" | "confirm";
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

function sameDeclaredBirthInput(
  left: unknown,
  right: unknown,
): boolean {
  const leftParsed = declaredBirthInputSchema.safeParse(left);
  const rightParsed = declaredBirthInputSchema.safeParse(right);
  return leftParsed.success
    && rightParsed.success
    && stableJson(leftParsed.data) === stableJson(rightParsed.data);
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey))
      .map(([key, nested]) => `${JSON.stringify(key)}:${stableJson(nested)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
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

function normalizedEventSemantics(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("zh-CN")
    .replace(/^(?:我|本人|其实|准确(?:的是)?|更正(?:为|成|：|:)*)+/u, "")
    .replace(/[\p{P}\p{S}\s]+/gu, "");
}

function uniqueScoreableLifeEventEvidence(
  evidence: ReadonlyArray<LifeEventEvidenceInput>,
  birthDate: string,
): ReadonlyArray<LifeEventEvidenceInput> {
  const seen = new Set<string>();
  return effectiveLifeEventEvidence(evidence)
    .filter((item) => item.scoreable === true
      && item.extractionStatus !== "needs_clarification"
      && !evidencePredatesBirthDate(item, birthDate))
    .filter((item) => {
      const identity = [
        item.dateValue ?? "",
        item.domain,
        normalizedEventSemantics(item.eventSummary),
      ].join("|");
      if (seen.has(identity)) return false;
      seen.add(identity);
      return true;
    });
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
      id: item.id,
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
        followUp: input.narrative.output.evidenceRequest.followUp,
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

type CorrectionResetReason =
  | "needs_clarification"
  | "non_scoreable"
  | "direction_change";

function nonScoringTurn(input: {
  readonly current: LoadedConversationalRectificationCase;
  readonly newEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  readonly latestUserText: string;
  readonly authoredNarrative?: RectificationNarrativeResult | null;
  readonly correctionReset?: Readonly<{
    packet: RectificationTechnicalPacket;
    reason: CorrectionResetReason;
  }>;
}): { readonly turn: ConversationalRectificationTurn; readonly receipt: ValidationReceipt } {
  const allEvidence = [...input.current.eventEvidence, ...input.newEvidence];
  const latestIncomplete = input.newEvidence
    .filter((item) => item.extractionStatus === "needs_clarification")
    .at(-1);
  const authoredNarrative = input.authoredNarrative;
  const latestSummary = input.newEvidence.at(-1)?.eventSummary;
  const fallbackSubject = latestSummary && latestSummary !== "事件内容待补充"
    ? latestSummary
    : input.latestUserText.trim().slice(0, 80);
  const narrative = authoredNarrative?.narrative
    ?? `我收到了你这轮关于“${fallbackSubject || "这段经历"}”的补充，但这次分析暂时没有完成。内容会保留，你可以继续补充它的时间和经过，或直接说下一件已经发生的经历。`;
  const status = input.correctionReset
    ? "active" as const
    : input.current.status === "confirming" ? "confirming" as const : "active" as const;
  const actions = actionsFor(status);
  const clarificationFollowUp = latestIncomplete?.dateValue === null
    && latestIncomplete.eventSummary !== "事件内容待补充"
    ? { kind: "event_date" as const, evidenceId: latestIncomplete.id }
    : latestIncomplete?.dateValue
      && latestIncomplete.eventSummary === "事件内容待补充"
      ? { kind: "event_detail" as const, evidenceId: latestIncomplete.id }
      : null;
  const authoredRequest = authoredNarrative?.output.evidenceRequest;
  const priorRequest = input.current.latestTurn.evidenceRequest;
  const evidenceRequest = status === "confirming" && priorRequest === null
    ? null
    : authoredRequest
      ? {
          domains: authoredRequest.domains,
          datePrecision: authoredRequest.datePrecision,
          freeTextAllowed: true as const,
          followUp: clarificationFollowUp ?? authoredRequest.followUp,
        }
      : priorRequest
        ? {
            ...priorRequest,
            followUp: clarificationFollowUp ?? priorRequest.followUp,
          }
        : null;
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
    receipt: authoredNarrative
      ? validationReceiptSchema.parse(authoredNarrative.validationReceipt)
      : validationReceiptSchema.parse({
          modelId: "deterministic-evidence-failure-continuation",
          schemaValidated: false,
          validatorVersion: transitionValidatorVersion,
          retryCount: 0,
          fallbackUsed: true,
          issues: ["technical_or_narrative_generation_failed"],
        }),
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

  function contextualizedAnswer(
    command: CommandOf<"answer">,
    current: LoadedConversationalRectificationCase,
  ): string {
    const followUp = current.latestTurn.evidenceRequest?.followUp;
    if (followUp?.kind !== "event_date" && followUp?.kind !== "event_detail") {
      return command.answer;
    }
    const activeEvidence = effectiveLifeEventEvidence(current.eventEvidence);
    const target = followUp.evidenceId
      ? activeEvidence.find((item) => item.id === followUp.evidenceId)
      : null;
    const anchor = target?.dateValue
      ? target
      : activeEvidence.filter((item) => item.dateValue !== null).at(-1);
    const anchorYear = Number(anchor?.dateValue?.slice(0, 4));
    if (!Number.isInteger(anchorYear)) return command.answer;

    const bareMonthDay = followUp.kind === "event_date"
      ? command.answer.match(contextualBareMonthDayPattern)
      : null;
    if (bareMonthDay) {
      return `${anchorYear}年${Number(bareMonthDay[1])}月${Number(bareMonthDay[2])}号`;
    }
    const bareDay = followUp.kind === "event_date"
      ? command.answer.match(contextualBareDayPattern)
      : null;
    const anchorMonth = Number(anchor?.dateValue?.slice(5, 7));
    if (bareDay && Number.isInteger(anchorMonth)) {
      return `${anchorYear}年${anchorMonth}月${Number(bareDay[1])}号`;
    }

    const match = command.answer.match(contextualRelativeMonthPattern);
    if (!match) return command.answer;
    const month = Number(match[1]);
    if (month < 1 || month > 12) return command.answer;
    const sameYear = /(?:同年|当年|那年)/.test(match[0]);
    return command.answer.replace(match[0], `${sameYear ? anchorYear : anchorYear + 1}年${month}月`);
  }

  async function extractedEvidence(
    command: CommandOf<"answer">,
    current: LoadedConversationalRectificationCase,
  ): Promise<readonly LifeEventEvidence[]> {
    let extracted: readonly LifeEventEvidence[];
    try {
      const answerForExtraction = contextualizedAnswer(command, current);
      extracted = extractLifeEventEvidence({
        rawText: answerForExtraction,
        sourceTurnId: command.actionId,
        asOfDate: ports.asOfDate(),
        correctsEvidenceId: command.correctsEvidenceId,
      }).map((item) => ({
        ...item,
        rawText: command.answer,
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
    const ambiguous = extracted.length === 1 && extracted[0]?.domain === "other"
      ? extracted[0]
      : null;
    if (ambiguous && ports.narrativeGenerator.classifyEvidenceDomain) {
      try {
        const domain = await ports.narrativeGenerator.classifyEvidenceDomain({
          text: command.answer,
          recentEvidence: effectiveLifeEventEvidence(current.eventEvidence).slice(-6).map((item) => ({
            summary: item.eventSummary,
            domain: item.domain,
          })),
        }, { signal: AbortSignal.timeout(8_000) });
        if (domain && domain !== "other") {
          return [{ ...ambiguous, domain }];
        }
      } catch {
        // Semantic classification is advisory. Keep the deterministic fallback
        // instead of blocking the user's event when the model is unavailable.
      }
    }
    return extracted;
  }

  function completeLatestClarification(input: Readonly<{
    command: CommandOf<"answer">;
    current: LoadedConversationalRectificationCase;
    extracted: readonly LifeEventEvidence[];
  }>): readonly LifeEventEvidence[] {
    if (input.command.correctsEvidenceId || input.extracted.length !== 1) return input.extracted;
    const activeEvidence = effectiveLifeEventEvidence(input.current.eventEvidence);
    const declaredFollowUp = input.current.latestTurn.evidenceRequest?.followUp;
    const supplied = input.extracted[0];
    if (declaredFollowUp?.kind === "new_event") return input.extracted;
    const followUp = declaredFollowUp;
    const pending = followUp?.evidenceId
      ? activeEvidence.find((item) => item.id === followUp.evidenceId)
      : activeEvidence.filter((item) => item.extractionStatus === "needs_clarification").at(-1);
    if (!pending || !supplied) return input.extracted;

    const pendingHasSummary = pending.eventSummary !== "事件内容待补充";
    const suppliedHasSummary = supplied.eventSummary !== "事件内容待补充";
    const suppliedMatchesPending = !suppliedHasSummary
      || supplied.domain === "other"
      || supplied.domain === pending.domain;
    const fillsMissingDate = followUp?.kind !== "event_detail"
      && pending.dateValue === null
      && supplied.dateValue !== null
      && !evidencePostdatesAsOfDate(supplied, ports.asOfDate())
      && pendingHasSummary
      && suppliedMatchesPending;
    const refinesKnownDate = followUp?.kind === "event_date"
      && pending.dateValue !== null
      && supplied.dateValue !== null
      && supplied.dateValue.startsWith(`${pending.dateValue}-`)
      && !evidencePostdatesAsOfDate(supplied, ports.asOfDate())
      && pendingHasSummary
      && suppliedMatchesPending;
    const fillsMissingSummary = followUp?.kind !== "event_date"
      && pending.dateValue !== null
      && supplied.dateValue === null
      && !pendingHasSummary
      && suppliedHasSummary;
    const addsEventDetail = followUp?.kind === "event_detail"
      && pending.dateValue !== null
      && suppliedHasSummary
      && (supplied.dateValue === null || supplied.dateValue === pending.dateValue);
    if (!fillsMissingDate && !refinesKnownDate && !fillsMissingSummary && !addsEventDetail) {
      return input.extracted;
    }

    const dateValue = supplied.dateValue ?? pending.dateValue;
    const summary = fillsMissingDate || refinesKnownDate
      ? pending.eventSummary
      : addsEventDetail
      ? [...new Set([pending.eventSummary, supplied.eventSummary])].join("；")
      : suppliedHasSummary ? supplied.eventSummary : pending.eventSummary;
    if (!dateValue || summary === "事件内容待补充") return input.extracted;
    // Re-parse the original event as one dated sentence. Detail replies may
    // contain punctuation that the extractor treats as separate boundaries;
    // apply the composed summary after deriving the single event metadata.
    const merged = extractLifeEventEvidence({
      rawText: `${dateValue} ${pending.eventSummary}`,
      sourceTurnId: input.command.actionId,
      asOfDate: ports.asOfDate(),
      correctsEvidenceId: pending.id,
    });
    if (merged.length !== 1) return input.extracted;
    return merged.map((item) => ({
      ...item,
      rawText: `${pending.rawText}\n补充：${input.command.answer}`,
      eventSummary: summary,
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

      // A new action id is not a new rectification session. The durable
      // reserve RPC rejects a second unfinished case for the same account,
      // so resolve that invariant before spending time or credits. This is
      // intentionally limited to the same declared birth input; a changed
      // profile must not silently continue an old calculation.
      let existingForUser: LoadedConversationalRectificationCase | null;
      try {
        existingForUser = await ports.store.loadCase({ userId });
      } catch (error) {
        throw safeFailure(error);
      }
      if (existingForUser && existingForUser.caseId !== caseId) {
        observeCase(existingForUser);
        if (sameDeclaredBirthInput(existingForUser.declaredBirthInput, declared.data)) {
          return publicTurn(existingForUser);
        }
        throw new ConversationalRectificationError("action_conflict");
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
        const failure = safeFailure(error);
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
        // A concurrent start can win between the account-level read above
        // and the reserve/create RPC. Re-read the account after releasing our
        // reservation and return the winner when it uses the same profile.
        if (failure.code === "action_conflict") {
          try {
            const winner = await ports.store.loadCase({ userId });
            if (winner && sameDeclaredBirthInput(winner.declaredBirthInput, declared.data)) {
              observeCase(winner);
              return publicTurn(winner);
            }
          } catch {
            // Preserve the original stable conflict below.
          }
        }
        throw failure;
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
          extracted: await extractedEvidence(command, current),
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
      const allScoreable = uniqueScoreableLifeEventEvidence(
        [...current.eventEvidence, ...evidence],
        current.declaredBirthInput.birthDate,
      );

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
            const authoredNarrative = await generateRectificationNarrative({
              phase: "intermediate",
              packet: gatedPacket,
              generator: ports.narrativeGenerator,
              context: narrativeConversationContext({
                latestUserText: command.answer,
                allEvidence: [...current.eventEvidence, ...evidence],
                newEvidence: evidence,
              }),
            });
            const next = nonScoringTurn({
              current,
              newEvidence: evidence,
              latestUserText: command.answer,
              authoredNarrative,
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
        let authoredNarrative: RectificationNarrativeResult | null = null;
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
          authoredNarrative = await generateRectificationNarrative({
            phase: "intermediate",
            packet: gatedPacket,
            generator: ports.narrativeGenerator,
            context: narrativeConversationContext({
              latestUserText: command.answer,
              allEvidence: [...current.eventEvidence, ...evidence],
              newEvidence: evidence,
            }),
          });
        } catch (error) {
          console.warn("[rectification-non-scoring-narrative-fallback]", JSON.stringify({
            error: error instanceof Error ? error.name : "UnknownError",
          }));
        }
        const next = nonScoringTurn({
          current,
          newEvidence: evidence,
          latestUserText: command.answer,
          authoredNarrative,
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
          narrative,
          evidence: [...current.eventEvidence, ...evidence],
        });
        const saved = await ports.store.saveTurn({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn: narratedTurn,
          evidence,
          validationReceipt: narrative.validationReceipt,
          privateCandidate,
        });
        return publicTurn(saved);
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async regenerate(userId, rawCommand) {
      resetTelemetryOutcome();
      const command = parseCommand("regenerate", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "save_turn", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      requireMutable(current);
      requireExactVersion(current, command.turnVersion);
      if (!current.latestTurn.actions.includes("answer")) {
        throw new ConversationalRectificationError("invalid_transition");
      }

      try {
        const activeEvidence = effectiveLifeEventEvidence(current.eventEvidence);
        const latestEvidence = activeEvidence.at(-1);
        const scoreableEvidence = uniqueScoreableLifeEventEvidence(
          current.eventEvidence,
          current.declaredBirthInput.birthDate,
        );
        const computed = await ports.buildTechnicalPacket({
          userId,
          caseId: command.caseId,
          asOfDate: ports.asOfDate(),
          declaredBirthInput: current.declaredBirthInput,
          privateCandidate: current.privateCandidate,
          evidence: scoreableEvidence,
          preserveCandidateRange: true,
        });
        const gatedPacket = confirmationGatedPacket(computed.packet, scoreableEvidence.length);
        const phase = gatedPacket.candidate.status === "ready_for_confirmation"
          ? "final" as const
          : activeEvidence.length === 0 ? "first" as const : "intermediate" as const;
        const narrative = await generateRectificationNarrative({
          phase,
          packet: gatedPacket,
          generator: ports.narrativeGenerator,
          context: latestEvidence ? narrativeConversationContext({
            latestUserText: latestEvidence.rawText,
            allEvidence: current.eventEvidence,
            newEvidence: [latestEvidence],
          }) : undefined,
        });
        const turn = turnFromNarrative({
          caseId: command.caseId,
          turnVersion: command.turnVersion + 1,
          pendingConsultationQuestion: current.pendingConsultationQuestion,
          packet: gatedPacket,
          narrative,
          evidence: current.eventEvidence,
        });
        const saved = await ports.store.saveTurn({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn,
          evidence: [],
          validationReceipt: narrative.validationReceipt,
          privateCandidate: current.privateCandidate,
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
        narrative: current.latestTurn.narrative,
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
        narrative: current.latestTurn.narrative,
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
        narrative: current.latestTurn.narrative,
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
