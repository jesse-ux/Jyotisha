import { z } from "zod";
import { BirthTimeGuideOutputError } from "./birth-time-guide-agent.ts";
import {
  dynamicQuestionSemanticFingerprint,
  dynamicServerCopyIsSafe,
  modelSafeDynamicQuestionPrompt,
  normalizeDynamicLabel,
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
const questionSelectionSchema = z.object({
  kind: z.literal("question"),
  opportunityId: exactServerIdSchema,
}).strict();
const noUsefulQuestionSchema = z.object({ kind: z.literal("no_useful_question") }).strict();
const dynamicQuestionOutputSchema = z.discriminatedUnion("kind", [
  questionSelectionSchema,
  noUsefulQuestionSchema,
]).readonly();
const reservedChoices = [
  { label: "不确定 / 不记得", kind: "unknown" as const },
  { label: "都不符合", kind: "unmatched" as const },
] as const;

export type ParsedDynamicQuestionOutput = z.infer<typeof dynamicQuestionOutputSchema>;
export type ParsedQuestionSelection = Extract<ParsedDynamicQuestionOutput, { readonly kind: "question" }>;
export type DynamicQuestionIdFactory = () => string;

export class BirthTimeDynamicBindingError extends Error {
  readonly name = "BirthTimeDynamicBindingError";
  readonly reason: "invalid_private_binding" | "invalid_server_id" | "invalid_persisted_question" | "invalid_server_copy";

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

export function generateDynamicQuestionPrompt(
  packet: CandidateDifferencePacket,
): string {
  return modelSafeDynamicQuestionPrompt(packet);
}

export function parseDynamicQuestionOutput(
  value: unknown,
  packet: CandidateDifferencePacket,
): ParsedDynamicQuestionOutput {
  const parsed = dynamicQuestionOutputSchema.safeParse(value);
  if (!parsed.success) return invalidQuestion();
  if (parsed.data.kind === "question") opportunityFor(packet, parsed.data.opportunityId);
  return parsed.data;
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

function serverRendering(opportunity: QuestionOpportunity): {
  readonly prompt: string;
  readonly options: readonly { readonly partitionId: string; readonly label: string }[];
} {
  const options = opportunity.partitions.map((partition) => ({
    partitionId: partition.partitionId,
    label: partition.fallbackLabel,
  }));
  const labels = [...options, ...reservedChoices]
    .map((option) => normalizeDynamicLabel(option.label));
  if (
    !dynamicServerCopyIsSafe(opportunity.fallbackPrompt, true)
    || options.some((option) => !dynamicServerCopyIsSafe(option.label, false))
    || new Set(labels).size !== labels.length
  ) throw new BirthTimeDynamicBindingError("invalid_server_copy");
  return { prompt: opportunity.fallbackPrompt, options };
}

function privatePartitionsFor(
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
  return opportunity.partitions.map((publicPartition) => {
    const privatePartition = byId.get(publicPartition.partitionId);
    if (
      !privatePartition
      || !scoredEvidencePartitionSchema.safeParse(privatePartition).success
      || privatePartition.descriptor !== publicPartition.descriptor
      || privatePartition.fallbackLabel !== publicPartition.fallbackLabel
      || Object.keys(privatePartition.candidateScores).length === 0
    ) throw new BirthTimeDynamicBindingError("invalid_private_binding");
    return privatePartition;
  });
}

function serverId(factory: DynamicQuestionIdFactory): string {
  const parsed = z.string().uuid().safeParse(factory());
  if (!parsed.success) throw new BirthTimeDynamicBindingError("invalid_server_id");
  return parsed.data.toLowerCase();
}

function bindQuestion(
  selection: ParsedQuestionSelection,
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
  source: "agent" | "fallback",
): PersistedDynamicChoiceQuestion {
  const opportunity = opportunityFor(build.packet, selection.opportunityId);
  const rendering = serverRendering(opportunity);
  const privatePartitions = privatePartitionsFor(build, opportunity);
  const questionFingerprint = dynamicQuestionSemanticFingerprint(rendering);
  if (
    build.packet.askedQuestionFingerprints.includes(questionFingerprint)
    || build.packet.candidatePartitionFingerprints.includes(opportunity.candidatePartitionFingerprint)
  ) throw new BirthTimeGuideOutputError("repeated_question");
  const questionId = serverId(createId);
  const primaryOptions = rendering.options.map((option, index) => {
    const partition = privatePartitions[index];
    if (!partition) throw new BirthTimeDynamicBindingError("invalid_private_binding");
    return {
      optionId: serverId(createId), label: option.label, kind: "primary" as const,
      partitionId: option.partitionId, candidateScores: partition.candidateScores,
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
    prompt: rendering.prompt,
    options: [
      ...primaryOptions,
      ...reservedChoices.map((choice) => ({
        optionId: serverId(createId),
        ...choice,
        partitionId: null,
        candidateScores: null,
      })),
    ],
  });
  if (!persisted.success) throw new BirthTimeDynamicBindingError("invalid_persisted_question");
  return persisted.data;
}

export function bindDynamicQuestion(
  selection: ParsedQuestionSelection,
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
): PersistedDynamicChoiceQuestion {
  return bindQuestion(selection, build, createId, "agent");
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
    try {
      return bindQuestion(
        { kind: "question", opportunityId: opportunity.opportunityId },
        build,
        createId,
        "fallback",
      );
    } catch (error) {
      if (error instanceof BirthTimeGuideOutputError && error.reason === "repeated_question") continue;
      throw error;
    }
  }
  return null;
}
