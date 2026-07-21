import { z } from "zod";
import type { LifeEvent } from "../birth-time-evidence.ts";
import { ConversationalRectificationError } from "./errors.ts";
import {
  declaredBirthInputSchema,
  lifeEventEvidenceSchema,
  type DeclaredBirthInput,
  type LifeEventEvidence,
} from "./persistence-contracts.ts";

const uuidSchema = z.string().uuid();
const dateSchema = z.string().date();
const timeRangeSchema = z.object({
  startTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  endTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
}).strict().readonly();

const unfinishedLegacyStatuses = new Set([
  "assessing",
  "rectifying",
  "candidate",
  "confirming",
]);

export type LegacyConversationalImportSource = Readonly<{
  caseId: string;
  userId: string;
  journeyProtocol: "legacy-guided-v1" | "dynamic-choice-v2";
  status: string;
  turnVersion: number;
  declaredBirthInput: DeclaredBirthInput;
  currentRange: Readonly<{ startTime: string; endTime: string }>;
  lifeEvents: readonly LifeEvent[];
  // Loaders may carry these old private fields. The projection deliberately
  // never reads them: choices are not dated life-event facts.
  currentChoicePrompt?: string | null;
  choiceAnswers?: readonly unknown[];
}>;

export type ProjectedLegacyConversationalImport = Readonly<{
  legacyCaseId: string;
  expectedVersion: number;
  declaredBirthInput: DeclaredBirthInput;
  currentRange: Readonly<{ startTime: string; endTime: string }>;
  evidence: readonly LifeEventEvidence[];
}>;

const domainLabels = {
  career: "事业",
  education: "学业",
  relocation: "迁居",
  relationship: "关系",
  family: "家庭",
  other: "其他",
} as const;

function importedDomain(domain: LifeEvent["domain"]): LifeEventEvidence["domain"] {
  return domain === "finance" || domain === "health_pressure" ? "other" : domain;
}

function eventIsWithinHistoricalWindow(
  event: LifeEvent,
  birthDate: string,
  asOfDate: string,
): boolean {
  const lowerBound = event.precision === "year"
    ? birthDate.slice(0, 4)
    : event.precision === "month" ? birthDate.slice(0, 7) : birthDate;
  const upperBound = event.precision === "year"
    ? asOfDate.slice(0, 4)
    : event.precision === "month" ? asOfDate.slice(0, 7) : asOfDate;
  return event.date >= lowerBound && event.date <= upperBound;
}

function importedEvidence(event: LifeEvent): LifeEventEvidence {
  const domain = importedDomain(event.domain);
  const label = domainLabels[domain];
  const summary = `旧校时记录中的${label}事件`;
  return lifeEventEvidenceSchema.parse({
    id: event.id,
    rawText: `${summary}（${event.date}）`,
    domain,
    eventSummary: summary,
    dateValue: event.date,
    datePrecision: event.precision,
    extractionStatus: "clear",
    scoreable: true,
    correctsEvidenceIds: [],
  });
}

export function projectLegacyCaseForConversationalImport(input: Readonly<{
  source: LegacyConversationalImportSource;
  asOfDate: string;
  expectedUserId?: string;
}>): ProjectedLegacyConversationalImport {
  const source = input.source;
  const sourceCaseId = uuidSchema.safeParse(source.caseId);
  const sourceUserId = uuidSchema.safeParse(source.userId);
  const expectedUserId = input.expectedUserId === undefined
    ? null
    : uuidSchema.safeParse(input.expectedUserId);
  if (!sourceCaseId.success || !sourceUserId.success
    || (expectedUserId !== null && (!expectedUserId.success
      || expectedUserId.data !== sourceUserId.data))) {
    throw new ConversationalRectificationError("case_not_found");
  }
  if (source.journeyProtocol !== "legacy-guided-v1"
    && source.journeyProtocol !== "dynamic-choice-v2") {
    throw new ConversationalRectificationError("case_not_found");
  }
  if (!unfinishedLegacyStatuses.has(source.status)) {
    throw new ConversationalRectificationError("invalid_transition");
  }
  if (!Number.isSafeInteger(source.turnVersion) || source.turnVersion < 0) {
    throw new ConversationalRectificationError("case_not_found");
  }
  const range = timeRangeSchema.safeParse(source.currentRange);
  const declared = declaredBirthInputSchema.safeParse(source.declaredBirthInput);
  const asOfDate = dateSchema.safeParse(input.asOfDate);
  if (!range.success || !declared.success || !asOfDate.success) {
    throw new ConversationalRectificationError("profile_incomplete");
  }

  const evidence: LifeEventEvidence[] = [];
  const importedIds = new Set<string>();
  for (const event of source.lifeEvents) {
    if (importedIds.has(event.id)
      || !eventIsWithinHistoricalWindow(event, declared.data.birthDate, asOfDate.data)) continue;
    try {
      const projected = importedEvidence(event);
      importedIds.add(projected.id);
      evidence.push(projected);
    } catch {
      // Legacy rows predate today's stricter schema. Invalid historical
      // fragments remain in the read-only old row and never become v3 facts.
    }
  }

  return Object.freeze({
    legacyCaseId: sourceCaseId.data,
    expectedVersion: source.turnVersion,
    declaredBirthInput: declared.data,
    currentRange: range.data,
    evidence: Object.freeze(evidence.slice(-20)),
  });
}
