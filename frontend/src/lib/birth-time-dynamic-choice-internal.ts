import { z } from "zod";
import { candidateResultSchema } from "./birth-time-evidence.ts";
import {
  publicChoiceKindSchema,
  publicDynamicChoiceQuestionSchema,
  timeRangeSchema,
  validateOptionSet,
} from "./birth-time-dynamic-choice.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";
import type { PublicChoiceKind, PublicDynamicChoiceQuestion, TimeRange } from "./birth-time-dynamic-choice.ts";

const finiteScoresSchema = z.record(z.number().finite());

export type EvidencePartition = {
  readonly partitionId: string;
  readonly descriptor: string;
  readonly fallbackLabel: string;
};

export type ScoredEvidencePartition = EvidencePartition & {
  readonly candidateScores: Readonly<Record<string, number>>;
};

export type QuestionOpportunity = {
  readonly opportunityId: string;
  readonly dimensionCode: string;
  readonly neutralContext: string;
  readonly estimatedInformationGain: number;
  readonly candidatePartitionFingerprint: string;
  readonly fallbackPrompt: string;
  readonly partitions: readonly EvidencePartition[];
};

export type CandidateDifferencePacket = {
  readonly caseId: string;
  readonly scoringVersion: "birth-time-choice-scoring-v2";
  readonly currentRange: TimeRange;
  readonly opportunities: readonly QuestionOpportunity[];
  readonly askedQuestionFingerprints: readonly string[];
  readonly candidatePartitionFingerprints: readonly string[];
  readonly recentRangeHistory: readonly TimeRange[];
};

export type CandidateDifferenceBuild = {
  readonly packet: CandidateDifferencePacket;
  readonly candidateModel: Readonly<Record<string, unknown>>;
  readonly scoringPartitions: Readonly<Record<string, readonly ScoredEvidencePartition[]>>;
};

export type PersistedDynamicChoiceQuestion = PublicDynamicChoiceQuestion & {
  readonly opportunityId: string;
  readonly dimensionCode: string;
  readonly estimatedInformationGain: number;
  readonly scoringVersion: string;
  readonly source: "agent" | "fallback";
  readonly questionFingerprint: string;
  readonly candidatePartitionFingerprint: string;
  readonly options: readonly {
    readonly optionId: string;
    readonly label: string;
    readonly kind: PublicChoiceKind;
    readonly partitionId: string | null;
    readonly candidateScores: Readonly<Record<string, number>> | null;
  }[];
};

export type StoredChoiceAnswer = {
  readonly questionId: string;
  readonly optionId: string;
  readonly kind: PublicChoiceKind;
  readonly opportunityId: string;
  readonly answeredAt: string;
};

export type ServerChoiceEvidence = {
  readonly questionId: string;
  readonly opportunityId: string;
  readonly partitionId: string;
  readonly dimensionCode: string;
  readonly candidateScores: Readonly<Record<string, number>>;
  readonly informationGain: number;
};

export type DynamicChoiceScoringResult = {
  readonly candidate: CandidateResult;
  readonly evidenceMode: "dynamic_choice";
  readonly effectiveAnswerCount: number;
  readonly dimensionCount: number;
};

export type PausedDynamicAction =
  | { readonly kind: "generate_dynamic_question" }
  | { readonly kind: "ask_dynamic_choice"; readonly questionId: string }
  | { readonly kind: "clarify_unmatched_answer"; readonly questionId: string }
  | { readonly kind: "retry_question_generation" }
  | { readonly kind: "score_pending"; readonly jobId: string }
  | { readonly kind: "retry_scoring"; readonly jobId: string };

export type DynamicControlState = {
  readonly asOfDate: string;
  readonly answeredCount: number;
  readonly effectiveAnswerCount: number;
  readonly plateauCount: number;
  readonly questionFingerprints: readonly string[];
  readonly partitionFingerprints: readonly string[];
  readonly dismissedOpportunityIds: readonly string[];
  readonly recentRanges: readonly TimeRange[];
  readonly pausedAction: PausedDynamicAction | null;
};

const evidencePartitionBaseSchema = z.object({
  partitionId: z.string().trim().min(1),
  descriptor: z.string().trim().min(1),
  fallbackLabel: z.string().trim().min(1).max(80),
}).strict();

export const evidencePartitionSchema = evidencePartitionBaseSchema.readonly();

export const scoredEvidencePartitionSchema = evidencePartitionBaseSchema.extend({
  candidateScores: finiteScoresSchema,
}).strict().readonly();

export const questionOpportunitySchema = z.object({
  opportunityId: z.string().trim().min(1),
  dimensionCode: z.string().trim().min(1),
  neutralContext: z.string().trim().min(1),
  estimatedInformationGain: z.number().finite().nonnegative(),
  candidatePartitionFingerprint: z.string().trim().min(1),
  fallbackPrompt: z.string().trim().min(1).max(240),
  partitions: z.array(evidencePartitionSchema).min(2).max(4).readonly(),
}).strict().readonly();

export const candidateDifferencePacketSchema = z.object({
  caseId: z.string().trim().min(1),
  scoringVersion: z.literal("birth-time-choice-scoring-v2"),
  currentRange: timeRangeSchema,
  opportunities: z.array(questionOpportunitySchema).readonly(),
  askedQuestionFingerprints: z.array(z.string().trim().min(1)).readonly(),
  candidatePartitionFingerprints: z.array(z.string().trim().min(1)).readonly(),
  recentRangeHistory: z.array(timeRangeSchema).readonly(),
}).strict().readonly();

export const candidateDifferenceBuildSchema = z.object({
  packet: candidateDifferencePacketSchema,
  candidateModel: z.record(z.unknown()),
  scoringPartitions: z.record(z.array(scoredEvidencePartitionSchema).readonly()),
}).strict().readonly();

const persistedPrimaryChoiceSchema = z.object({
  optionId: z.string().trim().min(1),
  label: z.string().trim().min(1).max(80),
  kind: z.literal("primary"),
  partitionId: z.string().trim().min(1),
  candidateScores: finiteScoresSchema,
}).strict().readonly();

const persistedSpecialChoiceSchema = (kind: "unknown" | "unmatched") => z.object({
  optionId: z.string().trim().min(1),
  label: z.string().trim().min(1).max(80),
  kind: z.literal(kind),
  partitionId: z.null(),
  candidateScores: z.null(),
}).strict().readonly();

export const persistedDynamicChoiceQuestionSchema = z.object({
  questionId: z.string().trim().min(1),
  opportunityId: z.string().trim().min(1),
  dimensionCode: z.string().trim().min(1),
  estimatedInformationGain: z.number().finite().nonnegative(),
  scoringVersion: z.string().trim().min(1),
  source: z.enum(["agent", "fallback"]),
  questionFingerprint: z.string().trim().min(1),
  candidatePartitionFingerprint: z.string().trim().min(1),
  prompt: z.string().trim().min(1).max(240),
  options: z.array(z.union([
    persistedPrimaryChoiceSchema,
    persistedSpecialChoiceSchema("unknown"),
    persistedSpecialChoiceSchema("unmatched"),
  ])).readonly(),
}).strict().superRefine(validateOptionSet).readonly();

export const storedChoiceAnswerSchema = z.object({
  questionId: z.string().trim().min(1),
  optionId: z.string().trim().min(1),
  kind: publicChoiceKindSchema,
  opportunityId: z.string().trim().min(1),
  answeredAt: z.string().datetime({ offset: true }),
}).strict().readonly();

export const serverChoiceEvidenceSchema = z.object({
  questionId: z.string().trim().min(1),
  opportunityId: z.string().trim().min(1),
  partitionId: z.string().trim().min(1),
  dimensionCode: z.string().trim().min(1),
  candidateScores: finiteScoresSchema,
  informationGain: z.number().finite().nonnegative(),
}).strict().readonly();

export const dynamicChoiceScoringResultSchema = z.object({
  candidate: candidateResultSchema,
  evidenceMode: z.literal("dynamic_choice"),
  effectiveAnswerCount: z.number().int().min(0),
  dimensionCount: z.number().int().min(0),
}).strict().readonly();

export const pausedDynamicActionSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("generate_dynamic_question") }).strict(),
  z.object({ kind: z.literal("ask_dynamic_choice"), questionId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("clarify_unmatched_answer"), questionId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("retry_question_generation") }).strict(),
  z.object({ kind: z.literal("score_pending"), jobId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("retry_scoring"), jobId: z.string().trim().min(1) }).strict(),
]).readonly();

export const dynamicControlStateSchema = z.object({
  asOfDate: z.string().date(),
  answeredCount: z.number().int().min(0),
  effectiveAnswerCount: z.number().int().min(0),
  plateauCount: z.number().int().min(0),
  questionFingerprints: z.array(z.string().trim().min(1)).readonly(),
  partitionFingerprints: z.array(z.string().trim().min(1)).readonly(),
  dismissedOpportunityIds: z.array(z.string().trim().min(1)).readonly(),
  recentRanges: z.array(timeRangeSchema).readonly(),
  pausedAction: pausedDynamicActionSchema.nullable(),
}).strict().readonly();

export function toPublicDynamicChoiceQuestion(
  question: PersistedDynamicChoiceQuestion,
): PublicDynamicChoiceQuestion {
  return publicDynamicChoiceQuestionSchema.parse({
    questionId: question.questionId,
    prompt: question.prompt,
    options: question.options.map(({ optionId, label, kind }) => ({ optionId, label, kind })),
  });
}
