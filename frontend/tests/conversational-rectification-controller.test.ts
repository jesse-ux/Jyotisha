import assert from "node:assert/strict";
import test from "node:test";
import {
  createConversationalRectificationController,
} from "../src/hooks/use-conversational-rectification.ts";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
} from "../src/lib/conversational-rectification/client.ts";
import type {
  ConversationalRectificationCommand,
  ConversationalRectificationResponse,
  ConversationalRectificationTurn,
} from "../src/lib/conversational-rectification/contracts.ts";

const caseId = "00000000-0000-4000-8000-000000000811";
const otherCaseId = "00000000-0000-4000-8000-000000000819";
const evidenceId = "00000000-0000-4000-8000-000000000818";
const actionIds = [
  "00000000-0000-4000-8000-000000000812",
  "00000000-0000-4000-8000-000000000813",
  "00000000-0000-4000-8000-000000000814",
  "00000000-0000-4000-8000-000000000815",
];

function activeTurn(turnVersion = 2): ConversationalRectificationTurn {
  return {
    caseId,
    journeyProtocol: "conversational-evidence-v3",
    status: "active",
    turnVersion,
    narrative: "候选仍需历史事件验证。",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:18",
      rangeStart: "05:10",
      rangeEnd: "05:26",
    },
    technicalReceipt: {
      calculationVersion: "rectification-technical-v1",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9", "D10"],
      candidateDifferenceRefs: ["consult-d9", "consult-d10"],
    },
    evidenceRequest: {
      domains: ["relationship", "career"],
      datePrecision: "month_preferred",
      freeTextAllowed: true,
    },
    evidenceRecap: [],
    actions: ["answer", "pause", "abandon"],
    pendingConsultationQuestion: null,
  };
}

function correctableTurn(turnVersion = 2): ConversationalRectificationTurn {
  return {
    ...activeTurn(turnVersion),
    evidenceRecap: [{
      id: evidenceId,
      summary: "开始第一份长期工作",
      dateLabel: "2021-07",
      isCorrection: false,
    }],
  };
}

function turnWithMessageHistory(turnVersion = 3): ConversationalRectificationResponse {
  return {
    ...activeTurn(turnVersion),
    narrative: "你提到第一份工作从数据分析开始。下一步想核对一次明确的职业转折。",
    messageHistory: [
      {
        turnVersion: 1,
        userMessage: null,
        narrative: "我们先从一件时间明确的经历开始。",
      },
      {
        turnVersion: 2,
        userMessage: "2017 年 7 月入职第一家公司，从事数据分析。",
        narrative: "这段职业起点已经记下。你当时为什么选择数据分析？",
      },
      {
        turnVersion: 3,
        userMessage: "专业相关，也觉得数据工作更适合我。",
        narrative: "你提到第一份工作从数据分析开始。下一步想核对一次明确的职业转折。",
      },
    ],
  };
}

function idFactory() {
  const ids = [...actionIds];
  return () => ids.shift() ?? assert.fail("unexpected action id allocation");
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

test("controller admits only one in-flight mutation and clears text only after success", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const pendingChanges: boolean[] = [];
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    onPendingChange: (pending) => pendingChanges.push(pending),
    send: async (command) => {
      commands.push(command);
      return request;
    },
  });
  controller.setDraft("2021 年 7 月开始第一份工作");

  const answer = controller.answer("career");
  const duplicate = controller.answer("career");
  const pause = controller.pause();

  assert.equal(controller.getSnapshot().pending, true);
  assert.equal(controller.getSnapshot().draft, "2021 年 7 月开始第一份工作");
  assert.equal(commands.length, 1);
  resolveRequest?.(activeTurn(3));
  await Promise.all([answer, duplicate, pause]);

  assert.equal(commands.length, 1);
  assert.equal(controller.getSnapshot().pending, false);
  assert.equal(controller.getSnapshot().draft, "");
  assert.equal(controller.getSnapshot().turn?.turnVersion, 3);
  assert.deepEqual(pendingChanges, [true, false]);
});

test("controller publishes streamed Agent text while the durable rectification turn is pending", async () => {
  const request = deferred<ConversationalRectificationResponse>();
  let emit: ((text: string) => void) | undefined;
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (_command, options) => {
      emit = options?.onNarrativeDelta;
      return request.promise;
    },
  });
  controller.setDraft("2024 年 8 月结束一段重要感情");

  const answer = controller.answer("relationship");
  emit?.("已记录关系事件，");
  emit?.("接下来核对开始时间。");

  assert.equal(controller.getSnapshot().pending, true);
  assert.equal(controller.getSnapshot().streamingAssistantText, "已记录关系事件，接下来核对开始时间。");

  request.resolve({
    ...activeTurn(3),
    narrative: "已记录关系事件，接下来核对开始时间。",
  });
  await answer;

  assert.equal(controller.getSnapshot().pending, false);
  assert.equal(controller.getSnapshot().streamingAssistantText, "");
  assert.equal(controller.getSnapshot().messages?.at(-1)?.text, "已记录关系事件，接下来核对开始时间。");
});

test("controller retains alternating user and Agent messages after each answer", async () => {
  const initial = activeTurn();
  const controller = createConversationalRectificationController({
    initialTurn: initial,
    createActionId: idFactory(),
    send: async () => ({
      ...activeTurn(3),
      narrative: "你提到 2021 年 7 月开始第一份工作，这次职业起点已经记下。接下来想核对一次搬迁。",
    }),
  });

  controller.setDraft("2021 年 7 月开始第一份工作");
  await controller.answer("career");

  assert.deepEqual(controller.getSnapshot().messages?.map(({ role, text }) => ({ role, text })), [
    { role: "assistant", text: initial.narrative },
    { role: "user", text: "2021 年 7 月开始第一份工作" },
    { role: "assistant", text: "你提到 2021 年 7 月开始第一份工作，这次职业起点已经记下。接下来想核对一次搬迁。" },
  ]);
});

test("controller restores the real user and Agent history without synthesizing recap templates", () => {
  const controller = createConversationalRectificationController({
    initialTurn: turnWithMessageHistory(),
  });

  const messages = controller.getSnapshot().messages?.map(({ role, text }) => ({ role, text }));
  assert.deepEqual(messages, [
    { role: "assistant", text: "我们先从一件时间明确的经历开始。" },
    { role: "user", text: "2017 年 7 月入职第一家公司，从事数据分析。" },
    { role: "assistant", text: "这段职业起点已经记下。你当时为什么选择数据分析？" },
    { role: "user", text: "专业相关，也觉得数据工作更适合我。" },
    { role: "assistant", text: "你提到第一份工作从数据分析开始。下一步想核对一次明确的职业转折。" },
  ]);
  assert.doesNotMatch(messages?.map(({ text }) => text).join("\n") ?? "", /已记录这段经历/);
});

test("legacy responses without message history show only the real latest Agent narrative", () => {
  const legacy = {
    ...correctableTurn(3),
    narrative: "你刚才补充的职业经历还缺离职原因，我先继续问这一件事。",
  };
  const controller = createConversationalRectificationController({ initialTurn: legacy });

  assert.deepEqual(controller.getSnapshot().messages?.map(({ role, text }) => ({ role, text })), [
    { role: "assistant", text: legacy.narrative },
  ]);
});

test("controller preserves the exact draft and stable action id across failures", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      throw new ConversationalRectificationRequestError(
        502,
        null,
        CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
      );
    },
  });
  controller.setDraft("2021 年 7 月毕业，具体日期不确定");

  await assert.rejects(controller.answer("education"));
  await assert.rejects(controller.answer("education"));

  const snapshot = controller.getSnapshot();
  assert.equal(snapshot.draft, "2021 年 7 月毕业，具体日期不确定");
  assert.equal(snapshot.error, CONVERSATIONAL_RECTIFICATION_UNAVAILABLE);
  assert.equal(commands.length, 2);
  assert.equal(commands[0]?.actionId, commands[1]?.actionId);
});

test("a correction target is explicit in the command identity, survives failure, and clears on success", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  let fail = true;
  const controller = createConversationalRectificationController({
    initialTurn: correctableTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      if (fail) throw new Error("offline");
      return { ...correctableTurn(3), evidenceRecap: [] };
    },
  });

  controller.beginEvidenceCorrection(evidenceId);
  assert.equal(controller.getSnapshot().correctionTarget?.id, evidenceId);
  assert.equal(
    controller.getSnapshot().draft,
    "",
    "the old summary/date must stay outside the submitted correction text",
  );
  controller.setDraft("更正：其实是 2020 年 11 月离职");
  await assert.rejects(controller.answer());
  assert.equal(controller.getSnapshot().correctionTarget?.id, evidenceId);
  assert.equal(commands[0]?.type, "answer");
  assert.equal(commands[0]?.type === "answer" ? commands[0].correctsEvidenceId : null, evidenceId);

  fail = false;
  await controller.answer();
  assert.equal(commands[0]?.actionId, commands[1]?.actionId);
  assert.equal(controller.getSnapshot().correctionTarget, null);
  assert.equal(controller.getSnapshot().draft, "");
});

test("canceling correction removes the target and changing targets changes the replay identity", async () => {
  const secondEvidenceId = "00000000-0000-4000-8000-000000000817";
  const commands: ConversationalRectificationCommand[] = [];
  const initial = {
    ...correctableTurn(),
    evidenceRecap: [
      ...correctableTurn().evidenceRecap,
      { id: secondEvidenceId, summary: "搬到另一座城市", dateLabel: "2022-03" },
    ],
  } satisfies ConversationalRectificationTurn;
  const controller = createConversationalRectificationController({
    initialTurn: initial,
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      throw new Error("offline");
    },
  });

  controller.beginEvidenceCorrection(evidenceId);
  controller.setDraft("更正：其实是 2020 年 11 月离职");
  await assert.rejects(controller.answer());
  controller.beginEvidenceCorrection(secondEvidenceId);
  controller.setDraft("更正：其实是 2022 年 3 月搬家");
  await assert.rejects(controller.answer());
  assert.notEqual(commands[0]?.actionId, commands[1]?.actionId);
  controller.cancelEvidenceCorrection();
  assert.equal(controller.getSnapshot().correctionTarget, null);
  assert.equal(controller.getSnapshot().draft, "");
});

test("a stale answer resumes the latest turn and returns recovered state without clearing text", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const recovered = activeTurn(5);
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      if (command.type === "answer") {
        throw new ConversationalRectificationRequestError(409, "stale_turn", "请加载最新进度后再试。");
      }
      assert.equal(command.type, "resume");
      return recovered;
    },
  });
  controller.setDraft("2022 年 3 月搬到另一座城市");
  controller.selectDomain("relocation");

  const result = await controller.answer();

  assert.deepEqual(result, recovered);
  assert.deepEqual(commands.map((command) => command.type), ["answer", "resume"]);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 5);
  assert.equal(controller.getSnapshot().draft, "2022 年 3 月搬到另一座城市");
  assert.equal(controller.getSnapshot().selectedDomain, null);
  assert.equal(controller.getSnapshot().error, "");
});

test("a stale recovery retains the selected domain only while the recovered turn still requests it", async () => {
  const recovered = activeTurn(5);
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async (command) => {
      if (command.type === "answer") {
        throw new ConversationalRectificationRequestError(409, "stale_turn", "请加载最新进度后再试。");
      }
      return recovered;
    },
  });
  controller.setDraft("2021 年 7 月开始第一份工作");
  controller.selectDomain("career");

  await controller.answer();

  assert.equal(controller.getSnapshot().draft, "2021 年 7 月开始第一份工作");
  assert.equal(controller.getSnapshot().selectedDomain, "career");
});

test("stale recovery retains a correction only when the latest effective recap still contains it", async () => {
  const recoveryCases: Array<[ConversationalRectificationTurn, string | null]> = [
    [correctableTurn(5), evidenceId],
    [{ ...correctableTurn(5), evidenceRecap: [] }, null],
  ];
  for (const [recovered, expected] of recoveryCases) {
    const controller = createConversationalRectificationController({
      initialTurn: correctableTurn(2),
      createActionId: idFactory(),
      send: async (command) => {
        if (command.type === "answer") {
          throw new ConversationalRectificationRequestError(409, "stale_turn", "请加载最新进度后再试。");
        }
        return recovered;
      },
    });
    controller.beginEvidenceCorrection(evidenceId);
    controller.setDraft("更正：其实是 2020 年 11 月离职");

    await controller.answer();

    assert.equal(controller.getSnapshot().correctionTarget?.id ?? null, expected);
    assert.equal(controller.getSnapshot().draft, "更正：其实是 2020 年 11 月离职");
  }
});

test("a changed payload receives a different action id after a failed send", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      throw new Error("offline");
    },
  });

  controller.setDraft("2021 年 7 月毕业");
  await assert.rejects(controller.answer("education"));
  controller.setDraft("2022 年 3 月搬家");
  await assert.rejects(controller.answer("relocation"));

  assert.notEqual(commands[0]?.actionId, commands[1]?.actionId);
});

test("a successful turn stays successful when the consumer onTurn callback throws", async () => {
  const next = activeTurn(3);
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async () => next,
    onTurn: () => {
      throw new Error("consumer render side effect failed");
    },
  });
  controller.setDraft("2021 年 7 月开始第一份工作");

  const result = await controller.answer("career");

  assert.deepEqual(result, next);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 3);
  assert.equal(controller.getSnapshot().draft, "");
  assert.equal(controller.getSnapshot().error, "");
});

test("external initial turns adopt only newer same-case state", () => {
  const controller = createConversationalRectificationController({ initialTurn: null });

  controller.synchronizeInitialTurn(activeTurn(4));
  assert.equal(controller.getSnapshot().turn?.turnVersion, 4);

  controller.setDraft("仍在填写的经历");
  controller.selectDomain("career");
  controller.synchronizeInitialTurn(activeTurn(3));
  assert.equal(controller.getSnapshot().turn?.turnVersion, 4);
  assert.equal(controller.getSnapshot().draft, "仍在填写的经历");
  assert.equal(controller.getSnapshot().selectedDomain, "career");

  const newer = {
    ...activeTurn(5),
    evidenceRequest: {
      domains: ["education", "relocation"],
      datePrecision: "month_preferred",
      freeTextAllowed: true,
    },
  } satisfies ConversationalRectificationTurn;
  controller.synchronizeInitialTurn(newer);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 5);
  assert.equal(controller.getSnapshot().draft, "仍在填写的经历");
  assert.equal(controller.getSnapshot().selectedDomain, null);
});

test("switching cases synchronizes immediately and an old in-flight response cannot overwrite it", async () => {
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async () => request,
  });
  controller.setDraft("旧案例输入");
  const pending = controller.answer("career");
  const newCase = { ...activeTurn(1), caseId: otherCaseId };

  controller.synchronizeInitialTurn(newCase);

  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().draft, "");
  resolveRequest?.(activeTurn(9));
  await pending;

  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 1);
  assert.equal(controller.getSnapshot().pending, false);
});

test("a case switch detaches the old mutation so the new case can mutate independently", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const caseARequest = deferred<ConversationalRectificationTurn>();
  const caseBRequest = deferred<ConversationalRectificationTurn>();
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      return command.type !== "start" && command.caseId === otherCaseId
        ? caseBRequest.promise
        : caseARequest.promise;
    },
  });
  controller.setDraft("案例 A 的在途输入");
  const caseAPending = controller.answer("career");
  const caseARejected = assert.rejects(caseAPending, /案例 A 普通失败/);

  const caseBTurn = { ...activeTurn(1), caseId: otherCaseId };
  controller.synchronizeInitialTurn(caseBTurn);
  assert.deepEqual(controller.getSnapshot(), {
    turn: caseBTurn,
    messages: [{
      role: "assistant",
      text: caseBTurn.narrative,
      renderKey: "assistant-1",
    }],
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    streamingAssistantText: "",
    error: "",
  });

  controller.setDraft("案例 B 自己的输入");
  const caseBPending = controller.answer("career");
  assert.notEqual(caseBPending, caseAPending);
  assert.deepEqual(commands.map((command) => (
    command.type === "start" ? "start" : `${command.caseId}:${command.type}`
  )), [`${caseId}:answer`, `${otherCaseId}:answer`]);
  assert.equal(controller.getSnapshot().pending, true);

  caseARequest.reject(new Error("案例 A 普通失败"));
  await caseARejected;
  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().draft, "案例 B 自己的输入");
  assert.equal(controller.getSnapshot().pending, true);
  assert.equal(controller.getSnapshot().error, "");

  caseBRequest.resolve({ ...activeTurn(2), caseId: otherCaseId });
  await caseBPending;
  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 2);
  assert.equal(controller.getSnapshot().draft, "");
  assert.equal(controller.getSnapshot().pending, false);
});

test("synchronizing to no case detaches an ordinary failure without publishing its error", async () => {
  const request = deferred<ConversationalRectificationTurn>();
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async () => request.promise,
  });
  controller.setDraft("即将离开的案例输入");
  const pending = controller.answer("career");
  const rejected = assert.rejects(pending, /案例 A 已离线/);

  controller.synchronizeInitialTurn(null);
  assert.deepEqual(controller.getSnapshot(), {
    turn: null,
    messages: [],
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    streamingAssistantText: "",
    error: "",
  });

  request.reject(new Error("案例 A 已离线"));
  await rejected;
  assert.deepEqual(controller.getSnapshot(), {
    turn: null,
    messages: [],
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    streamingAssistantText: "",
    error: "",
  });
});

test("a stale recovery failure from the old case cannot patch or unlock the new case", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const recoveryStarted = deferred<void>();
  const recovery = deferred<ConversationalRectificationTurn>();
  const caseBRequest = deferred<ConversationalRectificationTurn>();
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      if (command.type === "answer" && command.caseId === caseId) {
        throw new ConversationalRectificationRequestError(
          409,
          "stale_turn",
          "请加载最新进度后再试。",
        );
      }
      if (command.type === "resume" && command.caseId === caseId) {
        recoveryStarted.resolve();
        return recovery.promise;
      }
      return caseBRequest.promise;
    },
  });
  controller.setDraft("案例 A 的陈旧输入");
  const caseAPending = controller.answer("career");
  const caseARejected = assert.rejects(caseAPending, /恢复请求失败/);
  await recoveryStarted.promise;

  const caseBTurn = { ...activeTurn(1), caseId: otherCaseId };
  controller.synchronizeInitialTurn(caseBTurn);
  const caseBPending = controller.pause();
  assert.deepEqual(commands.map((command) => command.type), ["answer", "resume", "pause"]);
  assert.equal(controller.getSnapshot().pending, true);

  recovery.reject(new Error("恢复请求失败"));
  await caseARejected;
  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().pending, true);
  assert.equal(controller.getSnapshot().error, "");

  caseBRequest.resolve({
    ...activeTurn(2),
    caseId: otherCaseId,
    status: "paused",
    actions: ["answer", "abandon"],
  });
  await caseBPending;
  assert.equal(controller.getSnapshot().turn?.caseId, otherCaseId);
  assert.equal(controller.getSnapshot().turn?.status, "paused");
  assert.equal(controller.getSnapshot().pending, false);
  assert.equal(controller.getSnapshot().error, "");
});

test("a newer external same-case turn wins over an older in-flight response", async () => {
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async () => request,
  });
  controller.setDraft("在途输入");
  const pending = controller.answer("career");

  controller.synchronizeInitialTurn(activeTurn(5));
  resolveRequest?.(activeTurn(3));
  await pending;

  assert.equal(controller.getSnapshot().turn?.turnVersion, 5);
});

test("a newer synchronized response replaces local bubbles with its durable message history", () => {
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(1),
  });

  controller.synchronizeInitialTurn(turnWithMessageHistory(3));

  assert.deepEqual(controller.getSnapshot().messages?.map(({ role, text }) => ({ role, text })), [
    { role: "assistant", text: "我们先从一件时间明确的经历开始。" },
    { role: "user", text: "2017 年 7 月入职第一家公司，从事数据分析。" },
    { role: "assistant", text: "这段职业起点已经记下。你当时为什么选择数据分析？" },
    { role: "user", text: "专业相关，也觉得数据工作更适合我。" },
    { role: "assistant", text: "你提到第一份工作从数据分析开始。下一步想核对一次明确的职业转折。" },
  ]);
});

test("an external same-version turn is not replaced by a late response", async () => {
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(4),
    createActionId: idFactory(),
    send: async () => request,
  });
  controller.setDraft("在途输入");
  const pending = controller.answer("career");
  const external = { ...activeTurn(5), narrative: "外部已同步的最新轮次" };
  const lateResponse = { ...activeTurn(5), narrative: "较晚返回的旧请求" };

  controller.synchronizeInitialTurn(external);
  resolveRequest?.(lateResponse);
  await pending;

  assert.equal(controller.getSnapshot().turn?.narrative, "外部已同步的最新轮次");
});
