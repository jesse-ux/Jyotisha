import assert from "node:assert/strict";
import test from "node:test";
import {
  ConversationalRectificationError,
  toConversationalRectificationPublicError,
} from "../src/lib/conversational-rectification/errors.ts";
import {
  ConversationalRectificationStore,
  mapConversationalRectificationStoreError,
  type ConversationalRectificationRpcClient,
} from "../src/lib/conversational-rectification/store.ts";
import { ConversationalRectificationBilling } from "../src/lib/conversational-rectification/billing.ts";

const userId = "00000000-0000-4000-8000-000000000101";
const caseId = "00000000-0000-4000-8000-000000000102";
const actionId = "00000000-0000-4000-8000-000000000103";
const resultId = "00000000-0000-4000-8000-000000000104";
const importCaseId = "00000000-0000-4000-8000-000000000107";

const firstTurn = {
  caseId,
  journeyProtocol: "conversational-evidence-v3" as const,
  status: "active" as const,
  turnVersion: 0,
  narrative: "我们会用已经发生的人生事件验证当前候选范围。",
  candidate: {
    status: "pending_validation" as const,
    representativeTime: "05:21",
    rangeStart: "05:10",
    rangeEnd: "05:30",
  },
  technicalReceipt: {
    calculationVersion: "rectification-v3.1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9"],
    candidateDifferenceRefs: ["difference-1"],
  },
  evidenceRequest: {
    domains: ["career", "relocation"] as const,
    datePrecision: "month_preferred" as const,
    freeTextAllowed: true as const,
  },
  evidenceRecap: [],
  actions: ["answer", "pause", "abandon"] as const,
  pendingConsultationQuestion: null,
};

const storedRow = {
  case_id: caseId,
  user_id: userId,
  status: "active",
  turn_version: 0,
  revision_of_case_id: null,
  imported_from_case_id: null,
  baseline_active_time: "04:58",
  pending_consultation_question: null,
  billing_state: null,
  latest_turn: firstTurn,
  declared_birth_input: {
    birthDate: "1990-01-01",
    reportedTime: "05:20",
    source: "approximate",
    birthTimeClue: "家人记得天刚亮",
    birthplace: {
      countryCode: "TW",
      provinceCode: "TPE",
      cityCode: "TPE-CITY",
      districtCode: "DAAN",
      latitude: 25.0268,
      longitude: 121.5434,
      timezoneOffset: 8,
    },
  },
  private_candidate: {
    resultId,
    calculationVersion: "rectification-v3.1",
    candidateWeights: [0.6, 0.4],
  },
  event_evidence: [],
  validation_receipts: [{ modelId: "synthetic-model", schemaValidated: true }],
};

const validationReceipt = {
  modelId: "synthetic-model",
  schemaValidated: true,
};

function rpcClient(
  handler: (name: string, args: Readonly<Record<string, unknown>>) => unknown,
): ConversationalRectificationRpcClient {
  return {
    async rpc(name, args) {
      return { data: handler(name, args), error: null };
    },
  };
}

test("creates an account-level case and first public turn through one RPC", async () => {
  let call: { name: string; args: Readonly<Record<string, unknown>> } | undefined;
  const store = new ConversationalRectificationStore(rpcClient((name, args) => {
    call = { name, args };
    return storedRow;
  }));

  const result = await store.createCaseWithFirstTurn({
    userId,
    caseId,
    actionId: caseId,
    expectedVersion: 0,
    revisionOfCaseId: null,
    pendingConsultationQuestion: null,
    declaredBirthInput: {
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      source: "approximate",
      birthTimeClue: "家人记得天刚亮",
      birthplace: {
        countryCode: "TW",
        provinceCode: "TPE",
        cityCode: "TPE-CITY",
        districtCode: "DAAN",
        latitude: 25.0268,
        longitude: 121.5434,
        timezoneOffset: 8,
      },
    },
    firstTurn,
    validationReceipt,
    privateCandidate: {
      resultId,
      representativeTime: "05:21",
      calculationVersion: "rectification-v3.1",
      candidateWeights: [0.6, 0.4],
    },
  });

  assert.equal(call?.name, "create_conversational_rectification_case");
  assert.deepEqual(call?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_expected_version: 0,
    p_action_id: caseId,
    p_revision_of_case_id: null,
    p_pending_consultation_question: null,
    p_declared_birth_input: {
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      source: "approximate",
      birthTimeClue: "家人记得天刚亮",
      birthplace: {
        countryCode: "TW",
        provinceCode: "TPE",
        cityCode: "TPE-CITY",
        districtCode: "DAAN",
        latitude: 25.0268,
        longitude: 121.5434,
        timezoneOffset: 8,
      },
    },
    p_first_turn: firstTurn,
    p_validation_receipt: validationReceipt,
    p_private_candidate: {
      resultId,
      representativeTime: "05:21",
      calculationVersion: "rectification-v3.1",
      candidateWeights: [0.6, 0.4],
    },
  });
  assert.equal(result.caseId, caseId);
  assert.equal(result.baselineActiveTime, "04:58");
  assert.deepEqual(result.declaredBirthInput, storedRow.declared_birth_input);
  assert.deepEqual(result.latestTurn, firstTurn);
  assert.deepEqual(result.privateCandidate, storedRow.private_candidate);
  assert.deepEqual(result.eventEvidence, []);
  assert.deepEqual(result.validationReceipts, storedRow.validation_receipts);
});

test("loads the latest unfinished case by account without a chat identifier", async () => {
  const calls: unknown[] = [];
  const store = new ConversationalRectificationStore(rpcClient((name, args) => {
    calls.push([name, args]);
    return storedRow;
  }));

  const loaded = await store.loadCase({ userId });
  assert.equal(loaded?.caseId, caseId);
  assert.deepEqual(calls, [["load_conversational_rectification_case", {
    p_user_id: userId,
    p_case_id: null,
  }]]);
});

test("binds every paid start to the public action as its recoverable case id", async () => {
  let calls = 0;
  const client = rpcClient(() => {
    calls += 1;
    return storedRow;
  });
  const store = new ConversationalRectificationStore(client);
  const billing = new ConversationalRectificationBilling(client);

  await assert.rejects(
    billing.reserve({ userId, caseId, actionId, expectedVersion: 0, price: 3 }),
    (error: unknown) => error instanceof ConversationalRectificationError
      && error.code === "action_conflict",
  );
  await assert.rejects(
    store.createCaseWithFirstTurn({
      userId,
      caseId,
      actionId,
      expectedVersion: 0,
      revisionOfCaseId: null,
      pendingConsultationQuestion: null,
      declaredBirthInput: { birthDate: "1990-01-01", source: "approximate" },
      firstTurn,
      validationReceipt,
      privateCandidate: {},
    }),
    (error: unknown) => error instanceof ConversationalRectificationError
      && error.code === "action_conflict",
  );
  assert.equal(calls, 0);
});

test("save, pause, abandon, confirm, and import carry owner/version/action guards", async () => {
  const calls: Array<[string, Readonly<Record<string, unknown>>]> = [];
  const store = new ConversationalRectificationStore(rpcClient((name, args) => {
    calls.push([name, args]);
    return storedRow;
  }));
  const common = { userId, caseId, actionId, expectedVersion: 0 };
  const evidence = [{
    id: "00000000-0000-4000-8000-000000000105",
    rawText: "2019 年 7 月换工作",
    domain: "career" as const,
    eventSummary: "换工作",
    dateValue: "2019-07",
    datePrecision: "month" as const,
    extractionStatus: "clear" as const,
  }];

  await store.saveTurn({
    ...common,
    turn: { ...firstTurn, turnVersion: 1 },
    evidence,
    validationReceipt,
    privateCandidate: { resultId, calculationVersion: "rectification-v3.1" },
  });
  await store.pause({
    ...common,
    turn: { ...firstTurn, status: "paused", turnVersion: 1 },
    validationReceipt,
  });
  await store.abandon({
    ...common,
    turn: { ...firstTurn, status: "abandoned", turnVersion: 1 },
    validationReceipt,
  });
  await store.confirm({
    ...common,
    resultId,
    time: "05:21",
    calculationVersion: "rectification-v3.1",
    validationReceipt,
    turn: {
      ...firstTurn,
      status: "completed",
      turnVersion: 1,
      candidate: { ...firstTurn.candidate, status: "confirmed" },
      evidenceRequest: null,
      actions: ["continue_original_question"],
    },
  });
  await store.importLegacy({
    userId,
    caseId: importCaseId,
    actionId: importCaseId,
    expectedVersion: 0,
    legacyCaseId: "00000000-0000-4000-8000-000000000106",
    price: 3,
    pendingConsultationQuestion: null,
    firstTurn: { ...firstTurn, caseId: importCaseId },
    validationReceipt,
    privateCandidate: { resultId, calculationVersion: "rectification-v3.1" },
  });

  assert.deepEqual(calls.map(([name]) => name), [
    "save_conversational_rectification_turn",
    "pause_conversational_rectification_case",
    "abandon_conversational_rectification_case",
    "confirm_conversational_rectification_candidate",
    "import_legacy_conversational_rectification_case",
  ]);
  for (const [, args] of calls.slice(0, 4)) {
    assert.equal(args.p_user_id, userId);
    assert.equal(args.p_case_id, caseId);
    assert.equal(args.p_action_id, actionId);
    assert.equal(args.p_expected_version, 0);
    assert.deepEqual(args.p_validation_receipt, validationReceipt);
  }
  assert.equal(calls[4]?.[1].p_case_id, importCaseId);
  assert.equal(calls[4]?.[1].p_action_id, importCaseId);
  assert.deepEqual(calls[4]?.[1].p_validation_receipt, validationReceipt);
  assert.deepEqual(calls[0]?.[1].p_evidence, evidence);
  assert.equal(calls[0]?.[1].p_turn && typeof calls[0]?.[1].p_turn, "object");
  assert.equal("outputValidationReceipt" in (calls[0]?.[1].p_turn as object), false);
});

test("maps only exact allowlisted database failures to stable domain codes", () => {
  const exact = [
    ["conversational_case_not_found", "case_not_found"],
    ["conversational_stale_turn", "stale_turn"],
    ["conversational_action_conflict", "action_conflict"],
    ["conversational_candidate_changed", "candidate_changed"],
    ["conversational_billing_failed", "billing_failed"],
  ] as const;
  for (const [message, code] of exact) {
    const mapped = mapConversationalRectificationStoreError({ code: "P0001", message });
    assert.ok(mapped instanceof ConversationalRectificationError);
    assert.equal(mapped.code, code);
  }
  assert.equal(
    mapConversationalRectificationStoreError({ code: "08006", message: "conversational_stale_turn" }).code,
    "store_unavailable",
  );
  assert.equal(
    mapConversationalRectificationStoreError({ code: "P0001", message: "raw database detail" }).code,
    "store_unavailable",
  );
});

test("unknown Supabase errors never survive in the store or public error", async () => {
  const rawMessage = "WebKit SQL password=model-secret";
  const store = new ConversationalRectificationStore({
    async rpc() {
      return { data: null, error: { code: "08006", message: rawMessage } };
    },
  });

  let caught: unknown;
  try {
    await store.loadCase({ userId, caseId });
  } catch (error) {
    caught = error;
  }
  assert.ok(caught instanceof ConversationalRectificationError);
  assert.equal(caught.code, "store_unavailable");
  assert.equal(JSON.stringify(caught).includes(rawMessage), false);
  assert.equal(JSON.stringify(toConversationalRectificationPublicError(caught)).includes(rawMessage), false);
});

test("billing sends the server fee and never converts completion into a debit", async () => {
  const calls: Array<[string, Readonly<Record<string, unknown>>]> = [];
  const billing = new ConversationalRectificationBilling(rpcClient((name, args) => {
    calls.push([name, args]);
    return {
      success: true,
      credits: 7,
      billing_state: name.includes("complete") ? "charged" : name.includes("release") ? "released" : "reserved",
      error_code: null,
    };
  }));
  const common = { userId, caseId, actionId: caseId, expectedVersion: 0 };

  assert.equal((await billing.reserve({ ...common, price: 3 })).billingState, "reserved");
  assert.equal((await billing.complete(common)).billingState, "charged");
  assert.equal((await billing.release({ ...common, price: 3 })).billingState, "released");

  assert.deepEqual(calls.map(([name]) => name), [
    "reserve_conversational_rectification_fee",
    "complete_conversational_rectification_fee",
    "release_conversational_rectification_fee",
  ]);
  assert.equal(calls[0]?.[1].p_price, 3);
  assert.equal("p_price" in (calls[1]?.[1] ?? {}), false);
  assert.equal(calls[2]?.[1].p_price, 3);
});

test("billing rejections use stable domain errors instead of raw RPC messages", async () => {
  const insufficient = new ConversationalRectificationBilling(rpcClient(() => ({
    success: false,
    credits: 0,
    billing_state: null,
    error_code: "insufficient_credits",
  })));
  await assert.rejects(
    insufficient.reserve({ userId, caseId, actionId: caseId, expectedVersion: 0, price: 3 }),
    (error: unknown) => error instanceof ConversationalRectificationError
      && error.code === "insufficient_credits",
  );

  const failed = new ConversationalRectificationBilling(rpcClient(() => ({
    success: false,
    credits: 7,
    billing_state: "released",
    error_code: "already_charged",
  })));
  await assert.rejects(
    failed.release({ userId, caseId, actionId: caseId, expectedVersion: 0, price: 3 }),
    (error: unknown) => error instanceof ConversationalRectificationError
      && error.code === "billing_failed",
  );
});
