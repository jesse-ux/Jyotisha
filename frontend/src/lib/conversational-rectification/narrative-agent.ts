import { z } from "zod";
import {
  projectRectificationTechnicalPacket,
  type RectificationEvidenceDomain,
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";

export type RectificationNarrativePhase = "first" | "intermediate" | "final";

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const modelIdSchema = z.string().trim().min(1).max(120);
const validatorVersion = "rectification-narrative-grounding-v1";
const domainSchema = z.enum(["career", "education", "relocation", "relationship", "family", "other"]);
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
    domains: z.array(domainSchema).min(2).max(4),
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

function sameMembers(actual: readonly string[], expected: readonly string[]): boolean {
  const left = [...new Set(actual)].sort();
  const right = [...new Set(expected)].sort();
  return left.length === right.length && left.every((value, index) => value === right[index]);
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
  if (phase === "first" && !sameMembers(output.stableLayers, allowedStable)) {
    issues.push("first turn must carry every stable layer");
  }
  if (phase === "first" && !sameMembers(output.sensitiveLayers, allowedSensitive)) {
    issues.push("first turn must carry every sensitive layer");
  }

  for (const reference of output.referenceIds) {
    if (!packet.referenceIds.includes(reference)) issues.push(`reference ${reference} is not packet-grounded`);
  }
  const allowedDomains = new Map(packet.suggestedDomains.map((item) => [item.domain, item.layer]));
  for (const reason of output.domainReasons) {
    if (allowedDomains.get(reason.domain) !== reason.layer || !reason.reason.includes(reason.layer)) {
      issues.push(`domain reason ${reason.domain}/${reason.layer} is not packet-grounded`);
    }
  }
  if (phase === "first" && output.domainReasons.length < 2) {
    issues.push("first turn requires two discriminating domain reasons");
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
  for (const time of narrativeTimes(output.narrative)) {
    if (!allowedTimes.includes(time)) issues.push(`narrative time ${time} is not packet-grounded`);
  }
  const allowedLayers = [...allowedStable, ...allowedSensitive];
  for (const layer of narrativeLayers(output.narrative)) {
    if (!allowedLayers.includes(layer)) issues.push(`narrative layer ${layer} is not packet-grounded`);
  }
  for (const reference of narrativeReferences(output.narrative)) {
    if (!packet.referenceIds.includes(reference)) issues.push(`narrative reference ${reference} is not packet-grounded`);
  }
  if (phase === "first") {
    if (!output.narrative.includes(candidate.representativeTime)
      || !/(?:待验证|候选)/.test(output.narrative)) {
      issues.push("first narrative must state the pending candidate time");
    }
    if (!allowedStable.every((layer) => output.narrative.includes(layer))
      || !allowedSensitive.every((layer) => output.narrative.includes(layer))) {
      issues.push("first narrative must explain stable and sensitive layers");
    }
    if (!/(?:已经发生|已发生|过去)/.test(output.narrative)
      || !/年/.test(output.narrative)
      || !/月/.test(output.narrative)) {
      issues.push("first narrative must request real past events by year and month");
    }
    if (!/(?:不是[\s\S]*确认|不能[\s\S]*确定|仅[\s\S]*候选|必须[\s\S]*确认)/.test(output.narrative)) {
      issues.push("first narrative must state the candidate use boundary");
    }
  }
  return { valid: issues.length === 0, issues };
}

function grounding(packet: RectificationTechnicalPacket) {
  const projected = projectRectificationTechnicalPacket(packet);
  return {
    calculationVersion: packet.calculationVersion,
    candidate: projected.candidate,
    useBoundary: packet.useBoundary,
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
      requestRealPastEventsByYearAndMonth: phase !== "final",
      futureWindowsAreContextOnly: true,
      genericBroadYearRangeQuestionnaireForbidden: true,
    },
    retryIssues: boundedReceiptIssues(retryIssues),
  });
}

function fallbackNarrative(packet: RectificationTechnicalPacket, phase: RectificationNarrativePhase): string {
  const candidate = packet.candidate;
  const stable = packet.stableLayers
    .map((item) => `${item.layer}（${item.values.join(" / ")}）保持稳定`)
    .join("；");
  const sensitive = packet.sensitiveLayers
    .map((item) => `${item.layer}（${item.values.join(" / ")}）`)
    .join("；");
  const reasons = packet.suggestedDomains
    .map((item) => `${item.domain}事件可区分 ${item.layer}`)
    .join("；");
  const phaseLine = phase === "final"
    ? "当前证据已形成候选总结，但仍有残余不确定性；只有明确确认后才会替换当前排盘时间。"
    : `下一步请提供上述领域已经发生的真实事件，尽量写明哪一年、哪一月以及发生了什么；${reasons}。`;
  return [
    `${candidate.representativeTime} 是 ${candidate.range.startTime}–${candidate.range.endTime} 范围内的待验证候选。`,
    packet.useBoundary,
    `${stable || "D1 稳定性暂不可用"}；${sensitive} 是当前支持的分钟敏感层。`,
    phaseLine,
    "未来窗口只能作为背景，不能计入既成事件评分。",
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
      domains: packet.suggestedDomains.slice(0, 4).map((item) => item.domain),
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
    allowEvidenceScoringAdvance: false,
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
