import assert from "node:assert/strict";
import test from "node:test";
import {
  BirthTimeGuideOutputError,
  fallbackQuestionCopy,
  guideQuestionVariants,
  parseEvidenceDraftOutput,
  parseGuideQuestionOutput,
  renderQuestionVariant,
} from "../src/lib/birth-time-guide-agent.ts";
import {
  bindDynamicQuestion,
  generateDynamicQuestionPrompt,
  parseDynamicQuestionOutput,
} from "../src/lib/birth-time-dynamic-question-validator.ts";
import { toPublicDynamicChoiceQuestion } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import type {
  CandidateDifferenceBuild,
  CandidateDifferencePacket,
} from "../src/lib/birth-time-dynamic-choice-internal.ts";
import { evidenceDomains, type QuestionSpec } from "../src/lib/birth-time-question-planner.ts";
import { draftEvidenceStructureTool, getBirthTimeGuideAgent } from "../src/mastra/index.ts";
import type { ResolvedLanguageModel } from "../src/mastra/model.ts";

function question(domain: QuestionSpec["domain"]): QuestionSpec {
  return {
    questionId: `baseline_${domain}_1`,
    phase: "baseline",
    domain,
    requestedPrecision: ["year", "month"],
    allowUnknown: true,
    purposeCode: `candidate_difference_${domain}`,
    plannerVersion: "candidate-difference-v1",
  };
}

const dynamicPacket: CandidateDifferencePacket = {
  caseId: "7299894c-10a8-4b45-91d1-339007282c50",
  scoringVersion: "birth-time-choice-scoring-v2",
  currentRange: { startTime: "04:00", endTime: "04:01" },
  opportunities: [{
    opportunityId: "career-window",
    dimensionCode: "career",
    neutralContext: "一次明显的工作变化",
    estimatedInformationGain: 0.7,
    candidatePartitionFingerprint: "career-partitions-v1",
    fallbackPrompt: "哪一个时间段更接近这次工作变化？",
    partitions: [
      { partitionId: "window-a", descriptor: "较早阶段", fallbackLabel: "2018—2020 年" },
      { partitionId: "window-b", descriptor: "较晚阶段", fallbackLabel: "2021—2023 年" },
    ],
  }],
  askedQuestionFingerprints: [],
  candidatePartitionFingerprints: [],
  recentRangeHistory: [{ startTime: "04:00", endTime: "04:01" }],
};

const differenceBuild: CandidateDifferenceBuild = {
  packet: dynamicPacket,
  candidateModel: { candidates: ["04:00", "04:01"], confidence: "private" },
  scoringPartitions: {
    "career-window": [
      {
        partitionId: "window-a",
        descriptor: "较早阶段",
        fallbackLabel: "2018—2020 年",
        candidateScores: { "04:00": 1, "04:01": 0 },
      },
      {
        partitionId: "window-b",
        descriptor: "较晚阶段",
        fallbackLabel: "2021—2023 年",
        candidateScores: { "04:00": 0, "04:01": 1 },
      },
    ],
  },
};

const validDynamicOutput = {
  kind: "question",
  opportunityId: "career-window",
  prompt: "哪一个时间段更接近这次工作变化？",
  options: [
    { partitionId: "window-a", label: "2018—2020 年" },
    { partitionId: "window-b", label: "2021—2023 年" },
  ],
} as const;

function deterministicIds() {
  const values = [
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000002",
    "00000000-0000-4000-8000-000000000003",
    "00000000-0000-4000-8000-000000000004",
    "00000000-0000-4000-8000-000000000005",
  ];
  let index = 0;
  return () => {
    const value = values[index];
    index += 1;
    if (value === undefined) throw new Error("test id supply exhausted");
    return value;
  };
}

test("dynamic prompt exposes only model-safe opportunity copy and optional unmatched context", () => {
  const prompt = JSON.parse(generateDynamicQuestionPrompt(dynamicPacket, "  更像发生在年末  "));

  assert.deepEqual(prompt, {
    task: "generate_dynamic_choice_question",
    opportunities: [{
      opportunityId: "career-window",
      dimensionCode: "career",
      neutralContext: "一次明显的工作变化",
      partitions: [
        { partitionId: "window-a", descriptor: "较早阶段", fallbackLabel: "2018—2020 年" },
        { partitionId: "window-b", descriptor: "较晚阶段", fallbackLabel: "2021—2023 年" },
      ],
    }],
    unmatchedNote: "更像发生在年末",
  });
  const serialized = JSON.stringify(prompt);
  for (const forbidden of [
    "candidateScores",
    "candidateModel",
    "estimatedInformationGain",
    "currentRange",
    "scoringVersion",
    "askedQuestionFingerprints",
    "candidatePartitionFingerprints",
    "recentRangeHistory",
    "04:00",
    "confidence",
  ]) {
    assert.equal(serialized.includes(forbidden), false, forbidden);
  }
});

test("dynamic output references exactly one server opportunity and each of its partitions once", () => {
  const parsed = parseDynamicQuestionOutput(validDynamicOutput, dynamicPacket);

  assert.equal(parsed.kind, "question");
  for (const unsafe of [
    { ...validDynamicOutput, opportunityId: "invented" },
    { ...validDynamicOutput, options: [{ partitionId: "invented", label: "某个时间" }] },
    { ...validDynamicOutput, options: [validDynamicOutput.options[0], validDynamicOutput.options[0]] },
    { ...validDynamicOutput, options: [validDynamicOutput.options[0]] },
    { ...validDynamicOutput, options: [...validDynamicOutput.options, { partitionId: "window-c", label: "其他" }] },
  ]) {
    assert.throws(
      () => parseDynamicQuestionOutput(unsafe, dynamicPacket),
      BirthTimeGuideOutputError,
    );
  }
});

test("dynamic copy rejects birth-time, confidence, support, control, and oversized claims", () => {
  const unsafeCopies = [
    { ...validDynamicOutput, prompt: "你是 04:00 出生的吗？" },
    { ...validDynamicOutput, prompt: "哪个答案能提高置信度？" },
    { ...validDynamicOutput, options: [{ partitionId: "window-a", label: "支持候选 A" }, validDynamicOutput.options[1]] },
    { ...validDynamicOutput, prompt: "选择后系统会结束评估吗？" },
    { ...validDynamicOutput, prompt: "字".repeat(121) },
    { ...validDynamicOutput, options: [{ partitionId: "window-a", label: "字".repeat(81) }, validDynamicOutput.options[1]] },
  ];

  for (const unsafe of unsafeCopies) {
    assert.throws(
      () => parseDynamicQuestionOutput(unsafe, dynamicPacket),
      BirthTimeGuideOutputError,
    );
  }
});

test("server binds private score vectors and adds two public special options", () => {
  const output = parseDynamicQuestionOutput(validDynamicOutput, dynamicPacket);
  if (output.kind !== "question") throw new Error("expected a test question");

  const internal = bindDynamicQuestion(output, differenceBuild, deterministicIds(), "agent");
  const publicQuestion = toPublicDynamicChoiceQuestion(internal);

  assert.deepEqual(internal.options[0]?.candidateScores, { "04:00": 1, "04:01": 0 });
  assert.deepEqual(publicQuestion.options.slice(-2).map((item) => item.label), [
    "不确定 / 不记得",
    "都不符合",
  ]);
  assert.equal(publicQuestion.options.some((item) => "partitionId" in item), false);
  assert.equal(JSON.stringify(publicQuestion).includes("04:00"), false);
});

test("server rejects repeated public semantics and repeated candidate partitions", () => {
  const output = parseDynamicQuestionOutput(validDynamicOutput, dynamicPacket);
  if (output.kind !== "question") throw new Error("expected a test question");
  const first = bindDynamicQuestion(output, differenceBuild, deterministicIds(), "agent");

  assert.throws(() => bindDynamicQuestion(output, {
    ...differenceBuild,
    packet: { ...dynamicPacket, askedQuestionFingerprints: [first.questionFingerprint] },
  }, deterministicIds(), "agent"), BirthTimeGuideOutputError);
  assert.throws(() => bindDynamicQuestion(output, {
    ...differenceBuild,
    packet: {
      ...dynamicPacket,
      candidatePartitionFingerprints: ["career-partitions-v1"],
    },
  }, deterministicIds(), "agent"), BirthTimeGuideOutputError);
});

test("draft parser fails closed when the model changes the server-selected domain", () => {
  assert.throws(
    () => parseEvidenceDraftOutput(
      { domain: "relationship", precision: "month", date: "2023-04" },
      { requiredDomain: "career", sourceMessage: "2023 年 4 月换了工作" },
    ),
    BirthTimeGuideOutputError,
  );
});

test("ambiguous dates remain incomplete instead of being invented", () => {
  const draft = parseEvidenceDraftOutput(
    { domain: "career", precision: null, date: null },
    { requiredDomain: "career", sourceMessage: "大概是前几年" },
  );

  assert.deepEqual(draft, {
    domain: "career",
    precision: null,
    date: null,
    needsReview: true,
  });
});

test("an ungrounded model date is discarded", () => {
  const draft = parseEvidenceDraftOutput(
    { domain: "career", precision: "month", date: "2023-04" },
    { requiredDomain: "career", sourceMessage: "记不清具体时间" },
  );

  assert.equal(draft.precision, null);
  assert.equal(draft.date, null);
  assert.equal(draft.needsReview, true);
});

test("precision and date mismatch remains a review-only draft", () => {
  const draft = parseEvidenceDraftOutput(
    { domain: "career", precision: "day", date: "2023-04" },
    { requiredDomain: "career", sourceMessage: "2023 年 4 月换了工作" },
  );

  assert.equal(draft.precision, "day");
  assert.equal(draft.date, "2023-04");
  assert.equal(draft.needsReview, true);
});

test("grounded dates can produce a complete review-only proposal", () => {
  const draft = parseEvidenceDraftOutput(
    { domain: "career", precision: "month", date: "2023-04" },
    { requiredDomain: "career", sourceMessage: "我在 2023 年 4 月换了工作" },
  );

  assert.deepEqual(draft, {
    domain: "career",
    precision: "month",
    date: "2023-04",
    needsReview: false,
  });
});

test("date grounding accepts ISO and year-only evidence but never adds an unstated day", () => {
  const iso = parseEvidenceDraftOutput(
    { domain: "career", precision: "month", date: "2023-04" },
    { requiredDomain: "career", sourceMessage: "工作变动发生于 2023-04" },
  );
  const year = parseEvidenceDraftOutput(
    { domain: "career", precision: "year", date: "2023" },
    { requiredDomain: "career", sourceMessage: "只记得是 2023 年" },
  );
  const inventedDay = parseEvidenceDraftOutput(
    { domain: "career", precision: "day", date: "2023-04-18" },
    { requiredDomain: "career", sourceMessage: "只记得 ２０２３ 年 ４ 月" },
  );

  assert.equal(iso.needsReview, false);
  assert.equal(year.needsReview, false);
  assert.equal(inventedDay.date, null);
  assert.equal(inventedDay.precision, null);
  assert.equal(inventedDay.needsReview, true);
});

test("date grounding accepts fullwidth Chinese month and explicit Chinese or ISO days", () => {
  const cases = [
    {
      output: { domain: "career", precision: "month", date: "2023-04" },
      message: "工作变化发生在 ２０２３ 年 ４ 月",
    },
    {
      output: { domain: "career", precision: "day", date: "2023-04-18" },
      message: "工作变化发生在 2023 年 4 月 18 号",
    },
    {
      output: { domain: "career", precision: "day", date: "2023-04-18" },
      message: "工作变化发生在 2023-04-18",
    },
  ] as const;
  for (const value of cases) {
    const draft = parseEvidenceDraftOutput(value.output, {
      requiredDomain: "career",
      sourceMessage: value.message,
    });
    assert.equal(draft.needsReview, false, value.message);
  }
});

test("date grounding rejects substrings, partial ISO tokens, and scattered numbers", () => {
  const unsafeMessages = [
    "订单号20230",
    "编号 2023-04-X",
    "2023 年有变化，另外 4 月去了旅行",
    "账号 1202304",
  ] as const;

  for (const sourceMessage of unsafeMessages) {
    const draft = parseEvidenceDraftOutput(
      { domain: "career", precision: "month", date: "2023-04" },
      { requiredDomain: "career", sourceMessage },
    );
    assert.equal(draft.precision, null, sourceMessage);
    assert.equal(draft.date, null, sourceMessage);
    assert.equal(draft.needsReview, true, sourceMessage);
  }
});

test("year-only grounding requires a complete year token or explicit year semantics", () => {
  for (const sourceMessage of ["2023", " ２０２３ ", "大约在 2023 年"] as const) {
    const draft = parseEvidenceDraftOutput(
      { domain: "career", precision: "year", date: "2023" },
      { requiredDomain: "career", sourceMessage },
    );
    assert.equal(draft.needsReview, false, sourceMessage);
  }
  for (const sourceMessage of ["订单20230", "编号A2023B"] as const) {
    const draft = parseEvidenceDraftOutput(
      { domain: "career", precision: "year", date: "2023" },
      { requiredDomain: "career", sourceMessage },
    );
    assert.equal(draft.date, null, sourceMessage);
  }
});

test("server renders every approved variant from its QuestionSpec domain and precision", () => {
  const semanticMarkers = {
    education: /升学|转学|学习方向/,
    relocation: /搬家|离乡|居住地/,
    relationship: /关系进入|关系结束|关系.*转变/,
    career: /工作|职业方向|身份变化/,
    health_pressure: /健康压力|生活压力/,
  } as const;
  for (const domain of evidenceDomains) {
    for (const variant of guideQuestionVariants) {
      const copy = renderQuestionVariant(question(domain), variant);
      assert.equal((copy.match(/[？?]/g) ?? []).length, 1);
      assert.ok(copy.length <= 120);
      assert.match(copy, semanticMarkers[domain]);
      assert.doesNotMatch(copy, /哪一天|几号|具体日期|候选|支持|更符合|更接近|出生分钟/);
      for (const otherDomain of evidenceDomains.filter((item) => item !== domain)) {
        assert.doesNotMatch(copy, semanticMarkers[otherDomain]);
      }
    }
    assert.equal(fallbackQuestionCopy(question(domain)), renderQuestionVariant(question(domain), "direct"));
  }
});

test("question parser accepts only a finite variant and binds it to the server QuestionSpec", () => {
  const parsed = parseGuideQuestionOutput({ variant: "gentle" }, question("career"));
  assert.equal(parsed, renderQuestionVariant(question("career"), "gentle"));
  for (const unsafe of [
    { variant: "relationship" },
    { variant: "direct", domain: "relationship" },
    { question: "Which relationship changed?" },
    { question: "具体是哪一天？" },
    { question: "04：00 这个候选时间更符合吗？" },
    { variant: "direct", question: "越权覆盖" },
  ]) {
    assert.throws(() => parseGuideQuestionOutput(unsafe, question("career")), BirthTimeGuideOutputError);
  }
});

test("model output schemas reject extra fields", () => {
  assert.throws(() => parseEvidenceDraftOutput(
    { domain: "career", precision: null, date: null, confidence: "high" },
    { requiredDomain: "career", sourceMessage: "记不清" },
  ));
  assert.throws(() => parseGuideQuestionOutput({ variant: "direct", score: 9 }, question("career")));
});

test("birth-time guide registers only the review-only structure tool", async () => {
  const model: ResolvedLanguageModel = {
    id: "guide-test-model",
    label: "Guide test",
    description: "",
    creditCost: 1,
    isDefault: false,
    mode: "openai",
    model: "openai/gpt-5-mini",
  };
  const tools = await getBirthTimeGuideAgent(model).listTools();

  assert.deepEqual(Object.keys(tools), ["draftEvidenceStructureTool"]);
  assert.equal(draftEvidenceStructureTool.id, "draft-evidence-structure");
});
