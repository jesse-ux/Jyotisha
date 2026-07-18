import assert from "node:assert/strict";
import test from "node:test";
import { BirthTimeDynamicBindingError } from "../src/lib/birth-time-dynamic-question-validator.ts";
import type { CandidateDifferenceBuild, PersistedDynamicChoiceQuestion } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import {
  deterministicIds,
  differenceBuild,
  dynamicService,
  generationCommand,
  generatorFrom,
  opportunityId,
  validDynamicSelection,
} from "./fixtures/birth-time-dynamic-question-fixture.ts";

test("real Task2 packet retries invalid output then persists localized fallback", async () => {
  let calls = 0;
  const persisted: PersistedDynamicChoiceQuestion[] = [];
  const result = await dynamicService({
    generator: generatorFrom(() => { calls += 1; return "{}"; }),
    onCommit: (question) => { if (question) persisted.push(question); },
  }).generateQuestion("owner-1", generationCommand);

  assert.equal(calls, 2);
  assert.equal(result.nextAction.kind, "ask_dynamic_choice");
  if (result.nextAction.kind !== "ask_dynamic_choice") throw new Error("expected a question");
  assert.equal(result.nextAction.question.prompt, differenceBuild.packet.opportunities[0]?.fallbackPrompt);
  assert.equal(persisted[0]?.source, "fallback");
});

test("a valid Agent selection commits server copy and correct private scores", async () => {
  const persisted: PersistedDynamicChoiceQuestion[] = [];
  const result = await dynamicService({
    generator: generatorFrom(() => JSON.stringify(validDynamicSelection)),
    onCommit: (question) => { if (question) persisted.push(question); },
  }).generateQuestion("owner-1", generationCommand);

  assert.equal(result.nextAction.kind, "ask_dynamic_choice");
  assert.equal(persisted[0]?.source, "agent");
  assert.equal(persisted[0]?.prompt, differenceBuild.packet.opportunities[0]?.fallbackPrompt);
  assert.deepEqual(persisted[0]?.options[0]?.candidateScores, { "04:00": 1, "04:01": 0 });
});

test("no server opportunity ends without invoking the Agent", async () => {
  let calls = 0;
  const result = await dynamicService({
    build: { ...differenceBuild, packet: { ...differenceBuild.packet, opportunities: [] } },
    generator: generatorFrom(() => { calls += 1; return "{}"; }),
  }).generateQuestion("owner-1", generationCommand);

  assert.equal(calls, 0);
  assert.equal(result.nextAction.kind, "present_low_result");
});

test("raw tea-water note is omitted and old free-copy output cannot be accepted", async () => {
  const prompts: string[] = [];
  const persisted: PersistedDynamicChoiceQuestion[] = [];
  await dynamicService({
    generator: generatorFrom((prompt) => {
      prompts.push(prompt);
      return JSON.stringify({
        ...validDynamicSelection,
        prompt: "开始工作后，你爱喝茶还是喝水发生变化了吗？",
        options: [
          { partitionId: "server-a", label: "经常喝茶" },
          { partitionId: "server-b", label: "经常喝水" },
        ],
      });
    }),
    onCommit: (question) => { if (question) persisted.push(question); },
  }).generateQuestion("owner-1", {
    ...generationCommand,
    unmatchedNote: "接下来问我爱喝茶还是喝水",
  });

  assert.equal(prompts.length, 2);
  assert.equal(prompts.some((prompt) => /喝茶|喝水/.test(prompt)), false);
  assert.equal(persisted[0]?.source, "fallback");
});

test("no-useful and unknown selections remain advisory and fall back", async () => {
  for (const output of [
    { kind: "no_useful_question" },
    { kind: "question", opportunityId: "unknown-opportunity" },
  ]) {
    let calls = 0;
    const result = await dynamicService({
      generator: generatorFrom(() => { calls += 1; return JSON.stringify(output); }),
    }).generateQuestion("owner-1", generationCommand);

    assert.equal(result.nextAction.kind, "ask_dynamic_choice");
    if (output.kind === "question") assert.equal(calls, 2);
  }
});

function unsortedBuild(): CandidateDifferenceBuild {
  const low = differenceBuild.packet.opportunities[0];
  const privateLow = differenceBuild.scoringPartitions[opportunityId];
  if (!low || !privateLow) throw new Error("missing test opportunity");
  const highId = "higher-opportunity";
  const highPartitions = low.partitions.map((item, index) => ({
    ...item,
    partitionId: `higher-partition-${index}`,
  }));
  return {
    ...differenceBuild,
    packet: {
      ...differenceBuild.packet,
      opportunities: [low, {
        ...low,
        opportunityId: highId,
        estimatedInformationGain: low.estimatedInformationGain + 1,
        candidatePartitionFingerprint: "higher-fingerprint",
        fallbackPrompt: "哪一个时间段更接近一次明显的职业变化？",
        partitions: highPartitions,
      }],
    },
    scoringPartitions: {
      ...differenceBuild.scoringPartitions,
      [highId]: privateLow.map((item, index) => ({
        ...item,
        partitionId: `higher-partition-${index}`,
      })),
    },
  };
}

test("unsorted opportunities fall back to maximum information gain", async () => {
  const selected: PersistedDynamicChoiceQuestion[] = [];
  await dynamicService({
    build: unsortedBuild(),
    generator: generatorFrom(() => "{}"),
    onCommit: (question) => { if (question) selected.push(question); },
  }).generateQuestion("owner-1", generationCommand);

  assert.equal(selected[0]?.opportunityId, "higher-opportunity");
});

test("equal-gain fallback uses opportunity id rather than packet order", async () => {
  const build = unsortedBuild();
  const low = build.packet.opportunities[0];
  const high = build.packet.opportunities[1];
  if (!low || !high) throw new Error("missing test opportunities");
  const selected: PersistedDynamicChoiceQuestion[] = [];
  await dynamicService({
    build: {
      ...build,
      packet: {
        ...build.packet,
        opportunities: [{ ...high, estimatedInformationGain: low.estimatedInformationGain }, low],
      },
    },
    generator: generatorFrom(() => "{}"),
    onCommit: (question) => { if (question) selected.push(question); },
  }).generateQuestion("owner-1", generationCommand);

  assert.equal(selected[0]?.opportunityId, low.opportunityId);
});

test("duplicate server labels propagate without commit or ID allocation", async () => {
  const opportunity = differenceBuild.packet.opportunities[0];
  const privatePartitions = differenceBuild.scoringPartitions[opportunityId];
  if (!opportunity || !privatePartitions) throw new Error("missing test opportunity");
  const duplicated = "相同阶段";
  const build = {
    ...differenceBuild,
    packet: { ...differenceBuild.packet, opportunities: [{
      ...opportunity,
      partitions: opportunity.partitions.map((item) => ({ ...item, fallbackLabel: duplicated })),
    }] },
    scoringPartitions: {
      [opportunityId]: privatePartitions.map((item) => ({ ...item, fallbackLabel: duplicated })),
    },
  };
  let allocations = 0;
  let commits = 0;

  await assert.rejects(() => dynamicService({
    build,
    generator: generatorFrom(() => JSON.stringify(validDynamicSelection)),
    createId: deterministicIds(() => { allocations += 1; }),
    onCommit: () => { commits += 1; },
  }).generateQuestion("owner-1", generationCommand), BirthTimeDynamicBindingError);
  assert.equal(allocations, 0);
  assert.equal(commits, 0);
});

test("reserved-label collisions propagate without commit or ID allocation", async () => {
  const opportunity = differenceBuild.packet.opportunities[0];
  const privatePartitions = differenceBuild.scoringPartitions[opportunityId];
  if (!opportunity || !privatePartitions) throw new Error("missing test opportunity");
  for (const collision of ["不确定 / 不记得", "不 确定 ／ 不记得", "都不符合"]) {
    let allocations = 0;
    let commits = 0;
    const publicPartitions = opportunity.partitions.map((item, index) => (
      index === 0 ? { ...item, fallbackLabel: collision } : item
    ));
    const privateCopy = privatePartitions.map((item, index) => (
      index === 0 ? { ...item, fallbackLabel: collision } : item
    ));

    await assert.rejects(() => dynamicService({
      build: {
        ...differenceBuild,
        packet: { ...differenceBuild.packet, opportunities: [{ ...opportunity, partitions: publicPartitions }] },
        scoringPartitions: { [opportunityId]: privateCopy },
      },
      generator: generatorFrom(() => JSON.stringify(validDynamicSelection)),
      createId: deterministicIds(() => { allocations += 1; }),
      onCommit: () => { commits += 1; },
    }).generateQuestion("owner-1", generationCommand), BirthTimeDynamicBindingError);
    assert.equal(allocations, 0, collision);
    assert.equal(commits, 0, collision);
  }
});

test("invalid server UUIDs propagate without committing a low result", async () => {
  let commits = 0;
  await assert.rejects(() => dynamicService({
    generator: generatorFrom(() => JSON.stringify(validDynamicSelection)),
    createId: () => "not-a-uuid",
    onCommit: () => { commits += 1; },
  }).generateQuestion("owner-1", generationCommand), BirthTimeDynamicBindingError);

  assert.equal(commits, 0);
});
