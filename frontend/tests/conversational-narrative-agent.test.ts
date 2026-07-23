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
    sensitivityScope: {
      source: "time_linked_candidate_scan_samples",
      rangeStart: "05:16",
      rangeEnd: "05:24",
      sampleTimes: ["05:16", "05:24"],
    },
    stableLayers: [{ layer: "D1", values: ["Cancer"], referenceIds: ["consult-d1-ascendant"] }],
    sensitiveLayers: [
      { layer: "D9", values: ["Leo", "Virgo"], referenceIds: ["consult-d9-candidate-difference"] },
      { layer: "D10", values: ["Libra", "Scorpio"], referenceIds: ["consult-d10-candidate-difference"] },
    ],
    supportedSensitiveLayers: ["D9", "D10"],
    scoredHistoricalEvidence: [],
    suggestedDomains: [
      { domain: "relationship", layer: "D9", reason: "D9 在候选范围内呈现 Leo / Virgo 差异，可用已发生的关系事件区分。" },
      { domain: "career", layer: "D10", reason: "D10 在候选范围内呈现 Libra / Scorpio 差异，可用已发生的事业事件区分。" },
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
      "当前仍在核对 05:16–05:24 的候选范围，还不能把其中某一分钟当作确定出生时间。",
      "先说一件已经发生的重要关系经历好吗？尽量写明哪一年、哪一月以及发生了什么。",
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
      { domain: "relationship", layer: "D9", reason: packet.suggestedDomains[0]?.reason ?? "" },
      { domain: "career", layer: "D10", reason: packet.suggestedDomains[1]?.reason ?? "" },
    ],
    evidenceRequest: {
      domains: ["relationship"],
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
  assert.match(result.narrative, /05:16–05:24[\s\S]*不能/);
  assert.doesNotMatch(result.narrative, /\bD\d+\b/);
  assert.equal((result.narrative.match(/[？?]/g) ?? []).length, 1);
  assert.match(result.narrative, /已经发生[\s\S]*哪一年[\s\S]*哪一月/);
  assert.doesNotMatch(result.narrative, /^哪一个时间段[\s\S]*\d{4}[–—-]\d{4}/);
});

test("repairs missing safety wording without replacing the model-authored narrative", async () => {
  const packet = syntheticTechnicalPacket();
  const output = {
    ...richOutput(),
    narrative: "我们先从你印象最深的一次关系变化聊起，好吗？",
    evidenceRequest: {
      domains: ["relationship" as const],
      datePrecision: "month_preferred" as const,
      prompt: "那段关系大约是什么时候发生的？",
    },
  };

  const result = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([output]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.match(result.narrative, /印象最深的一次关系变化/);
  assert.match(result.narrative, /05:16–05:24/);
  assert.match(result.narrative, /不能直接当作已经确认/);
  assert.match(result.narrative, /关系变化[\s\S]*什么时候发生/);
  assert.doesNotMatch(result.narrative, /请只提供已经发生/);
  assert.match(result.output.evidenceRequest?.prompt ?? "", /关系大约是什么时候/);
  assert.doesNotMatch(result.output.evidenceRequest?.prompt ?? "", /请以已经发生的真实事件为准/);
});

test("repairs a natural intermediate follow-up prompt without discarding the specific reply", async () => {
  const packet = syntheticTechnicalPacket();
  const output = {
    ...richOutput(),
    narrative: "你把毕业和读研的衔接说清楚了，这两段会分别记录。下一步想确认毕业后的第一份工作是什么时候开始的？",
    evidenceRequest: {
      domains: ["career" as const],
      datePrecision: "month_preferred" as const,
      prompt: "第一份工作是什么时候开始的？",
    },
  };

  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet,
    generator: generator([output]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.match(result.narrative, /毕业和读研的衔接/);
  assert.doesNotMatch(result.narrative, /当前累计/);
  assert.equal(result.output.evidenceRequest?.prompt, "第一份工作是什么时候开始的？");
});

test("makes an internal evidence prompt visible when the acknowledgement contains no question", async () => {
  const output = {
    ...richOutput(),
    narrative: "已记录本科毕业后衔接读研，这是一段连续教育转折，暂时不重复计数。",
    evidenceRequest: {
      domains: ["career" as const],
      datePrecision: "month_preferred" as const,
      prompt: "毕业后的第一份工作是什么时候开始的？",
    },
  };

  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    generator: generator([output]),
  });

  assert.equal(result.fallbackUsed, false);
  assert.match(result.narrative, /连续教育转折/);
  assert.match(result.narrative, /第一份工作是什么时候开始的/);
  assert.doesNotMatch(result.narrative, /请只提供已经发生/);
});

test("adds the concrete question when the acknowledgement only says whether more detail is needed", async () => {
  const output = {
    ...richOutput(),
    narrative: "这次入职会作为一条事业事件记录，但还需要知道后续是否发生过离职、转岗或升职。",
    evidenceRequest: {
      domains: ["career" as const],
      datePrecision: "month_preferred" as const,
      prompt: "这份工作后来第一次发生明确变化是在什么时候？",
    },
  };

  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    generator: generator([output]),
  });

  assert.equal(result.fallbackUsed, false);
  assert.match(result.narrative, /还需要知道后续是否发生过/);
  assert.match(result.narrative, /第一次发生明确变化是在什么时候/);
});

test("passes the bounded expert workflow to the skill-guided narrator", async () => {
  const prompts: string[] = [];
  const packet = {
    ...syntheticTechnicalPacket(),
    expertWorkflow: {
      boundary: "not_auto_rectified" as const,
      candidateWindows: [{
        startTime: "05:16",
        endTime: "05:24",
        status: "pending_validation" as const,
      }],
      techniqueAuditTable: [{
        technique: "KP cusp / sub-lord",
        status: "blocked" as const,
        evidence: [],
        boundary: "当前评分合同没有可审计结果。",
      }],
      confirmationAllowed: false,
      hardBlockers: ["minute_holdout_not_ready"],
      gates: {},
    },
  };

  await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([richOutput()], prompts),
  });

  assert.match(prompts[0] ?? "", /expertWorkflow/);
  assert.match(prompts[0] ?? "", /KP cusp \/ sub-lord/);
  assert.match(prompts[0] ?? "", /blockedOrNotEvaluatedTechniquesMustNeverBeClaimedAsUsed/);
});

test("passes the user's latest concrete event to an intermediate skill-guided reply", async () => {
  const prompts: string[] = [];
  await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: {
      latestEvidence: [{
        dateLabel: "2023-09",
        summary: "离开家乡去上海开始第一份长期工作",
        domain: "career",
      }],
    },
    generator: generator([richOutput()], prompts),
  });

  assert.match(prompts[0] ?? "", /离开家乡去上海开始第一份长期工作/);
  assert.match(prompts[0] ?? "", /acknowledgeLatestEvidenceSpecificallyBeforeAsking/);
  assert.match(prompts[0] ?? "", /doNotRepeatCandidateBoundaryUnlessItChangedOrTheUserAsked/);
});

test("passes the active event ledger and unresolved facts to the intermediate agent", async () => {
  const prompts: string[] = [];
  await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: {
      latestUserText: "23年关系结束后发生过一次交通事故",
      latestEvidence: [{
        dateLabel: "2023",
        summary: "关系结束后发生过一次交通事故",
        domain: "health_pressure",
      }],
      eventLedger: [{
        id: "relationship-ending",
        rawText: "2024年8月8日一段重要关系结束",
        dateLabel: "2024-08-08",
        summary: "一段重要关系结束",
        domain: "relationship",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
      unresolvedEvidence: [{
        id: "accident-year-conflict",
        rawText: "23年关系结束后发生过一次交通事故",
        summary: "关系结束后发生过一次交通事故",
        domain: "health_pressure",
        dateLabel: "2023",
      }],
    },
    generator: generator([richOutput()], prompts),
  });

  const prompt = prompts[0] ?? "";
  assert.match(prompt, /23年关系结束后发生过一次交通事故/);
  assert.match(prompt, /2024-08-08/);
  assert.match(prompt, /一段重要关系结束/);
  assert.match(prompt, /finishCurrentEventBeforeSwitchingDomains/);
  assert.match(prompt, /resolveDateContradictionsBeforeScoring/);
  assert.match(prompt, /mergeSameEventDetailsWithoutDoubleCounting/);
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

test("accepts a concise first turn without exposing technical layer values", () => {
  const packet = syntheticTechnicalPacket();
  const invalid = {
    ...richOutput(),
    narrative: "当前仍在核对 05:16–05:24 的候选范围，不能视为已经确认的出生分钟。先说一件过去的重要关系经历好吗？请写明哪一年、哪一月。",
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.deepEqual(result, { valid: true, issues: [] });
});

test("rejects duplicated generic domain reasons that are not packet-grounded", () => {
  const packet = syntheticTechnicalPacket();
  const relationshipReason = richOutput().domainReasons[0];
  assert.ok(relationshipReason);
  const invalid = {
    ...richOutput(),
    domainReasons: [
      { ...relationshipReason, reason: "D9 may matter for this question" },
      { ...relationshipReason, reason: "D9 may matter for another question" },
    ],
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("packet discrimination explanation")));
});

test("rejects a generic broad-year choice questionnaire and uses a safe scoring-compatible fallback", async () => {
  const invalid = {
    ...richOutput(),
    narrative: [
      "05:20 是 05:16–05:24 范围内的待验证候选，不能视为已经确认的出生分钟。",
      "D1 的 Cancer 保持稳定；D9 的 Leo / Virgo 与 D10 的 Libra / Scorpio 都有分钟敏感差异。",
      "关系事件可区分 D9，事业事件可区分 D10。请按已经发生的经历选择哪一年、哪一月：A. 2018–2020；B. 2021–2023，哪个时间段更符合？",
    ].join("\n"),
    evidenceRequest: {
      domains: ["relationship", "career"],
      datePrecision: "month_preferred",
      prompt: "请按过去经历选择哪一年、哪一月：A. 2018–2020；B. 2021–2023，哪个时间段更符合？",
    },
  } satisfies RectificationNarrativeModelOutput;
  const direct = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

  assert.equal(direct.valid, false);
  assert.ok(direct.issues.some((issue) => issue.includes("broad-year choice questionnaire")));

  const result = await generateRectificationNarrative({
    phase: "first",
    packet: syntheticTechnicalPacket(),
    generator: generator([invalid, invalid]),
  });
  assert.equal(result.attempts, 2);
  assert.equal(result.fallbackUsed, true);
  assert.equal(result.allowEvidenceScoringAdvance, true);
});

test("rejects generic individual-year options even without a written range", () => {
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const invalid = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: "请按过去已经发生的事件选择哪一年、哪一月更符合：A. 2018年；B. 2021年。",
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("broad-year choice questionnaire")));
});

for (const prompt of [
  "请提供已经发生的真实事件：2018年还是2021年？也请说明哪一月以及发生了什么。",
  "请提供已经发生的真实事件，并说明哪一年：2018年、2021年；也请说明哪一月以及发生了什么。",
  "请提供已经发生的真实事件：2018年或2021年，也请说明哪一月以及发生了什么。",
]) {
  test(`rejects a rich first turn that proposes multiple years: ${prompt}`, () => {
    const output = richOutput();
    assert.ok(output.evidenceRequest);
    const invalid = {
      ...output,
      evidenceRequest: { ...output.evidenceRequest, prompt },
    } satisfies RectificationNarrativeModelOutput;
    const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

    assert.equal(result.valid, false);
    assert.ok(result.issues.some((issue) => issue.includes("broad-year choice questionnaire")));
  });
}

test("accepts a request for one real past event's year and month without proposed years", () => {
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const legitimate = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: "请提供一件已经发生的真实事件，并说明是哪一年、哪一月以及发生了什么。",
    },
  } satisfies RectificationNarrativeModelOutput;

  assert.deepEqual(
    validateNarrativeAgainstPacket(legitimate, syntheticTechnicalPacket(), "first"),
    { valid: true, issues: [] },
  );
});

test("accepts a natural reply that mentions several known dates before asking a non-year alternative", () => {
  const output = richOutput();
  const legitimate = {
    ...output,
    narrative: "你在2014年开始读研，并在2017年正常毕业，这条教育线已经完整。毕业后的第一份工作是直接入职，还是先休息了一段时间？",
    evidenceRequest: {
      domains: ["career" as const],
      datePrecision: "month_preferred" as const,
      prompt: "毕业后的第一份工作是什么时候开始的？",
    },
  } satisfies RectificationNarrativeModelOutput;

  assert.deepEqual(
    validateNarrativeAgainstPacket(legitimate, syntheticTechnicalPacket(), "intermediate"),
    { valid: true, issues: [] },
  );
});

test("rejects ungrounded layers and references nested in a domain reason", () => {
  const output = richOutput();
  const firstReason = output.domainReasons[0];
  assert.ok(firstReason);
  const invalid = {
    ...output,
    domainReasons: [
      { ...firstReason, reason: `${firstReason.reason} D60 另见 invented-reference。` },
      ...output.domainReasons.slice(1),
    ],
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("domainReasons[0].reason") && issue.includes("D60")));
  assert.ok(result.issues.some((issue) => issue.includes("domainReasons[0].reason") && issue.includes("invented-reference")));
});

test("rejects ungrounded times and references nested in the evidence request prompt", () => {
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const invalid = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: `${output.evidenceRequest.prompt} 请以 06:45 和 invented-reference 为准。`,
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("evidenceRequest.prompt") && issue.includes("06:45")));
  assert.ok(result.issues.some((issue) => issue.includes("evidenceRequest.prompt") && issue.includes("invented-reference")));
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
  assert.match(prompts[0] ?? "", /time_linked_candidate_scan_samples/);
  assert.equal(prompts.some((prompt) => prompt.includes("candidateWeights")), false);
  assert.equal(prompts.some((prompt) => prompt.includes("private-partition")), false);
});

test("uses a deterministic one-question conversational fallback after the second mismatch", async () => {
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
  assert.equal(first.allowEvidenceScoringAdvance, true);
  assert.equal(first.narrative, second.narrative);
  assert.match(first.narrative, /05:16–05:24[\s\S]*不能/);
  assert.doesNotMatch(first.narrative, /\bD\d+\b/);
  assert.match(first.narrative, /已经发生[\s\S]*年[\s\S]*月/);
  assert.equal((first.narrative.match(/[？?]/g) ?? []).length, 1);
  assert.deepEqual(first.output.evidenceRequest?.domains, ["relationship"]);
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
