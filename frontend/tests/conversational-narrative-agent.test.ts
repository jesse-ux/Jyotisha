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

test("preserves a complete model-authored first-turn narrative verbatim", async () => {
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
  assert.equal(result.narrative, output.narrative);
  assert.doesNotMatch(result.narrative, /05:16–05:24|不能直接当作已经确认/);
  assert.equal(result.output.evidenceRequest?.prompt, "那段关系大约是什么时候发生的？");
});

test("allows a first-turn acknowledgement without forcing a question", async () => {
  const narrative = "我们先把你记得的出生范围当作起点。你可以按自己的节奏往下讲。";
  const result = await generateRectificationNarrative({
    phase: "first",
    packet: syntheticTechnicalPacket(),
    generator: generator([{ narrative, evidenceRequest: null }]),
  });

  assert.equal(result.fallbackUsed, false);
  assert.equal(result.narrative, narrative);
  assert.equal(result.output.evidenceRequest, null);
  assert.doesNotMatch(result.narrative, /[？?]/);
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

test("preserves the target event in an intermediate detail follow-up", async () => {
  const evidenceId = "00000000-0000-4000-8000-000000000321";
  const output = {
    ...richOutput(),
    narrative: "记下了你在 2017 年 5 月参加工作。那是第一份正式工作，还是实习或兼职？",
    evidenceRequest: {
      domains: ["career" as const],
      datePrecision: "month_preferred" as const,
      prompt: "那是第一份正式工作，还是实习或兼职？",
      followUp: { kind: "event_detail" as const, evidenceId },
    },
  };

  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    generator: generator([output]),
    context: {
      eventLedger: [{
        id: evidenceId,
        rawText: "2017年5月参加工作",
        dateLabel: "2017-05",
        summary: "参加工作",
        domain: "career",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
    },
  });

  assert.equal(result.fallbackUsed, false);
  assert.deepEqual(result.output.evidenceRequest?.followUp, {
    kind: "event_detail",
    evidenceId,
  });
});

test("keeps a natural intermediate acknowledgement without appending a question", async () => {
  const narrative = "已记录本科毕业后衔接读研，这是一段连续教育转折，暂时不重复计数。你可以继续讲。";
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    generator: generator([{ narrative, evidenceRequest: null }]),
  });

  assert.equal(result.fallbackUsed, false);
  assert.equal(result.narrative, narrative);
  assert.equal(result.output.evidenceRequest, null);
  assert.doesNotMatch(result.narrative, /[？?]/);
});

test("keeps technical packets and event bookkeeping out of ordinary narrative turns", async () => {
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
    phase: "intermediate",
    packet,
    context: {
      latestUserText: "2016 年离家去外地上大学",
      recentConversation: [{ role: "user", text: "2016 年离家去外地上大学" }],
      eventLedger: [{
        id: "00000000-0000-4000-8000-000000000801",
        rawText: "2016 年离家去外地上大学",
        dateLabel: "2016",
        summary: "离家去外地上大学",
        domain: "education",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
    },
    generator: generator([{
      narrative: "第一次长期离开家，生活节奏应该一下子变了很多。你可以接着讲后来发生的事。",
      evidenceRequest: null,
    }], prompts),
  });

  assert.match(prompts[0] ?? "", /2016 年离家去外地上大学/);
  assert.doesNotMatch(prompts[0] ?? "", /packet/);
  assert.doesNotMatch(prompts[0] ?? "", /eventLedger/);
  assert.doesNotMatch(prompts[0] ?? "", /expertWorkflow/);
  assert.doesNotMatch(prompts[0] ?? "", /KP cusp \/ sub-lord/);
  assert.doesNotMatch(prompts[0] ?? "", /minute_holdout_not_ready/);
  assert.doesNotMatch(prompts[0] ?? "", /05:16|05:24|D9|D10/);
});

test("drops a hidden follow-up that the user cannot see", async () => {
  const hidden = {
    narrative: "第一次长期离开家，生活节奏应该一下子变了很多。你可以接着讲后来发生的事。",
    evidenceRequest: {
      datePrecision: "month_preferred" as const,
      prompt: "2016 年离家去外地上大学大概是几月？",
      followUp: { kind: "new_event" as const, evidenceId: null },
    },
  };
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: { latestUserText: "2016 年离家去外地上大学" },
    generator: generator([hidden]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.output.evidenceRequest, null);
});

test("appends the three auditable tables to every final Agent answer", async () => {
  const packet: RectificationTechnicalPacket = {
    ...syntheticTechnicalPacket(),
    scoredHistoricalEvidence: [{
      evidenceId: "00000000-0000-4000-8000-000000000602",
      domain: "career",
      candidateTime: "05:20",
      score: 3.5,
      ruleRefs: ["vim-md-career"],
    }],
    expertWorkflow: {
      boundary: "not_auto_rectified",
      candidateWindows: [{
        startTime: "05:16",
        endTime: "05:24",
        status: "ready_for_confirmation",
      }],
      techniqueAuditTable: [{
        technique: "VedAstro official validation",
        status: "used",
        evidence: ["official_verified", "event_discrimination_pass"],
        boundary: "胜出分钟必须在已发生事件扫描中严格领先次优分钟。",
      }],
      confirmationAllowed: true,
      hardBlockers: [],
      gates: {},
    },
  };
  const output: RectificationNarrativeModelOutput = {
    ...richOutput(),
    narrative: "当前证据支持 05:20 作为建议确认的分钟；写回前仍需你明确确认。",
    evidenceRequest: null,
  };
  const prompts: string[] = [];
  const result = await generateRectificationNarrative({
    phase: "final",
    packet,
    context: {
      eventLedger: [{
        id: "00000000-0000-4000-8000-000000000602",
        rawText: "2019年7月入职第一家公司",
        dateLabel: "2019-07",
        summary: "入职第一家公司",
        domain: "career",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
    },
    generator: generator([output], prompts),
  });

  assert.match(result.narrative, /### Technique Audit Table/);
  assert.match(result.narrative, /VedAstro official validation/);
  assert.match(result.narrative, /### 事件验证表/);
  assert.match(result.narrative, /2019-07[\s\S]*入职第一家公司[\s\S]*已纳入验证[\s\S]*已纳入当前候选比较/);
  assert.doesNotMatch(result.narrative, /3\.5|得分 \/ 状态|内部(?:分数|权重)/);
  assert.doesNotMatch(prompts[0] ?? "", /"score"\s*:\s*3\.5/);
  assert.match(result.narrative, /### 候选时间差异表/);
  assert.match(result.narrative, /05:16–05:24[\s\S]*D9[\s\S]*minute_sensitive/);
});

test("appends canonical final tables when the model only emits empty or incomplete headings", async () => {
  const output: RectificationNarrativeModelOutput = {
    ...richOutput(),
    narrative: [
      "当前证据已经形成建议结论，写回前仍需确认。",
      "### Technique Audit Table",
      "### 事件验证表",
      "| 时间 | 事件 |",
      "|---|---|",
      "### 候选时间差异表",
    ].join("\n\n"),
    evidenceRequest: null,
  };

  const result = await generateRectificationNarrative({
    phase: "final",
    packet: syntheticTechnicalPacket(),
    generator: generator([output]),
  });

  assert.equal(result.fallbackUsed, false);
  assert.match(result.narrative, /\| 技法 \| 状态 \| 证据 \| 使用边界 \|/);
  assert.match(result.narrative, /\| 时间 \| 事件 \| 领域 \| 验证状态 \| 结论 \|/);
  assert.match(result.narrative, /\| 候选范围 \| 层 \| 状态 \| 差异 \/ 证据 \|/);
  assert.equal((result.narrative.match(/### Technique Audit Table/g) ?? []).length, 2);
  assert.equal((result.narrative.match(/### 事件验证表/g) ?? []).length, 2);
  assert.equal((result.narrative.match(/### 候选时间差异表/g) ?? []).length, 2);
});

test("rejects a model-authored event table that exposes private numeric scoring", async () => {
  const packet: RectificationTechnicalPacket = {
    ...syntheticTechnicalPacket(),
    scoredHistoricalEvidence: [{
      evidenceId: "00000000-0000-4000-8000-000000000602",
      domain: "career",
      candidateTime: "05:20",
      score: 3.5,
      ruleRefs: ["vim-md-career"],
    }],
  };
  const unsafe: RectificationNarrativeModelOutput = {
    ...richOutput(),
    narrative: [
      "当前证据形成了候选结论。",
      "### 事件验证表",
      "| 时间 | 事件 | 得分 / 状态 |",
      "|---|---|---|",
      "| 2019-07 | 入职第一家公司 | 3.5 |",
    ].join("\n"),
    evidenceRequest: null,
  };

  const result = await generateRectificationNarrative({
    phase: "final",
    packet,
    generator: generator([unsafe, unsafe]),
  });

  assert.equal(result.fallbackUsed, true);
  assert.doesNotMatch(result.narrative, /3\.5|得分 \/ 状态/);
  assert.match(result.narrative, /候选范围/);
  assert.match(result.narrative, /系统验证尚未闭环/);
  assert.match(result.narrative, /不会替换当前排盘时间/);
  assert.doesNotMatch(result.narrative, /先说一件|再说一件/);
  assert.equal(result.output.evidenceRequest, null);
  assert.match(result.narrative, /\| 时间 \| 事件 \| 领域 \| 验证状态 \| 结论 \|/);
});

test("passes the user's latest words to an ordinary intermediate reply", async () => {
  const prompts: string[] = [];
  await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: {
      latestUserText: "2023年9月离开家乡去上海开始第一份长期工作",
      latestEvidence: [{
        dateLabel: "2023-09",
        summary: "离开家乡去上海开始第一份长期工作",
        domain: "career",
      }],
    },
    generator: generator([{
      narrative: "第一次长期离开家去工作，适应过程应该不轻松。你可以接着讲。",
      evidenceRequest: null,
    }], prompts),
  });

  assert.match(prompts[0] ?? "", /离开家乡去上海开始第一份长期工作/);
  assert.match(prompts[0] ?? "", /不要把自己写成记录员/);
  assert.doesNotMatch(prompts[0] ?? "", /latestEvidence/);
  assert.doesNotMatch(prompts[0] ?? "", /候选范围.*05:16/);
});

test("keeps internal event domains and suggested-domain routing out of the narrator context", async () => {
  const prompts: string[] = [];
  await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: {
      latestEvidence: [{
        id: "00000000-0000-4000-8000-000000000111",
        dateLabel: "2020-04",
        summary: "去石油化工研究院实习做研究员",
        domain: "other",
      }],
      eventLedger: [{
        id: "00000000-0000-4000-8000-000000000111",
        rawText: "2020年4月去石油化工研究院实习做研究员",
        dateLabel: "2020-04",
        summary: "去石油化工研究院实习做研究员",
        domain: "career",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
    },
    generator: generator([richOutput()], prompts),
  });

  const prompt = JSON.parse(prompts[0] ?? "{}") as {
    conversation?: Record<string, unknown>;
    packet?: Record<string, unknown>;
  };
  assert.equal(prompt.conversation?.latestEvidence, undefined);
  assert.equal(prompt.conversation?.eventLedger, undefined);
  assert.equal(prompt.packet?.suggestedDomains, undefined);
});

test("keeps the event ledger and unresolved facts out of the ordinary intermediate agent", async () => {
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
  assert.doesNotMatch(prompt, /2024-08-08/);
  assert.doesNotMatch(prompt, /eventLedger|unresolvedEvidence|resolveDateContradictionsBeforeScoring/);
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

test("accepts a natural first turn without a forced range, boundary, or date request", () => {
  const packet = syntheticTechnicalPacket();
  const invalid = {
    ...richOutput(),
    narrative: "我们先从你印象最深、最愿意讲的一段人生变化开始。发生了什么？",
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.deepEqual(result, { valid: true, issues: [] });
});

test("accepts natural domain explanations while still rejecting unknown domain-layer pairs", () => {
  const packet = syntheticTechnicalPacket();
  const relationshipReason = richOutput().domainReasons[0];
  assert.ok(relationshipReason);
  const paraphrased = {
    ...richOutput(),
    domainReasons: [
      { ...relationshipReason, reason: "D9 may matter for this question" },
      { ...relationshipReason, reason: "D9 may matter for another question" },
    ],
  } satisfies RectificationNarrativeModelOutput;
  assert.deepEqual(validateNarrativeAgainstPacket(paraphrased, packet, "first"), { valid: true, issues: [] });

  const ungrounded = {
    ...richOutput(),
    domainReasons: [{ domain: "finance" as const, layer: "D60", reason: "This invented layer should be rejected." }],
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(ungrounded, packet, "first");
  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("domain reason finance/D60")));
});

test("allows packet-grounded technical tables during an intermediate turn", () => {
  const packet = syntheticTechnicalPacket();
  const output = {
    ...richOutput(),
    narrative: [
      "你补充的关系变化已经记入当前事件线。",
      "### 候选时间差异表",
      "| 层级 | 当前观察 |",
      "| --- | --- |",
      "| D9 | 在候选范围内呈分钟敏感差异 |",
      "下一步我想继续了解这段关系结束后的直接变化。",
    ].join("\n"),
    evidenceRequest: null,
  } satisfies RectificationNarrativeModelOutput;

  assert.deepEqual(validateNarrativeAgainstPacket(output, packet, "intermediate"), { valid: true, issues: [] });
});

test("replaces a generic broad-year choice questionnaire with the safe fallback", async () => {
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
  assert.equal(result.fallbackUsed, true);
  assert.equal(result.output.evidenceRequest, null);
  assert.doesNotMatch(result.narrative, /2018–2020/);
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
      prompt: "毕业后的第一份工作是直接入职，还是先休息了一段时间？",
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
      { ...firstReason, reason: `${firstReason.reason} D60 另见【invented-reference】。` },
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
      prompt: `${output.evidenceRequest.prompt} 请以 06:45 和【invented-reference】为准。`,
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("evidenceRequest.prompt") && issue.includes("06:45")));
  assert.ok(result.issues.some((issue) => issue.includes("evidenceRequest.prompt") && issue.includes("invented-reference")));
});

test("rejects an invented citation-marked technical reference omitted from the reference list", () => {
  const packet = syntheticTechnicalPacket();
  const invalid = {
    ...richOutput(),
    narrative: `${richOutput().narrative}\n另见【invented-reference】。`,
  };
  const result = validateNarrativeAgainstPacket(invalid, packet, "first");

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.includes("invented-reference")));
});

test("does not mistake ordinary machine-readable status words for technical citations", () => {
  const output = {
    ...richOutput(),
    narrative: `${richOutput().narrative}\n当前仍是 pending_validation，并遵守 not_auto_rectified 边界。`,
  } satisfies RectificationNarrativeModelOutput;

  assert.deepEqual(
    validateNarrativeAgainstPacket(output, syntheticTechnicalPacket(), "first"),
    { valid: true, issues: [] },
  );
});

test("rejects a date confirmation question without structured follow-up state", () => {
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const invalid = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: "这个10月是2020年10月吗？",
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(invalid, syntheticTechnicalPacket(), "intermediate");

  assert.equal(result.valid, false);
  assert.ok(result.issues.includes("date confirmation prompt lacks structured proposedDate"));
});

test("retries when an affirmative answer receives the same resolved date question", async () => {
  const evidenceId = "11111111-1111-4111-8111-111111111111";
  const repeatedPrompt = "这个10月是2020年10月吗？";
  const followUp = {
    kind: "event_date" as const,
    evidenceId,
    answerMode: "yes_no" as const,
    proposedDate: { value: "2020-10", precision: "month" as const },
  };
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const repeated = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: repeatedPrompt,
      followUp,
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    context: {
      latestUserText: "是的",
      previousEvidencePrompt: repeatedPrompt,
      previousFollowUp: followUp,
    },
    generator: generator([repeated, output]),
  });

  assert.equal(result.attempts, 2);
  assert.notEqual(result.output.evidenceRequest?.prompt, repeatedPrompt);
});

test("rejects a follow-up that still targets evidence completed by an affirmative answer", () => {
  const evidenceId = "11111111-1111-4111-8111-111111111111";
  const previousFollowUp = {
    kind: "event_date" as const,
    evidenceId,
    answerMode: "yes_no" as const,
    proposedDate: { value: "2020-10", precision: "month" as const },
  };
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const invalid = {
    ...output,
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: "这段实习结束后，下一份工作是什么时候开始的？",
      followUp: {
        kind: "event_detail" as const,
        evidenceId,
        answerMode: "free_text" as const,
        proposedDate: null,
      },
    },
  } satisfies RectificationNarrativeModelOutput;
  const result = validateNarrativeAgainstPacket(
    invalid,
    syntheticTechnicalPacket(),
    "intermediate",
    { latestUserText: "是的", previousFollowUp },
  );

  assert.equal(result.valid, false);
  assert.ok(result.issues.includes("resolved follow-up still targets completed evidence"));
});

test("allows natural discussion of an event after it has contributed to scoring", () => {
  const evidenceId = "11111111-1111-4111-8111-111111111111";
  const packet: RectificationTechnicalPacket = {
    ...syntheticTechnicalPacket(),
    scoredHistoricalEvidence: [{
      evidenceId,
      domain: "career",
      candidateTime: "05:20",
      score: 3.5,
      ruleRefs: ["vim-md-career"],
    }],
  };
  const output = richOutput();
  assert.ok(output.evidenceRequest);
  const conversational = {
    ...output,
    narrative: "我理解，这次离开不只是换工作。你当时为什么辞职，是主动还是被动，对生活有什么影响？",
    evidenceRequest: {
      ...output.evidenceRequest,
      prompt: "你当时为什么辞职，是主动还是被动，对生活有什么影响？",
      followUp: {
        kind: "event_detail" as const,
        evidenceId,
        answerMode: "free_text" as const,
        proposedDate: null,
      },
    },
  } satisfies RectificationNarrativeModelOutput;

  assert.deepEqual(validateNarrativeAgainstPacket(conversational, packet, "intermediate"), {
    valid: true,
    issues: [],
  });
});

test("retries a grounded validation failure once with a compact packet", async () => {
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
  assert.ok((prompts[0]?.length ?? Number.POSITIVE_INFINITY) < 5_000);
  assert.equal(prompts.some((prompt) => prompt.includes("scoredHistoricalEvidence")), false);
  assert.equal(prompts.some((prompt) => prompt.includes("referenceIds")), false);
  assert.equal(prompts.some((prompt) => prompt.includes("candidateWeights")), false);
  assert.equal(prompts.some((prompt) => prompt.includes("private-partition")), false);
});

test("gives each validation attempt a fresh bounded deadline", async () => {
  const signals: Array<AbortSignal | undefined> = [];
  const attempts: Array<1 | 2 | undefined> = [];
  const invalid = { ...richOutput(), representativeTime: "06:45" };
  const result = await generateRectificationNarrative({
    phase: "first",
    packet: syntheticTechnicalPacket(),
    generator: {
      modelId: "test-model",
      async generate(_prompt, options) {
        signals.push(options?.signal);
        attempts.push(options?.attempt);
        return { text: JSON.stringify(signals.length === 1 ? invalid : richOutput()) };
      },
    },
  });

  assert.equal(result.fallbackUsed, false);
  assert.equal(signals.length, 2);
  assert.ok(signals[0] instanceof AbortSignal);
  assert.ok(signals[1] instanceof AbortSignal);
  assert.notEqual(signals[0], signals[1]);
  assert.deepEqual(attempts, [1, 2]);
});

test("accepts lightweight model-authored output and injects packet facts on the server", async () => {
  const packet = syntheticTechnicalPacket();
  const result = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([{
      narrative: "先从一件你印象最深、时间也比较明确的人生转折说起吧。",
      evidenceRequest: {
        datePrecision: "year_accepted",
        prompt: "那件事大约发生在哪一年？",
      },
    }]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.output.candidateStatus, packet.candidate.status);
  assert.equal(result.output.representativeTime, packet.candidate.representativeTime);
  assert.deepEqual(result.output.stableLayers, ["D1"]);
  assert.deepEqual(result.output.sensitiveLayers, ["D9", "D10"]);
  assert.deepEqual(result.output.referenceIds, []);
  assert.deepEqual(result.output.domainReasons, packet.suggestedDomains);
  assert.deepEqual(result.output.evidenceRequest?.domains, ["relationship", "career"]);
});

test("replaces legacy model-selected evidence domains instead of rejecting the answer", async () => {
  const packet = syntheticTechnicalPacket();
  const output = richOutput();
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet,
    generator: generator([{
      ...output,
      narrative: `${output.narrative}\n${output.evidenceRequest?.prompt ?? ""}`,
      evidenceRequest: {
        ...output.evidenceRequest,
        domains: ["finance"],
      },
    }]),
  });

  assert.equal(result.attempts, 1);
  assert.deepEqual(result.output.evidenceRequest?.domains, ["relationship", "career"]);
});

test("keeps authored prose but drops follow-up state when no grounded routing domain exists", async () => {
  const packet = { ...syntheticTechnicalPacket(), suggestedDomains: [] };
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet,
    generator: generator([{
      narrative: "这段经历已经记下。你愿意的话，可以继续讲当时发生了什么。",
      evidenceRequest: {
        domains: ["career"],
        datePrecision: "month_preferred",
        prompt: "当时发生了什么？",
        followUp: { kind: "new_event", evidenceId: null },
      },
    }]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.output.evidenceRequest, null);
  assert.match(result.narrative, /继续讲/);
});

test("uses a fresh second provider request after the first attempt times out", async () => {
  let calls = 0;
  const signals: Array<AbortSignal | undefined> = [];
  const result = await generateRectificationNarrative({
    phase: "first",
    packet: syntheticTechnicalPacket(),
    generator: {
      modelId: "pro-model",
      async generate(_prompt, options) {
        calls += 1;
        signals.push(options?.signal);
        if (options?.attempt === 1) {
          throw new DOMException("timed out", "TimeoutError");
        }
        return {
          text: JSON.stringify(richOutput()),
          modelId: "flash-model",
        };
      },
    },
  });

  assert.equal(calls, 2);
  assert.equal(result.attempts, 2);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.validationReceipt.modelId, "flash-model");
  assert.equal(result.validationReceipt.retryCount, 1);
  assert.ok(signals[0] instanceof AbortSignal);
  assert.ok(signals[1] instanceof AbortSignal);
  assert.notEqual(signals[0], signals[1]);
});

test("retries when a final narrative asks for more evidence", async () => {
  const invalid = richOutput();
  const valid = {
    ...richOutput(),
    narrative: "当前证据只能支持候选范围，本次不再要求继续提供人生事件。",
    evidenceRequest: null,
  } satisfies RectificationNarrativeModelOutput;
  const result = await generateRectificationNarrative({
    phase: "final",
    packet: syntheticTechnicalPacket(),
    generator: generator([invalid, valid]),
  });

  assert.equal(result.attempts, 2);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.output.evidenceRequest, null);
});

test("does not force a retry when the Agent naturally discusses a scored event", async () => {
  const evidenceId = "00000000-0000-4000-8000-000000000709";
  const packet = {
    ...syntheticTechnicalPacket(),
    scoredHistoricalEvidence: [{
      evidenceId,
      domain: "education" as const,
      candidateTime: "05:20",
      score: 8,
      ruleRefs: ["synthetic-education-rule"],
    }],
  };
  const output = {
    ...richOutput(),
    narrative: "我理解，这几个月的学业压力不只是结果，也影响了你当时的选择。",
    evidenceRequest: null,
  };
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet,
    context: {
      eventLedger: [{
        id: evidenceId,
        rawText: "1972年12月因为学业压力正式退学",
        dateLabel: "1972-12",
        summary: "因为学业压力正式退学",
        domain: "education",
        extractionStatus: "clear",
        active: true,
        correctsEvidenceIds: [],
      }],
    },
    generator: generator([output]),
  });

  assert.equal(result.attempts, 1);
  assert.equal(result.fallbackUsed, false);
  assert.equal(result.output.evidenceRequest, null);
  assert.equal(result.narrative, output.narrative);
});

test("records first-turn generation timeouts separately from schema failures", async () => {
  const warnings: string[] = [];
  const originalWarn = console.warn;
  console.warn = (...values: unknown[]) => warnings.push(values.map(String).join(" "));
  let result: Awaited<ReturnType<typeof generateRectificationNarrative>>;
  try {
    result = await generateRectificationNarrative({
      phase: "first",
      packet: syntheticTechnicalPacket(),
      generator: {
        modelId: "test-model",
        async generate() { throw new DOMException("timed out", "TimeoutError"); },
      },
    });
  } finally {
    console.warn = originalWarn;
  }

  assert.equal(result.fallbackUsed, true);
  assert.match(warnings.at(-1) ?? "", /"issueCodes":\["timeout"\]/);
});

test("falls back safely when the first-turn model output is invalid", async () => {
  const packet = syntheticTechnicalPacket();
  const invalid = { ...richOutput(), sensitiveLayers: ["D60"] };
  const result = await generateRectificationNarrative({
    phase: "first",
    packet,
    generator: generator([invalid, invalid]),
  });
  assert.equal(result.fallbackUsed, true);
  assert.doesNotMatch(result.narrative, /D60/);
});

test("falls back safely when an intermediate narrative is invalid", async () => {
  const inventedReference = `invented-${"x".repeat(500)}`;
  const invalid = {
    ...richOutput(),
    narrative: `${richOutput().narrative}\n另见【${inventedReference}】。`,
  };
  const result = await generateRectificationNarrative({
    phase: "intermediate",
    packet: syntheticTechnicalPacket(),
    generator: generator([invalid, invalid]),
  });
  assert.equal(result.fallbackUsed, true);
  assert.doesNotMatch(result.narrative, /invented-/);
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
