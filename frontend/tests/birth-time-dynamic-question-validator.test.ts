import assert from "node:assert/strict";
import test from "node:test";
import { BirthTimeGuideOutputError } from "../src/lib/birth-time-guide-agent.ts";
import {
  BirthTimeDynamicBindingError,
  bindDynamicQuestion,
  generateDynamicQuestionPrompt,
  parseDynamicQuestionOutput,
} from "../src/lib/birth-time-dynamic-question-validator.ts";
import { toPublicDynamicChoiceQuestion } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import {
  deterministicIds,
  differenceBuild,
  dynamicPacket,
  firstPartitionId,
  opportunityId,
  validDynamicSelection,
} from "./fixtures/birth-time-dynamic-question-fixture.ts";

test("prompt exposes only public opportunity-selection fields", () => {
  const serialized = generateDynamicQuestionPrompt(
    dynamicPacket,
  );
  const prompt = JSON.parse(serialized);

  assert.equal("unmatchedNote" in prompt, false);
  for (const forbidden of [
    "candidateScores", "candidateModel", "estimatedInformationGain", "currentRange",
    "scoringVersion", "askedQuestionFingerprints", "candidatePartitionFingerprints",
    "recentRangeHistory", "04:00", "confidence",
  ]) assert.equal(serialized.includes(forbidden), false, forbidden);
});

test("model output is a strict selection over one exact server opportunity", () => {
  assert.equal(parseDynamicQuestionOutput(validDynamicSelection, dynamicPacket).kind, "question");
  for (const unsafe of [
    { ...validDynamicSelection, opportunityId: ` ${opportunityId}` },
    { ...validDynamicSelection, opportunityId: "unknown-opportunity" },
    {
      ...validDynamicSelection,
      prompt: "开始工作后，你爱喝茶还是喝水发生变化了吗？",
      options: [
        { partitionId: firstPartitionId, label: "经常喝茶" },
        { partitionId: firstPartitionId, label: "经常喝水" },
      ],
    },
    { ...validDynamicSelection, prompt: "出生时间更接近 04:00 吗？" },
  ]) assert.throws(() => parseDynamicQuestionOutput(unsafe, dynamicPacket), BirthTimeGuideOutputError);
});

test("server renders selected copy and attaches the corresponding private vectors", () => {
  const selection = parseDynamicQuestionOutput(validDynamicSelection, dynamicPacket);
  if (selection.kind !== "question") throw new Error("expected a selection");

  const internal = bindDynamicQuestion(selection, differenceBuild, deterministicIds());
  const opportunity = dynamicPacket.opportunities[0];
  const publicQuestion = toPublicDynamicChoiceQuestion(internal);

  assert.equal(internal.source, "agent");
  assert.equal(publicQuestion.prompt, opportunity?.fallbackPrompt);
  assert.deepEqual(publicQuestion.options.slice(0, 2).map((item) => item.label),
    opportunity?.partitions.map((item) => item.fallbackLabel));
  assert.deepEqual(internal.options[0]?.candidateScores, { "04:00": 1, "04:01": 0 });
  assert.deepEqual(publicQuestion.options.slice(-2).map((item) => item.label), [
    "不确定 / 不记得", "都不符合",
  ]);
  assert.equal(JSON.stringify(publicQuestion).includes(firstPartitionId), false);
  assert.equal(JSON.stringify(publicQuestion).includes("04:00"), false);
});

test("private bindings fail before allocating a server id", () => {
  const selection = parseDynamicQuestionOutput(validDynamicSelection, dynamicPacket);
  if (selection.kind !== "question") throw new Error("expected a selection");
  let allocations = 0;
  const malformed = {
    ...differenceBuild,
    scoringPartitions: {
      [opportunityId]: differenceBuild.scoringPartitions[opportunityId]?.slice(0, 1) ?? [],
    },
  };

  assert.throws(() => bindDynamicQuestion(selection, malformed, deterministicIds(() => {
    allocations += 1;
  })), BirthTimeDynamicBindingError);
  assert.equal(allocations, 0);
});

test("normalized duplicate server labels fail before allocating a server id", () => {
  const opportunity = dynamicPacket.opportunities[0];
  const privatePartitions = differenceBuild.scoringPartitions[opportunityId];
  if (!opportunity || !privatePartitions) throw new Error("missing test opportunity");
  const labels = ["２０１８ 年", "2018年"];
  const malformed = {
    ...differenceBuild,
    packet: {
      ...dynamicPacket,
      opportunities: [{
        ...opportunity,
        partitions: opportunity.partitions.map((item, index) => ({
          ...item, fallbackLabel: labels[index] ?? item.fallbackLabel,
        })),
      }],
    },
    scoringPartitions: {
      [opportunityId]: privatePartitions.map((item, index) => ({
        ...item, fallbackLabel: labels[index] ?? item.fallbackLabel,
      })),
    },
  };
  let allocations = 0;

  assert.throws(() => bindDynamicQuestion(
    validDynamicSelection,
    malformed,
    deterministicIds(() => { allocations += 1; }),
  ), BirthTimeDynamicBindingError);
  assert.equal(allocations, 0);
});

test("primary labels cannot collide with either reserved visible choice", () => {
  const opportunity = dynamicPacket.opportunities[0];
  const privatePartitions = differenceBuild.scoringPartitions[opportunityId];
  if (!opportunity || !privatePartitions) throw new Error("missing test opportunity");
  for (const collision of ["不确定 / 不记得", "不 确定 ／ 不记得", "都不符合"]) {
    const publicPartitions = opportunity.partitions.map((item, index) => (
      index === 0 ? { ...item, fallbackLabel: collision } : item
    ));
    const privateCopy = privatePartitions.map((item, index) => (
      index === 0 ? { ...item, fallbackLabel: collision } : item
    ));
    let allocations = 0;

    assert.throws(() => bindDynamicQuestion(validDynamicSelection, {
      ...differenceBuild,
      packet: { ...dynamicPacket, opportunities: [{ ...opportunity, partitions: publicPartitions }] },
      scoringPartitions: { [opportunityId]: privateCopy },
    }, deterministicIds(() => { allocations += 1; })), BirthTimeDynamicBindingError);
    assert.equal(allocations, 0, collision);
  }
});

test("server prompt accepts 120 characters but rejects longer copy before IDs", () => {
  const opportunity = dynamicPacket.opportunities[0];
  if (!opportunity) throw new Error("missing test opportunity");
  const promptWithLength = (length: number) => `${"问".repeat(length - 1)}？`;
  const buildWithPrompt = (length: number) => ({
    ...differenceBuild,
    packet: {
      ...dynamicPacket,
      opportunities: [{ ...opportunity, fallbackPrompt: promptWithLength(length) }],
    },
  });

  assert.equal(
    bindDynamicQuestion(validDynamicSelection, buildWithPrompt(120), deterministicIds()).prompt.length,
    120,
  );
  for (const length of [121, 240]) {
    let allocations = 0;
    assert.throws(() => bindDynamicQuestion(
      validDynamicSelection,
      buildWithPrompt(length),
      deterministicIds(() => { allocations += 1; }),
    ), BirthTimeDynamicBindingError);
    assert.equal(allocations, 0, String(length));
  }
});

test("repeated server semantics and partitions remain recoverable rejections", () => {
  const selection = parseDynamicQuestionOutput(validDynamicSelection, dynamicPacket);
  if (selection.kind !== "question") throw new Error("expected a selection");
  const first = bindDynamicQuestion(selection, differenceBuild, deterministicIds());

  assert.throws(() => bindDynamicQuestion(selection, {
    ...differenceBuild,
    packet: { ...dynamicPacket, askedQuestionFingerprints: [first.questionFingerprint] },
  }, deterministicIds()), BirthTimeGuideOutputError);
  assert.throws(() => bindDynamicQuestion(selection, {
    ...differenceBuild,
    packet: {
      ...dynamicPacket,
      candidatePartitionFingerprints: [dynamicPacket.opportunities[0]?.candidatePartitionFingerprint ?? ""],
    },
  }, deterministicIds()), BirthTimeGuideOutputError);
});
