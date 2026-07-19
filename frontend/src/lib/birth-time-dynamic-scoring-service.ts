import { dynamicChoiceScoringResultSchema } from "./birth-time-dynamic-choice-internal.ts";
import {
  dynamicChoiceScoreInput,
  dynamicDifferenceInput,
} from "./birth-time-dynamic-engine-input.ts";
import { completeDynamicScoreTransition, isDynamicTerminal, withDynamicAction } from "./birth-time-dynamic-transitions.ts";
import { storedDynamicJourneyResponse } from "./birth-time-journey-response.ts";
import type {
  BirthTimeJourneyEngine,
  BirthTimeJourneyPorts,
  DynamicStoredRectificationCase,
} from "./birth-time-journey-service.ts";
import {
  BirthTimeScoringJobError,
  dynamicChoiceScoringAlgorithmVersion,
  dynamicEvidenceFingerprint,
} from "./birth-time-scoring-job.ts";

function engineFrom(ports: BirthTimeJourneyPorts): Pick<BirthTimeJourneyEngine,
  "buildDifferencePacket" | "scoreChoices"
> {
  if (!("buildDifferencePacket" in ports.engine) || !("scoreChoices" in ports.engine)) {
    throw new BirthTimeScoringJobError("unavailable");
  }
  return ports.engine;
}

function requirePending(
  value: Awaited<ReturnType<BirthTimeJourneyPorts["store"]["loadCase"]>>,
  jobId: string,
): DynamicStoredRectificationCase {
  if (!value || value.journeyProtocol !== "dynamic-choice-v2" || isDynamicTerminal(value)) {
    throw new BirthTimeScoringJobError("invalid_turn");
  }
  const action = value.dynamicTurnState.nextAction;
  if ((action.kind !== "score_pending" && action.kind !== "retry_scoring")
    || action.jobId !== jobId) throw new BirthTimeScoringJobError("invalid_turn");
  return value;
}

function requireDynamic(
  value: Awaited<ReturnType<BirthTimeJourneyPorts["store"]["loadCase"]>>,
): DynamicStoredRectificationCase {
  if (!value || value.journeyProtocol !== "dynamic-choice-v2") {
    throw new BirthTimeScoringJobError("invalid_turn");
  }
  return value;
}

function requireCounts(stored: DynamicStoredRectificationCase, result: ReturnType<
  typeof dynamicChoiceScoringResultSchema.parse
>): void {
  const dimensions = new Set(stored.choiceEvidence.map((item) => item.dimensionCode)).size;
  const effective = stored.dynamicControl.effectiveAnswerCount;
  if (result.effectiveAnswerCount !== effective
    || result.candidate.eventCount !== effective
    || result.dimensionCount !== dimensions
    || result.candidate.domainCount !== dimensions
    || result.candidate.algorithmVersion !== dynamicChoiceScoringAlgorithmVersion) {
    throw new BirthTimeScoringJobError("invalid_result");
  }
}

export function createDynamicScoringService(ports: BirthTimeJourneyPorts) {
  return {
    async poll(userId: string, caseId: string, jobId: string) {
      const loaded = requireDynamic(await ports.store.loadCase(userId, caseId));
      const claimJob = ports.store.claimDynamicScoringJob;
      if (!claimJob) throw new BirthTimeScoringJobError("unavailable");
      const fingerprint = dynamicEvidenceFingerprint(loaded.choiceEvidence);
      const claim = await claimJob({
        userId,
        caseId,
        jobId,
        evidenceFingerprint: fingerprint,
        algorithmVersion: dynamicChoiceScoringAlgorithmVersion,
        now: (ports.now?.() ?? new Date()).toISOString(),
      });
      if (claim.kind === "completed") {
        const completed = await ports.store.loadCase(userId, caseId);
        if (!completed || completed.journeyProtocol !== "dynamic-choice-v2") {
          throw new BirthTimeScoringJobError("unavailable");
        }
        return storedDynamicJourneyResponse(completed);
      }
      const stored = requirePending(loaded, jobId);
      if (claim.kind === "processing") return storedDynamicJourneyResponse(stored);
      if (claim.algorithmVersion !== dynamicChoiceScoringAlgorithmVersion) {
        throw new BirthTimeScoringJobError("algorithm_mismatch");
      }
      const engine = engineFrom(ports);
      let updated: DynamicStoredRectificationCase;
      try {
        const result = dynamicChoiceScoringResultSchema.parse(
          await engine.scoreChoices(dynamicChoiceScoreInput(stored)),
        );
        requireCounts(stored, result);
        const build = await engine.buildDifferencePacket(dynamicDifferenceInput(stored));
        const useful = build.packet.opportunities.filter((opportunity) => (
          opportunity.estimatedInformationGain > 0
          && !stored.dynamicControl.partitionFingerprints.includes(
            opportunity.candidatePartitionFingerprint,
          )
        ));
        updated = completeDynamicScoreTransition({
          stored,
          candidate: result.candidate,
          usefulOpportunityCount: useful.length,
          repeatedOnly: build.packet.opportunities.length > 0 && useful.length === 0,
          nextVersion: stored.turnVersion + 1,
          candidateModel: build.candidateModel,
        });
      } catch (error) {
        if (!(error instanceof Error)) throw error;
        const retry = withDynamicAction(
          stored,
          { kind: "retry_scoring", jobId },
          stored.turnVersion + 1,
        );
        const failed = await ports.store.failDynamicScoringJob(retry, {
          expectedVersion: stored.turnVersion,
          jobId,
          evidenceFingerprint: fingerprint,
          algorithmVersion: dynamicChoiceScoringAlgorithmVersion,
          failureCode: error instanceof BirthTimeScoringJobError
            ? error.reason
            : "engine_error",
        });
        return storedDynamicJourneyResponse(failed);
      }
      const completed = await ports.store.completeDynamicScoringJob(updated, {
        expectedVersion: stored.turnVersion,
        jobId,
        evidenceFingerprint: fingerprint,
        algorithmVersion: dynamicChoiceScoringAlgorithmVersion,
      });
      return storedDynamicJourneyResponse(completed);
    },
  };
}
