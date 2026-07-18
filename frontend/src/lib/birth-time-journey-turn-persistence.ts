import type { SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";
import {
  parseRectificationQuestionnaire,
  parseRectificationScoring,
} from "./birth-time-journey-adapters.ts";
import {
  candidateResultSchema,
  journeySnapshotSchema,
  lifeEventSchema,
} from "./birth-time-journey.ts";
import type { JourneySnapshot } from "./birth-time-journey.ts";
import type { StoredRectificationCase } from "./birth-time-journey-service.ts";
import { evidenceDomains } from "./birth-time-question-planner.ts";
import {
  evidenceDraftSchema,
  journeyTurnStateSchema,
} from "./birth-time-journey-turn.ts";
import type { EvidenceDomain } from "./birth-time-question-planner.ts";
import type { EvidenceDraft, JourneyTurnState } from "./birth-time-journey-turn.ts";

const answerSchema = z.enum(["A", "B", "C", "D"]);
const actionIdSchema = z.string().uuid();
const storedCaseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  journey_snapshot: journeySnapshotSchema,
  questionnaire: z.record(z.unknown()),
  answers: z.record(answerSchema),
  scoring_result: z.record(z.unknown()),
  reported_date: z.string(),
  life_events: z.array(lifeEventSchema).default([]),
  candidate_result: z.record(z.unknown()).default({}),
  turn_version: z.number().int().nonnegative().default(0),
  turn_state: z.unknown().default({}),
  evidence_draft: z.unknown().nullable().default(null),
  processed_action_ids: z.array(z.string().uuid()).default([]),
  adaptive_round: z.number().int().min(0).max(3).default(0),
  asked_domains: z.array(z.enum(evidenceDomains)).default([]),
});
const eventLocationSchema = z.object({
  latitude: z.number(),
  longitude: z.number(),
  timezone_offset: z.number(),
});

export class BirthTimeJourneyStoreError extends Error {
  readonly name = "BirthTimeJourneyStoreError";
  readonly operation: "insert_case" | "update_profile" | "load_case" | "update_case";

  constructor(operation: "insert_case" | "update_profile" | "load_case" | "update_case") {
    super(`Birth-time journey persistence failed during ${operation}`);
    this.operation = operation;
  }
}

export type PersistedJourneyProgress = {
  readonly adaptiveRound: number;
  readonly askedDomains: readonly EvidenceDomain[];
};

export type PersistedJourneyTurn = {
  readonly turnVersion: number;
  readonly turnState: JourneyTurnState | null;
  readonly evidenceDraft: EvidenceDraft | null;
  readonly processedActionIds: readonly string[];
  readonly persistedProgress: PersistedJourneyProgress;
};

export class StaleJourneyTurnError extends Error {
  readonly name = "StaleJourneyTurnError";
  readonly caseId: string;
  readonly expectedVersion: number;
  readonly currentVersion: number;

  constructor(
    caseId: string,
    expectedVersion: number,
    currentVersion: number,
  ) {
    super(`Journey turn ${caseId} is stale at version ${expectedVersion}`);
    this.caseId = caseId;
    this.expectedVersion = expectedVersion;
    this.currentVersion = currentVersion;
  }
}

export function caseStatus(snapshot: JourneySnapshot) {
  switch (snapshot.state) {
    case "ready":
      return "confirmed";
    case "candidate":
      return "candidate";
    case "confirming":
      return "confirming";
    case "rectifying":
      return "rectifying";
    default: {
      const exhaustive: never = snapshot.state;
      return exhaustive;
    }
  }
}

export function profileStatus(snapshot: JourneySnapshot) {
  if (snapshot.state === "ready") return "confirmed";
  if (snapshot.state === "confirming") return "candidate";
  return caseStatus(snapshot);
}

function isExactEmptyLegacyTurn(value: unknown): boolean {
  return typeof value === "object"
    && value !== null
    && !Array.isArray(value)
    && Object.keys(value).length === 0;
}

function parsePersistedTurnState(value: unknown): JourneyTurnState | null {
  if (isExactEmptyLegacyTurn(value)) return null;
  const parsed = journeyTurnStateSchema.safeParse(value);
  if (parsed.success) return parsed.data;
  throw new BirthTimeJourneyStoreError("load_case");
}

function parsePersistedEvidenceDraft(value: unknown): EvidenceDraft | null {
  if (value === null) return null;
  const parsed = evidenceDraftSchema.safeParse(value);
  if (parsed.success) return parsed.data;
  throw new BirthTimeJourneyStoreError("load_case");
}

function canonicalAskedDomains(input: readonly EvidenceDomain[]): readonly EvidenceDomain[] {
  return evidenceDomains.filter((domain) => input.includes(domain));
}

export async function loadStoredRectificationCase(
  supabase: SupabaseClient,
  userId: string,
  caseId: string,
): Promise<StoredRectificationCase | null> {
  const { data, error } = await supabase
    .from("birth_time_rectification_cases")
    .select("id,user_id,journey_snapshot,questionnaire,answers,scoring_result,reported_date,life_events,candidate_result,turn_version,turn_state,evidence_draft,processed_action_ids,adaptive_round,asked_domains")
    .eq("id", caseId)
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw new BirthTimeJourneyStoreError("load_case");
  if (!data) return null;
  const parsed = storedCaseSchema.parse(data);
  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("latitude,longitude,timezone_offset")
    .eq("id", userId)
    .maybeSingle();
  if (profileError || !profile) throw new BirthTimeJourneyStoreError("load_case");
  const location = eventLocationSchema.parse(profile);
  const scoring = Object.keys(parsed.scoring_result).length > 0
    ? parseRectificationScoring(parsed.scoring_result)
    : undefined;
  const questionnaire = Object.keys(parsed.questionnaire).length > 0
    ? parseRectificationQuestionnaire(parsed.questionnaire)
    : null;
  const candidateResult = Object.keys(parsed.candidate_result).length > 0
    ? candidateResultSchema.parse(parsed.candidate_result)
    : null;
  const turnState = parsePersistedTurnState(parsed.turn_state);
  const evidenceDraft = parsePersistedEvidenceDraft(parsed.evidence_draft);
  return {
    id: parsed.id,
    userId: parsed.user_id,
    snapshot: parsed.journey_snapshot,
    questionnaire,
    answers: parsed.answers,
    eventContext: {
      birthDate: parsed.reported_date,
      lat: location.latitude,
      lon: location.longitude,
      tz: location.timezone_offset,
    },
    lifeEvents: parsed.life_events,
    candidateResult,
    turnVersion: parsed.turn_version,
    turnState,
    evidenceDraft,
    processedActionIds: parsed.processed_action_ids,
    persistedProgress: {
      adaptiveRound: parsed.adaptive_round,
      askedDomains: parsed.asked_domains,
    },
    ...(scoring ? { scoring } : {}),
  } satisfies StoredRectificationCase;
}

export function createJourneyTurnPersistence(
  supabase: SupabaseClient,
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
) {
  return {
    async saveTurn(
      value: StoredRectificationCase,
      expectedVersion: number,
      actionId: string,
    ): Promise<StoredRectificationCase> {
      if (!value.turnState) throw new BirthTimeJourneyStoreError("update_case");
      const parsedActionId = actionIdSchema.parse(actionId).toLowerCase();
      const receipts = [...(value.processedActionIds ?? []), parsedActionId].slice(-100);
      const askedDomains = canonicalAskedDomains(value.persistedProgress?.askedDomains ?? []);
      const { data, error } = await supabase
        .from("birth_time_rectification_cases")
        .update({
          status: caseStatus(value.snapshot),
          journey_snapshot: value.snapshot,
          answers: value.answers,
          life_events: value.lifeEvents ?? [],
          candidate_result: value.candidateResult ?? {},
          turn_version: expectedVersion + 1,
          turn_state: value.turnState,
          evidence_draft: value.evidenceDraft ?? null,
          processed_action_ids: receipts,
          adaptive_round: value.persistedProgress?.adaptiveRound ?? 0,
          asked_domains: askedDomains,
          updated_at: new Date().toISOString(),
        })
        .eq("id", value.id)
        .eq("user_id", value.userId)
        .eq("turn_version", expectedVersion)
        .not("processed_action_ids", "cs", `{${parsedActionId}}`)
        .select("id")
        .maybeSingle();
      if (error) throw new BirthTimeJourneyStoreError("update_case");
      if (data) {
        return {
          ...value,
          turnVersion: expectedVersion + 1,
          processedActionIds: receipts,
          persistedProgress: {
            adaptiveRound: value.persistedProgress?.adaptiveRound ?? 0,
            askedDomains,
          },
        } satisfies StoredRectificationCase;
      }
      const current = await loadCase(value.userId, value.id);
      if (current?.processedActionIds?.includes(parsedActionId)) return current;
      throw new StaleJourneyTurnError(value.id, expectedVersion, current?.turnVersion ?? 0);
    },
  };
}
