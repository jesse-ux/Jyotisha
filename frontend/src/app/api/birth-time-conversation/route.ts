import { randomUUID } from "node:crypto";
import path from "node:path";
import {
  conversationalRectificationCommandSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationTurn,
} from "../../../lib/conversational-rectification/contracts.ts";
import {
  ConversationalRectificationError,
  toConversationalRectificationPublicError,
} from "../../../lib/conversational-rectification/errors.ts";
import {
  createConversationalRectificationService,
  conversationalRectificationTelemetryOutcome,
  evidencePredatesBirthDate,
  type ConversationalRectificationPacketBuildInput,
  type ConversationalRectificationService,
} from "../../../lib/conversational-rectification/orchestrator.ts";
import {
  declaredBirthInputSchema,
  type DeclaredBirthInput,
  type LifeEventEvidence,
} from "../../../lib/conversational-rectification/persistence-contracts.ts";
import type { RectificationNarrativeGenerator } from "../../../lib/conversational-rectification/narrative-agent.ts";
import type { BirthTimeJourneyEngine, RectificationQuestionnaire } from "../../../lib/birth-time-journey-service.ts";
import type { CandidateResult, LifeEvent } from "../../../lib/birth-time-evidence.ts";
import type { CandidateDifferenceBuild } from "../../../lib/birth-time-dynamic-choice-internal.ts";
import { conversationalRectificationCreationPolicyFromEnvironment } from "../../../lib/conversational-rectification/creation-policy.ts";
import { MAXIMUM_SCOREABLE_EVENTS } from "../../../lib/conversational-rectification/convergence.ts";
import {
  conversationalRectificationLatencyBucket,
  createConversationalRectificationTelemetry,
  recordConversationalRectificationTelemetry,
  safeConversationalRectificationDeploymentSha,
  type ConversationalRectificationTelemetryPayload,
  type ConversationalRectificationTelemetrySink,
} from "../../../lib/birth-time-journey-telemetry.ts";

export const runtime = "nodejs";
export const maxDuration = 60;

const jyotishSkillPath = process.env.JYOTISH_SKILL_PATH?.trim()
  || path.resolve(process.cwd(), "..", "skills", "jyotish-vedic-astrology");

type AuthenticatedRequest = Readonly<{
  userId: string;
  context: unknown;
}>;

export type BirthTimeConversationRouteService = ConversationalRectificationService;

export type BirthTimeConversationRouteLog = Readonly<{
  code: string;
}>;

export type BirthTimeConversationPostDependencies = Readonly<{
  authenticate(request: Request): Promise<AuthenticatedRequest | null>;
  createService(authenticated: AuthenticatedRequest): Promise<BirthTimeConversationRouteService>;
  createRequestId?(request: Request): string;
  log?(entry: BirthTimeConversationRouteLog): void;
  telemetry?: ConversationalRectificationTelemetrySink;
  deploymentSha?: string;
  now?(): number;
}>;

type ProfileQueryResult = Readonly<{
  data: unknown;
  error: unknown;
}>;

type ProfileClient = {
  from(table: string): {
    select(columns: string): {
      eq(column: string, value: string): {
        maybeSingle(): PromiseLike<ProfileQueryResult>;
      };
    };
  };
};

async function authenticateProductionRequest(): Promise<AuthenticatedRequest | null> {
  const { createServerSupabaseClient } = await import("../../../lib/supabase/server.ts");
  const serverClient = await createServerSupabaseClient();
  const { data: { user }, error } = await serverClient.auth.getUser();
  if (error || !user) return null;
  return { userId: user.id, context: serverClient };
}

async function requestPayload(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch (error) {
    if (error instanceof SyntaxError) return null;
    throw error;
  }
}

function profileRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function integer(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) ? value : null;
}

function declaredBirthInputFromProfile(value: unknown): DeclaredBirthInput {
  const profile = profileRecord(value);
  if (!profile) throw new ConversationalRectificationError("profile_incomplete");
  const birthDate = text(profile.birth_date);
  const source = text(profile.birth_time_source);
  const cityCode = text(profile.city_code);
  const latitude = finiteNumber(profile.latitude);
  const longitude = finiteNumber(profile.longitude);
  const timezoneOffset = finiteNumber(profile.timezone_offset);
  if (!birthDate || !source || !cityCode || latitude === null || longitude === null
    || timezoneOffset === null) {
    throw new ConversationalRectificationError("profile_incomplete");
  }
  const birthplace = {
    ...(text(profile.country_code) ? { countryCode: text(profile.country_code) } : {}),
    ...(text(profile.province_code) ? { provinceCode: text(profile.province_code) } : {}),
    cityCode,
    ...(text(profile.district_code) ? { districtCode: text(profile.district_code) } : {}),
    latitude,
    longitude,
    timezoneOffset,
  };
  const common = {
    birthDate,
    birthTimeClue: text(profile.birth_time_clue),
    birthplace,
  };
  const reportedTime = text(profile.reported_birth_time)?.slice(0, 5) ?? null;
  const period = text(profile.birth_time_period);
  const before = integer(profile.uncertainty_before_minutes);
  const after = integer(profile.uncertainty_after_minutes);
  let declaredBirthInput: unknown;
  switch (source) {
    case "hospital_record":
      declaredBirthInput = {
        ...common, source, reportedTime,
        uncertaintyBeforeMinutes: 2, uncertaintyAfterMinutes: 2,
      };
      break;
    case "family_exact":
    case "approximate":
      declaredBirthInput = {
        ...common, source, reportedTime,
        uncertaintyBeforeMinutes: before, uncertaintyAfterMinutes: after,
      };
      break;
    case "period_only":
      declaredBirthInput = { ...common, source, reportedPeriod: period };
      break;
    case "unknown":
      declaredBirthInput = { ...common, source };
      break;
    case "legacy_import":
      declaredBirthInput = {
        ...common,
        source,
        ...(reportedTime ? { reportedTime } : {}),
        ...(period ? { reportedPeriod: period } : {}),
        ...(before === null ? {} : { uncertaintyBeforeMinutes: before }),
        ...(after === null ? {} : { uncertaintyAfterMinutes: after }),
      };
      break;
    default:
      throw new ConversationalRectificationError("profile_incomplete");
  }
  const parsed = declaredBirthInputSchema.safeParse(declaredBirthInput);
  if (!parsed.success) throw new ConversationalRectificationError("profile_incomplete");
  return parsed.data;
}

export function declaredBirthInputForLegacyCase(
  currentProfileValue: unknown,
  legacyCaseValue: unknown,
): DeclaredBirthInput {
  const currentProfile = profileRecord(currentProfileValue);
  const legacyCase = profileRecord(legacyCaseValue);
  if (!currentProfile || !legacyCase) {
    throw new ConversationalRectificationError("profile_incomplete");
  }
  return declaredBirthInputFromProfile({
    ...currentProfile,
    birth_date: legacyCase.reported_date,
    reported_birth_time: legacyCase.reported_time,
    birth_time_source: legacyCase.source,
    birth_time_period: legacyCase.reported_period,
    uncertainty_before_minutes: legacyCase.uncertainty_before_minutes,
    uncertainty_after_minutes: legacyCase.uncertainty_after_minutes,
  });
}

export type ProductionConversationalRectificationProfileDependencies = Readonly<{
  loadProfile(userId: string): Promise<unknown>;
  loadRectificationCase(userId: string, caseId: string): Promise<unknown>;
}>;

export async function loadProductionConversationalRectificationProfile(
  dependencies: ProductionConversationalRectificationProfileDependencies,
  userId: string,
): Promise<Readonly<{
  declaredBirthInput: DeclaredBirthInput;
  revisionOfCaseId: string | null;
  legacyCaseId: string | null;
}>> {
  const profileValue = await dependencies.loadProfile(userId);
  const profile = profileRecord(profileValue);
  if (!profile) throw new ConversationalRectificationError("profile_incomplete");
  const declaredBirthInput = declaredBirthInputFromProfile(profile);
  const priorCaseId = text(profile.rectification_case_id);
  if (!priorCaseId) return {
    declaredBirthInput,
    revisionOfCaseId: null,
    legacyCaseId: null,
  };

  const prior = profileRecord(await dependencies.loadRectificationCase(userId, priorCaseId));
  const terminalV3Revision = prior
    && text(prior.id) === priorCaseId
    && text(prior.journey_protocol) === "conversational-evidence-v3"
    && (text(prior.status) === "completed" || text(prior.status) === "abandoned");
  const protocol = prior ? text(prior.journey_protocol) : null;
  const status = prior ? text(prior.status) : null;
  const unfinishedLegacyStatuses = new Set([
    "assessing",
    "rectifying",
    "candidate",
    "confirming",
  ]);
  const unfinishedLegacy = prior
    && text(prior.id) === priorCaseId
    && (protocol === "legacy-guided-v1" || protocol === "dynamic-choice-v2")
    && status !== null
    && unfinishedLegacyStatuses.has(status);
  return {
    declaredBirthInput,
    revisionOfCaseId: terminalV3Revision ? priorCaseId : null,
    legacyCaseId: unfinishedLegacy ? priorCaseId : null,
  };
}

function priceCredits(): number {
  const raw = process.env.RECTIFICATION_PRICE_CREDITS?.trim() ?? "1";
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < 1 || value > 100) {
    throw new ConversationalRectificationError("service_unavailable");
  }
  return value;
}

function minute(value: string): number {
  const [hour = 0, part = 0] = value.split(":").map(Number);
  return hour * 60 + part;
}

function clock(value: number): string {
  const normalized = ((value % 1_440) + 1_440) % 1_440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function declaredRange(input: DeclaredBirthInput): { readonly startTime: string; readonly endTime: string } {
  if (input.source === "period_only") {
    return {
      early_morning: { startTime: "04:00", endTime: "07:59" },
      morning: { startTime: "08:00", endTime: "11:59" },
      afternoon: { startTime: "12:00", endTime: "17:59" },
      evening: { startTime: "18:00", endTime: "22:59" },
      late_night: { startTime: "23:00", endTime: "03:59" },
    }[input.reportedPeriod];
  }
  if (input.source === "unknown") return { startTime: "00:00", endTime: "23:59" };
  if (input.source === "legacy_import" && !input.reportedTime) {
    if (input.reportedPeriod) {
      return declaredRange({ ...input, source: "period_only", reportedPeriod: input.reportedPeriod });
    }
    return { startTime: "00:00", endTime: "23:59" };
  }
  const reportedTime = input.reportedTime;
  if (!reportedTime) throw new ConversationalRectificationError("profile_incomplete");
  const before = input.uncertaintyBeforeMinutes ?? 2;
  const after = input.uncertaintyAfterMinutes ?? 2;
  return {
    startTime: clock(minute(reportedTime) - before),
    endTime: clock(minute(reportedTime) + after),
  };
}

function scanCoordinates(range: { readonly startTime: string; readonly endTime: string }) {
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  if (end < start) end += 1_440;
  const center = Math.round((start + end) / 2);
  return {
    centerTime: clock(center),
    uncertaintyMinutes: Math.max(1, Math.ceil((end - start) / 2)),
  };
}

function boundedScanRanges(range: { readonly startTime: string; readonly endTime: string }) {
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  if (end < start) end += 1_440;
  if (end - start <= 360) return [range];

  const ranges: Array<{ readonly startTime: string; readonly endTime: string }> = [];
  let cursor = start;
  while (end - cursor > 360) {
    ranges.push({ startTime: clock(cursor), endTime: clock(cursor + 360) });
    cursor += 360;
  }
  if (cursor < end) {
    // A symmetric integer-minute scan needs an even endpoint span. Pull an
    // odd final span back by one minute, overlapping rather than inventing a
    // minute outside the user's declared range.
    const finalStart = (end - cursor) % 2 === 0 ? cursor : cursor - 1;
    ranges.push({ startTime: clock(finalStart), endTime: clock(end) });
  }
  return ranges;
}

function currentRange(input: ConversationalRectificationPacketBuildInput) {
  const start = input.privateCandidate?.rangeStart;
  const end = input.privateCandidate?.rangeEnd;
  return start && end ? { startTime: start, endTime: end } : declaredRange(input.declaredBirthInput);
}

function scoreableLifeEvents(
  evidence: readonly LifeEventEvidence[],
  birthDate: string,
): LifeEvent[] {
  return evidence.flatMap((item) => {
    if (item.scoreable !== true || !item.dateValue
      || !(["day", "month", "year"] as const).includes(item.datePrecision as "day" | "month" | "year")
      || evidencePredatesBirthDate(item, birthDate)) {
      return [];
    }
    if (item.domain === "family" || item.domain === "other") return [];
    return [{
      id: item.id,
      domain: item.domain,
      precision: item.datePrecision as "day" | "month" | "year",
      date: item.dateValue,
    } as LifeEvent];
  }).slice(-MAXIMUM_SCOREABLE_EVENTS);
}

function sampleTimes(scan: RectificationQuestionnaire): readonly { readonly sampleIndex: number; readonly time: string }[] {
  const raw = profileRecord(scan.raw.candidate_scan);
  const samples = Array.isArray(raw?.samples) ? raw.samples : [];
  const links = samples.flatMap((item, sampleIndex) => {
    const rawTime = text(profileRecord(item)?.time);
    const match = rawTime?.match(/(?:^|[T\s])(([01]\d|2[0-3]):[0-5]\d)/);
    return match?.[1] ? [{ sampleIndex, time: match[1] }] : [];
  });
  if (links.length !== scan.samples.length) {
    throw new ConversationalRectificationError("service_unavailable");
  }
  return links;
}

function timeOffsetFromRangeStart(time: string, rangeStart: string): number {
  const start = minute(rangeStart);
  let value = minute(time);
  if (value < start) value += 1_440;
  return value - start;
}

function timeIsInsideRange(
  time: string,
  range: { readonly startTime: string; readonly endTime: string },
): boolean {
  const offset = timeOffsetFromRangeStart(time, range.startTime);
  const endOffset = timeOffsetFromRangeStart(range.endTime, range.startTime);
  return offset <= endOffset;
}

function mergeQuestionnaireScans(
  scans: readonly RectificationQuestionnaire[],
  range: { readonly startTime: string; readonly endTime: string },
): RectificationQuestionnaire {
  const first = scans[0];
  if (!first) throw new ConversationalRectificationError("service_unavailable");

  const byTime = new Map<string, {
    sample: RectificationQuestionnaire["samples"][number];
    rawSample: unknown;
  }>();
  const questions = new Map<string, RectificationQuestionnaire["questions"][number]>();
  for (const scan of scans) {
    for (const question of scan.questions) {
      if (!questions.has(question.id)) questions.set(question.id, question);
    }
    const rawCandidateScan = profileRecord(scan.raw.candidate_scan);
    const rawSamples = Array.isArray(rawCandidateScan?.samples) ? rawCandidateScan.samples : [];
    for (const link of sampleTimes(scan)) {
      const sample = scan.samples[link.sampleIndex];
      const rawSample = rawSamples[link.sampleIndex];
      if (!sample || rawSample === undefined || !timeIsInsideRange(link.time, range)) continue;
      if (!byTime.has(link.time)) byTime.set(link.time, { sample, rawSample });
    }
  }
  const merged = [...byTime.entries()].sort(([left], [right]) =>
    timeOffsetFromRangeStart(left, range.startTime)
      - timeOffsetFromRangeStart(right, range.startTime));
  const firstCandidateScan = profileRecord(first.raw.candidate_scan) ?? {};
  return {
    questions: [...questions.values()],
    samples: merged.map(([, item]) => item.sample),
    raw: {
      ...first.raw,
      candidate_scan: {
        ...firstCandidateScan,
        samples: merged.map(([, item]) => item.rawSample),
      },
    },
  };
}

function layerMetadata(scan: RectificationQuestionnaire, calculationVersion: string) {
  const layers = [
    ["D1", "ascendantSign"],
    ["D4", "d4Sign"],
    ["D9", "d9Sign"],
    ["D10", "d10Sign"],
    ["D2", "d2Sign"],
    ["D11", "d11Sign"],
    ["D24", "d24Sign"],
    ["D30", "d30Sign"],
    ["A7", "a7Sign"],
    ["UL", "ulSign"],
    ["A10", "a10Sign"],
  ] as const;
  const availableLayers = layers
    .filter(([, key]) => scan.samples.some((sample) => typeof sample[key] === "string" && sample[key]?.trim()))
    .map(([layer]) => layer);
  return {
    availableLayers,
    layerReferences: Object.fromEntries(availableLayers.map((layer) => [
      layer,
      [`server-scan-${calculationVersion}-${layer.toLowerCase()}`],
    ])),
  };
}

function unavailableCandidateDifferences(
  caseId: string,
  range: { readonly startTime: string; readonly endTime: string },
): CandidateDifferenceBuild {
  return {
    packet: {
      caseId,
      scoringVersion: "birth-time-choice-scoring-v2",
      currentRange: range,
      opportunities: [],
      askedQuestionFingerprints: [],
      candidatePartitionFingerprints: [],
      recentRangeHistory: [],
    },
    candidateModel: { version: "birth-time-choice-scoring-v2" },
    scoringPartitions: {},
  };
}

function candidateDifferencesAreUnavailable(error: unknown): boolean {
  return error instanceof Error && [
    "AbortError",
    "TimeoutError",
    "BirthTimeJourneyEngineError",
    "BirthTimeJourneyEngineConfigurationError",
  ].includes(error.name);
}

function candidateDifferenceRangeIsTooWide(
  range: { readonly startTime: string; readonly endTime: string },
): boolean {
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  if (end < start) end += 1_440;
  return end - start > 360;
}

function boundaryDistance(range: { readonly startTime: string; readonly endTime: string }, representative: string) {
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  let value = minute(representative);
  if (end < start) end += 1_440;
  if (value < start) value += 1_440;
  return Math.max(0, Math.min(value - start, end - value));
}

async function rectificationPacketStage<Value>(
  stage: "score_events" | "scan" | "merge_scans" | "candidate_differences" | "time_links" | "technical_packet",
  operation: () => Value | Promise<Value>,
): Promise<Value> {
  try {
    return await operation();
  } catch (error) {
    const errorKind = error instanceof Error ? error.name : typeof error;
    const status = error !== null && typeof error === "object" && "status" in error
      && typeof error.status === "number" ? error.status : null;
    console.error(`[birth-time-conversation-packet] stage=${stage} error=${errorKind}${status === null ? "" : ` status=${status}`}`);
    throw error;
  }
}

export async function buildProductionConversationalRectificationPacket(
  engine: BirthTimeJourneyEngine,
  input: ConversationalRectificationPacketBuildInput,
) {
  const place = input.declaredBirthInput.birthplace;
  if (place.latitude === undefined || place.longitude === undefined) {
    throw new ConversationalRectificationError("profile_incomplete");
  }
  const latitude = place.latitude;
  const longitude = place.longitude;
  const baseRange = currentRange(input);
  const events = scoreableLifeEvents(
    input.evidence as readonly LifeEventEvidence[],
    input.declaredBirthInput.birthDate,
  );
  const eventScore: CandidateResult | null = events.length >= 3
    ? await rectificationPacketStage("score_events", () => engine.scoreEvents({
        birthDate: input.declaredBirthInput.birthDate,
        startTime: baseRange.startTime,
        endTime: baseRange.endTime,
        lat: latitude,
        lon: longitude,
        tz: place.timezoneOffset,
        events,
      }))
    : null;
  const selectedRange = !input.preserveCandidateRange && eventScore?.winningSegment
    ? { startTime: eventScore.winningSegment.startTime, endTime: eventScore.winningSegment.endTime }
    : baseRange;
  const calculationVersion = eventScore
    ? eventScore.algorithmVersion
    : null;
  const technicalPacketModule = await import(
    "../../../lib/conversational-rectification/technical-packet.ts"
  );
  const buildForRange = async (
    range: { readonly startTime: string; readonly endTime: string },
    packetEventScore: CandidateResult | null,
  ) => {
    const questionnaires: RectificationQuestionnaire[] = [];
    for (const scanRange of boundedScanRanges(range)) {
      const scanPoint = scanCoordinates(scanRange);
      const { questionnaire } = await rectificationPacketStage("scan", () => engine.scan({
        birthTime: `${input.declaredBirthInput.birthDate} ${scanPoint.centerTime}`,
        uncertaintyMinutes: scanPoint.uncertaintyMinutes,
        lat: latitude,
        lon: longitude,
        tz: place.timezoneOffset,
        ayanamsa: "lahiri",
      }));
      questionnaires.push(questionnaire);
    }
    const questionnaire = await rectificationPacketStage(
      "merge_scans",
      () => mergeQuestionnaireScans(questionnaires, range),
    );
    let candidateDifferences = unavailableCandidateDifferences(input.caseId, range);
    if (!candidateDifferenceRangeIsTooWide(range)) {
      try {
        candidateDifferences = await rectificationPacketStage(
          "candidate_differences",
          () => engine.buildDifferencePacket({
          caseId: input.caseId,
          asOfDate: input.asOfDate,
          birthDate: input.declaredBirthInput.birthDate,
          startTime: range.startTime,
          endTime: range.endTime,
          lat: latitude,
          lon: longitude,
          tz: place.timezoneOffset,
          evidence: [],
          events,
          dismissedOpportunityIds: [],
          questionFingerprints: [],
          partitionFingerprints: [],
          recentRanges: [],
          candidateModel: null,
          }),
        );
      } catch (error) {
        if (!candidateDifferencesAreUnavailable(error)) throw error;
        // Candidate partitions improve question ranking, but evidence collection can still
        // proceed from the server scan. Do not turn an optional slow dependency into a 503.
      }
    }
    const version = calculationVersion
      ? `${candidateDifferences.packet.scoringVersion}+${calculationVersion}`
      : candidateDifferences.packet.scoringVersion;
    const metadata = layerMetadata(questionnaire, version);
    const timeLinkedScanSamples = await rectificationPacketStage(
      "time_links",
      () => sampleTimes(questionnaire),
    );
    const representative = packetEventScore?.winningSegment?.representativeTime
      ?? scanCoordinates(range).centerTime;
    return technicalPacketModule.buildRectificationTechnicalPacket({
      scan: questionnaire,
      candidateDifferences,
      eventScore: packetEventScore,
      consultation: {
        source: "server_consultation_workflow",
        calculationVersion: version,
        availableLayers: metadata.availableLayers,
        layerReferences: metadata.layerReferences,
        timeLinkedScanSamples,
        boundaryDistanceMinutes: boundaryDistance(range, representative),
        futureWindows: [],
      },
    });
  };

  const packetEventScore = input.preserveCandidateRange && eventScore
    ? { ...eventScore, confidence: "low" as const, canApply: false, winningSegment: null }
    : eventScore;
  try {
    return {
      packet: await buildForRange(selectedRange, packetEventScore),
      resultId: eventScore?.resultId ?? null,
    };
  } catch (error) {
    const selectedWasNarrowed = selectedRange.startTime !== baseRange.startTime
      || selectedRange.endTime !== baseRange.endTime;
    if (!selectedWasNarrowed
      || !(error instanceof technicalPacketModule.RectificationTechnicalPacketRangeError)) {
      return rectificationPacketStage("technical_packet", () => Promise.reject(error));
    }
    return {
      packet: await rectificationPacketStage("technical_packet", () => buildForRange(
        baseRange,
        eventScore
          ? { ...eventScore, confidence: "low", canApply: false, winningSegment: null }
          : null,
      )),
      resultId: null,
    };
  }
}

async function productionNarrativeGenerator(): Promise<RectificationNarrativeGenerator> {
  const [{ defaultLanguageModel }, { Agent }] = await Promise.all([
    import("../../../mastra/model.ts"),
    import("@mastra/core/agent"),
  ]);
  const model = defaultLanguageModel();
  if (!model) {
    return {
      modelId: "deterministic-rectification-fallback",
      async generate() { throw new Error("NarrativeModelUnavailable"); },
    };
  }
  const agent = new Agent({
    id: `conversational-rectification-${model.id}`,
    name: "Conversational Rectification Narrator",
    model: model.model,
    skills: [jyotishSkillPath],
    instructions: "Return only the exact JSON object requested by the user prompt. Use the Jyotish Skill only to choose a natural, one-question-at-a-time evidence strategy and wording. Treat supplied packet facts as the exclusive source of candidate times, status, dates, layers, scores, references, and confirmation permissions. Never invent, recalculate, or confirm candidate data.",
  });
  return {
    modelId: model.id,
    async generate(prompt) {
      const result = await agent.generate([{ role: "user", content: prompt }]);
      return { text: result.text };
    },
  };
}

async function createProductionService(
  authenticated: AuthenticatedRequest,
): Promise<BirthTimeConversationRouteService> {
  const [
    { createAdminSupabaseClient },
    { createSupabaseConversationalRectificationStore },
    { createSupabaseConversationalRectificationBilling },
    { createJyotishBirthTimeJourneyEngine },
    narrativeGenerator,
  ] = await Promise.all([
    import("../../../lib/supabase/admin.ts"),
    import("../../../lib/conversational-rectification/store.ts"),
    import("../../../lib/conversational-rectification/billing.ts"),
    import("../../../lib/birth-time-journey-engine.ts"),
    productionNarrativeGenerator(),
  ]);
  const admin = createAdminSupabaseClient();
  const profileClient = authenticated.context as ProfileClient;
  const engine = createJyotishBirthTimeJourneyEngine();
  return createConversationalRectificationService({
    store: createSupabaseConversationalRectificationStore(admin),
    billing: createSupabaseConversationalRectificationBilling(admin),
    get rectificationPriceCredits() { return priceCredits(); },
    allowNewCaseCreation: conversationalRectificationCreationPolicyFromEnvironment(
      authenticated.userId,
    ).allowNewCaseCreation,
    async loadDeclaredProfile(userId) {
      return loadProductionConversationalRectificationProfile({
        async loadProfile(receivedUserId) {
          const { data, error } = await profileClient
            .from("profiles")
            .select("birth_date,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,rectification_case_id")
            .eq("id", receivedUserId)
            .maybeSingle();
          if (error) throw new ConversationalRectificationError("store_unavailable");
          return data;
        },
        async loadRectificationCase(receivedUserId, receivedCaseId) {
          const { data, error } = await admin
            .from("birth_time_rectification_cases")
            .select("id,journey_protocol,status")
            .eq("id", receivedCaseId)
            .eq("user_id", receivedUserId)
            .maybeSingle();
          if (error) throw new ConversationalRectificationError("store_unavailable");
          return data;
        },
      }, userId);
    },
    async loadLegacyCase(userId, legacyCaseId) {
      const { createJourneyLoadClient, loadStoredRectificationCase } = await import(
        "../../../lib/birth-time-journey-case-loader.ts"
      );
      const { data: identity, error } = await admin
        .from("birth_time_rectification_cases")
        .select("id,user_id,journey_protocol,status,reported_date,reported_time,reported_period,source,uncertainty_before_minutes,uncertainty_after_minutes")
        .eq("id", legacyCaseId)
        .eq("user_id", userId)
        .maybeSingle();
      if (error || !identity
        || (identity.journey_protocol !== "legacy-guided-v1"
          && identity.journey_protocol !== "dynamic-choice-v2")) return null;
      const { data: currentProfile, error: profileError } = await profileClient
        .from("profiles")
        .select("birth_date,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,rectification_case_id")
        .eq("id", userId)
        .maybeSingle();
      if (profileError || !currentProfile) {
        throw new ConversationalRectificationError("store_unavailable");
      }
      const declaredBirthInput = declaredBirthInputForLegacyCase(currentProfile, identity);
      const loaded = await loadStoredRectificationCase(
        createJourneyLoadClient(admin),
        userId,
        legacyCaseId,
      );
      if (!loaded) return null;
      const winning = loaded.candidateResult?.winningSegment;
      const snapshotRange = loaded.snapshot.reportedRange;
      const currentRange = loaded.journeyProtocol === "dynamic-choice-v2"
        ? loaded.dynamicTurnState.progress.currentRange
        : winning
          ? { startTime: winning.startTime, endTime: winning.endTime }
          : snapshotRange.startTime && snapshotRange.endTime
            ? { startTime: snapshotRange.startTime, endTime: snapshotRange.endTime }
            : null;
      if (!currentRange) throw new ConversationalRectificationError("store_unavailable");
      return {
        caseId: loaded.id,
        userId: loaded.userId,
        journeyProtocol: loaded.journeyProtocol,
        status: identity.status,
        turnVersion: loaded.turnVersion ?? 0,
        declaredBirthInput,
        currentRange,
        lifeEvents: loaded.lifeEvents ?? [],
      };
    },
    buildTechnicalPacket: (input) => buildProductionConversationalRectificationPacket(engine, input),
    narrativeGenerator,
    asOfDate: () => new Date().toISOString().slice(0, 10),
  });
}

function stableRequestId(request: Request): string {
  const supplied = request.headers.get("x-request-id");
  return supplied && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(supplied)
    ? supplied.toLowerCase()
    : randomUUID();
}

async function dispatch(
  service: BirthTimeConversationRouteService,
  userId: string,
  command: ConversationalRectificationCommand,
): Promise<ConversationalRectificationTurn> {
  switch (command.type) {
    case "start": return service.start(userId, command);
    case "resume": return service.resume(userId, command);
    case "answer": return service.answer(userId, command);
    case "pause": return service.pause(userId, command);
    case "abandon": return service.abandon(userId, command);
    case "confirm": return service.confirm(userId, command);
  }
}

function telemetryPhase(
  turn: Pick<ConversationalRectificationTurn, "status"> | null,
): ConversationalRectificationTelemetryPayload["phase"] {
  switch (turn?.status) {
    case "active": return "collecting_evidence";
    case "paused": return "paused";
    case "confirming": return "confirming";
    case "completed": return "completed";
    case "abandoned": return "abandoned";
    default: return "entry";
  }
}

function telemetryErrorCategory(
  code: string,
): ConversationalRectificationTelemetryPayload["errorCategory"] {
  if (code === "authentication_required") return "authentication";
  if (code === "invalid_command" || code === "profile_incomplete") return "validation";
  if (code === "stale_turn" || code === "action_conflict" || code === "candidate_changed"
    || code === "invalid_transition" || code === "case_not_found") return "conflict";
  if (code === "billing_failed") return "billing";
  if (code === "service_unavailable" || code === "store_unavailable") return "dependency";
  return "unknown";
}

function telemetryResultCategory(
  status: number,
): ConversationalRectificationTelemetryPayload["resultCategory"] {
  if (status === 409) return "conflict";
  if (status >= 400 && status < 500) return "rejected";
  return "failed";
}

export function createBirthTimeConversationPostHandler(
  dependencies: BirthTimeConversationPostDependencies,
) {
  return async function handleBirthTimeConversationPost(request: Request): Promise<Response> {
    const startedAt = dependencies.now?.() ?? Date.now();
    const now = dependencies.now ?? Date.now;
    const telemetry = dependencies.telemetry
      ? createConversationalRectificationTelemetry(dependencies.telemetry)
      : recordConversationalRectificationTelemetry;
    const deploymentSha = safeConversationalRectificationDeploymentSha(
      dependencies.deploymentSha
      ?? process.env.GITHUB_SHA
      ?? process.env.VERCEL_GIT_COMMIT_SHA
      ?? process.env.NEXT_PUBLIC_GIT_COMMIT,
    );
    dependencies.createRequestId?.(request);
    let actionKind: ConversationalRectificationTelemetryPayload["actionKind"] = "unknown";
    let service: BirthTimeConversationRouteService | null = null;
    try {
      const authenticated = await dependencies.authenticate(request);
      if (!authenticated) throw new ConversationalRectificationError("authentication_required");

      const parsed = conversationalRectificationCommandSchema.safeParse(await requestPayload(request));
      if (!parsed.success) throw new ConversationalRectificationError("invalid_command");
      actionKind = parsed.data.type;

      service = await dependencies.createService(authenticated);
      const turn = await dispatch(service, authenticated.userId, parsed.data);
      const outcome = conversationalRectificationTelemetryOutcome(service);
      telemetry({
        protocol: "conversational-evidence-v3",
        phase: telemetryPhase(turn),
        actionKind,
        resultCategory: "success",
        latencyBucket: conversationalRectificationLatencyBucket(now() - startedAt),
        billingState: outcome?.billingState ?? (actionKind === "start" ? "unknown" : "unchanged"),
        errorCategory: "none",
        deploymentSha,
      });
      return Response.json(turn);
    } catch (error) {
      const publicError = toConversationalRectificationPublicError(error);
      const outcome = service ? conversationalRectificationTelemetryOutcome(service) : null;
      dependencies.log?.({ code: publicError.code });
      telemetry({
        protocol: "conversational-evidence-v3",
        phase: telemetryPhase(outcome?.caseStatus ? { status: outcome.caseStatus } : null),
        actionKind,
        resultCategory: telemetryResultCategory(publicError.status),
        latencyBucket: conversationalRectificationLatencyBucket(now() - startedAt),
        billingState: outcome?.billingState
          ?? (publicError.code === "billing_failed" ? "unknown" : "not_applicable"),
        errorCategory: telemetryErrorCategory(publicError.code),
        deploymentSha,
      });
      return Response.json(publicError, { status: publicError.status });
    }
  };
}

const productionPost = createBirthTimeConversationPostHandler({
  authenticate: authenticateProductionRequest,
  createService: createProductionService,
  createRequestId: stableRequestId,
  deploymentSha: process.env.GITHUB_SHA
    ?? process.env.VERCEL_GIT_COMMIT_SHA
    ?? process.env.NEXT_PUBLIC_GIT_COMMIT,
  log(entry) {
    console.error(`[birth-time-conversation] code=${entry.code}`);
  },
});

export async function POST(request: Request) {
  return productionPost(request);
}
