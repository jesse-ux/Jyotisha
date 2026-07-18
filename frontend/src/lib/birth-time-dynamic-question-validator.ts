import { z } from "zod";
import { BirthTimeGuideOutputError } from "./birth-time-guide-agent.ts";
import {
  dynamicPublicCopyIsSafe,
  dynamicQuestionIsGrounded,
  dynamicQuestionSemanticFingerprint,
  modelSafeDynamicQuestionPrompt,
} from "./birth-time-dynamic-question-copy.ts";
import {
  persistedDynamicChoiceQuestionSchema,
  scoredEvidencePartitionSchema,
  type CandidateDifferenceBuild,
  type CandidateDifferencePacket,
  type PersistedDynamicChoiceQuestion,
  type QuestionOpportunity,
  type ScoredEvidencePartition,
} from "./birth-time-dynamic-choice-internal.ts";

const exactServerIdSchema = z.string().min(1).refine(
  (value) => value === value.trim(),
  "server ids must be byte-exact",
);
const modelQuestionSchema = z.object({
  kind: z.literal("question"),
  opportunityId: exactServerIdSchema,
  prompt: z.string().trim().min(1).max(120),
  options: z.array(z.object({
    partitionId: exactServerIdSchema,
    label: z.string().trim().min(1).max(80),
  }).strict()).min(2).max(4),
}).strict();
const noUsefulQuestionSchema = z.object({ kind: z.literal("no_useful_question") }).strict();
const dynamicQuestionOutputSchema = z.discriminatedUnion("kind", [
  modelQuestionSchema,
  noUsefulQuestionSchema,
]).readonly();

export type ParsedDynamicQuestionOutput = z.infer<typeof dynamicQuestionOutputSchema>;
export type ParsedQuestionOutput = Extract<ParsedDynamicQuestionOutput, { readonly kind: "question" }>;
export type DynamicQuestionIdFactory = () => string;

export class BirthTimeDynamicBindingError extends Error {
  readonly name = "BirthTimeDynamicBindingError";
  readonly reason: "invalid_private_binding" | "invalid_server_id" | "invalid_persisted_question" | "invalid_fallback_copy";

  constructor(reason: BirthTimeDynamicBindingError["reason"]) {
    super(`Birth-time dynamic question binding ${reason}`);
    this.reason = reason;
  }
}

function invalidQuestion(): never {
  throw new BirthTimeGuideOutputError("invalid_question");
}

export function isRecoverableDynamicQuestionError(
  error: unknown,
): error is BirthTimeGuideOutputError {
  return error instanceof BirthTimeGuideOutputError
    && ["invalid_json", "invalid_question", "repeated_question"].includes(error.reason);
}

function opportunityFor(
  packet: CandidateDifferencePacket,
  opportunityId: string,
): QuestionOpportunity {
  const opportunity = packet.opportunities.find((item) => item.opportunityId === opportunityId);
  if (!opportunity) return invalidQuestion();
  return opportunity;
}

function validateQuestionOutput(
  output: ParsedQuestionOutput,
  packet: CandidateDifferencePacket,
): ParsedQuestionOutput {
  const opportunity = opportunityFor(packet, output.opportunityId);
  if (
    !dynamicPublicCopyIsSafe(output.prompt, true)
    || !dynamicQuestionIsGrounded(output.prompt, opportunity.neutralContext)
    || output.options.some((option) => !dynamicPublicCopyIsSafe(option.label, false))
  ) return invalidQuestion();
  const expected = opportunity.partitions.map((item) => item.partitionId);
  const actual = output.options.map((item) => item.partitionId);
  if (new Set(actual).size !== actual.length) return invalidQuestion();
  if (actual.length !== expected.length || actual.some((item) => !expected.includes(item))) {
    return invalidQuestion();
  }
  return output;
}

export function generateDynamicQuestionPrompt(
  packet: CandidateDifferencePacket,
  unmatchedNote: string | null,
): string {
  return modelSafeDynamicQuestionPrompt(packet, unmatchedNote);
}

export function parseDynamicQuestionOutput(
  value: unknown,
  packet: CandidateDifferencePacket,
): ParsedDynamicQuestionOutput {
  const parsed = dynamicQuestionOutputSchema.safeParse(value);
  if (!parsed.success) return invalidQuestion();
  if (parsed.data.kind === "no_useful_question") return parsed.data;
  return validateQuestionOutput(parsed.data, packet);
}

export function parseDynamicQuestionText(
  text: string,
  packet: CandidateDifferencePacket,
): ParsedDynamicQuestionOutput {
  try {
    return parseDynamicQuestionOutput(JSON.parse(text.trim()), packet);
  } catch (error) {
    if (error instanceof SyntaxError) throw new BirthTimeGuideOutputError("invalid_json");
    throw error;
  }
}

export function dynamicQuestionFingerprint(output: ParsedQuestionOutput): string {
  return dynamicQuestionSemanticFingerprint(output);
}

function privatePartitionsFor(
  output: ParsedQuestionOutput,
  build: CandidateDifferenceBuild,
  opportunity: QuestionOpportunity,
): readonly ScoredEvidencePartition[] {
  const privatePartitions = build.scoringPartitions[opportunity.opportunityId];
  if (!privatePartitions || privatePartitions.length !== opportunity.partitions.length) {
    throw new BirthTimeDynamicBindingError("invalid_private_binding");
  }
  const byId = new Map(privatePartitions.map((partition) => [partition.partitionId, partition]));
  if (byId.size !== privatePartitions.length) {
    throw new BirthTimeDynamicBindingError("invalid_private_binding");
  }
  for (const publicPartition of opportunity.partitions) {
    const privatePartition = byId.get(publicPartition.partitionId);
    if (
      !privatePartition
      || !scoredEvidencePartitionSchema.safeParse(privatePartition).success
      || privatePartition.descriptor !== publicPartition.descriptor
      || privatePartition.fallbackLabel !== publicPartition.fallbackLabel
      || Object.keys(privatePartition.candidateScores).length === 0
    ) throw new BirthTimeDynamicBindingError("invalid_private_binding");
  }
  return output.options.map((option) => {
    const partition = byId.get(option.partitionId);
    if (!partition) throw new BirthTimeDynamicBindingError("invalid_private_binding");
    return partition;
  });
}

function serverId(factory: DynamicQuestionIdFactory): string {
  const parsed = z.string().uuid().safeParse(factory());
  if (!parsed.success) throw new BirthTimeDynamicBindingError("invalid_server_id");
  return parsed.data.toLowerCase();
}

function bindQuestion(
  output: ParsedQuestionOutput,
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
  source: "agent" | "fallback",
): PersistedDynamicChoiceQuestion {
  const validated = validateQuestionOutput(output, build.packet);
  const opportunity = opportunityFor(build.packet, validated.opportunityId);
  const questionFingerprint = dynamicQuestionFingerprint(validated);
  if (
    build.packet.askedQuestionFingerprints.includes(questionFingerprint)
    || build.packet.candidatePartitionFingerprints.includes(opportunity.candidatePartitionFingerprint)
  ) throw new BirthTimeGuideOutputError("repeated_question");
  const privatePartitions = privatePartitionsFor(validated, build, opportunity);
  const questionId = serverId(createId);
  const primaryOptions = validated.options.map((option, index) => {
    const partition = privatePartitions[index];
    if (!partition) throw new BirthTimeDynamicBindingError("invalid_private_binding");
    return {
      optionId: serverId(createId), label: option.label, kind: "primary" as const,
      partitionId: partition.partitionId, candidateScores: partition.candidateScores,
    };
  });
  const persisted = persistedDynamicChoiceQuestionSchema.safeParse({
    questionId,
    opportunityId: opportunity.opportunityId,
    dimensionCode: opportunity.dimensionCode,
    estimatedInformationGain: opportunity.estimatedInformationGain,
    scoringVersion: build.packet.scoringVersion,
    source,
    questionFingerprint,
    candidatePartitionFingerprint: opportunity.candidatePartitionFingerprint,
    prompt: validated.prompt,
    options: [
      ...primaryOptions,
      { optionId: serverId(createId), label: "不确定 / 不记得", kind: "unknown", partitionId: null, candidateScores: null },
      { optionId: serverId(createId), label: "都不符合", kind: "unmatched", partitionId: null, candidateScores: null },
    ],
  });
  if (!persisted.success) throw new BirthTimeDynamicBindingError("invalid_persisted_question");
  return persisted.data;
}

export function bindDynamicQuestion(
  output: ParsedQuestionOutput,
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
): PersistedDynamicChoiceQuestion {
  return bindQuestion(output, build, createId, "agent");
}

export function bindFallbackDynamicQuestion(
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
): PersistedDynamicChoiceQuestion | null {
  const opportunities = [...build.packet.opportunities].sort((left, right) => (
    right.estimatedInformationGain - left.estimatedInformationGain
    || (left.opportunityId < right.opportunityId ? -1 : left.opportunityId > right.opportunityId ? 1 : 0)
  ));
  for (const opportunity of opportunities) {
    let output: ParsedDynamicQuestionOutput;
    try {
      output = parseDynamicQuestionOutput({
        kind: "question",
        opportunityId: opportunity.opportunityId,
        prompt: opportunity.fallbackPrompt,
        options: opportunity.partitions.map((partition) => ({
          partitionId: partition.partitionId,
          label: partition.fallbackLabel,
        })),
      }, build.packet);
    } catch (error) {
      if (isRecoverableDynamicQuestionError(error)) {
        throw new BirthTimeDynamicBindingError("invalid_fallback_copy");
      }
      throw error;
    }
    if (output.kind !== "question") throw new BirthTimeDynamicBindingError("invalid_fallback_copy");
    try {
      return bindQuestion(output, build, createId, "fallback");
    } catch (error) {
      if (error instanceof BirthTimeGuideOutputError && error.reason === "repeated_question") continue;
      throw error;
    }
  }
  return null;
}
