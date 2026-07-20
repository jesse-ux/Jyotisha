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
