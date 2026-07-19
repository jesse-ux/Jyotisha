import { z } from "zod";
import { BirthTimeScoringJobError } from "./birth-time-scoring-job.ts";
import type {
  BirthTimeJourneyStore,
  DynamicStoredRectificationCase,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import { BirthTimeJourneyStoreError, StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

type RpcError = { readonly message: string };
type RpcResult = { readonly data: unknown; readonly error: RpcError | null };
export type DynamicScoringRpcClient = {
  readonly rpc: (
    name: string,
    args: Readonly<Record<string, unknown>>,
  ) => PromiseLike<RpcResult>;
};

const versionSchema = z.number().int().nonnegative();
const claimSchema = z.union([
  z.object({
    claim_state: z.enum(["claimed", "processing", "completed"]),
    algorithm_version: z.string().trim().min(1),
  }).strict().readonly(),
  z.array(z.object({
    claim_state: z.enum(["claimed", "processing", "completed"]),
    algorithm_version: z.string().trim().min(1),
  }).strict().readonly()).length(1).transform((rows) => rows[0]),
]);

type DynamicScoringMethods = Required<Pick<BirthTimeJourneyStore,
  "createDynamicScoringJob" | "claimDynamicScoringJob"
>>;

function privateState(value: DynamicStoredRectificationCase) {
  return {
    candidateModel: value.candidateModel,
    currentChoiceQuestion: value.currentChoiceQuestion,
    choiceAnswers: value.choiceAnswers,
    choiceEvidence: value.choiceEvidence,
    dynamicControl: value.dynamicControl,
    agentContext: value.agentContext,
  };
}

async function loadDynamic(
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
  userId: string,
  caseId: string,
): Promise<DynamicStoredRectificationCase> {
  const stored = await loadCase(userId, caseId);
  if (!stored || stored.journeyProtocol !== "dynamic-choice-v2") {
    throw new BirthTimeJourneyStoreError("load_case");
  }
  return stored;
}

function claimError(message: string): BirthTimeScoringJobError {
  if (message.includes("algorithm_mismatch")) {
    return new BirthTimeScoringJobError("algorithm_mismatch");
  }
  if (message.includes("turn_invalid") || message.includes("result_inconsistent")) {
    return new BirthTimeScoringJobError("invalid_turn");
  }
  return new BirthTimeScoringJobError("unavailable");
}

export function createDynamicScoringJobStore(
  client: DynamicScoringRpcClient,
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
): DynamicScoringMethods {
  return {
    async createDynamicScoringJob(value, expectedVersion, actionId, questionId, job) {
      const receipt = actionId.toLowerCase();
      const result = await client.rpc("create_birth_time_dynamic_scoring_job", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_job_id: job.jobId,
        p_expected_version: expectedVersion,
        p_action_id: receipt,
        p_question_id: questionId,
        p_evidence_fingerprint: job.evidenceFingerprint,
        p_algorithm_version: job.algorithmVersion,
        p_expires_at: job.expiresAt,
        p_public_turn_state: { ...value.dynamicTurnState, turnVersion: expectedVersion + 1 },
        p_snapshot: value.snapshot,
        p_private_state: privateState(value),
      });
      if (result.error) {
        const current = await loadCase(value.userId, value.id);
        if (current?.journeyProtocol === "dynamic-choice-v2"
          && current.processedActionIds.includes(receipt)) return current;
        if (result.error.message.includes("stale_birth_time_dynamic_scoring_job")) {
          throw new StaleJourneyTurnError(value.id, expectedVersion, current?.turnVersion ?? 0);
        }
        throw new BirthTimeJourneyStoreError("update_case");
      }
      const version = versionSchema.safeParse(result.data);
      if (!version.success || version.data !== expectedVersion + 1) {
        throw new BirthTimeJourneyStoreError("update_case");
      }
      return loadDynamic(loadCase, value.userId, value.id);
    },

    async claimDynamicScoringJob(identity) {
      const result = await client.rpc("claim_birth_time_dynamic_scoring_job", {
        p_user_id: identity.userId,
        p_case_id: identity.caseId,
        p_job_id: identity.jobId,
        p_evidence_fingerprint: identity.evidenceFingerprint,
        p_algorithm_version: identity.algorithmVersion,
        p_now: identity.now,
      });
      if (result.error) throw claimError(result.error.message);
      const parsed = claimSchema.safeParse(result.data);
      if (!parsed.success) throw new BirthTimeJourneyStoreError("load_case");
      return {
        kind: parsed.data.claim_state,
        algorithmVersion: parsed.data.algorithm_version,
      };
    },
  };
}
