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
import { conversationalRectificationTurnSchema } from "../src/lib/conversational-rectification/contracts.ts";
import {
  conversationalRectificationActionReceiptRequestSchema,
  conversationalRectificationActionReceiptResponseSchema,
  declaredBirthInputSchema,
  lifeEventEvidenceSchema,
  privateCandidateSchema,
  validationReceiptSchema,
} from "../src/lib/conversational-rectification/persistence-contracts.ts";
import { postgresJsonbTextBytes } from "../src/lib/conversational-rectification/json-bounds.ts";

const userId = "00000000-0000-4000-8000-000000000101";
const caseId = "00000000-0000-4000-8000-000000000102";
const actionId = "00000000-0000-4000-8000-000000000103";
const resultId = "00000000-0000-4000-8000-000000000104";
const importCaseId = "00000000-0000-4000-8000-000000000107";
const commandFingerprint = "c".repeat(64);

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
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
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
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
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
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
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

test("loads an exact owner-scoped historical mutation receipt before current case state", async () => {
  const calls: unknown[] = [];
  const publicReceiptRow: Partial<typeof storedRow> = { ...storedRow };
  delete publicReceiptRow.declared_birth_input;
  delete publicReceiptRow.private_candidate;
  delete publicReceiptRow.event_evidence;
  delete publicReceiptRow.validation_receipts;
  const store = new ConversationalRectificationStore(rpcClient((name, args) => {
    calls.push([name, args]);
    return publicReceiptRow;
  }));

  const replayed = await store.loadActionReceipt({
    userId,
    caseId,
    actionId,
    actionKind: "save_turn",
    expectedVersion: 0,
    commandFingerprint,
  });

  assert.equal(replayed?.caseId, caseId);
  assert.deepEqual(replayed?.latestTurn, firstTurn);
  assert.equal(replayed && "privateCandidate" in replayed, false);
  assert.deepEqual(calls, [["replay_conversational_rectification_action", {
    p_user_id: userId,
    p_case_id: caseId,
    p_action_id: actionId,
    p_action_kind: "save_turn",
    p_expected_version: 0,
    p_command_fingerprint: commandFingerprint,
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
      declaredBirthInput: storedRow.declared_birth_input as never,
      firstTurn,
      validationReceipt,
      privateCandidate: storedRow.private_candidate,
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
  const common = { userId, caseId, actionId, expectedVersion: 0, commandFingerprint };
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
    assert.equal(args.p_command_fingerprint, commandFingerprint);
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

test("declared birth input is strict, source-aware, bounded, and location-complete", () => {
  assert.equal(declaredBirthInputSchema.safeParse(storedRow.declared_birth_input).success, true);
  const commonDeclaration = {
    birthDate: "1990-01-01",
    birthTimeClue: null,
    birthplace: {
      city: "Taipei",
      latitude: 25.03,
      longitude: 121.56,
      timezoneOffset: 8,
    },
  };
  for (const value of [
    { ...commonDeclaration, source: "hospital_record", reportedTime: "05:20", uncertaintyBeforeMinutes: 2, uncertaintyAfterMinutes: 2 },
    { ...commonDeclaration, source: "family_exact", reportedTime: "05:20", uncertaintyBeforeMinutes: 10, uncertaintyAfterMinutes: 10 },
    { ...commonDeclaration, source: "period_only", reportedPeriod: "morning" },
    { ...commonDeclaration, source: "unknown" },
    { ...commonDeclaration, source: "legacy_import", reportedTime: "05:20", uncertaintyBeforeMinutes: 0, uncertaintyAfterMinutes: 0 },
  ]) {
    assert.equal(declaredBirthInputSchema.safeParse(value).success, true);
  }

  const invalid = [
    { ...storedRow.declared_birth_input, unexpected: true },
    { ...storedRow.declared_birth_input, birthDate: "2023-02-30" },
    { ...storedRow.declared_birth_input, birthTimeClue: undefined },
    { ...storedRow.declared_birth_input, birthplace: undefined },
    { ...storedRow.declared_birth_input, source: "unrecognized" },
    {
      ...storedRow.declared_birth_input,
      uncertaintyAfterMinutes: 60,
    },
    {
      ...storedRow.declared_birth_input,
      reportedPeriod: "morning",
    },
    {
      ...storedRow.declared_birth_input,
      birthplace: { ...storedRow.declared_birth_input.birthplace, latitude: 91 },
    },
    {
      ...storedRow.declared_birth_input,
      birthplace: { timezoneOffset: 8 },
    },
  ];
  for (const value of invalid) {
    assert.equal(declaredBirthInputSchema.safeParse(value).success, false);
  }
  const exactClue = declaredBirthInputSchema.parse({
    ...storedRow.declared_birth_input,
    birthTimeClue: "  exact clue spacing  ",
  });
  assert.equal(exactClue.birthTimeClue, "  exact clue spacing  ");
});

test("durable JSON uses PostgreSQL-stable numeric vectors recursively", () => {
  const stableVector = {
    zero: 0,
    minFraction: 0.000001,
    ieeeRoundingBoundary: 1.000001,
    decimal: 0.123456,
    maxSafe: 9_007_199_254_740_991,
  };
  assert.equal(postgresJsonbTextBytes(stableVector), 120);
  assert.equal(declaredBirthInputSchema.safeParse({
    ...storedRow.declared_birth_input,
    birthplace: {
      ...storedRow.declared_birth_input.birthplace,
      latitude: 25.0268,
      longitude: 121.5434,
      timezoneOffset: 8,
    },
  }).success, true);

  assert.ok(Number.isSafeInteger(1.000001 * 1_000_000) === false);
  for (const candidateWeights of [[1e-7], [1e-100], [0.0000012], [0.1234567]]) {
    assert.equal(privateCandidateSchema.safeParse({
      resultId,
      calculationVersion: "rectification-v3.1",
      candidateWeights,
    }).success, false);
  }
  assert.equal(privateCandidateSchema.safeParse({
    resultId,
    calculationVersion: "rectification-v3.1",
    scoredHistoricalEvidence: [{
      evidenceId: "00000000-0000-4000-8000-000000000105",
      domain: "career",
      candidateTime: "05:21",
      score: 1e-100,
      ruleRefs: [],
    }],
  }).success, false);
  assert.equal(declaredBirthInputSchema.safeParse({
    ...storedRow.declared_birth_input,
    birthplace: {
      ...storedRow.declared_birth_input.birthplace,
      latitude: 1e-100,
    },
  }).success, false);
  assert.equal(postgresJsonbTextBytes({ nested: [{ score: 1e-100 }] }), Number.POSITIVE_INFINITY);
});

test("durable text uses ECMAScript nonblank and UTF-16 maximum semantics", () => {
  const unicodeWhitespace = "\u00a0\u2007\ufeff";
  const validAstral80 = "😀".repeat(40);
  const invalidAstral82 = "😀".repeat(41);

  assert.equal(validationReceiptSchema.safeParse({
    modelId: "😀".repeat(60),
    schemaValidated: true,
  }).success, true);
  assert.equal(validationReceiptSchema.safeParse({
    modelId: "😀".repeat(61),
    schemaValidated: true,
  }).success, false);
  assert.equal(privateCandidateSchema.safeParse({
    resultId,
    calculationVersion: validAstral80,
  }).success, true);
  assert.equal(privateCandidateSchema.safeParse({
    resultId,
    calculationVersion: invalidAstral82,
  }).success, false);

  for (const invalid of [
    { ...firstTurn, narrative: unicodeWhitespace },
    {
      ...firstTurn,
      technicalReceipt: { ...firstTurn.technicalReceipt, calculationVersion: unicodeWhitespace },
    },
    {
      ...firstTurn,
      technicalReceipt: { ...firstTurn.technicalReceipt, stableLayers: [unicodeWhitespace] },
    },
    {
      ...firstTurn,
      evidenceRecap: [{ id: resultId, summary: unicodeWhitespace, dateLabel: "2020-01" }],
    },
    { ...firstTurn, pendingConsultationQuestion: unicodeWhitespace },
  ]) {
    assert.equal(conversationalRectificationTurnSchema.safeParse(invalid).success, false);
  }

  for (const invalid of [
    { modelId: unicodeWhitespace, schemaValidated: true },
    { modelId: "model", schemaValidated: true, validatorVersion: unicodeWhitespace },
    { modelId: "model", schemaValidated: true, issues: [unicodeWhitespace] },
  ]) {
    assert.equal(validationReceiptSchema.safeParse(invalid).success, false);
  }

  for (const invalid of [
    { resultId, calculationVersion: unicodeWhitespace },
    { resultId, calculationVersion: "v1", candidateModelRefs: [unicodeWhitespace] },
    {
      resultId,
      calculationVersion: "v1",
      futureWindows: [{
        label: unicodeWhitespace,
        startDate: "2020-01-01",
        endDate: "2020-01-02",
        scoreable: false,
      }],
    },
    {
      resultId,
      calculationVersion: "v1",
      workingState: { phase: "initial", iteration: 0, notes: [unicodeWhitespace] },
    },
  ]) {
    assert.equal(privateCandidateSchema.safeParse(invalid).success, false);
  }

  assert.equal(declaredBirthInputSchema.safeParse({
    ...storedRow.declared_birth_input,
    birthTimeClue: unicodeWhitespace,
  }).success, false);
  assert.equal(declaredBirthInputSchema.safeParse({
    ...storedRow.declared_birth_input,
    birthplace: { ...storedRow.declared_birth_input.birthplace, city: unicodeWhitespace },
  }).success, false);
});

test("evidence recap enforces the SQL-matched aggregate byte limit", () => {
  const evidenceRecap = Array.from({ length: 9 }, (_, index) => ({
    id: `00000000-0000-4000-8000-${(700 + index).toString().padStart(12, "0")}`,
    summary: "事".repeat(900),
    dateLabel: "2020-01",
  }));
  const turn = { ...firstTurn, evidenceRecap };

  assert.ok(postgresJsonbTextBytes(evidenceRecap) > 24_576);
  assert.ok(postgresJsonbTextBytes(turn) < 65_536);
  assert.equal(conversationalRectificationTurnSchema.safeParse(turn).success, false);
});

test("nested receipt and private-candidate arrays match SQL UTF-8 byte caps", () => {
  const fullLayer = "事".repeat(80);
  const receiptAtLimit = [
    ...Array.from({ length: 16 }, () => fullLayer),
    `${"事".repeat(62)}aa`,
  ];
  const receiptOverLimit = [
    ...Array.from({ length: 16 }, () => fullLayer),
    "事".repeat(61),
    "aa",
  ];
  assert.equal(postgresJsonbTextBytes(receiptAtLimit), 4_096);
  assert.equal(postgresJsonbTextBytes(receiptOverLimit), 4_097);

  for (const field of ["stableLayers", "sensitiveLayers"] as const) {
    assert.equal(conversationalRectificationTurnSchema.safeParse({
      ...firstTurn,
      technicalReceipt: { ...firstTurn.technicalReceipt, [field]: receiptAtLimit },
    }).success, true, `${field} at its SQL byte limit`);
    assert.equal(conversationalRectificationTurnSchema.safeParse({
      ...firstTurn,
      technicalReceipt: { ...firstTurn.technicalReceipt, [field]: receiptOverLimit },
    }).success, false, `${field} above its SQL byte limit`);
  }

  const fullModelReference = "事".repeat(120);
  const modelReferencesAtLimit = [
    ...Array.from({ length: 44 }, () => fullModelReference),
    "事".repeat(119),
    "aaa",
  ];
  const modelReferencesOverLimit = [
    ...Array.from({ length: 44 }, () => fullModelReference),
    "事".repeat(119),
    "aaaa",
  ];
  assert.equal(postgresJsonbTextBytes(modelReferencesAtLimit), 16_384);
  assert.equal(postgresJsonbTextBytes(modelReferencesOverLimit), 16_385);

  const supportedLayersAtLimit = [
    ...Array.from({ length: 33 }, () => fullLayer),
    `${"事".repeat(45)}a`,
  ];
  const supportedLayersOverLimit = [
    ...Array.from({ length: 33 }, () => fullLayer),
    `${"事".repeat(45)}aa`,
  ];
  assert.equal(postgresJsonbTextBytes(supportedLayersAtLimit), 8_192);
  assert.equal(postgresJsonbTextBytes(supportedLayersOverLimit), 8_193);

  for (const [field, atLimit, overLimit] of [
    ["candidateModelRefs", modelReferencesAtLimit, modelReferencesOverLimit],
    ["supportedSensitiveLayers", supportedLayersAtLimit, supportedLayersOverLimit],
  ] as const) {
    assert.equal(privateCandidateSchema.safeParse({
      resultId,
      calculationVersion: "rectification-v3.1",
      [field]: atLimit,
    }).success, true, `${field} at its SQL byte limit`);
    assert.equal(privateCandidateSchema.safeParse({
      resultId,
      calculationVersion: "rectification-v3.1",
      [field]: overLimit,
    }).success, false, `${field} above its SQL byte limit`);
  }
});

test("life-event evidence rejects unknown, blank, and non-boolean durable values", () => {
  const evidence = {
    id: "00000000-0000-4000-8000-000000000105",
    rawText: "2019 年 7 月换工作",
    domain: "career" as const,
    eventSummary: "换工作",
    dateValue: "2019-07",
    datePrecision: "month" as const,
    extractionStatus: "clear" as const,
    scoreable: true,
  };
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
  for (const invalid of [
    { ...evidence, extra: "discard me" },
    { ...evidence, eventSummary: " \t " },
    { ...evidence, dateValue: " \t " },
    { ...evidence, scoreable: null },
    { ...evidence, scoreable: "true" },
  ]) {
    assert.equal(lifeEventEvidenceSchema.safeParse(invalid).success, false);
  }
});

test("durable private and receipt schemas accept boundaries and reject oversize or unknown fields", () => {
  assert.equal(postgresJsonbTextBytes({ a: [1, 2] }), 13);
  assert.equal(validationReceiptSchema.safeParse({
    modelId: "m".repeat(120),
    schemaValidated: true,
    validatorVersion: "v".repeat(80),
    retryCount: 2,
    fallbackUsed: false,
    issues: ["i".repeat(240)],
  }).success, true);
  assert.equal(validationReceiptSchema.safeParse({
    modelId: "m".repeat(121),
    schemaValidated: true,
  }).success, false);
  assert.equal(validationReceiptSchema.safeParse({
    modelId: `${"m".repeat(120)} `,
    schemaValidated: true,
  }).success, false);
  assert.equal(validationReceiptSchema.safeParse({
    modelId: "model",
    schemaValidated: true,
    validatedAt: "2026-07-20T12:00:00.123456789012345678901Z",
  }).success, false);

  const candidate = {
    resultId,
    representativeTime: "05:21",
    calculationVersion: "rectification-v3.1",
    candidateWeights: Array.from({ length: 1_440 }, () => 0.5),
    candidateModelRefs: ["model-ref"],
    suggestedDomains: ["career", "relocation"],
  };
  assert.equal(privateCandidateSchema.safeParse(candidate).success, true);
  assert.equal(privateCandidateSchema.safeParse({
    ...candidate,
    candidateWeights: [...candidate.candidateWeights, 0.5],
  }).success, false);
  assert.equal(privateCandidateSchema.safeParse({
    calculationVersion: "v1",
    rangeStart: null,
  }).success, false);
  assert.equal(privateCandidateSchema.safeParse({ ...candidate, secretExtra: true }).success, false);

  const request = {
    kind: "save_turn",
    userId,
    caseId,
    expectedVersion: 0,
    actionId,
    requestFingerprint: "a".repeat(64),
    commandFingerprint,
  };
  assert.equal(conversationalRectificationActionReceiptRequestSchema.safeParse(request).success, true);
  assert.equal(conversationalRectificationActionReceiptRequestSchema.safeParse({
    ...request,
    extra: "not durable",
  }).success, false);
  assert.equal(conversationalRectificationActionReceiptRequestSchema.safeParse({
    ...request,
    requestFingerprint: "a".repeat(65),
  }).success, false);
  assert.equal(conversationalRectificationActionReceiptRequestSchema.safeParse({
    ...request,
    commandFingerprint: "c".repeat(63),
  }).success, false);
  assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
    success: false,
    credits: 7,
    billing_state: null,
    error_code: "e".repeat(80),
  }).success, true);
  assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
    success: false,
    credits: 7,
    billing_state: null,
    error_code: "e".repeat(81),
  }).success, false);
});

test("durable UUID text is canonical hyphenated syntax and case-insensitive", () => {
  const canonical = "a9890e09-d535-46f0-9a36-86017515a5a1";
  const compact = canonical.replaceAll("-", "");
  const braced = `{${canonical}}`;

  for (const validResultId of [canonical, canonical.toUpperCase()]) {
    assert.equal(privateCandidateSchema.safeParse({
      resultId: validResultId,
      calculationVersion: "v1",
    }).success, true);
  }
  for (const invalidResultId of [compact, braced]) {
    assert.equal(privateCandidateSchema.safeParse({
      resultId: invalidResultId,
      calculationVersion: "v1",
    }).success, false);
    assert.equal(conversationalRectificationTurnSchema.safeParse({
      ...firstTurn,
      evidenceRecap: [{ id: invalidResultId, summary: "summary", dateLabel: "2020-01" }],
    }).success, false);
  }
});

test("public turn JSON fields reject field and byte boundary violations", () => {
  assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
    ...storedRow,
    declared_birth_input: undefined,
    private_candidate: undefined,
    event_evidence: undefined,
    validation_receipts: undefined,
  }).success, true);

  const exact = {
    ...firstTurn,
    technicalReceipt: {
      ...firstTurn.technicalReceipt,
      calculationVersion: "v".repeat(80),
    },
    evidenceRecap: [{
      id: "00000000-0000-4000-8000-000000000108",
      summary: "事".repeat(1_000),
      dateLabel: "d".repeat(80),
    }],
  };
  assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
    ...storedRow,
    latest_turn: exact,
    declared_birth_input: undefined,
    private_candidate: undefined,
    event_evidence: undefined,
    validation_receipts: undefined,
  }).success, true);

  const nearTurnLimit = {
    ...exact,
    narrative: "n".repeat(12_000),
    evidenceRecap: Array.from({ length: 7 }, (_, index) => ({
      id: `00000000-0000-4000-8000-${(300 + index).toString().padStart(12, "0")}`,
      summary: "事".repeat(1_000),
      dateLabel: "d".repeat(80),
    })),
  };
  assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
    ...storedRow,
    latest_turn: nearTurnLimit,
    declared_birth_input: undefined,
    private_candidate: undefined,
    event_evidence: undefined,
    validation_receipts: undefined,
  }).success, true);

  for (const latest_turn of [
    {
      ...exact,
      candidate: { ...exact.candidate, unknown: true },
    },
    {
      ...exact,
      technicalReceipt: { ...exact.technicalReceipt, calculationVersion: "v".repeat(81) },
    },
    {
      ...exact,
      evidenceRecap: [{ ...exact.evidenceRecap[0], summary: "事".repeat(1_001) }],
    },
    {
      ...exact,
      narrative: "n".repeat(12_000),
      evidenceRecap: Array.from({ length: 20 }, (_, index) => ({
        id: `00000000-0000-4000-8000-${(200 + index).toString().padStart(12, "0")}`,
        summary: "事".repeat(1_000),
        dateLabel: "d".repeat(80),
      })),
    },
  ]) {
    assert.equal(conversationalRectificationActionReceiptResponseSchema.safeParse({
      ...storedRow,
      latest_turn,
      declared_birth_input: undefined,
      private_candidate: undefined,
      event_evidence: undefined,
      validation_receipts: undefined,
    }).success, false);
  }
});

test("store rejects invalid durable inputs before issuing an RPC", async () => {
  let calls = 0;
  const store = new ConversationalRectificationStore(rpcClient(() => {
    calls += 1;
    return storedRow;
  }));

  await assert.rejects(store.createCaseWithFirstTurn({
    userId,
    caseId,
    actionId: caseId,
    expectedVersion: 0,
    revisionOfCaseId: null,
    pendingConsultationQuestion: null,
    declaredBirthInput: {
      birthDate: "1990-01-01",
      source: "approximate",
      reportedTime: "05:20",
      birthTimeClue: null,
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
    } as never,
    firstTurn,
    validationReceipt,
    privateCandidate: {
      resultId,
      calculationVersion: "rectification-v3.1",
    },
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "action_conflict");
  assert.equal(calls, 0);
});
