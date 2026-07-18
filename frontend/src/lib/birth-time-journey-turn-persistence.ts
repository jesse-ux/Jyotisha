import type { SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";
import type { JourneySnapshot } from "./birth-time-journey.ts";
import type { StoredRectificationCase } from "./birth-time-journey-service.ts";
import { evidenceDomains } from "./birth-time-question-planner.ts";
import type { EvidenceDomain } from "./birth-time-question-planner.ts";
import type { EvidenceDraft, JourneyTurnState } from "./birth-time-journey-turn.ts";
import {
  BirthTimeJourneyStoreError,
  StaleJourneyTurnError,
} from "./birth-time-journey-store-errors.ts";

const actionIdSchema = z.string().uuid();

export { createJourneyLoadClient, loadStoredRectificationCase } from "./birth-time-journey-case-loader.ts";
export { BirthTimeJourneyStoreError, StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

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

function canonicalAskedDomains(input: readonly EvidenceDomain[]): readonly EvidenceDomain[] {
  return evidenceDomains.filter((domain) => input.includes(domain));
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
