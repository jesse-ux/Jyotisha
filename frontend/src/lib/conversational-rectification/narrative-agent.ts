import { z } from "zod";
import {
  projectRectificationTechnicalPacket,
  type RectificationEvidenceDomain,
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";

export type RectificationNarrativePhase = "first" | "intermediate" | "final";

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const modelIdSchema = z.string().trim().min(1).max(120);
const validatorVersion = "rectification-narrative-grounding-v2";
const domainSchema = z.enum(["career", "education", "finance", "health_pressure", "relocation", "relationship", "family", "other"]);
const broadYearRangePattern = /(?:19|20)\d{2}\s*年?\s*(?:[-–—~～至到\/]|\.\.)\s*(?:19|20)\d{2}\s*年?/i;
const explicitYearPattern = /(?:19|20)\d{2}\s*年?/g;
const proposedYearAlternativesPattern = /(?:19|20)\d{2}\s*年?\s*(?:还是|或者|或是|或|、|,|，)\s*(?:19|20)\d{2}\s*年?/i;
const choiceQuestionPattern = /(?:哪(?:一|个)?(?:年|年份|年代|时间段|区间|时期)|哪个时间段|还是|选择|选项|更符合|更匹配|A\s*[.、:：)]|B\s*[.、:：)]|which\s+(?:year|period|range)|options?)/i;
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
const narrativeOutputSchema = z.object({
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
  }).strict().nullable(),
}).strict();

export type RectificationNarrativeModelOutput = z.infer<typeof narrativeOutputSchema>;

export type NarrativeValidation = {
  readonly valid: boolean;
  readonly issues: readonly string[];
};

export interface RectificationNarrativeGenerator {
  readonly modelId: string;
  generate(prompt: string): Promise<{ readonly text: string }>;
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

function unique(values: readonly string[]): string[] {
  return [...new Set(values)];
}

function parseModelOutput(text: string): RectificationNarrativeModelOutput {
  const normalized = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const start = normalized.indexOf("{");
  const end = normalized.lastIndexOf("}");
  if (start < 0 || end <= start) throw new TypeError("narrative output is not JSON");
  return narrativeOutputSchema.parse(JSON.parse(normalized.slice(start, end + 1)));
}

function narrativeTimes(value: string): string[] {
  return unique(value.match(/(?:[01]\d|2[0-3]):[0-5]\d/g) ?? []);
}

function narrativeLayers(value: string): string[] {
  return unique(value.match(/\bD\d{1,3}\b|\b(?:UL|A7|A10|KP_cusp)\b/g) ?? []);
}

function narrativeReferences(value: string): string[] {
  const bracketed = [...value.matchAll(/【([^】]+)】/g)]
    .map((match) => match[1] ?? "")
    .filter(Boolean);
  const plainTechnicalIds = value.match(/\b[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+\b/g) ?? [];
  return unique([...bracketed, ...plainTechnicalIds]);
}

function isGenericBroadYearChoiceQuestionnaire(value: string): boolean {
  const distinctYears = unique((value.match(explicitYearPattern) ?? [])
    .map((year) => year.replace(/\s*年$/, "")));
  return proposedYearAlternativesPattern.test(value)
    || (choiceQuestionPattern.test(value)
      && (broadYearRangePattern.test(value) || distinctYears.length >= 2));
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

function pairKey(value: { readonly domain: RectificationEvidenceDomain; readonly layer: string }): string {
  return `${value.domain}\0${value.layer}`;
}

export function validateNarrativeAgainstPacket(
  output: RectificationNarrativeModelOutput,
  packet: RectificationTechnicalPacket,
  phase: RectificationNarrativePhase = "first",
): NarrativeValidation {
  const issues: string[] = [];
  const candidate = packet.candidate;
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
  const packetReasons = new Map(packet.suggestedDomains.map((item) => [pairKey(item), item.reason]));
  for (const [index, reason] of output.domainReasons.entries()) {
    const expectedReason = packetReasons.get(pairKey(reason));
    if (!expectedReason) {
      issues.push(`domain reason ${reason.domain}/${reason.layer} is not packet-grounded`);
    } else if (reason.reason !== expectedReason) {
      issues.push(`domainReasons[${index}].reason must use the packet discrimination explanation`);
    }
  }
  if (output.evidenceRequest) {
    for (const domain of output.evidenceRequest.domains) {
      if (!allowedDomains.has(domain)) issues.push(`evidence domain ${domain} is not packet-grounded`);
    }
    if (!/(?:已经发生|已发生|过去)/.test(output.evidenceRequest.prompt)
      || !/年/.test(output.evidenceRequest.prompt)
      || !/月/.test(output.evidenceRequest.prompt)) {
      issues.push("evidence request must ask for a real past event by year and month");
    }
  } else if (phase !== "final") {
    issues.push("non-final turns require an evidence request");
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
  if (phase !== "final") {
    if (!output.narrative.includes(candidate.range.startTime)
      || !output.narrative.includes(candidate.range.endTime)
      || !/(?:待验证|候选|核对)/.test(output.narrative)) {
      issues.push("first narrative must state the pending candidate range");
    }
    if (narrativeLayers(output.narrative).length > 0) {
      issues.push("visible evidence narrative must not expose technical layer tokens");
    }
    if (!/(?:已经发生|已发生|过去)/.test(output.narrative)
      || !/年/.test(output.narrative)
      || !/月/.test(output.narrative)) {
      issues.push("first narrative must request real past events by year and month");
    }
    if (!/(?:不是[\s\S]*确认|不能[\s\S]*(?:确定|确认)|仅[\s\S]*候选|必须[\s\S]*确认)/.test(output.narrative)) {
      issues.push("first narrative must state the candidate use boundary");
    }
  }
  const uniqueIssues = unique(issues);
  return { valid: uniqueIssues.length === 0, issues: uniqueIssues };
}

function grounding(packet: RectificationTechnicalPacket) {
  const projected = projectRectificationTechnicalPacket(packet);
  return {
    calculationVersion: packet.calculationVersion,
    candidate: projected.candidate,
    useBoundary: packet.useBoundary,
    sensitivityScope: projected.technicalReceipt.sensitivityScope,
    stableLayers: packet.stableLayers,
    sensitiveLayers: packet.sensitiveLayers,
    scoredHistoricalEvidence: packet.scoredHistoricalEvidence,
    suggestedDomains: packet.suggestedDomains,
    referenceIds: packet.referenceIds,
    futureWindows: projected.futureWindows,
  };
}

function boundedReceiptIssues(issues: readonly string[]): string[] {
  return issues
    .slice(0, 20)
    .map((issue) => issue.trim().slice(0, 240) || "narrative_mismatch");
}

function promptFor(
  phase: RectificationNarrativePhase,
  packet: RectificationTechnicalPacket,
  retryIssues: readonly string[] = [],
): string {
  return JSON.stringify({
    task: "write_grounded_rectification_narrative",
    phase,
    packet: grounding(packet),
    outputContract: {
      candidateFactsMustMatch: true,
      onlyListedLayersAndReferences: true,
      everyAuthoredStringMustBeGrounded: true,
      keepTechnicalLayerValuesOutOfVisibleNarrative: phase !== "final",
      askExactlyOneHighInformationQuestion: phase !== "final",
      usePacketDomainReasonTextExactly: true,
      requestRealPastEventsByYearAndMonth: phase !== "final",
      futureWindowsAreContextOnly: true,
      genericBroadYearRangeQuestionnaireForbidden: true,
    },
    retryIssues: boundedReceiptIssues(retryIssues),
  });
}

function fallbackNarrative(packet: RectificationTechnicalPacket, phase: RectificationNarrativePhase): string {
  const candidate = packet.candidate;
  const nextDomain = packet.suggestedDomains[0]?.domain;
  const nextLabel = nextDomain ? domainLabels[nextDomain] : "重要经历";
  const phaseLine = phase === "final"
    ? "当前证据已形成候选总结，但仍有残余不确定性；只有明确确认后才会替换当前排盘时间。"
    : `先说一件已经发生的${nextLabel}事件好吗？尽量写明哪一年、哪一月以及发生了什么。`;
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
    evidenceRequest: phase === "final" ? null : {
      domains: packet.suggestedDomains.slice(0, 1).map((item) => item.domain),
      datePrecision: "month_preferred",
      prompt: "请提供已经发生的真实事件，并尽量写明哪一年、哪一月以及发生了什么。",
    },
  };
}

export async function generateRectificationNarrative(input: {
  readonly phase: RectificationNarrativePhase;
  readonly packet: RectificationTechnicalPacket;
  readonly generator: RectificationNarrativeGenerator;
}): Promise<RectificationNarrativeResult> {
  const modelId = modelIdSchema.parse(input.generator.modelId);
  let issues: readonly string[] = [];
  for (const attempt of [1, 2] as const) {
    try {
      const generated = await input.generator.generate(promptFor(input.phase, input.packet, issues));
      const output = parseModelOutput(generated.text);
      const validation = validateNarrativeAgainstPacket(output, input.packet, input.phase);
      if (validation.valid) {
        return {
          narrative: output.narrative,
          output,
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
      issues = validation.issues;
    } catch (error) {
      issues = [error instanceof Error ? error.name : "NarrativeOutputError"];
    }
  }
  const output = fallbackOutput(input.packet, input.phase);
  return {
    narrative: output.narrative,
    output,
    attempts: 2,
    fallbackUsed: true,
    // The fallback is rendered entirely from the validated deterministic packet.
    // A prose-model failure must not discard scoreable evidence or block narrowing.
    allowEvidenceScoringAdvance: true,
    validationReceipt: {
      modelId,
      schemaValidated: false,
      validatorVersion,
      retryCount: 1,
      fallbackUsed: true,
      issues: boundedReceiptIssues(issues),
    },
  };
}

export type { RectificationEvidenceDomain };
