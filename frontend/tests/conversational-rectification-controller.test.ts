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
  ConversationalRectificationTurn,
} from "../src/lib/conversational-rectification/contracts.ts";

const caseId = "00000000-0000-4000-8000-000000000811";
const otherCaseId = "00000000-0000-4000-8000-000000000819";
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
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
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
    draft: "",
    selectedDomain: null,
    pending: false,
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
    draft: "",
    selectedDomain: null,
    pending: false,
    error: "",
  });

  request.reject(new Error("案例 A 已离线"));
  await rejected;
  assert.deepEqual(controller.getSnapshot(), {
    turn: null,
    draft: "",
    selectedDomain: null,
    pending: false,
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
