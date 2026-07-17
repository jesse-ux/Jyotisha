import "server-only";

import type { SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";
import { parseRectificationQuestionnaire } from "./birth-time-journey-adapters.ts";
import type {
  BirthTimeJourneyStore,
  PersistedJourneyAssessment,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import {
  journeySnapshotSchema,
  type JourneySnapshot,
} from "./birth-time-journey.ts";

const answerSchema = z.enum(["A", "B", "C", "D"]);
const storedCaseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  journey_snapshot: journeySnapshotSchema,
  questionnaire: z.record(z.unknown()),
  answers: z.record(answerSchema),
  scoring_result: z.record(z.unknown()),
});

export class BirthTimeJourneyStoreError extends Error {
  readonly name = "BirthTimeJourneyStoreError";

  constructor(readonly operation: "insert_case" | "update_profile" | "load_case" | "update_case") {
    super(`Birth-time journey persistence failed during ${operation}`);
  }
}

function caseStatus(snapshot: JourneySnapshot) {
  switch (snapshot.state) {
    case "ready":
      return "confirmed";
    case "candidate":
      return "candidate";
    case "rectifying":
      return "rectifying";
    default: {
      const exhaustive: never = snapshot.state;
      return exhaustive;
    }
  }
}

function profileStatus(snapshot: JourneySnapshot) {
  return snapshot.state === "ready" ? "confirmed" : caseStatus(snapshot);
}

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

    async loadCase(userId, caseId) {
      const { data, error } = await supabase
        .from("birth_time_rectification_cases")
        .select("id,user_id,journey_snapshot,questionnaire,answers,scoring_result")
        .eq("id", caseId)
        .eq("user_id", userId)
        .maybeSingle();
      if (error) throw new BirthTimeJourneyStoreError("load_case");
      if (!data) return null;
      const parsed = storedCaseSchema.parse(data);
      const scoring = Object.keys(parsed.scoring_result).length > 0
        ? {
            answeredCount: 0,
            candidateClusterRankings: [],
            raw: parsed.scoring_result,
          }
        : undefined;
      const questionnaire = Object.keys(parsed.questionnaire).length > 0
        ? parseRectificationQuestionnaire(parsed.questionnaire)
        : null;
      return {
        id: parsed.id,
        userId: parsed.user_id,
        snapshot: parsed.journey_snapshot,
        questionnaire,
        answers: parsed.answers,
        ...(scoring ? { scoring } : {}),
      } satisfies StoredRectificationCase;
    },

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
  };
}
