import { z } from "zod";
import {
  conversationalRectificationTurnSchema,
  type ConversationalRectificationTurn,
} from "./contracts.ts";
import {
  ConversationalRectificationError,
  type ConversationalRectificationErrorCode,
} from "./errors.ts";
import {
  declaredBirthInputSchema,
  lifeEventEvidenceSchema,
  privateCandidateSchema,
  storedCaseRowSchema,
  validationReceiptSchema,
  type DeclaredBirthInput,
  type LifeEventEvidence,
  type PrivateCandidate,
  type ValidationReceipt,
} from "./persistence-contracts.ts";

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
export type PrivateCandidateInput = DeepReadonly<PrivateCandidate>;
export type ValidationReceiptInput = DeepReadonly<ValidationReceipt>;

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
  declaredBirthInput?: DeepReadonly<DeclaredBirthInput>;
  privateCandidate?: DeepReadonly<PrivateCandidate>;
  eventEvidence?: ReadonlyArray<LifeEventEvidenceInput>;
  validationReceipts?: ReadonlyArray<DeepReadonly<ValidationReceipt>>;
}>;

export type LoadedConversationalRectificationCase =
  StoredConversationalRectificationCase & Readonly<{
    declaredBirthInput: DeepReadonly<DeclaredBirthInput>;
    privateCandidate: DeepReadonly<PrivateCandidate>;
    eventEvidence: ReadonlyArray<LifeEventEvidenceInput>;
    validationReceipts: ReadonlyArray<DeepReadonly<ValidationReceipt>>;
  }>;

type MutationIdentity = Readonly<{
  userId: string;
  caseId: string;
  expectedVersion: number;
  actionId: string;
}>;

type CommandMutationIdentity = MutationIdentity & Readonly<{
  commandFingerprint: string;
}>;

export type ConversationalRectificationActionKind =
  | "save_turn"
  | "pause"
  | "abandon"
  | "confirm";

export type LoadConversationalRectificationActionReceiptInput = CommandMutationIdentity & Readonly<{
  actionKind: ConversationalRectificationActionKind;
}>;

export type CreateConversationalRectificationCaseInput = MutationIdentity & Readonly<{
  revisionOfCaseId: string | null;
  pendingConsultationQuestion: string | null;
  declaredBirthInput: DeepReadonly<DeclaredBirthInput>;
  firstTurn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
  privateCandidate: PrivateCandidateInput;
}>;

export type LifeEventEvidenceInput = DeepReadonly<LifeEventEvidence>;

export type SaveConversationalRectificationTurnInput = CommandMutationIdentity & Readonly<{
  turn: ConversationalRectificationTurnInput;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
  validationReceipt: ValidationReceiptInput;
  privateCandidate: PrivateCandidateInput;
}>;

export type ConversationalRectificationTransitionInput = CommandMutationIdentity & Readonly<{
  turn: ConversationalRectificationTurnInput;
  validationReceipt: ValidationReceiptInput;
}>;

export type ConfirmConversationalRectificationInput = CommandMutationIdentity & Readonly<{
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
  declaredBirthInput: DeepReadonly<DeclaredBirthInput>;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
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
    ...(value.declared_birth_input === undefined
      ? {} : { declaredBirthInput: value.declared_birth_input }),
    ...(value.private_candidate === undefined
      ? {} : { privateCandidate: value.private_candidate }),
    ...(value.event_evidence === undefined
      ? {} : { eventEvidence: value.event_evidence }),
    ...(value.validation_receipts === undefined
      ? {} : { validationReceipts: value.validation_receipts }),
  });
}

function requirePublicTurn(turn: ConversationalRectificationTurnInput): ConversationalRectificationTurn {
  const parsed = conversationalRectificationTurnSchema.safeParse(turn);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  return parsed.data;
}

/**
 * A new-event marker is only an explicit form of the legacy default. Older
 * databases reject that optional field and surface a misleading
 * action_conflict, so omit it at the durable boundary. The follow-up migration
 * remains required for event_date/event_detail turns.
 */
function turnForDurableContract(
  turn: ConversationalRectificationTurnInput,
): ConversationalRectificationTurn {
  const parsed = requirePublicTurn(turn);
  if (parsed.evidenceRequest?.followUp?.kind !== "new_event") return parsed;
  const evidenceRequest = { ...parsed.evidenceRequest };
  delete evidenceRequest.followUp;
  return { ...parsed, evidenceRequest };
}

function invalidDurableInput(): never {
  throw new ConversationalRectificationError("action_conflict");
}

function requireDeclaredBirthInput(input: DeepReadonly<DeclaredBirthInput>): DeclaredBirthInput {
  const parsed = declaredBirthInputSchema.safeParse(input);
  if (!parsed.success) return invalidDurableInput();
  return parsed.data;
}

function requirePrivateCandidate(input: PrivateCandidateInput): PrivateCandidate {
  const parsed = privateCandidateSchema.safeParse(input);
  if (!parsed.success) return invalidDurableInput();
  return parsed.data;
}

function requireValidationReceipt(input: ValidationReceiptInput): ValidationReceipt {
  const parsed = validationReceiptSchema.safeParse(input);
  if (!parsed.success) return invalidDurableInput();
  return parsed.data;
}

function requireEvidence(input: ReadonlyArray<LifeEventEvidenceInput>): ReadonlyArray<LifeEventEvidence> {
  const parsed = z.array(lifeEventEvidenceSchema).max(20).safeParse(input);
  if (!parsed.success) return invalidDurableInput();
  return parsed.data;
}

const mutationIdentitySchema = z.object({
  userId: z.string().uuid(),
  caseId: z.string().uuid(),
  expectedVersion: z.number().int().nonnegative(),
  actionId: z.string().uuid(),
}).strict();

const commandFingerprintSchema = z.string().regex(/^[0-9a-f]{64}$/);
const actionKindSchema = z.enum(["save_turn", "pause", "abandon", "confirm"]);

function mutationArgs(input: MutationIdentity): Readonly<Record<string, unknown>> {
  const parsed = mutationIdentitySchema.safeParse({
    userId: input.userId,
    caseId: input.caseId,
    expectedVersion: input.expectedVersion,
    actionId: input.actionId,
  });
  if (!parsed.success) return invalidDurableInput();
  return {
    p_user_id: parsed.data.userId,
    p_case_id: parsed.data.caseId,
    p_expected_version: parsed.data.expectedVersion,
    p_action_id: parsed.data.actionId,
  };
}

function commandFingerprint(input: CommandMutationIdentity): string {
  const parsed = commandFingerprintSchema.safeParse(input.commandFingerprint);
  if (!parsed.success) return invalidDurableInput();
  return parsed.data;
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
      if (error) {
        throw mapConversationalRectificationStoreError(error);
      }
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
      p_declared_birth_input: requireDeclaredBirthInput(input.declaredBirthInput),
      p_first_turn: turnForDurableContract(input.firstTurn),
      p_validation_receipt: requireValidationReceipt(input.validationReceipt),
      p_private_candidate: requirePrivateCandidate(input.privateCandidate),
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

  async loadActionReceipt(
    input: LoadConversationalRectificationActionReceiptInput,
  ): Promise<StoredConversationalRectificationCase | null> {
    const actionKind = actionKindSchema.safeParse(input.actionKind);
    if (!actionKind.success) return invalidDurableInput();
    return this.callCaseRpc("replay_conversational_rectification_action", {
      ...mutationArgs(input),
      p_action_kind: actionKind.data,
      p_command_fingerprint: commandFingerprint(input),
    }, true);
  }

  async saveTurn(
    input: SaveConversationalRectificationTurnInput,
  ): Promise<StoredConversationalRectificationCase> {
    const functionName = input.turn.status === "completed"
      ? "complete_conversational_rectification_with_range"
      : "save_conversational_rectification_turn";
    const result = await this.callCaseRpc(functionName, {
      ...mutationArgs(input),
      p_command_fingerprint: commandFingerprint(input),
      p_turn: turnForDurableContract(input.turn),
      p_evidence: requireEvidence(input.evidence),
      p_validation_receipt: requireValidationReceipt(input.validationReceipt),
      p_private_candidate: requirePrivateCandidate(input.privateCandidate),
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
    return this.requireTransition("abandon_conversational_rectification_without_result", input);
  }

  private async requireTransition(
    functionName: string,
    input: ConversationalRectificationTransitionInput,
  ): Promise<StoredConversationalRectificationCase> {
    const result = await this.callCaseRpc(functionName, {
      ...mutationArgs(input),
      p_command_fingerprint: commandFingerprint(input),
      p_turn: requirePublicTurn(input.turn),
      p_validation_receipt: requireValidationReceipt(input.validationReceipt),
    });
    if (!result) throw new ConversationalRectificationError("store_unavailable");
    return result;
  }

  async confirm(
    input: ConfirmConversationalRectificationInput,
  ): Promise<StoredConversationalRectificationCase> {
    const result = await this.callCaseRpc("confirm_conversational_rectification_candidate", {
      ...mutationArgs(input),
      p_command_fingerprint: commandFingerprint(input),
      p_result_id: input.resultId,
      p_time: input.time,
      p_calculation_version: input.calculationVersion,
      p_turn: requirePublicTurn(input.turn),
      p_validation_receipt: requireValidationReceipt(input.validationReceipt),
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
    if (!Number.isSafeInteger(input.price) || input.price < 1 || input.price > 1_000_000) {
      throw new ConversationalRectificationError("action_conflict");
    }
    const result = await this.callCaseRpc("import_legacy_conversational_rectification_case", {
      ...mutationArgs(input),
      p_legacy_case_id: input.legacyCaseId,
      p_price: input.price,
      p_pending_consultation_question: input.pendingConsultationQuestion,
      p_declared_birth_input: requireDeclaredBirthInput(input.declaredBirthInput),
      p_evidence: requireEvidence(input.evidence),
      p_first_turn: requirePublicTurn(input.firstTurn),
      p_validation_receipt: requireValidationReceipt(input.validationReceipt),
      p_private_candidate: requirePrivateCandidate(input.privateCandidate),
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
