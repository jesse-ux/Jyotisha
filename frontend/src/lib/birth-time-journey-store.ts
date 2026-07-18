import "server-only";

import type { SupabaseClient } from "@supabase/supabase-js";
import type {
  BirthTimeJourneyStore,
} from "./birth-time-journey-service.ts";
import {
  BirthTimeJourneyStoreError,
  caseStatus,
  createJourneyLoadClient,
  createJourneyTurnPersistence,
  loadStoredRectificationCase,
  profileStatus,
} from "./birth-time-journey-turn-persistence.ts";
import { createSupabaseScoringJobStore } from "./birth-time-scoring-job-store.ts";
import { createSupabaseGuidedCandidateStore } from "./birth-time-guided-candidate-store.ts";
import {
  createDynamicTurnPersistence,
  type DynamicRpcClient,
} from "./birth-time-journey-dynamic-persistence.ts";
import { saveDynamicAssessment } from "./birth-time-journey-dynamic-case.ts";

export { BirthTimeJourneyStoreError } from "./birth-time-journey-turn-persistence.ts";

export function createSupabaseBirthTimeJourneyStore(
  supabase: SupabaseClient,
  now: () => Date = () => new Date(),
): BirthTimeJourneyStore {
  const loadClient = createJourneyLoadClient(supabase);
  const loadCase = (userId: string, caseId: string) => loadStoredRectificationCase(loadClient, userId, caseId);
  const turns = createJourneyTurnPersistence(supabase, loadCase);
  const dynamicRpc: DynamicRpcClient = {
    async rpc(name, args) {
      const { data, error } = await supabase.rpc(name, args);
      return { data, error: error ? { message: error.message } : null };
    },
  };
  const dynamicTurns = createDynamicTurnPersistence(
    dynamicRpc,
    loadCase,
    () => now().toISOString().slice(0, 10),
  );
  const scoringJobs = createSupabaseScoringJobStore(supabase, loadCase);
  const guidedCandidates = createSupabaseGuidedCandidateStore(supabase, loadCase);
  return {
    async saveAssessment(value) {
      return saveDynamicAssessment(dynamicRpc, value, now());
    },

    loadCase,
    saveTurn: turns.saveTurn,
    ...dynamicTurns,
    ...scoringJobs,
    ...guidedCandidates,

    async saveScoring(value) {
      const { error } = await supabase
        .from("birth_time_rectification_cases")
        .update({
          status: caseStatus(value.snapshot),
          journey_snapshot: value.snapshot,
          answers: value.answers,
          scoring_result: value.scoring?.raw ?? {},
          updated_at: new Date().toISOString(),
        })
        .eq("id", value.id)
        .eq("user_id", value.userId);
      if (error) throw new BirthTimeJourneyStoreError("update_case");

      const { error: profileError } = await supabase
        .from("profiles")
        .update({ birth_time_status: profileStatus(value.snapshot) })
        .eq("id", value.userId)
        .eq("rectification_case_id", value.id);
      if (profileError) throw new BirthTimeJourneyStoreError("update_profile");
    },

    async saveCandidateResult(value) {
      const winner = value.candidateResult?.winningSegment ?? null;
      const { error } = await supabase
        .from("birth_time_rectification_cases")
        .update({
          status: caseStatus(value.snapshot),
          journey_snapshot: value.snapshot,
          life_events: value.lifeEvents ?? [],
          candidate_result: value.candidateResult ?? {},
          event_scoring_version: value.candidateResult?.algorithmVersion ?? null,
          candidate_result_id: value.candidateResult?.resultId ?? null,
          candidate_start: winner?.startTime ?? null,
          candidate_end: winner?.endTime ?? null,
          updated_at: new Date().toISOString(),
        })
        .eq("id", value.id)
        .eq("user_id", value.userId);
      if (error) throw new BirthTimeJourneyStoreError("update_case");

      const { error: profileError } = await supabase
        .from("profiles")
        .update({
          birth_time_status: profileStatus(value.snapshot),
          rectification_confidence: value.candidateResult?.marginPercent ?? null,
        })
        .eq("id", value.userId)
        .eq("rectification_case_id", value.id);
      if (profileError) throw new BirthTimeJourneyStoreError("update_profile");
    },

    async saveCandidate(value) {
      const { error } = await supabase
        .from("birth_time_rectification_cases")
        .update({ candidate_saved_at: new Date().toISOString(), updated_at: new Date().toISOString() })
        .eq("id", value.id)
        .eq("user_id", value.userId)
        .eq("candidate_result_id", value.candidateResult?.resultId ?? null);
      if (error) throw new BirthTimeJourneyStoreError("update_case");
    },

    async confirmCandidate(value) {
      const { error } = await supabase.rpc("confirm_birth_time_candidate", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_result_id: value.candidateResult?.resultId,
        p_time: value.snapshot.activeTime,
        p_snapshot: value.snapshot,
      });
      if (error) throw new BirthTimeJourneyStoreError("update_case");
    },
  };
}
