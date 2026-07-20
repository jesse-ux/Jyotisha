import { z } from "zod";
import {
  conversationalRectificationTurnSchema,
  type ConversationalRectificationTurn,
} from "./contracts.ts";
import {
  ConversationalRectificationError,
  type ConversationalRectificationErrorCode,
} from "./errors.ts";

export type ConversationalRectificationRpcError = Readonly<{
  code?: string;
  message?: string;
}>;

export type ConversationalRectificationRpcClient = {
  rpc(
    functionName: string,
    args: Readonly<Record<string, unknown>>,
  ): PromiseLike<Readonly<{
    data: unknown;
    error: ConversationalRectificationRpcError | null;
  }>>;
};

type DeepReadonly<T> = T extends (...args: never[]) => unknown
  ? T
  : T extends ReadonlyArray<infer Item>
    ? ReadonlyArray<DeepReadonly<Item>>
    : T extends object
      ? { readonly [Key in keyof T]: DeepReadonly<T[Key]> }
      : T;

export type ConversationalRectificationTurnInput = DeepReadonly<ConversationalRectificationTurn>;
export type PrivateCandidateInput = Readonly<Record<string, unknown>>;
export type ValidationReceiptInput = Readonly<Record<string, unknown>>;

export type StoredConversationalRectificationCase = Readonly<{
  caseId: string;
  userId: string;
  status: "starting" | "active" | "paused" | "confirming" | "completed" | "abandoned";
  turnVersion: number;
  revisionOfCaseId: string | null;
  importedFromCaseId: string | null;
  baselineActiveTime: string | null;
  pendingConsultationQuestion: string | null;
  billingState: "reserved" | "charged" | "released" | "migration_waived" | null;
  latestTurn: ConversationalRectificationTurn;
  declaredBirthInput?: Readonly<Record<string, unknown>>;
  privateCandidate?: Readonly<Record<string, unknown>>;
  eventEvidence?: ReadonlyArray<LifeEventEvidenceInput>;
  validationReceipts?: ReadonlyArray<Readonly<Record<string, unknown>>>;
}>;

export type LoadedConversationalRectificationCase =
  StoredConversationalRectificationCase & Readonly<{
    declaredBirthInput: Readonly<Record<string, unknown>>;
    privateCandidate: Readonly<Record<string, unknown>>;
    eventEvidence: ReadonlyArray<LifeEventEvidenceInput>;
    validationReceipts: ReadonlyArray<Readonly<Record<string, unknown>>>;
  }>;

type MutationIdentity = Readonly<{
  userId: string;
  caseId: string;
  expectedVersion: number;
  actionId: string;
}>;

export type CreateConversationalRectificationCaseInput = MutationIdentity & Readonly<{
  revisionOfCaseId: string | null;
  pendingConsultationQuestion: string | null;
  declaredBirthInput: Readonly<Record<string, unknown>>;
  firstTurn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
  privateCandidate: PrivateCandidateInput;
}>;

export type LifeEventEvidenceInput = Readonly<{
  id: string;
  rawText: string;
  domain: "career" | "education" | "relocation" | "relationship" | "family" | "other";
  eventSummary: string;
  dateValue: string | null;
  datePrecision: "day" | "month" | "year" | "range" | "unknown";
  extractionStatus: "clear" | "needs_clarification" | "corrected";
  scoreable?: boolean;
}>;

export type SaveConversationalRectificationTurnInput = MutationIdentity & Readonly<{
  turn: ConversationalRectificationTurnInput;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
  validationReceipt: ValidationReceiptInput;
  privateCandidate: PrivateCandidateInput;
}>;

export type ConversationalRectificationTransitionInput = MutationIdentity & Readonly<{
  turn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
}>;

export type ConfirmConversationalRectificationInput = MutationIdentity & Readonly<{
  resultId: string;
  time: string;
  calculationVersion: string;
  turn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
}>;

export type ImportLegacyConversationalRectificationInput = MutationIdentity & Readonly<{
  legacyCaseId: string;
  price: number;
  pendingConsultationQuestion: string | null;
  firstTurn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
  privateCandidate: PrivateCandidateInput;
}>;

const stableP0001Codes: Readonly<Record<string, ConversationalRectificationErrorCode>> = {
  conversational_case_not_found: "case_not_found",
  conversational_stale_turn: "stale_turn",
  conversational_action_conflict: "action_conflict",
  conversational_imported_case_read_only: "action_conflict",
  conversational_candidate_changed: "candidate_changed",
  conversational_billing_failed: "billing_failed",
};

function safeRpcErrorFields(error: unknown): { code?: string; message?: string } {
  if (error === null || typeof error !== "object") return {};
  try {
    const candidate = error as { code?: unknown; message?: unknown };
    return {
      code: typeof candidate.code === "string" ? candidate.code : undefined,
      message: typeof candidate.message === "string" ? candidate.message : undefined,
    };
  } catch {
    return {};
  }
}

export function mapConversationalRectificationStoreError(
  error: unknown,
): ConversationalRectificationError {
  const { code, message } = safeRpcErrorFields(error);
  const domainCode = code === "P0001" && message ? stableP0001Codes[message] : undefined;
  return new ConversationalRectificationError(domainCode ?? "store_unavailable");
}

const storedCaseRowSchema = z.object({
  case_id: z.string().uuid(),
  user_id: z.string().uuid(),
  status: z.enum(["starting", "active", "paused", "confirming", "completed", "abandoned"]),
  turn_version: z.number().int().nonnegative(),
  revision_of_case_id: z.string().uuid().nullable(),
  imported_from_case_id: z.string().uuid().nullable(),
  baseline_active_time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/).nullable(),
  pending_consultation_question: z.string().min(1).max(500).nullable(),
  billing_state: z.enum(["reserved", "charged", "released", "migration_waived"]).nullable(),
  latest_turn: conversationalRectificationTurnSchema,
  declared_birth_input: z.record(z.unknown()).optional(),
  private_candidate: z.record(z.unknown()).optional(),
  event_evidence: z.array(z.object({
    id: z.string().uuid(),
    rawText: z.string().trim().min(1).max(4_000),
    domain: z.enum(["career", "education", "relocation", "relationship", "family", "other"]),
    eventSummary: z.string().min(1).max(1_000),
    dateValue: z.string().min(1).max(80).nullable(),
    datePrecision: z.enum(["day", "month", "year", "range", "unknown"]),
    extractionStatus: z.enum(["clear", "needs_clarification", "corrected"]),
    scoreable: z.boolean(),
  }).strict()).optional(),
  validation_receipts: z.array(z.record(z.unknown())).optional(),
}).strict();

function unwrapSingle(data: unknown, allowNull: boolean): unknown {
  if (Array.isArray(data)) {
    if (data.length === 0 && allowNull) return null;
    if (data.length !== 1) throw new ConversationalRectificationError("store_unavailable");
    return data[0];
  }
  return data;
}

function parseStoredCase(data: unknown, allowNull = false): StoredConversationalRectificationCase | null {
  const candidate = unwrapSingle(data, allowNull);
  if (candidate === null && allowNull) return null;
  const parsed = storedCaseRowSchema.safeParse(candidate);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  const value = parsed.data;
  return Object.freeze({
    caseId: value.case_id,
    userId: value.user_id,
    status: value.status,
    turnVersion: value.turn_version,
    revisionOfCaseId: value.revision_of_case_id,
    importedFromCaseId: value.imported_from_case_id,
    baselineActiveTime: value.baseline_active_time,
    pendingConsultationQuestion: value.pending_consultation_question,
    billingState: value.billing_state,
    latestTurn: value.latest_turn,
    declaredBirthInput: value.declared_birth_input,
    privateCandidate: value.private_candidate,
    eventEvidence: value.event_evidence,
    validationReceipts: value.validation_receipts,
  });
}

function requirePublicTurn(turn: ConversationalRectificationTurnInput): ConversationalRectificationTurn {
  const parsed = conversationalRectificationTurnSchema.safeParse(turn);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  return parsed.data;
}

function mutationArgs(input: MutationIdentity): Readonly<Record<string, unknown>> {
  return {
    p_user_id: input.userId,
    p_case_id: input.caseId,
    p_expected_version: input.expectedVersion,
    p_action_id: input.actionId,
  };
}

/**
 * A public start action is also its durable case identity. This makes a retry
 * recoverable even when the first response was lost before the caller learned
 * a separately generated case id.
 */
export function conversationalRectificationCaseIdForStartAction(actionId: string): string {
  const parsed = z.string().uuid().safeParse(actionId);
  if (!parsed.success) throw new ConversationalRectificationError("action_conflict");
  return parsed.data;
}

export class ConversationalRectificationStore {
  constructor(private readonly supabase: ConversationalRectificationRpcClient) {}

  private async callCaseRpc(
    functionName: string,
    args: Readonly<Record<string, unknown>>,
    allowNull = false,
  ): Promise<StoredConversationalRectificationCase | null> {
    try {
      const { data, error } = await this.supabase.rpc(functionName, args);
      if (error) throw mapConversationalRectificationStoreError(error);
      return parseStoredCase(data, allowNull);
    } catch (error) {
      if (error instanceof ConversationalRectificationError) throw error;
      throw new ConversationalRectificationError("store_unavailable");
    }
  }

  async createCaseWithFirstTurn(
    input: CreateConversationalRectificationCaseInput,
  ): Promise<StoredConversationalRectificationCase> {
    if (input.caseId !== conversationalRectificationCaseIdForStartAction(input.actionId)) {
      throw new ConversationalRectificationError("action_conflict");
    }
    const result = await this.callCaseRpc("create_conversational_rectification_case", {
      ...mutationArgs(input),
      p_revision_of_case_id: input.revisionOfCaseId,
      p_pending_consultation_question: input.pendingConsultationQuestion,
      p_declared_birth_input: input.declaredBirthInput,
      p_first_turn: requirePublicTurn(input.firstTurn),
      p_validation_receipt: input.validationReceipt,
      p_private_candidate: input.privateCandidate,
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }

  async loadCase(input: Readonly<{
    userId: string;
    caseId?: string;
  }>): Promise<LoadedConversationalRectificationCase | null> {
    const loaded = await this.callCaseRpc("load_conversational_rectification_case", {
      p_user_id: input.userId,
      p_case_id: input.caseId ?? null,
    }, true);
    if (!loaded) return null;
    if (loaded.declaredBirthInput === undefined
      || loaded.privateCandidate === undefined
      || loaded.eventEvidence === undefined
      || loaded.validationReceipts === undefined) {
      throw new ConversationalRectificationError("store_unavailable");
    }
    return loaded as LoadedConversationalRectificationCase;
  }

  async saveTurn(
    input: SaveConversationalRectificationTurnInput,
  ): Promise<StoredConversationalRectificationCase> {
    const result = await this.callCaseRpc("save_conversational_rectification_turn", {
      ...mutationArgs(input),
      p_turn: requirePublicTurn(input.turn),
      p_evidence: input.evidence,
      p_validation_receipt: input.validationReceipt,
      p_private_candidate: input.privateCandidate,
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }

  async pause(
    input: ConversationalRectificationTransitionInput,
  ): Promise<StoredConversationalRectificationCase> {
    return this.requireTransition("pause_conversational_rectification_case", input);
  }

  async abandon(
    input: ConversationalRectificationTransitionInput,
  ): Promise<StoredConversationalRectificationCase> {
    return this.requireTransition("abandon_conversational_rectification_case", input);
  }

  private async requireTransition(
    functionName: string,
    input: ConversationalRectificationTransitionInput,
  ): Promise<StoredConversationalRectificationCase> {
    const result = await this.callCaseRpc(functionName, {
      ...mutationArgs(input),
      p_turn: requirePublicTurn(input.turn),
      p_validation_receipt: input.validationReceipt,
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }

  async confirm(
    input: ConfirmConversationalRectificationInput,
  ): Promise<StoredConversationalRectificationCase> {
    const result = await this.callCaseRpc("confirm_conversational_rectification_candidate", {
      ...mutationArgs(input),
      p_result_id: input.resultId,
      p_time: input.time,
      p_calculation_version: input.calculationVersion,
      p_turn: requirePublicTurn(input.turn),
      p_validation_receipt: input.validationReceipt,
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }

  async importLegacy(
    input: ImportLegacyConversationalRectificationInput,
  ): Promise<StoredConversationalRectificationCase> {
    if (input.caseId !== conversationalRectificationCaseIdForStartAction(input.actionId)) {
      throw new ConversationalRectificationError("action_conflict");
    }
    const result = await this.callCaseRpc("import_legacy_conversational_rectification_case", {
      ...mutationArgs(input),
      p_legacy_case_id: input.legacyCaseId,
      p_price: input.price,
      p_pending_consultation_question: input.pendingConsultationQuestion,
      p_first_turn: requirePublicTurn(input.firstTurn),
      p_validation_receipt: input.validationReceipt,
      p_private_candidate: input.privateCandidate,
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }
}

export function createSupabaseConversationalRectificationStore(
  supabase: ConversationalRectificationRpcClient,
): ConversationalRectificationStore {
  return new ConversationalRectificationStore(supabase);
}
