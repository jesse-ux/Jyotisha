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
import type { StoredRectificationCase } from "./birth-time-journey-service.ts";
import { evidenceDomains } from "./birth-time-question-planner.ts";
import {
  dynamicJourneyTurnStateSchema,
  evidenceDraftSchema,
  journeyTurnStateSchema,
} from "./birth-time-journey-turn.ts";
import type { EvidenceDraft, JourneyTurnState } from "./birth-time-journey-turn.ts";
import {
  dynamicTurnMatchesPrivateQuestion,
  parseDynamicPrivateRow,
} from "./birth-time-journey-dynamic-state.ts";
import { BirthTimeJourneyStoreError } from "./birth-time-journey-store-errors.ts";

type JourneyLoadResult = { readonly data: unknown; readonly error: unknown };
type JourneyLoadQuery = {
  eq(column: string, value: string): JourneyLoadQuery;
  maybeSingle(): PromiseLike<JourneyLoadResult>;
};
export type JourneyLoadClient = {
  from(table: string): { select(columns: string): JourneyLoadQuery };
};

export function createJourneyLoadClient(supabase: SupabaseClient): JourneyLoadClient {
  return {
    from(table) {
      return {
        select(columns) {
          const query = supabase.from(table).select(columns);
          const loadQuery: JourneyLoadQuery = {
            eq(column, value) {
              query.eq(column, value);
              return loadQuery;
            },
            async maybeSingle() {
              const { data, error } = await query.maybeSingle();
              return { data, error };
            },
          };
          return loadQuery;
        },
      };
    },
  };
}

const storedCaseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  journey_protocol: z.enum(["legacy-guided-v1", "dynamic-choice-v2"]).default("legacy-guided-v1"),
  journey_snapshot: journeySnapshotSchema,
  questionnaire: z.record(z.unknown()),
  answers: z.record(z.enum(["A", "B", "C", "D"])),
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

const requiredDynamicPublicFields = [
  "journey_protocol",
  "life_events",
  "candidate_result",
  "turn_version",
  "turn_state",
  "evidence_draft",
  "processed_action_ids",
  "adaptive_round",
  "asked_domains",
] as const;

function hasRequiredDynamicPublicFields(value: unknown): boolean {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  return requiredDynamicPublicFields.every((field) => Object.prototype.hasOwnProperty.call(value, field));
}

function exactEmptyObject(value: unknown): boolean {
  return typeof value === "object"
    && value !== null
    && !Array.isArray(value)
    && Object.keys(value).length === 0;
}

function parseLegacyTurn(value: unknown): JourneyTurnState | null {
  if (exactEmptyObject(value)) return null;
  const parsed = journeyTurnStateSchema.safeParse(value);
  if (parsed.success) return parsed.data;
  throw new BirthTimeJourneyStoreError("load_case");
}

function parseEvidenceDraft(value: unknown): EvidenceDraft | null {
  if (value === null) return null;
  const parsed = evidenceDraftSchema.safeParse(value);
  if (parsed.success) return parsed.data;
  throw new BirthTimeJourneyStoreError("load_case");
}

export async function loadStoredRectificationCase(
  client: JourneyLoadClient,
  userId: string,
  caseId: string,
): Promise<StoredRectificationCase | null> {
  const { data, error } = await client
    .from("birth_time_rectification_cases")
    .select("id,user_id,journey_protocol,journey_snapshot,questionnaire,answers,scoring_result,reported_date,life_events,candidate_result,turn_version,turn_state,evidence_draft,processed_action_ids,adaptive_round,asked_domains")
    .eq("id", caseId)
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw new BirthTimeJourneyStoreError("load_case");
  if (!data) return null;
  if (
    typeof data === "object"
    && data !== null
    && "journey_protocol" in data
    && data.journey_protocol === "dynamic-choice-v2"
    && !hasRequiredDynamicPublicFields(data)
  ) throw new BirthTimeJourneyStoreError("load_case");
  const parsed = storedCaseSchema.parse(data);
  const { data: profile, error: profileError } = await client
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
  const turnState = parsed.journey_protocol === "legacy-guided-v1"
    ? parseLegacyTurn(parsed.turn_state)
    : null;
  const dynamicTurn = parsed.journey_protocol === "dynamic-choice-v2"
    ? dynamicJourneyTurnStateSchema.safeParse(parsed.turn_state)
    : null;
  if (dynamicTurn && !dynamicTurn.success) throw new BirthTimeJourneyStoreError("load_case");
  const dynamicTurnState = dynamicTurn?.data ?? null;
  const evidenceDraft = parseEvidenceDraft(parsed.evidence_draft);
  let dynamicPrivate = null;
  if (parsed.journey_protocol === "dynamic-choice-v2") {
    const { data: privateRow, error: privateError } = await client
      .from("birth_time_rectification_dynamic_state")
      .select("case_id,user_id,candidate_model,current_choice_question,choice_answers,choice_evidence,dynamic_control,agent_context")
      .eq("case_id", caseId)
      .eq("user_id", userId)
      .maybeSingle();
    if (privateError) throw new BirthTimeJourneyStoreError("load_case");
    dynamicPrivate = parseDynamicPrivateRow(privateRow, userId, caseId);
    if (
      dynamicTurnState === null
      || !dynamicTurnMatchesPrivateQuestion(dynamicTurnState, dynamicPrivate)
    ) throw new BirthTimeJourneyStoreError("load_case");
  }
  const common = {
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
    processedActionIds: parsed.processed_action_ids,
    persistedProgress: {
      adaptiveRound: parsed.adaptive_round,
      askedDomains: parsed.asked_domains,
    },
    ...(scoring ? { scoring } : {}),
  };
  if (parsed.journey_protocol === "legacy-guided-v1") {
    return {
      ...common,
      journeyProtocol: "legacy-guided-v1",
      turnState,
      evidenceDraft,
    } satisfies StoredRectificationCase;
  }
  if (dynamicTurnState === null || dynamicPrivate === null || evidenceDraft !== null) {
    throw new BirthTimeJourneyStoreError("load_case");
  }
  return {
    ...common,
    journeyProtocol: "dynamic-choice-v2",
    turnState: null,
    dynamicTurnState,
    evidenceDraft: null,
    ...dynamicPrivate,
  } satisfies StoredRectificationCase;
}
