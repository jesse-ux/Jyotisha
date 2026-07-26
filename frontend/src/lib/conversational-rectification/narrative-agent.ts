import { z } from "zod";
import {
  rectificationFollowUpSchema,
  type RectificationFollowUp,
} from "./contracts.ts";
import {
  projectRectificationTechnicalPacket,
  type RectificationEvidenceDomain,
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";

export type RectificationNarrativePhase = "first" | "intermediate" | "final";

export type RectificationConversationMessage = Readonly<{
  role: "assistant" | "user";
  text: string;
}>;

export type RectificationNarrativeContext = Readonly<{
  recentConversation?: ReadonlyArray<RectificationConversationMessage>;
  latestUserText?: string;
  previousAssistantNarrative?: string;
  previousEvidencePrompt?: string;
  previousFollowUp?: RectificationFollowUp;
  latestEvidence?: ReadonlyArray<{
    id?: string;
    dateLabel: string;
    summary: string;
    domain: RectificationEvidenceDomain;
  }>;
  eventLedger?: ReadonlyArray<{
    id: string;
    rawText: string;
    dateLabel: string;
    summary: string;
    domain: RectificationEvidenceDomain;
    extractionStatus: "clear" | "needs_clarification" | "corrected";
    active: boolean;
    correctsEvidenceIds: readonly string[];
  }>;
  unresolvedEvidence?: ReadonlyArray<{
    id: string;
    rawText: string;
    summary: string;
    domain: RectificationEvidenceDomain;
    dateLabel: string;
  }>;
}>;

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const modelIdSchema = z.string().trim().min(1).max(120);
const validatorVersion = "rectification-narrative-grounding-v2";
// Keep the complete route within its 60 second platform budget. The first
// attempt gets enough time for the richer model, while the second is a short,
// independent recovery attempt that production routes to the Flash model.
const narrativeAttemptTimeoutMs = [38_000, 14_000] as const;
const domainSchema = z.enum(["career", "education", "finance", "health_pressure", "relocation", "relationship", "family", "other"]);
export const rectificationEvidenceDomainOutputSchema = z.object({
  domain: domainSchema,
}).strict();
const broadYearRangePattern = /(?:19|20)\d{2}\s*年?\s*(?:[-–—~～至到\/]|\.\.)\s*(?:19|20)\d{2}\s*年?/i;
const proposedYearAlternativesPattern = /(?:19|20)\d{2}\s*年?\s*(?:还是|或者|或是|或|、|,|，)\s*(?:19|20)\d{2}\s*年?/i;
const choiceQuestionPattern = /(?:哪(?:一|个)?(?:年|年份|年代|时间段|区间|时期)|哪个时间段|还是|选择|选项|更符合|更匹配|A\s*[.、:：)]|B\s*[.、:：)]|which\s+(?:year|period|range)|options?)/i;
const labeledYearChoicesPattern = /A\s*[.、:：)]?[\s\S]{0,80}(?:19|20)\d{2}\s*年?[\s\S]{0,120}B\s*[.、:：)]?[\s\S]{0,80}(?:19|20)\d{2}\s*年?/i;
const affirmativeAnswerPattern = /^\s*(?:是(?:的)?|对(?:的)?|没错|正确|确认|就是|嗯+|没问题)\s*[。.!！,，]?\s*$/u;
const negativeAnswerPattern = /^\s*(?:不是|不对|错了|并不是|否)\s*[。.!！,，]?\s*$/u;
const proposedDateQuestionPattern = /(?:19|20)\d{2}\s*年(?:\s*(?:1[0-2]|0?[1-9])\s*月)?(?:\s*(?:3[01]|[12]\d|0?[1-9])\s*(?:日|号))?[\s\S]{0,30}(?:吗|是否|是不是|确认|对不对|正确)/u;
const domainLabels = {
  career: "事业",
  education: "学业",
  finance: "财富",
  health_pressure: "健康与重大压力",
  relocation: "迁居",
  relationship: "关系",
  family: "家庭",
  other: "其他",
} as const satisfies Readonly<Record<RectificationEvidenceDomain, string>>;
export const rectificationNarrativeOutputSchema = z.object({
  narrative: z.string().trim().min(1).max(12_000),
  candidateStatus: z.enum(["pending_validation", "ready_for_confirmation"]),
  representativeTime: timeSchema,
  rangeStart: timeSchema,
  rangeEnd: timeSchema,
  useBoundary: z.string().trim().min(1).max(1_000),
  stableLayers: z.array(z.string().trim().min(1)).max(20),
  sensitiveLayers: z.array(z.string().trim().min(1)).max(20),
  referenceIds: z.array(z.string().trim().min(1)).max(80),
  domainReasons: z.array(z.object({
    domain: domainSchema,
    layer: z.string().trim().min(1),
    reason: z.string().trim().min(8).max(1_000),
  }).strict()).max(6),
  evidenceRequest: z.object({
    domains: z.array(domainSchema).min(1).max(4),
    datePrecision: z.enum(["month_preferred", "year_accepted"]),
    prompt: z.string().trim().min(1).max(1_000),
    followUp: rectificationFollowUpSchema.default({ kind: "new_event", evidenceId: null }),
  }).strict().nullable(),
}).strict();

export const rectificationNarrativeAuthoredOutputSchema = z.object({
  narrative: z.string().trim().min(1).max(12_000),
  evidenceRequest: z.object({
    // Domain routing is private scoring metadata. Older providers may still
    // return it, but the server always replaces it from the technical packet.
    domains: z.array(domainSchema).min(1).max(4).optional(),
    datePrecision: z.enum(["month_preferred", "year_accepted"]),
    prompt: z.string().trim().min(1).max(1_000),
    followUp: rectificationFollowUpSchema.default({ kind: "new_event", evidenceId: null }),
  }).strict().nullable(),
}).strict();

// Callers may construct a pre-parse model payload without the defaulted
// follow-up field; parsed runtime output always receives the schema default.
export type RectificationNarrativeModelOutput = z.input<typeof rectificationNarrativeOutputSchema>;

export type NarrativeValidation = {
  readonly valid: boolean;
  readonly issues: readonly string[];
};

export interface RectificationNarrativeGenerator {
  readonly modelId: string;
  classifyEvidenceDomain?(
    input: Readonly<{
      text: string;
      recentEvidence: readonly Readonly<{
        summary: string;
        domain: RectificationEvidenceDomain;
      }>[];
    }>,
    options?: Readonly<{ signal?: AbortSignal }>,
  ): Promise<RectificationEvidenceDomain | null>;
  generate(
    prompt: string,
    options?: Readonly<{ signal?: AbortSignal; attempt?: 1 | 2 }>,
  ): Promise<{ readonly text: string; readonly modelId?: string }>;
}

export type RectificationNarrativeResult = {
  readonly narrative: string;
  readonly output: RectificationNarrativeModelOutput;
  readonly attempts: 1 | 2;
  readonly fallbackUsed: boolean;
  readonly allowEvidenceScoringAdvance: boolean;
  readonly validationReceipt: {
    readonly modelId: string;
    readonly schemaValidated: boolean;
    readonly validatorVersion: string;
    readonly retryCount: 0 | 1;
    readonly fallbackUsed: boolean;
    readonly issues: readonly string[];
  };
};

function unique<T extends string>(values: readonly T[]): T[] {
  return [...new Set(values)];
}

function groundedEvidenceDomains(
  requested: readonly RectificationEvidenceDomain[] | undefined,
  packet: RectificationTechnicalPacket,
): RectificationEvidenceDomain[] {
  const suggested = packet.suggestedDomains.slice(0, 4).map((item) => item.domain);
  if (!requested?.length) return suggested;
  const allowed = new Set(suggested);
  const grounded = unique(requested.filter((domain) => allowed.has(domain)));
  return grounded.length > 0 ? grounded : suggested;
}

function groundedEvidenceRequest(
  request: z.infer<typeof rectificationNarrativeAuthoredOutputSchema>["evidenceRequest"],
  packet: RectificationTechnicalPacket,
) {
  if (request === null) return null;
  const domains = groundedEvidenceDomains(request.domains, packet);
  return domains.length > 0 ? { ...request, domains } : null;
}

function completeAuthoredOutput(
  output: z.infer<typeof rectificationNarrativeAuthoredOutputSchema>,
  packet: RectificationTechnicalPacket,
): RectificationNarrativeModelOutput {
  const evidenceRequest = groundedEvidenceRequest(output.evidenceRequest, packet);
  return {
    ...output,
    evidenceRequest,
    candidateStatus: packet.candidate.status,
    representativeTime: packet.candidate.representativeTime,
    rangeStart: packet.candidate.range.startTime,
    rangeEnd: packet.candidate.range.endTime,
    useBoundary: packet.useBoundary,
    stableLayers: packet.stableLayers.map((item) => item.layer),
    sensitiveLayers: packet.sensitiveLayers.map((item) => item.layer),
    referenceIds: [],
    domainReasons: packet.suggestedDomains.map((item) => ({ ...item })),
  };
}

function parseModelOutput(
  text: string,
  packet: RectificationTechnicalPacket,
): RectificationNarrativeModelOutput {
  const normalized = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const start = normalized.indexOf("{");
  const end = normalized.lastIndexOf("}");
  if (start < 0 || end <= start) throw new TypeError("narrative output is not JSON");
  const parsed: unknown = JSON.parse(normalized.slice(start, end + 1));
  const legacy = rectificationNarrativeOutputSchema.safeParse(parsed);
  if (legacy.success) {
    return {
      ...legacy.data,
      // The next conversational topic is authored by the model, but the
      // scoring-domain allowlist remains server-owned. If no grounded routing
      // domain exists, keep the prose and omit only the optional follow-up state.
      evidenceRequest: groundedEvidenceRequest(legacy.data.evidenceRequest, packet),
    };
  }
  return completeAuthoredOutput(rectificationNarrativeAuthoredOutputSchema.parse(parsed), packet);
}

function narrativeTimes(value: string): string[] {
  return unique(value.match(/(?:[01]\d|2[0-3]):[0-5]\d/g) ?? []);
}

function narrativeLayers(value: string): string[] {
  return unique(value.match(/\bD\d{1,3}\b|\b(?:UL|A7|A10|KP_cusp)\b/g) ?? []);
}

function narrativeReferences(value: string): string[] {
  return [...value.matchAll(/【([^】]+)】/g)]
    .map((match) => match[1] ?? "")
    .filter(Boolean);
}

function isGenericBroadYearChoiceQuestionnaire(value: string): boolean {
  return proposedYearAlternativesPattern.test(value)
    || labeledYearChoicesPattern.test(value)
    || (choiceQuestionPattern.test(value) && broadYearRangePattern.test(value));
}

function proseFields(output: RectificationNarrativeModelOutput): readonly {
  readonly path: string;
  readonly value: string;
}[] {
  return [
    { path: "narrative", value: output.narrative },
    ...output.domainReasons.map((item, index) => ({
      path: `domainReasons[${index}].reason`,
      value: item.reason,
    })),
    ...(output.evidenceRequest
      ? [{ path: "evidenceRequest.prompt", value: output.evidenceRequest.prompt }]
      : []),
  ];
}

export function validateNarrativeAgainstPacket(
  output: RectificationNarrativeModelOutput,
  packet: RectificationTechnicalPacket,
  phase: RectificationNarrativePhase = "first",
  context: RectificationNarrativeContext = {},
): NarrativeValidation {
  const issues: string[] = [];
  const candidate = packet.candidate;
  if (phase === "final" && output.evidenceRequest !== null) {
    issues.push("final narrative must not request more evidence");
  }
  if (output.candidateStatus !== candidate.status) {
    issues.push(`candidateStatus ${output.candidateStatus} is not packet-grounded`);
  }
  if (output.representativeTime !== candidate.representativeTime) {
    issues.push(`representativeTime ${output.representativeTime} is not packet-grounded`);
  }
  if (output.rangeStart !== candidate.range.startTime || output.rangeEnd !== candidate.range.endTime) {
    issues.push("candidate range is not packet-grounded");
  }
  if (output.useBoundary !== packet.useBoundary) issues.push("useBoundary is not packet-grounded");

  const allowedStable = packet.stableLayers.map((item) => item.layer);
  const allowedSensitive = packet.sensitiveLayers.map((item) => item.layer);
  for (const layer of output.stableLayers) {
    if (!allowedStable.includes(layer)) issues.push(`stable layer ${layer} is not packet-grounded`);
  }
  for (const layer of output.sensitiveLayers) {
    if (!allowedSensitive.includes(layer)) issues.push(`sensitive layer ${layer} is not packet-grounded`);
  }

  for (const reference of output.referenceIds) {
    if (!packet.referenceIds.includes(reference)) issues.push(`reference ${reference} is not packet-grounded`);
  }
  const allowedDomains = new Map(packet.suggestedDomains.map((item) => [item.domain, item.layer]));
  for (const reason of output.domainReasons) {
    if (allowedDomains.get(reason.domain) !== reason.layer) {
      issues.push(`domain reason ${reason.domain}/${reason.layer} is not packet-grounded`);
    }
  }
  if (output.evidenceRequest) {
    for (const domain of output.evidenceRequest.domains) {
      if (!allowedDomains.has(domain)) issues.push(`evidence domain ${domain} is not packet-grounded`);
    }
    const followUp = output.evidenceRequest.followUp;
    if (proposedDateQuestionPattern.test(output.evidenceRequest.prompt)
      && (followUp?.kind !== "event_date"
        || followUp.answerMode !== "yes_no"
        || !followUp.proposedDate)) {
      issues.push("date confirmation prompt lacks structured proposedDate");
    }
  }

  const previousFollowUp = context.previousFollowUp;
  const latestUserText = context.latestUserText ?? "";
  if (previousFollowUp?.kind === "event_date" && previousFollowUp.answerMode === "yes_no") {
    const nextRequest = output.evidenceRequest;
    if (affirmativeAnswerPattern.test(latestUserText)) {
      if (nextRequest?.followUp?.evidenceId === previousFollowUp.evidenceId) {
        issues.push("resolved follow-up still targets completed evidence");
      }
      if (context.previousEvidencePrompt
        && normalizedQuestion(nextRequest?.prompt ?? "") === normalizedQuestion(context.previousEvidencePrompt)) {
        issues.push("repeated resolved follow-up");
      }
    }
    if (negativeAnswerPattern.test(latestUserText)
      && nextRequest?.followUp?.evidenceId === previousFollowUp.evidenceId
      && nextRequest.followUp?.answerMode === "yes_no") {
      issues.push("repeated rejected follow-up");
    }
  }

  const allowedTimes = [candidate.representativeTime, candidate.range.startTime, candidate.range.endTime];
  const allowedLayers = [...allowedStable, ...allowedSensitive];
  for (const field of proseFields(output)) {
    const layers = narrativeLayers(field.value);
    for (const time of narrativeTimes(field.value)) {
      if (!allowedTimes.includes(time)) issues.push(`${field.path} time ${time} is not packet-grounded`);
    }
    for (const layer of layers) {
      if (!allowedLayers.includes(layer)) issues.push(`${field.path} layer ${layer} is not packet-grounded`);
    }
    for (const reference of narrativeReferences(field.value)) {
      if (!layers.includes(reference) && !packet.referenceIds.includes(reference)) {
        issues.push(`${field.path} reference ${reference} is not packet-grounded`);
      }
    }
    if (isGenericBroadYearChoiceQuestionnaire(field.value)) {
      issues.push(`${field.path} is a forbidden generic broad-year choice questionnaire`);
    }
  }
  const authoredEventTable = markdownSection(output.narrative, "### 事件验证表");
  if (authoredEventTable && /(?:\|\s*(?:得分|score)(?:\s*\/\s*状态)?\s*\||内部(?:分数|权重))/i.test(authoredEventTable)) {
    issues.push("event validation table exposes a private score or weight");
  }
  const uniqueIssues = unique(issues);
  return { valid: uniqueIssues.length === 0, issues: uniqueIssues };
}

function normalizedQuestion(value: string): string {
  return value
    .normalize("NFKC")
    .replace(/[\p{P}\p{S}\s]+/gu, "")
    .toLocaleLowerCase("zh-CN");
}

function grounding(packet: RectificationTechnicalPacket, phase: RectificationNarrativePhase) {
  const projected = projectRectificationTechnicalPacket(packet);
  const base = {
    calculationVersion: packet.calculationVersion,
    candidate: projected.candidate,
    useBoundary: packet.useBoundary,
    stableLayers: packet.stableLayers.map(({ layer }) => layer),
    sensitiveLayers: packet.sensitiveLayers.map(({ layer }) => layer),
  };
  if (phase === "first") return base;
  return {
    ...base,
    sensitivityScope: {
      rangeStart: projected.technicalReceipt.sensitivityScope.rangeStart,
      rangeEnd: projected.technicalReceipt.sensitivityScope.rangeEnd,
    },
    layerValues: {
      stable: packet.stableLayers.map(({ layer, values }) => ({ layer, values })),
      sensitive: packet.sensitiveLayers.map(({ layer, values }) => ({ layer, values })),
    },
    expertWorkflow: packet.expertWorkflow ? {
      boundary: packet.expertWorkflow.boundary,
      candidateWindows: packet.expertWorkflow.candidateWindows,
      techniqueStates: packet.expertWorkflow.techniqueAuditTable
        .filter((row) => phase === "final" || row.status === "used" || row.status === "partial")
        .map((row) => ({
        technique: row.technique,
        status: row.status,
        boundary: row.boundary,
      })),
      confirmationAllowed: phase === "final" ? packet.expertWorkflow.confirmationAllowed : undefined,
      hardBlockers: phase === "final" ? packet.expertWorkflow.hardBlockers : undefined,
    } : undefined,
  };
}

function narrativeConversationContext(context: RectificationNarrativeContext) {
  return {
    recentConversation: context.recentConversation?.slice(-40),
    latestUserText: context.latestUserText,
    previousAssistantNarrative: context.previousAssistantNarrative,
    previousEvidencePrompt: context.previousEvidencePrompt,
    previousFollowUp: context.previousFollowUp,
    latestEvidence: context.latestEvidence?.map(({ id, dateLabel, summary }) => ({
      id,
      dateLabel,
      summary,
    })),
    eventLedger: context.eventLedger?.map(({
      id,
      rawText,
      dateLabel,
      summary,
      extractionStatus,
      active,
      correctsEvidenceIds,
    }) => ({
      id,
      rawText,
      dateLabel,
      summary,
      extractionStatus,
      active,
      correctsEvidenceIds,
    })),
    unresolvedEvidence: context.unresolvedEvidence?.map(({ id, rawText, summary, dateLabel }) => ({
      id,
      rawText,
      summary,
      dateLabel,
    })),
  };
}

function boundedReceiptIssues(issues: readonly string[]): string[] {
  return issues
    .slice(0, 20)
    .map((issue) => issue.trim().slice(0, 240) || "narrative_mismatch");
}

type NarrativeDiagnosticIssueCode =
  | "candidate_status_mismatch"
  | "representative_time_mismatch"
  | "candidate_range_mismatch"
  | "use_boundary_mismatch"
  | "ungrounded_domain_reason"
  | "ungrounded_evidence_domain"
  | "broad_year_questionnaire"
  | "ungrounded_layer"
  | "ungrounded_reference"
  | "timeout"
  | "schema_invalid"
  | "generation_error"
  | "narrative_validation_failed";

function diagnosticIssueCodes(issues: readonly string[]): NarrativeDiagnosticIssueCode[] {
  const codes = issues.map((issue): NarrativeDiagnosticIssueCode => {
    if (issue.startsWith("candidateStatus ")) return "candidate_status_mismatch";
    if (issue.startsWith("representativeTime ")) return "representative_time_mismatch";
    if (issue === "candidate range is not packet-grounded") return "candidate_range_mismatch";
    if (issue === "useBoundary is not packet-grounded") return "use_boundary_mismatch";
    if (issue.startsWith("domain reason ")) return "ungrounded_domain_reason";
    if (issue.startsWith("evidence domain ")) return "ungrounded_evidence_domain";
    if (issue.includes("broad-year choice questionnaire")) return "broad_year_questionnaire";
    if (issue.includes(" layer ") || issue.startsWith("stable layer ") || issue.startsWith("sensitive layer ")) {
      return "ungrounded_layer";
    }
    if (issue.includes(" reference ") || issue.startsWith("reference ")) return "ungrounded_reference";
    if (issue === "TimeoutError" || issue === "AbortError") return "timeout";
    if (/^(?:root|[\w.]+):/.test(issue)) return "schema_invalid";
    if (/Error$/.test(issue) || issue === "NarrativeOutputError") return "generation_error";
    return "narrative_validation_failed";
  });
  return [...new Set(codes)];
}

function logNarrativeGeneration(input: Readonly<{
  phase: RectificationNarrativePhase;
  retryCount: 0 | 1;
  fallbackUsed: boolean;
  source: "model" | "model_retry" | "fallback" | "failed";
  issues: readonly string[];
  startedAt: number;
}>): void {
  const payload = {
    phase: input.phase,
    retryCount: input.retryCount,
    fallbackUsed: input.fallbackUsed,
    source: input.source,
    issueCodes: diagnosticIssueCodes(input.issues),
    elapsedMs: Math.max(0, Date.now() - input.startedAt),
  };
  if (input.fallbackUsed || input.source === "failed") {
    console.warn("[rectification-narrative]", JSON.stringify(payload));
    return;
  }
  console.info("[rectification-narrative]", JSON.stringify(payload));
}

function promptFor(
  phase: RectificationNarrativePhase,
  packet: RectificationTechnicalPacket,
  context: RectificationNarrativeContext,
  retryIssues: readonly string[] = [],
): string {
  if (phase === "first") {
    return JSON.stringify({
      task: "用自然、有人味的中文开启生时校正。用户可以按自己的节奏自由叙述，一次说一件或多件经历；自然回应即可，不必每轮提问，也不要使用固定模板。",
      phase,
      conversationContext: narrativeConversationContext(context),
      packet: grounding(packet, phase),
      output: "只返回 narrative 和 evidenceRequest。没有提出需要下一轮短答承接的明确问题时，evidenceRequest 必须为 null；若提出明确问题，可用 domains 作为不可见路由元数据，并包含 datePrecision、prompt、followUp。narrative 不得输出或讨论事件分类、领域标签，也不要重复输出候选状态、时间、分盘或引用字段。",
      safety: "技术事实只能来自 packet；不能确认未经验证的分钟；不得展示内部权重、分数、事件分类或内部路由元数据。",
      retryIssues: boundedReceiptIssues(retryIssues),
    });
  }
  return JSON.stringify({
    task: "write_grounded_rectification_narrative",
    phase,
    conversationContext: narrativeConversationContext(context),
    continuity: "recentConversation 是同一会话的真实连续问答。必须直接理解用户对上一条问题的确认、否认、补充或纠正，不得把“是的/对/来年/那次”等回复当成脱离上下文的新事件，也不得重复询问已经确认的信息。",
    packet: grounding(packet, phase),
    outputContract: {
      returnOnlyNarrativeAndEvidenceRequest: true,
      candidateFactsAreInjectedByServerAndMustNotBeRepeatedAsJsonFields: true,
      onlyListedLayersAndReferences: true,
      everyAuthoredTechnicalClaimMustBeGrounded: true,
      futureWindowsAreContextOnly: true,
      genericBroadYearRangeQuestionnaireForbidden: true,
      useExpertWorkflowAsTechniqueTruth: true,
      blockedOrNotEvaluatedTechniquesMustNeverBeClaimedAsUsed: true,
      technicalTablesMayAppearWhenRelevant: true,
      completeTechnicalTableSummaryRequiredBeforeConfirmation: phase === "final"
        && packet.candidate.status === "ready_for_confirmation",
      unchangedTechnicalTablesShouldNotBeRepeated: true,
      privateScoresAndCandidateWeightsMustNeverBeShown: true,
      internalEventDomainsAndRoutingMustNeverBeShown: true,
    },
    conversationGuidance: {
      freeConversation: phase !== "final",
      questionsAreOptional: phase !== "final",
      userControlsNarrativePace: phase !== "final",
      acceptMultipleEventsInOneMessage: phase !== "final",
      acknowledgeAndReflectBeforeAnyClarification: phase === "intermediate",
      doNotTurnEveryMessageIntoAQuestionnaire: phase !== "final",
      askOnlyWhenAClarificationWouldMateriallyHelpTheConversation: phase !== "final",
      neverMentionHowTheEventWasClassifiedOrLabeledInternally: phase === "intermediate",
      doNotVolunteerNotEvaluatedOrBlockedTechniqueInventory: phase === "intermediate",
      doNotRepeatCandidateBoundaryUnlessItChangedOrTheUserAsked: phase === "intermediate",
      resolveDateContradictionsBeforeScoring: phase === "intermediate",
      mergeSameEventDetailsWithoutDoubleCounting: phase === "intermediate",
      useEventLedgerToAvoidRepeatingAnsweredQuestions: phase === "intermediate",
      optionalFollowUpState: phase !== "final"
        ? "Only when narrative contains a clear question that expects a short next-turn answer, persist its exact intent. Use event_detail or event_date with an existing evidenceId. For a yes/no date proposal, set answerMode=yes_no and proposedDate={value,precision}; otherwise use answerMode=free_text and no proposedDate. Use new_event with null evidenceId only for a genuinely new event. Otherwise evidenceRequest must be null."
        : false,
      boundedResultBoundary: phase === "final" && packet.candidate.status === "pending_validation"
        ? "当前只支持候选范围，系统验证尚未闭环。本次不会替换当前排盘时间，也不再要求用户继续提供人生事件；evidenceRequest 必须为 null。"
        : false,
      domainReasonsMayBeNaturallyParaphrased: true,
    },
    retryIssues: boundedReceiptIssues(retryIssues),
  });
}

function fallbackNarrative(packet: RectificationTechnicalPacket, phase: RectificationNarrativePhase): string {
  const candidate = packet.candidate;
  const phaseLine = phase === "final" && candidate.status === "ready_for_confirmation"
    ? "当前证据已形成候选总结，但仍有残余不确定性；只有明确确认后才会替换当前排盘时间。"
    : phase === "final"
      ? "当前证据只能支持候选范围，系统验证尚未闭环；本次不会替换当前排盘时间，也不再强制追问更多人生事件。"
    : `我收到了这段叙述。你可以继续讲这段经历，也可以按自己的节奏说下一件想到的事。`;
  return [
    `当前仍在核对 ${candidate.range.startTime}–${candidate.range.endTime} 的候选范围，还不能把其中某一分钟当作确定出生时间。`,
    phaseLine,
  ].join("\n");
}

function fallbackOutput(
  packet: RectificationTechnicalPacket,
  phase: RectificationNarrativePhase,
): RectificationNarrativeModelOutput {
  return {
    narrative: fallbackNarrative(packet, phase),
    candidateStatus: packet.candidate.status,
    representativeTime: packet.candidate.representativeTime,
    rangeStart: packet.candidate.range.startTime,
    rangeEnd: packet.candidate.range.endTime,
    useBoundary: packet.useBoundary,
    stableLayers: packet.stableLayers.map((item) => item.layer),
    sensitiveLayers: packet.sensitiveLayers.map((item) => item.layer),
    referenceIds: [],
    domainReasons: packet.suggestedDomains.map((item) => ({ ...item })),
    evidenceRequest: null,
  };
}

function markdownCell(value: unknown): string {
  return String(value ?? "")
    .replace(/\|/g, "\\|")
    .replace(/\r?\n/g, " ")
    .trim() || "—";
}

function analysisTableSections(
  packet: RectificationTechnicalPacket,
  context: RectificationNarrativeContext,
): ReadonlyArray<{
  readonly heading: string;
  readonly header: string;
  readonly markdown: string;
}> {
  const workflow = packet.expertWorkflow;
  const techniqueRows = workflow?.techniqueAuditTable ?? [];
  const techniqueTable = [
    "### Technique Audit Table",
    "| 技法 | 状态 | 证据 | 使用边界 |",
    "|---|---|---|---|",
    ...(techniqueRows.length > 0
      ? techniqueRows.map((row) => (
          `| ${markdownCell(row.technique)} | ${markdownCell(row.status)} | ${markdownCell(row.evidence.join("、"))} | ${markdownCell(row.boundary)} |`
        ))
      : ["| — | 待评估 | 尚无可展示证据 | 不得声称已运行 |"]),
  ].join("\n");

  const scoreByEvidenceId = new Map(packet.scoredHistoricalEvidence.map((item) => [item.evidenceId, item]));
  const activeEvents = (context.eventLedger ?? []).filter((item) => item.active);
  const eventTable = [
    "### 事件验证表",
    "| 时间 | 事件 | 领域 | 验证状态 | 结论 |",
    "|---|---|---|---|---|",
    ...(activeEvents.length > 0
      ? activeEvents.map((event) => {
          const score = scoreByEvidenceId.get(event.id);
          const status = score ? "已纳入验证" : "待验证";
          const conclusion = score ? "已纳入当前候选比较" : "尚未完成候选比较";
          return `| ${markdownCell(event.dateLabel)} | ${markdownCell(event.summary)} | ${markdownCell(domainLabels[event.domain])} | ${status} | ${conclusion} |`;
        })
      : ["| — | 尚无可评分事件 | — | 待验证 | 尚未完成候选比较 |"]),
  ].join("\n");

  const candidateRows = [
    ...(workflow?.candidateWindows ?? []).map((window) => ({
      range: `${window.startTime}–${window.endTime}`,
      layer: "候选窗口",
      status: window.status,
      evidence: packet.useBoundary,
    })),
    ...packet.stableLayers.map((layer) => ({
      range: `${packet.candidate.range.startTime}–${packet.candidate.range.endTime}`,
      layer: layer.layer,
      status: "stable",
      evidence: layer.values.join(" / "),
    })),
    ...packet.sensitiveLayers.map((layer) => ({
      range: `${packet.candidate.range.startTime}–${packet.candidate.range.endTime}`,
      layer: layer.layer,
      status: "minute_sensitive",
      evidence: layer.values.join(" / "),
    })),
  ];
  const candidateTable = [
    "### 候选时间差异表",
    "| 候选范围 | 层 | 状态 | 差异 / 证据 |",
    "|---|---|---|---|",
    ...(candidateRows.length > 0
      ? candidateRows.map((row) => `| ${markdownCell(row.range)} | ${markdownCell(row.layer)} | ${markdownCell(row.status)} | ${markdownCell(row.evidence)} |`)
      : ["| — | — | 待计算 | 尚无可展示差异 |"]),
  ].join("\n");

  return [
    {
      heading: "### Technique Audit Table",
      header: "| 技法 | 状态 | 证据 | 使用边界 |",
      markdown: techniqueTable,
    },
    {
      heading: "### 事件验证表",
      header: "| 时间 | 事件 | 领域 | 验证状态 | 结论 |",
      markdown: eventTable,
    },
    {
      heading: "### 候选时间差异表",
      header: "| 候选范围 | 层 | 状态 | 差异 / 证据 |",
      markdown: candidateTable,
    },
  ];
}

function markdownSection(narrative: string, heading: string): string | null {
  const start = narrative.indexOf(heading);
  if (start < 0) return null;
  const nextHeading = narrative.indexOf("\n### ", start + heading.length);
  return narrative.slice(start, nextHeading < 0 ? undefined : nextHeading);
}

function hasCompleteAnalysisTable(
  narrative: string,
  section: Readonly<{ readonly heading: string; readonly header: string }>,
): boolean {
  const authoredSection = markdownSection(narrative, section.heading);
  if (!authoredSection || !authoredSection.includes(section.header)) return false;
  const tableLines = authoredSection
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|") && line.endsWith("|"));
  return tableLines.length >= 3;
}

function appendFinalAnalysisTables(
  narrative: string,
  packet: RectificationTechnicalPacket,
  context: RectificationNarrativeContext,
): string {
  const missing = analysisTableSections(packet, context)
    .filter((section) => !hasCompleteAnalysisTable(narrative, section))
    .map((section) => section.markdown);
  return missing.length > 0 ? [narrative.trim(), ...missing].filter(Boolean).join("\n\n") : narrative;
}

export async function generateRectificationNarrative(input: {
  readonly phase: RectificationNarrativePhase;
  readonly packet: RectificationTechnicalPacket;
  readonly generator: RectificationNarrativeGenerator;
  readonly context?: RectificationNarrativeContext;
}): Promise<RectificationNarrativeResult> {
  const startedAt = Date.now();
  const defaultModelId = modelIdSchema.parse(input.generator.modelId);
  let issues: readonly string[] = [];
  for (const attempt of [1, 2] as const) {
    try {
      const signal = AbortSignal.timeout(narrativeAttemptTimeoutMs[attempt - 1]);
      const generated = await input.generator.generate(promptFor(
        input.phase,
        input.packet,
        input.context ?? {},
        issues,
      ), { signal, attempt });
      const modelId = modelIdSchema.parse(generated.modelId ?? defaultModelId);
      const output = parseModelOutput(generated.text, input.packet);
      const validation = validateNarrativeAgainstPacket(
        output,
        input.packet,
        input.phase,
        input.context ?? {},
      );
      if (validation.valid) {
        const narrative = input.phase === "final"
          ? appendFinalAnalysisTables(output.narrative, input.packet, input.context ?? {})
          : output.narrative;
        const finalOutput = narrative === output.narrative ? output : { ...output, narrative };
        logNarrativeGeneration({
          phase: input.phase,
          retryCount: attempt === 1 ? 0 : 1,
          fallbackUsed: false,
          source: attempt === 1 ? "model" : "model_retry",
          issues,
          startedAt,
        });
        return {
          narrative,
          output: finalOutput,
          attempts: attempt,
          fallbackUsed: false,
          allowEvidenceScoringAdvance: true,
          validationReceipt: {
            modelId,
            schemaValidated: true,
            validatorVersion,
            retryCount: attempt === 1 ? 0 : 1,
            fallbackUsed: false,
            issues: [],
          },
        };
      }
      issues = [...issues, ...validation.issues];
    } catch (error) {
      const attemptIssues = error instanceof z.ZodError
        ? error.issues.map((issue) => `${issue.path.join(".") || "root"}:${issue.code}`)
        : [error instanceof Error ? error.name : "NarrativeOutputError"];
      issues = [...issues, ...attemptIssues];
    }
  }
  const output = fallbackOutput(input.packet, input.phase);
  const narrative = input.phase === "final"
    ? appendFinalAnalysisTables(output.narrative, input.packet, input.context ?? {})
    : output.narrative;
  const finalOutput = narrative === output.narrative ? output : { ...output, narrative };
  logNarrativeGeneration({
    phase: input.phase,
    retryCount: 1,
    fallbackUsed: true,
    source: "fallback",
    issues: boundedReceiptIssues(issues),
    startedAt,
  });
  return {
    narrative,
    output: finalOutput,
    attempts: 2,
    fallbackUsed: true,
    // The fallback is rendered entirely from the validated deterministic packet.
    // A prose-model failure must not discard scoreable evidence or block narrowing.
    allowEvidenceScoringAdvance: true,
    validationReceipt: {
      modelId: defaultModelId,
      schemaValidated: false,
      validatorVersion,
      retryCount: 1,
      fallbackUsed: true,
      issues: boundedReceiptIssues(issues),
    },
  };
}

export type { RectificationEvidenceDomain };
