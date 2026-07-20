import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  createBirthTimeConversationPostHandler,
  type BirthTimeConversationRouteService,
} from "../src/app/api/birth-time-conversation/route.ts";
import { ConversationalRectificationError } from "../src/lib/conversational-rectification/errors.ts";

const userId = "00000000-0000-4000-8000-000000000711";
const actionId = "00000000-0000-4000-8000-000000000712";
const caseId = "00000000-0000-4000-8000-000000000713";
const requestId = "00000000-0000-4000-8000-000000000714";

const turn = {
  caseId,
  journeyProtocol: "conversational-evidence-v3" as const,
  status: "active" as const,
  turnVersion: 2,
  narrative: "这是经过服务端验证的合成校正解释。",
  candidate: {
    status: "pending_validation" as const,
    representativeTime: "05:20",
    rangeStart: "05:10",
    rangeEnd: "05:30",
  },
  technicalReceipt: {
    calculationVersion: "rectification-technical-v1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    candidateDifferenceRefs: ["consult-d9", "consult-d10"],
  },
  evidenceRequest: {
    domains: ["relationship" as const, "career" as const],
    datePrecision: "month_preferred" as const,
    freeTextAllowed: true as const,
  },
  evidenceRecap: [],
  actions: ["answer" as const, "pause" as const, "abandon" as const],
  pendingConsultationQuestion: null,
};

function request(body: unknown, events: string[]) {
  return {
    headers: new Headers({ "x-request-id": requestId }),
    async json() {
      events.push("body");
      return body;
    },
  } as Request;
}

function service(overrides: Partial<BirthTimeConversationRouteService> = {}): BirthTimeConversationRouteService {
  const response = async () => turn;
  return {
    start: response,
    resume: response,
    answer: response,
    pause: response,
    abandon: response,
    confirm: response,
    ...overrides,
  };
}

test("authentication happens before body parsing and unauthenticated requests create no privileged service", async () => {
  const events: string[] = [];
  let creates = 0;
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return null;
    },
    async createService() {
      creates += 1;
      return service();
    },
    createRequestId: () => requestId,
  });
  const response = await handler(request({ type: "start", actionId }, events));
  assert.equal(response.status, 401);
  assert.deepEqual(events, ["auth"]);
  assert.equal(creates, 0);
  assert.deepEqual(await response.json(), {
    code: "authentication_required",
    status: 401,
    error: "请先登录",
    message: "登录后才能继续生时校正。",
    retryable: false,
  });
});

test("strict invalid commands return 400 before admin, billing, or service construction", async () => {
  const events: string[] = [];
  let creates = 0;
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return { userId, context: null };
    },
    async createService() {
      creates += 1;
      return service();
    },
    createRequestId: () => requestId,
  });
  const response = await handler(request({ type: "start", actionId, price: 0 }, events));
  assert.equal(response.status, 400);
  assert.deepEqual(events, ["auth", "body"]);
  assert.equal(creates, 0);
  assert.equal((await response.json() as { code: string }).code, "invalid_command");
});

test("valid commands dispatch exactly one authenticated service method", async () => {
  const events: string[] = [];
  const calls: unknown[] = [];
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return { userId, context: { authenticated: true } };
    },
    async createService() {
      events.push("service");
      return service({
        async answer(receivedUserId, command) {
          calls.push([receivedUserId, command]);
          return turn;
        },
      });
    },
    createRequestId: () => requestId,
  });
  const command = { type: "answer", caseId, actionId, turnVersion: 1, answer: "2021年7月毕业" };
  const response = await handler(request(command, events));
  assert.equal(response.status, 200);
  assert.deepEqual(events, ["auth", "body", "service"]);
  assert.deepEqual(calls, [[userId, command]]);
  assert.deepEqual(await response.json(), turn);
});

test("known conflicts and unavailable failures use stable safe Chinese responses", async () => {
  for (const [failure, status, code] of [
    [new ConversationalRectificationError("stale_turn"), 409, "stale_turn"],
    [new ConversationalRectificationError("action_conflict"), 409, "action_conflict"],
    [new ConversationalRectificationError("service_unavailable"), 503, "service_unavailable"],
  ] as const) {
    const logs: unknown[] = [];
    const handler = createBirthTimeConversationPostHandler({
      async authenticate() { return { userId, context: null }; },
      async createService() {
        return service({ async resume() { throw failure; } });
      },
      createRequestId: () => requestId,
      log: (entry) => logs.push(entry),
    });
    const response = await handler(request({ type: "resume", caseId, actionId, turnVersion: 1 }, []));
    const body = await response.json() as { code: string; error: string; message: string };
    assert.equal(response.status, status);
    assert.equal(body.code, code);
    assert.match(`${body.error}${body.message}`, /校正|服务|进度|稍后|重试/);
    assert.deepEqual(logs, [{ requestId, actionId, caseId, code }]);
  }
});

test("unknown SQL, model, and browser errors are never exposed or logged", async () => {
  const raw = "duplicate key SQL WebKit DOMException model response with token=secret";
  const logs: unknown[] = [];
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() { return { userId, context: null }; },
    async createService() {
      return service({ async pause() { throw new Error(raw); } });
    },
    createRequestId: () => requestId,
    log: (entry) => logs.push(entry),
  });
  const response = await handler(request({ type: "pause", caseId, actionId, turnVersion: 1 }, []));
  const serialized = JSON.stringify(await response.json());
  assert.equal(response.status, 503);
  assert.equal(serialized.includes(raw), false);
  assert.equal(JSON.stringify(logs).includes(raw), false);
  assert.deepEqual(logs, [{ requestId, actionId, caseId, code: "service_unavailable" }]);
});

test("production route lazily creates privileged clients only after authentication and strict parsing", () => {
  const source = readFileSync(new URL("../src/app/api/birth-time-conversation/route.ts", import.meta.url), "utf8");
  assert.doesNotMatch(source, /^import .*supabase\/admin/m);
  const authenticateCall = source.indexOf("dependencies.authenticate(request)");
  const parseCall = source.indexOf("safeParse(await requestPayload(request))");
  const serviceCall = source.indexOf("dependencies.createService(authenticated)");
  assert.ok(authenticateCall < parseCall);
  assert.ok(parseCall < serviceCall);
  assert.match(source, /import\(["'].*supabase\/admin(?:\.ts)?["']\)/);
  assert.match(source, /process\.env\.RECTIFICATION_PRICE_CREDITS/);
  assert.doesNotMatch(source, /BIRTH_TIME_RECTIFICATION_PRICE_CREDITS/);
  assert.doesNotMatch(source, /command\.price|parsed\.data\.price/);
});
