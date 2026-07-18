import { readFileSync } from "node:fs";
import { parseCandidateDifferenceBuild } from "../../src/lib/birth-time-journey-dynamic-adapters.ts";
import { createBirthTimeGuideService } from "../../src/lib/birth-time-guide-service.ts";
import type { BirthTimeGuideGenerator } from "../../src/lib/birth-time-guide-agent.ts";
import type { CandidateDifferenceBuild, PersistedDynamicChoiceQuestion } from "../../src/lib/birth-time-dynamic-choice-internal.ts";
import type {
  DynamicQuestionGenerationCommand,
  DynamicQuestionGenerationCommit,
} from "../../src/lib/birth-time-guide-service.ts";

export const caseId = "7299894c-10a8-4b45-91d1-339007282c50";
export const actionId = "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1";
const task2ApiPacket: unknown = JSON.parse(readFileSync(
  new URL("./task2-dynamic-rectification-packet.json", import.meta.url),
  "utf8",
));
export const differenceBuild = parseCandidateDifferenceBuild(task2ApiPacket);
export const dynamicPacket = differenceBuild.packet;
const opportunity = dynamicPacket.opportunities[0];
const firstPartition = opportunity?.partitions[0];
const secondPartition = opportunity?.partitions[1];
if (!opportunity || !firstPartition || !secondPartition) {
  throw new Error("Task2 fixture requires one opportunity with two partitions");
}
export const opportunityId = opportunity.opportunityId;
export const firstPartitionId = firstPartition.partitionId;
export const secondPartitionId = secondPartition.partitionId;

export const validDynamicOutput = {
  kind: "question",
  opportunityId,
  prompt: "哪一个时间段更接近你的工作变化？",
  options: [
    { partitionId: firstPartitionId, label: "2018—2020 年" },
    { partitionId: secondPartitionId, label: "2021—2023 年" },
  ],
} as const;

export const generationCommand: DynamicQuestionGenerationCommand = {
  caseId,
  actionId,
  turnVersion: 4,
  unmatchedNote: null,
};

export function deterministicIds(onCreate?: () => void): () => string {
  const values = [
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000002",
    "00000000-0000-4000-8000-000000000003",
    "00000000-0000-4000-8000-000000000004",
    "00000000-0000-4000-8000-000000000005",
  ];
  let index = 0;
  return () => {
    onCreate?.();
    const value = values[index];
    index += 1;
    if (value === undefined) throw new Error("test id supply exhausted");
    return value;
  };
}

export function generatorFrom(
  generate: (prompt: string) => string | Promise<string>,
): BirthTimeGuideGenerator {
  return { async generate(prompt) { return { text: await generate(prompt) }; } };
}

export function dynamicService(input?: {
  readonly build?: CandidateDifferenceBuild;
  readonly generator?: BirthTimeGuideGenerator | null;
  readonly createId?: () => string;
  readonly onCommit?: (
    question: PersistedDynamicChoiceQuestion | null,
    commit: DynamicQuestionGenerationCommit,
  ) => void;
}) {
  return createBirthTimeGuideService({
    generator: input?.generator ?? null,
    timeoutMs: 20,
    async loadCase() { return null; },
    async proposeEvidenceDraft() { throw new Error("legacy draft is outside this harness"); },
    async loadDynamicQuestionBuild() { return input?.build ?? differenceBuild; },
    async commitDynamicQuestion(_userId, _command, question, commit) {
      input?.onCommit?.(question, commit);
      return commit;
    },
    createDynamicId: input?.createId ?? deterministicIds(),
  });
}
