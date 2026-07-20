import type { CandidateDifferenceBuild } from "../birth-time-dynamic-choice-internal.ts";
import type { CandidateResult } from "../birth-time-evidence.ts";
import type { RectificationQuestionnaire } from "../birth-time-journey-service.ts";

export type RectificationEvidenceDomain =
  | "career"
  | "education"
  | "relocation"
  | "relationship"
  | "family"
  | "other";

export type ServerComputedRectificationConsultation = {
  readonly source: "server_consultation_workflow";
  readonly calculationVersion: string;
  readonly availableLayers: readonly string[];
  readonly layerReferences: Readonly<Record<string, readonly string[]>>;
  readonly boundaryDistanceMinutes: number | null;
  readonly futureWindows: readonly {
    readonly label: string;
    readonly startDate: string;
    readonly endDate: string;
  }[];
};

export type RectificationLayerEvidence = {
  readonly layer: string;
  readonly values: readonly string[];
  readonly referenceIds: readonly string[];
};

export type SuggestedEvidenceDomain = {
  readonly domain: RectificationEvidenceDomain;
  readonly layer: string;
  readonly reason: string;
};

export type RectificationTechnicalPacket = {
  readonly calculationVersion: string;
  readonly candidate: {
    readonly status: "pending_validation" | "ready_for_confirmation";
    readonly representativeTime: string;
    readonly range: { readonly startTime: string; readonly endTime: string };
  };
  readonly useBoundary: string;
  readonly candidateModelRefs: readonly string[];
  readonly candidateDifferenceRefs: readonly string[];
  readonly candidateWeights: Readonly<Record<string, number>>;
  readonly partitionIds: readonly string[];
  readonly d1Stability: "stable" | "sensitive" | "unavailable";
  readonly boundaryDistanceMinutes: number | null;
  readonly stableLayers: readonly RectificationLayerEvidence[];
  readonly sensitiveLayers: readonly RectificationLayerEvidence[];
  readonly supportedSensitiveLayers: readonly string[];
  readonly scoredHistoricalEvidence: readonly {
    readonly evidenceId: string;
    readonly domain: RectificationEvidenceDomain;
    readonly candidateTime: string | null;
    readonly score: number;
    readonly ruleRefs: readonly string[];
  }[];
  readonly suggestedDomains: readonly SuggestedEvidenceDomain[];
  readonly referenceIds: readonly string[];
  readonly futureWindows: readonly {
    readonly label: string;
    readonly startDate: string;
    readonly endDate: string;
    readonly scoreable: false;
  }[];
};

type PacketInput = {
  readonly scan: RectificationQuestionnaire;
  readonly candidateDifferences: CandidateDifferenceBuild;
  readonly eventScore: CandidateResult | null;
  readonly consultation: ServerComputedRectificationConsultation;
};

const layerFields = [
  ["D1", "ascendantSign"],
  ["D4", "d4Sign"],
  ["D9", "d9Sign"],
  ["D10", "d10Sign"],
  ["D24", "d24Sign"],
  ["D30", "d30Sign"],
] as const;

const domainByLayer = {
  D9: "relationship",
  D10: "career",
  D24: "education",
  D4: "relocation",
} as const satisfies Readonly<Record<string, RectificationEvidenceDomain>>;

function unique(values: readonly string[]): string[] {
  return [...new Set(values.filter((value) => value.trim().length > 0))];
}

function timeToMinute(value: string): number {
  const [hour = 0, minute = 0] = value.split(":").map(Number);
  return hour * 60 + minute;
}

function minuteToTime(value: number): string {
  const normalized = ((value % 1_440) + 1_440) % 1_440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function midpoint(startTime: string, endTime: string): string {
  const start = timeToMinute(startTime);
  let end = timeToMinute(endTime);
  if (end < start) end += 1_440;
  return minuteToTime(Math.round((start + end) / 2));
}

function candidateWeights(model: Readonly<Record<string, unknown>>): Readonly<Record<string, number>> {
  const raw = model.candidateWeights ?? model.candidate_weights;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
  const entries: [string, number][] = [];
  for (const [time, weight] of Object.entries(raw)) {
    if (typeof weight === "number" && Number.isFinite(weight) && weight >= 0) {
      entries.push([time, weight]);
    }
  }
  return Object.fromEntries(entries.sort((left, right) => left[0].localeCompare(right[0])));
}

function eventDomain(domain: CandidateResult["evidence"][number]["domain"]): RectificationEvidenceDomain {
  return domain === "finance" || domain === "health_pressure" ? "other" : domain;
}

function layerEvidence(input: PacketInput): RectificationLayerEvidence[] {
  return layerFields.map(([layer, field]) => ({
    layer,
    values: unique(input.scan.samples.map((sample) => sample[field] ?? "")),
    referenceIds: unique(input.consultation.layerReferences[layer] ?? []),
  })).filter((item) => item.values.length > 0);
}

function suggestedDomains(layers: readonly RectificationLayerEvidence[]): SuggestedEvidenceDomain[] {
  return layers.flatMap((item) => {
    const domain = domainByLayer[item.layer as keyof typeof domainByLayer];
    if (!domain) return [];
    return [{
      domain,
      layer: item.layer,
      reason: `${item.layer} 在候选范围内呈现 ${item.values.join(" / ")} 差异，可用已发生的${domain}事件区分。`,
    }];
  });
}

export function buildRectificationTechnicalPacket(input: PacketInput): RectificationTechnicalPacket {
  if (input.consultation.source !== "server_consultation_workflow") {
    throw new TypeError("rectification packet requires server-computed consultation data");
  }
  const eventSegment = input.eventScore?.winningSegment;
  const range = eventSegment
    ? { startTime: eventSegment.startTime, endTime: eventSegment.endTime }
    : input.candidateDifferences.packet.currentRange;
  const representativeTime = eventSegment?.representativeTime
    ?? midpoint(range.startTime, range.endTime);
  const layers = layerEvidence(input);
  const d1 = layers.find((item) => item.layer === "D1");
  const d1Stability = !d1 ? "unavailable" : d1.values.length === 1 ? "stable" : "sensitive";
  const available = new Set(input.consultation.availableLayers);
  const sensitiveLayers = layers.filter((item) => item.layer !== "D1"
    && item.values.length > 1
    && available.has(item.layer));
  const domains = suggestedDomains(sensitiveLayers);
  if (domains.length < 2) {
    throw new TypeError("rectification packet requires two server-computed discriminating domains");
  }
  const scoredHistoricalEvidence = (input.eventScore?.evidence ?? []).map((item) => ({
    evidenceId: item.eventId,
    domain: eventDomain(item.domain),
    candidateTime: item.candidateTime ?? null,
    score: item.points,
    ruleRefs: [...item.ruleIds],
  }));
  const opportunityRefs = input.candidateDifferences.packet.opportunities.map((item) => item.opportunityId);
  const ruleRefs = scoredHistoricalEvidence.flatMap((item) => item.ruleRefs);
  const layerRefs = layers.flatMap((item) => item.referenceIds);
  const modelVersion = input.candidateDifferences.candidateModel.version;
  const candidateModelRefs = unique([
    input.candidateDifferences.packet.scoringVersion,
    typeof modelVersion === "string" ? modelVersion : "",
    input.eventScore?.algorithmVersion ?? "",
  ]);
  const partitionIds = unique(Object.values(input.candidateDifferences.scoringPartitions)
    .flatMap((partitions) => partitions.map((partition) => partition.partitionId)));

  return {
    calculationVersion: input.consultation.calculationVersion,
    candidate: {
      status: input.eventScore?.canApply ? "ready_for_confirmation" : "pending_validation",
      representativeTime,
      range,
    },
    useBoundary: input.eventScore?.canApply
      ? "该候选已达到确认门槛，但必须由用户明确确认后才能替换当前排盘时间。"
      : "该时间与范围仅是待验证候选，可用于比较稳定层和分钟敏感层，不能视为出生记录中的确定分钟。",
    candidateModelRefs,
    candidateDifferenceRefs: unique([...opportunityRefs, ...ruleRefs, ...layerRefs]),
    candidateWeights: candidateWeights(input.candidateDifferences.candidateModel),
    partitionIds,
    d1Stability,
    boundaryDistanceMinutes: input.consultation.boundaryDistanceMinutes,
    stableLayers: d1Stability === "stable" && d1 ? [d1] : [],
    sensitiveLayers,
    supportedSensitiveLayers: sensitiveLayers.map((item) => item.layer),
    scoredHistoricalEvidence,
    suggestedDomains: domains.slice(0, 4),
    referenceIds: unique([...opportunityRefs, ...ruleRefs, ...layerRefs]),
    futureWindows: input.consultation.futureWindows.map((window) => ({ ...window, scoreable: false })),
  };
}

export function projectRectificationTechnicalPacket(packet: RectificationTechnicalPacket) {
  return {
    candidate: {
      status: packet.candidate.status,
      representativeTime: packet.candidate.representativeTime,
      rangeStart: packet.candidate.range.startTime,
      rangeEnd: packet.candidate.range.endTime,
    },
    useBoundary: packet.useBoundary,
    technicalReceipt: {
      calculationVersion: packet.calculationVersion,
      stableLayers: packet.stableLayers.map((item) => item.layer),
      sensitiveLayers: [...packet.supportedSensitiveLayers],
      candidateDifferenceRefs: packet.candidateDifferenceRefs
        .filter((reference) => reference.trim().length > 0 && reference.length <= 120)
        .slice(0, 40),
    },
    evidenceRequest: {
      domains: packet.suggestedDomains.map((item) => item.domain),
      datePrecision: "month_preferred" as const,
      freeTextAllowed: true as const,
    },
    futureWindows: packet.futureWindows.map((window) => ({ ...window })),
  };
}
