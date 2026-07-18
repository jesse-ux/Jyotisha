import "server-only";

import type { SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";
import type {
  BirthTimeJourneyStore,
  PersistedJourneyAssessment,
} from "./birth-time-journey-service.ts";
import { projectJourneyTurn } from "./birth-time-journey-turn.ts";
import {
  BirthTimeJourneyStoreError,
  caseStatus,
  createJourneyTurnPersistence,
  loadStoredRectificationCase,
  profileStatus,
} from "./birth-time-journey-turn-persistence.ts";
import { createSupabaseScoringJobStore } from "./birth-time-scoring-job-store.ts";
import { createSupabaseGuidedCandidateStore } from "./birth-time-guided-candidate-store.ts";

export { BirthTimeJourneyStoreError } from "./birth-time-journey-turn-persistence.ts";

function assessmentValues(value: PersistedJourneyAssessment) {
  const assessment = value.assessment;
  return {
    reportedTime: "reportedTime" in assessment ? assessment.reportedTime : null,
    period: assessment.source === "period_only" ? assessment.period : null,
    clue: assessment.source === "unknown" ? assessment.clue : null,
    before: "uncertaintyBeforeMinutes" in assessment
      ? assessment.uncertaintyBeforeMinutes
      : null,
    after: "uncertaintyAfterMinutes" in assessment
      ? assessment.uncertaintyAfterMinutes
      : null,
  };
}

export function createSupabaseBirthTimeJourneyStore(
  supabase: SupabaseClient,
): BirthTimeJourneyStore {
  const loadCase = (userId: string, caseId: string) => loadStoredRectificationCase(supabase, userId, caseId);
  const turns = createJourneyTurnPersistence(supabase, loadCase);
  const scoringJobs = createSupabaseScoringJobStore(supabase, loadCase);
  const guidedCandidates = createSupabaseGuidedCandidateStore(supabase, loadCase);
  return {
    async saveAssessment(value) {
      const details = assessmentValues(value);
      const { data, error } = await supabase
        .from("birth_time_rectification_cases")
        .insert({
          user_id: value.userId,
          status: caseStatus(value.snapshot),
          reported_date: value.assessment.date,
          reported_time: details.reportedTime,
          reported_period: details.period,
          source: value.assessment.source,
          uncertainty_before_minutes: details.before,
          uncertainty_after_minutes: details.after,
          questionnaire: value.questionnaire?.raw ?? {},
          journey_snapshot: value.snapshot,
          candidate_scan: value.candidateScan?.raw ?? {},
          turn_state: projectJourneyTurn({
            turnVersion: 0,
            snapshot: value.snapshot,
            questionnaire: value.questionnaire,
            candidateResult: null,
            lifeEvents: [],
          }),
          candidate_start: value.snapshot.reportedRange.startTime,
          candidate_end: value.snapshot.reportedRange.endTime,
          confirmed_time: value.snapshot.activeTime,
          confirmed_at: value.snapshot.state === "ready" ? new Date().toISOString() : null,
        })
        .select("id")
        .single();
      if (error) throw new BirthTimeJourneyStoreError("insert_case");
      const caseId = z.string().uuid().parse(data.id);

      const { error: profileError } = await supabase
        .from("profiles")
        .update({
          reported_birth_time: details.reportedTime,
          active_birth_time: value.snapshot.activeTime,
          birth_time: value.snapshot.activeTime,
          birth_time_source: value.assessment.source,
          birth_time_period: details.period,
          birth_time_clue: details.clue,
          uncertainty_before_minutes: details.before,
          uncertainty_after_minutes: details.after,
          birth_time_status: profileStatus(value.snapshot),
          rectification_confidence: null,
          rectification_case_id: caseId,
        })
        .eq("id", value.userId);
      if (profileError) throw new BirthTimeJourneyStoreError("update_profile");
      return caseId;
    },

    loadCase,
    saveTurn: turns.saveTurn,
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
