import assert from "node:assert/strict";
import test from "node:test";
import {
  generateRectificationNarrative,
  validateNarrativeAgainstPacket,
  type RectificationNarrativeModelOutput,
} from "../src/lib/conversational-rectification/narrative-agent.ts";
import { validationReceiptSchema } from "../src/lib/conversational-rectification/persistence-contracts.ts";
import type { RectificationTechnicalPacket } from "../src/lib/conversational-rectification/technical-packet.ts";

function syntheticTechnicalPacket(): RectificationTechnicalPacket {
  return {
    calculationVersion: "rectification-technical-v1",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:20",
      range: { startTime: "05:16", endTime: "05:24" },
    },
    useBoundary: "该时间与范围仅是待验证候选，可用于比较稳定层和分钟敏感层，不能视为出生记录中的确定分钟。",
    candidateModelRefs: ["synthetic-candidate-model-v1"],
    candidateDifferenceRefs: ["difference-d9-relationship", "difference-d10-career"],
    candidateWeights: { "05:10": 0.4, "05:30": 0.6 },
    partitionIds: ["private-partition-early", "private-partition-late"],
    d1Stability: "stable",
    boundaryDistanceMinutes: 4,
    stableLayers: [{ layer: "D1", values: ["Cancer"], referenceIds: ["consult-d1-ascendant"] }],
    sensitiveLayers: [
      { layer: "D9", values: ["Leo", "Virgo"], referenceIds: ["consult-d9-candidate-difference"] },
      { layer: "D10", values: ["Libra", "Scorpio"], referenceIds: ["consult-d10-candidate-difference"] },
    ],
    supportedSensitiveLayers: ["D9", "D10"],
    scoredHistoricalEvidence: [],
    suggestedDomains: [
      { domain: "relationship", layer: "D9", reason: "D9 在候选范围内变化" },
      { domain: "career", layer: "D10", reason: "D10 在候选范围内变化" },
    ],
    referenceIds: [
      "difference-d9-relationship",
      "difference-d10-career",
      "consult-d1-ascendant",
      "consult-d9-candidate-difference",
      "consult-d10-candidate-difference",
    ],
    futureWindows: [{
      label: "2028 career context window",
      startDate: "2028-03-01",
      endDate: "2028-05-31",
      scoreable: false,
    }],
  };
}

function richOutput(): RectificationNarrativeModelOutput {
  const packet = syntheticTechnicalPacket();
  return {
    narrative: [
      "05:20 是 05:16–05:24 范围内的待验证候选，不是已经确认的出生分钟。",
      "D1 上升在范围内保持 Cancer，属于稳定层【consult-d1-ascendant】；D9 与 D10 分别出现 Leo/Virgo、Libra/Scorpio 的分钟敏感变化。",
      "因此关系事件可区分 D9，事业事件可区分 D10。请提供已经发生的真实事件，尽量写明哪一年、哪一月以及发生了什么。",
      "未来窗口只能作为背景，不能计入既成事件评分。",
    ].join("\n"),
    candidateStatus: "pending_validation",
    representativeTime: "05:20",
    rangeStart: "05:16",
    rangeEnd: "05:24",
    useBoundary: packet.useBoundary,
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    referenceIds: ["consult-d1-ascendant"],
    domainReasons: [
      { domain: "relationship", layer: "D9", reason: "D9 changes across the candidate minutes" },
      { domain: "career", layer: "D10", reason: "D10 changes across the candidate minutes" },
    ],
    evidenceRequest: {
      domains: ["relationship", "career"],
      datePrecision: "month_preferred",
      prompt: "请提供已经发生的真实关系或事业事件，并尽量说明哪一年、哪一月以及发生了什么。",
    },
  };
}

function generator(outputs: readonly unknown[], prompts: string[] = []) {
  let index = 0;
  return {
    modelId: "synthetic-narrative-model",
    async generate(prompt: string) {
      prompts.push(prompt);
      const output = outputs[Math.min(index, outputs.length - 1)];
      index += 1;
      return { text: JSON.stringify(output) };
    },
  };
}

test("validates a rich first-turn narrative against the technical packet", async () => {
  const packet = syntheticTechnicalPacket();
  const output = richOutput();
  assert.deepEqual(validateNarrativeAgainstPacket(output, packet, "first"), { valid: true, issues: [] });

  const result = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([output]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.allowEvidenceScoringAdvance, true);
  assert.equal(validationReceiptSchema.safeParse(result.validationReceipt).success, true);
  assert.equal(result.output.candidateStatus, "pending_validation");
  assert.match(result.narrative, /待验证候选/);
  assert.match(result.narrative, /D1/);
  assert.match(result.narrative, /D9[\s\S]*D10/);
  assert.match(result.narrative, /关系[\s\S]*D9[\s\S]*事业[\s\S]*D10/);
  assert.match(result.narrative, /已经发生[\s\S]*哪一年[\s\S]*哪一月/);
  assert.doesNotMatch(result.narrative, /^哪一个时间段[\s\S]*\d{4}[–—-]\d{4}/);
});

test("rejects invented representative times, layers, and references", () => {
  const packet = syntheticTechnicalPacket();
  const invalid = {
    ...richOutput(),
    representativeTime: "06:45",
    sensitiveLayers: ["D9", "D60"],
    referenceIds: ["invented-reference"],
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("representativeTime")));
  assert.ok(result.issues.some((issue) => issue.includes("D60")));
  assert.ok(result.issues.some((issue) => issue.includes("invented-reference")));
});

test("rejects an invented plain-text technical reference omitted from the reference list", () => {
  const packet = syntheticTechnicalPacket();
  const invalid = {
    ...richOutput(),
    narrative: `${richOutput().narrative}\n另见 invented-reference。`,
  };
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("invented-reference")));
});

test("retries expression exactly once with the same grounded packet", async () => {
  const packet = syntheticTechnicalPacket();
  const prompts: string[] = [];
  const result = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([{ ...richOutput(), representativeTime: "06:45" }, richOutput()], prompts),
  });

  assert.equal(result.attempts, 2);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.allowEvidenceScoringAdvance, true);
  assert.equal(prompts.length, 2);
  assert.match(prompts[0] ?? "", /rectification-technical-v1/);
  assert.match(prompts[1] ?? "", /rectification-technical-v1/);
  assert.equal(prompts.some((prompt) => prompt.includes("candidateWeights")), false);
  assert.equal(prompts.some((prompt) => prompt.includes("private-partition")), false);
});

test("uses a deterministic rich Chinese fallback after the second mismatch and holds scoring", async () => {
  const packet = syntheticTechnicalPacket();
  const invalid = { ...richOutput(), sensitiveLayers: ["D60"] };
  const first = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([invalid, invalid]),
  });
  const second = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([invalid, invalid]),
  });

  assert.equal(first.attempts, 2);
  assert.equal(first.fallbackUsed, true);
  assert.equal(first.allowEvidenceScoringAdvance, false);
  assert.equal(first.narrative, second.narrative);
  assert.match(first.narrative, /05:20[\s\S]*待验证/);
  assert.match(first.narrative, /D1[\s\S]*稳定/);
  assert.match(first.narrative, /D9[\s\S]*D10[\s\S]*敏感/);
  assert.match(first.narrative, /已经发生[\s\S]*年[\s\S]*月/);
  assert.match(first.narrative, /未来[\s\S]*不能[\s\S]*评分/);
});

test("bounds fallback validation issues for the durable receipt", async () => {
  const inventedReference = `invented-${"x".repeat(500)}`;
  const invalid = {
    ...richOutput(),
    narrative: `${richOutput().narrative}\n另见 ${inventedReference}。`,
  };
  const result = await generateRectificationNarrative({
    phase: "first",
    packet: syntheticTechnicalPacket(),
    generator: generator([invalid, invalid]),
  });

  assert.equal(result.fallbackUsed, true);
  assert.ok(result.validationReceipt.issues.length <= 20);
  assert.ok(result.validationReceipt.issues.every((issue) => issue.length <= 240));
});

test("builds distinct first, intermediate, and final grounded prompts", async () => {
  for (const phase of ["first", "intermediate", "final"] as const) {
    const prompts: string[] = [];
    await generateRectificationNarrative({
      phase,
      packet: syntheticTechnicalPacket(),
      generator: generator([richOutput()], prompts),
    });
    assert.match(prompts[0] ?? "", new RegExp(`\\"phase\\":\\"${phase}\\"`));
  }
});
