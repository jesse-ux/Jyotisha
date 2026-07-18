import { z } from "zod";
import type { PersistedJourneyAssessment } from "./birth-time-journey-service.ts";
import type { DynamicRpcClient } from "./birth-time-journey-dynamic-persistence.ts";
import { createInitialDynamicState } from "./birth-time-journey-dynamic-state.ts";
import { BirthTimeJourneyStoreError } from "./birth-time-journey-store-errors.ts";
import { caseStatus, profileStatus } from "./birth-time-journey-turn-persistence.ts";

function assessmentDetails(value: PersistedJourneyAssessment) {
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

export async function saveDynamicAssessment(
  client: DynamicRpcClient,
  value: PersistedJourneyAssessment,
  at: Date,
): Promise<string> {
  const details = assessmentDetails(value);
  const initial = createInitialDynamicState(
    value.snapshot,
    at.toISOString().slice(0, 10),
  );
  const result = await client.rpc("create_birth_time_dynamic_case", {
    p_user_id: value.userId,
    p_public_case: {
      journeyProtocol: "dynamic-choice-v2",
      status: caseStatus(value.snapshot),
      reportedDate: value.assessment.date,
      reportedTime: details.reportedTime,
      reportedPeriod: details.period,
      source: value.assessment.source,
      uncertaintyBeforeMinutes: details.before,
      uncertaintyAfterMinutes: details.after,
      questionnaire: value.questionnaire?.raw ?? {},
      journeySnapshot: value.snapshot,
      candidateScan: value.candidateScan?.raw ?? {},
      turnState: initial.turn,
      candidateStart: value.snapshot.reportedRange.startTime,
      candidateEnd: value.snapshot.reportedRange.endTime,
      confirmedTime: value.snapshot.activeTime,
      confirmedAt: value.snapshot.state === "ready" ? at.toISOString() : null,
    },
    p_private_state: initial.privateState,
    p_profile: {
      reportedBirthTime: details.reportedTime,
      activeBirthTime: value.snapshot.activeTime,
      birthTime: value.snapshot.activeTime,
      birthTimeSource: value.assessment.source,
      birthTimePeriod: details.period,
      birthTimeClue: details.clue,
      uncertaintyBeforeMinutes: details.before,
      uncertaintyAfterMinutes: details.after,
      birthTimeStatus: profileStatus(value.snapshot),
    },
  });
  if (result.error) throw new BirthTimeJourneyStoreError("insert_case");
  return z.string().uuid().parse(result.data);
}
