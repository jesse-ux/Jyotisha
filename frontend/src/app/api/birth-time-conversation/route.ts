import { randomUUID } from "node:crypto";
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

export const runtime = "nodejs";
export const maxDuration = 60;

type AuthenticatedRequest = Readonly<{
  userId: string;
  context: unknown;
}>;

export type BirthTimeConversationRouteService = ConversationalRectificationService;

export type BirthTimeConversationRouteLog = Readonly<{
  requestId: string;
  actionId: string | null;
  caseId: string | null;
  code: string;
}>;

export type BirthTimeConversationPostDependencies = Readonly<{
  authenticate(request: Request): Promise<AuthenticatedRequest | null>;
  createService(authenticated: AuthenticatedRequest): Promise<BirthTimeConversationRouteService>;
  createRequestId?(request: Request): string;
  log?(entry: BirthTimeConversationRouteLog): void;
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
}>> {
  const profileValue = await dependencies.loadProfile(userId);
  const profile = profileRecord(profileValue);
  if (!profile) throw new ConversationalRectificationError("profile_incomplete");
  const declaredBirthInput = declaredBirthInputFromProfile(profile);
  const priorCaseId = text(profile.rectification_case_id);
  if (!priorCaseId) return { declaredBirthInput, revisionOfCaseId: null };

  const prior = profileRecord(await dependencies.loadRectificationCase(userId, priorCaseId));
  const terminalV3Revision = prior
    && text(prior.id) === priorCaseId
    && text(prior.journey_protocol) === "conversational-evidence-v3"
    && (text(prior.status) === "completed" || text(prior.status) === "abandoned");
  return {
    declaredBirthInput,
    revisionOfCaseId: terminalV3Revision ? priorCaseId : null,
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
  }).slice(-6);
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
    ["D24", "d24Sign"],
    ["D30", "d30Sign"],
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

function boundaryDistance(range: { readonly startTime: string; readonly endTime: string }, representative: string) {
  const start = minute(range.startTime);
  let end = minute(range.endTime);
  let value = minute(representative);
  if (end < start) end += 1_440;
  if (value < start) value += 1_440;
  return Math.max(0, Math.min(value - start, end - value));
}

export async function buildProductionConversationalRectificationPacket(
  engine: BirthTimeJourneyEngine,
  input: ConversationalRectificationPacketBuildInput,
) {
  const place = input.declaredBirthInput.birthplace;
  if (place.latitude === undefined || place.longitude === undefined) {
    throw new ConversationalRectificationError("profile_incomplete");
  }
  const baseRange = currentRange(input);
  const events = scoreableLifeEvents(
    input.evidence as readonly LifeEventEvidence[],
    input.declaredBirthInput.birthDate,
  );
  const eventScore: CandidateResult | null = events.length >= 3
    ? await engine.scoreEvents({
        birthDate: input.declaredBirthInput.birthDate,
        startTime: baseRange.startTime,
        endTime: baseRange.endTime,
        lat: place.latitude,
        lon: place.longitude,
        tz: place.timezoneOffset,
        events,
      })
    : null;
  const selectedRange = eventScore?.winningSegment
    ? { startTime: eventScore.winningSegment.startTime, endTime: eventScore.winningSegment.endTime }
    : baseRange;
  const questionnaires: RectificationQuestionnaire[] = [];
  for (const scanRange of boundedScanRanges(selectedRange)) {
    const scanPoint = scanCoordinates(scanRange);
    const { questionnaire } = await engine.scan({
      birthTime: `${input.declaredBirthInput.birthDate} ${scanPoint.centerTime}`,
      uncertaintyMinutes: scanPoint.uncertaintyMinutes,
      lat: place.latitude,
      lon: place.longitude,
      tz: place.timezoneOffset,
      ayanamsa: "lahiri",
    });
    questionnaires.push(questionnaire);
  }
  const questionnaire = mergeQuestionnaireScans(questionnaires, selectedRange);
  const candidateDifferences = await engine.buildDifferencePacket({
    caseId: input.caseId,
    asOfDate: input.asOfDate,
    birthDate: input.declaredBirthInput.birthDate,
    startTime: selectedRange.startTime,
    endTime: selectedRange.endTime,
    lat: place.latitude,
    lon: place.longitude,
    tz: place.timezoneOffset,
    evidence: [],
    dismissedOpportunityIds: [],
    questionFingerprints: [],
    partitionFingerprints: [],
    recentRanges: [],
    candidateModel: null,
  });
  const calculationVersion = eventScore
    ? `${candidateDifferences.packet.scoringVersion}+${eventScore.algorithmVersion}`
    : candidateDifferences.packet.scoringVersion;
  const metadata = layerMetadata(questionnaire, calculationVersion);
  const representative = eventScore?.winningSegment?.representativeTime
    ?? scanCoordinates(selectedRange).centerTime;
  const { buildRectificationTechnicalPacket } = await import(
    "../../../lib/conversational-rectification/technical-packet.ts"
  );
  return {
    packet: buildRectificationTechnicalPacket({
      scan: questionnaire,
      candidateDifferences,
      eventScore,
      consultation: {
        source: "server_consultation_workflow",
        calculationVersion,
        availableLayers: metadata.availableLayers,
        layerReferences: metadata.layerReferences,
        timeLinkedScanSamples: sampleTimes(questionnaire),
        boundaryDistanceMinutes: boundaryDistance(selectedRange, representative),
        futureWindows: [],
      },
    }),
    resultId: eventScore?.resultId ?? null,
  };
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
    instructions: "Return only the exact JSON object requested by the user prompt. Use only supplied packet facts. Never invent times, layers, references, scores, dates, or confirmation state.",
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

function errorResponse(error: unknown) {
  const publicError = toConversationalRectificationPublicError(error);
  return Response.json(publicError, { status: publicError.status });
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

export function createBirthTimeConversationPostHandler(
  dependencies: BirthTimeConversationPostDependencies,
) {
  return async function handleBirthTimeConversationPost(request: Request): Promise<Response> {
    const requestId = dependencies.createRequestId?.(request) ?? stableRequestId(request);
    let actionId: string | null = null;
    let caseId: string | null = null;
    try {
      const authenticated = await dependencies.authenticate(request);
      if (!authenticated) return errorResponse(new ConversationalRectificationError("authentication_required"));

      const parsed = conversationalRectificationCommandSchema.safeParse(await requestPayload(request));
      if (!parsed.success) return errorResponse(new ConversationalRectificationError("invalid_command"));
      actionId = parsed.data.actionId;
      caseId = parsed.data.type === "start" ? parsed.data.actionId : parsed.data.caseId;

      const service = await dependencies.createService(authenticated);
      return Response.json(await dispatch(service, authenticated.userId, parsed.data));
    } catch (error) {
      const publicError = toConversationalRectificationPublicError(error);
      dependencies.log?.({ requestId, actionId, caseId, code: publicError.code });
      return Response.json(publicError, { status: publicError.status });
    }
  };
}

const productionPost = createBirthTimeConversationPostHandler({
  authenticate: authenticateProductionRequest,
  createService: createProductionService,
  createRequestId: stableRequestId,
  log(entry) {
    console.error(
      `[birth-time-conversation] request=${entry.requestId} action=${entry.actionId ?? "none"} case=${entry.caseId ?? "none"} code=${entry.code}`,
    );
  },
});

export async function POST(request: Request) {
  return productionPost(request);
}
