import { createHash } from "node:crypto";
import { z } from "zod";
import { BirthTimeGuideOutputError } from "./birth-time-guide-agent.ts";
import {
  persistedDynamicChoiceQuestionSchema,
  type CandidateDifferenceBuild,
  type CandidateDifferencePacket,
  type PersistedDynamicChoiceQuestion,
  type QuestionOpportunity,
} from "./birth-time-dynamic-choice-internal.ts";

const modelQuestionSchema = z.object({
  kind: z.literal("question"),
  opportunityId: z.string().trim().min(1),
  prompt: z.string().trim().min(1).max(120),
  options: z.array(z.object({
    partitionId: z.string().trim().min(1),
    label: z.string().trim().min(1).max(80),
  }).strict()).min(2).max(4),
}).strict();

const noUsefulQuestionSchema = z.object({
  kind: z.literal("no_useful_question"),
}).strict();

const dynamicQuestionOutputSchema = z.discriminatedUnion("kind", [
  modelQuestionSchema,
  noUsefulQuestionSchema,
]).readonly();

export type ParsedDynamicQuestionOutput = z.infer<typeof dynamicQuestionOutputSchema>;
export type ParsedQuestionOutput = Extract<ParsedDynamicQuestionOutput, { readonly kind: "question" }>;
export type DynamicQuestionSource = "agent" | "fallback";
export type DynamicQuestionIdFactory = () => string;

const timeOfBirthPattern = /(?:^|[^\d])(?:[01]?\d|2[0-3])\s*[:：]\s*[0-5]\d(?:$|[^\d])/;
const forbiddenClaimPattern = /出生(?:时间|时刻|分钟|几点)|生时|候选(?:时间|分钟|答案)|置信(?:度)?|可信度|评分|得分|权重|算法|模型|证据分区|分区标识|停止提问|结束评估|应用(?:到)?排盘|更新排盘|系统(?:会|将)/;
const candidateSupportPattern = /(?:支持|排除).*(?:候选|出生)|(?:候选|出生).*(?:支持|排除|更符合|更接近)/;

function invalidQuestion(): never {
  throw new BirthTimeGuideOutputError("invalid_question");
}

function publicCopyIsSafe(value: string, question: boolean): boolean {
  const normalized = value.normalize("NFKC").trim();
  if (!/[\u3400-\u9fff]/u.test(normalized) || /[A-Za-z]/.test(normalized)) return false;
  if (timeOfBirthPattern.test(normalized)) return false;
  if (forbiddenClaimPattern.test(normalized) || candidateSupportPattern.test(normalized)) return false;
  return !question || (normalized.match(/[？?]/g) ?? []).length === 1;
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
  if (!publicCopyIsSafe(output.prompt, true)) return invalidQuestion();
  if (output.options.some((option) => !publicCopyIsSafe(option.label, false))) {
    return invalidQuestion();
  }
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
  const note = unmatchedNote?.trim() || null;
  if (note !== null && note.length > 240) return invalidQuestion();
  return JSON.stringify({
    task: "generate_dynamic_choice_question",
    opportunities: packet.opportunities.map((opportunity) => ({
      opportunityId: opportunity.opportunityId,
      dimensionCode: opportunity.dimensionCode,
      neutralContext: opportunity.neutralContext,
      partitions: opportunity.partitions.map((partition) => ({
        partitionId: partition.partitionId,
        descriptor: partition.descriptor,
        fallbackLabel: partition.fallbackLabel,
      })),
    })),
    unmatchedNote: note,
  });
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
    if (error instanceof SyntaxError) {
      throw new BirthTimeGuideOutputError("invalid_json");
    }
    throw error;
  }
}

function normalizeSemanticCopy(value: string): string {
  return value.normalize("NFKC").trim().replace(/\s+/g, " ");
}

export function dynamicQuestionFingerprint(output: ParsedQuestionOutput): string {
  const semantics = {
    prompt: normalizeSemanticCopy(output.prompt),
    options: output.options.map((option) => normalizeSemanticCopy(option.label)),
  };
  return createHash("sha256")
    .update(`birth-time-dynamic-question-v1\n${JSON.stringify(semantics)}`, "utf8")
    .digest("hex");
}

function serverId(factory: DynamicQuestionIdFactory): string {
  const parsed = z.string().uuid().safeParse(factory());
  if (!parsed.success) return invalidQuestion();
  return parsed.data.toLowerCase();
}

export function bindDynamicQuestion(
  output: ParsedQuestionOutput,
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
  source: DynamicQuestionSource,
): PersistedDynamicChoiceQuestion {
  const validated = validateQuestionOutput(output, build.packet);
  const opportunity = opportunityFor(build.packet, validated.opportunityId);
  const questionFingerprint = dynamicQuestionFingerprint(validated);
  if (
    build.packet.askedQuestionFingerprints.includes(questionFingerprint)
    || build.packet.candidatePartitionFingerprints.includes(
      opportunity.candidatePartitionFingerprint,
    )
  ) {
    throw new BirthTimeGuideOutputError("repeated_question");
  }
  const scoringPartitions = build.scoringPartitions[opportunity.opportunityId];
  if (!scoringPartitions) return invalidQuestion();
  const questionId = serverId(createId);
  const primaryOptions = validated.options.map((option) => {
    const partition = scoringPartitions.find((item) => item.partitionId === option.partitionId);
    if (!partition) return invalidQuestion();
    return {
      optionId: serverId(createId),
      label: option.label,
      kind: "primary" as const,
      partitionId: partition.partitionId,
      candidateScores: partition.candidateScores,
    };
  });
  if (
    scoringPartitions.length !== primaryOptions.length
    || new Set(scoringPartitions.map((item) => item.partitionId)).size !== primaryOptions.length
  ) return invalidQuestion();
  return persistedDynamicChoiceQuestionSchema.parse({
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
      {
        optionId: serverId(createId),
        label: "不确定 / 不记得",
        kind: "unknown",
        partitionId: null,
        candidateScores: null,
      },
      {
        optionId: serverId(createId),
        label: "都不符合",
        kind: "unmatched",
        partitionId: null,
        candidateScores: null,
      },
    ],
  });
}

export function bindFallbackDynamicQuestion(
  build: CandidateDifferenceBuild,
  createId: DynamicQuestionIdFactory,
): PersistedDynamicChoiceQuestion | null {
  for (const opportunity of build.packet.opportunities) {
    try {
      const output = parseDynamicQuestionOutput({
        kind: "question",
        opportunityId: opportunity.opportunityId,
        prompt: opportunity.fallbackPrompt,
        options: opportunity.partitions.map((partition) => ({
          partitionId: partition.partitionId,
          label: partition.fallbackLabel,
        })),
      }, build.packet);
      if (output.kind === "question") {
        return bindDynamicQuestion(output, build, createId, "fallback");
      }
    } catch (error) {
      if (!(error instanceof BirthTimeGuideOutputError)) throw error;
    }
  }
  return null;
}
