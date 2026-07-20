import { createHash } from "node:crypto";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationTurn,
} from "./contracts.ts";
import { ConversationalRectificationError } from "./errors.ts";
import { extractLifeEventEvidence } from "./evidence-extractor.ts";
import {
  declaredBirthInputSchema,
  privateCandidateSchema,
  validationReceiptSchema,
  type DeclaredBirthInput,
  type LifeEventEvidence,
  type PrivateCandidate,
  type ValidationReceipt,
} from "./persistence-contracts.ts";
import {
  generateRectificationNarrative,
  type RectificationNarrativeGenerator,
  type RectificationNarrativeResult,
} from "./narrative-agent.ts";
import {
  projectRectificationTechnicalPacket,
  type RectificationEvidenceDomain,
  type RectificationTechnicalPacket,
} from "./technical-packet.ts";
import type { ConversationalRectificationBilling } from "./billing.ts";
import type {
  ConversationalRectificationStore,
  LifeEventEvidenceInput,
  LoadedConversationalRectificationCase,
  PrivateCandidateInput,
  StoredConversationalRectificationCase,
} from "./store.ts";

type CommandOf<Type extends ConversationalRectificationCommand["type"]> = Extract<
  ConversationalRectificationCommand,
  { readonly type: Type }
>;

export type ComputedConversationalRectificationPacket = Readonly<{
  packet: RectificationTechnicalPacket;
  resultId: string | null;
}>;

export type ConversationalRectificationProfile = Readonly<{
  declaredBirthInput: unknown;
  revisionOfCaseId: string | null;
}>;

export type ConversationalRectificationPacketBuildInput = Readonly<{
  userId: string;
  caseId: string;
  asOfDate: string;
  declaredBirthInput: DeclaredBirthInput;
  privateCandidate: PrivateCandidateInput | null;
  evidence: ReadonlyArray<LifeEventEvidenceInput>;
}>;

export type ConversationalRectificationServicePorts = Readonly<{
  store: Pick<ConversationalRectificationStore,
    "createCaseWithFirstTurn" | "loadCase" | "loadActionReceipt" | "saveTurn" | "pause" | "abandon" | "confirm">;
  billing: Pick<ConversationalRectificationBilling, "reserve" | "complete" | "release">;
  rectificationPriceCredits: number;
  loadDeclaredProfile(userId: string): Promise<ConversationalRectificationProfile>;
  buildTechnicalPacket(
    input: ConversationalRectificationPacketBuildInput,
  ): Promise<ComputedConversationalRectificationPacket>;
  narrativeGenerator: RectificationNarrativeGenerator;
  asOfDate(): string;
}>;

export type ConversationalRectificationService = Readonly<{
  start(userId: string, command: CommandOf<"start">): Promise<ConversationalRectificationTurn>;
  resume(userId: string, command: CommandOf<"resume">): Promise<ConversationalRectificationTurn>;
  answer(userId: string, command: CommandOf<"answer">): Promise<ConversationalRectificationTurn>;
  pause(userId: string, command: CommandOf<"pause">): Promise<ConversationalRectificationTurn>;
  abandon(userId: string, command: CommandOf<"abandon">): Promise<ConversationalRectificationTurn>;
  confirm(userId: string, command: CommandOf<"confirm">): Promise<ConversationalRectificationTurn>;
}>;

const transitionValidatorVersion = "conversational-rectification-orchestrator-v1";
const explicitDirectionChangePattern = /(?:都不符合|都不是|不符合|换(?:个|一)?(?:方向|领域)|其他方向|别的方向|不想(?:谈|说|回答)|拒绝回答)/;
const genericUncertaintyPattern = /(?:不知道|不确定)/;

export function evidencePredatesBirthDate(
  evidence: Pick<LifeEventEvidence, "dateValue" | "datePrecision">,
  birthDate: string,
): boolean {
  if (!evidence.dateValue) return false;
  const boundary = evidence.datePrecision === "year"
    ? birthDate.slice(0, 4)
    : evidence.datePrecision === "month"
      ? birthDate.slice(0, 7)
      : evidence.datePrecision === "day"
        ? birthDate
        : null;
  return boundary !== null && evidence.dateValue < boundary;
}

function evidenceForDeclaredBirthDate(
  evidence: readonly LifeEventEvidence[],
  birthDate: string,
): readonly LifeEventEvidence[] {
  return evidence.map((item) => item.scoreable === true
    && evidencePredatesBirthDate(item, birthDate)
    ? { ...item, extractionStatus: "needs_clarification" as const, scoreable: false }
    : item);
}

function safeFailure(error: unknown): ConversationalRectificationError {
  return error instanceof ConversationalRectificationError
    ? error
    : new ConversationalRectificationError("service_unavailable");
}

function parseCommand<Type extends ConversationalRectificationCommand["type"]>(
  type: Type,
  value: unknown,
): CommandOf<Type> {
  const parsed = conversationalRectificationCommandSchema.safeParse(value);
  if (!parsed.success || parsed.data.type !== type) {
    throw new ConversationalRectificationError("invalid_command");
  }
  return parsed.data as CommandOf<Type>;
}

type MutableCommand = Extract<ConversationalRectificationCommand, {
  readonly type: "answer" | "pause" | "abandon" | "confirm";
}>;

function commandFingerprint(command: MutableCommand): string {
  const identity = command.type === "answer"
    ? [command.type, command.caseId, command.actionId, command.turnVersion,
        command.domain ?? null, command.answer]
    : command.type === "confirm"
      ? [command.type, command.caseId, command.actionId, command.turnVersion, command.time]
      : [command.type, command.caseId, command.actionId, command.turnVersion];
  return createHash("sha256").update(JSON.stringify(identity), "utf8").digest("hex");
}

function publicTurn(value: StoredConversationalRectificationCase): ConversationalRectificationTurn {
  const parsed = conversationalRectificationTurnSchema.safeParse(value.latestTurn);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  return parsed.data;
}

function transitionReceipt(modelId = "deterministic-rectification-transition"): ValidationReceipt {
  return validationReceiptSchema.parse({
    modelId,
    schemaValidated: true,
    validatorVersion: transitionValidatorVersion,
    retryCount: 0,
    fallbackUsed: false,
    issues: [],
  });
}

function latestReceipt(value: LoadedConversationalRectificationCase): ValidationReceipt {
  const receipt = value.validationReceipts.at(-1);
  const parsed = validationReceiptSchema.safeParse(receipt);
  if (!parsed.success) throw new ConversationalRectificationError("store_unavailable");
  return parsed.data;
}

function evidenceRecap(evidence: ReadonlyArray<LifeEventEvidenceInput>) {
  return evidence.slice(-20).map((item) => ({
    id: item.id,
    summary: item.eventSummary,
    dateLabel: item.dateValue
      ? item.scoreable === false && item.extractionStatus !== "needs_clarification"
        ? `${item.dateValue}（未来，仅作背景）`
        : item.dateValue
      : "日期待补充",
  }));
}

function exactTechnicalReceipt(packet: RectificationTechnicalPacket) {
  const projected = projectRectificationTechnicalPacket(packet);
  return {
    calculationVersion: projected.technicalReceipt.calculationVersion,
    stableLayers: projected.technicalReceipt.stableLayers,
    sensitiveLayers: projected.technicalReceipt.sensitiveLayers,
    candidateDifferenceRefs: projected.technicalReceipt.candidateDifferenceRefs,
  };
}

function actionsFor(status: "active" | "confirming") {
  if (status === "confirming") {
    return ["answer", "pause", "abandon", "confirm"] as const;
  }
  return ["answer", "pause", "abandon"] as const;
}

function turnFromNarrative(input: {
  readonly caseId: string;
  readonly turnVersion: number;
  readonly pendingConsultationQuestion: string | null;
  readonly packet: RectificationTechnicalPacket;
  readonly narrative: RectificationNarrativeResult;
  readonly evidence: ReadonlyArray<LifeEventEvidenceInput>;
}): ConversationalRectificationTurn {
  const projected = projectRectificationTechnicalPacket(input.packet);
  const status = projected.candidate.status === "ready_for_confirmation" ? "confirming" : "active";
  const evidenceRequest = input.narrative.output.evidenceRequest
    ? {
        domains: input.narrative.output.evidenceRequest.domains,
        datePrecision: input.narrative.output.evidenceRequest.datePrecision,
        freeTextAllowed: true as const,
      }
    : null;
  const candidate = {
    status: projected.candidate.status,
    representativeTime: projected.candidate.representativeTime,
    rangeStart: projected.candidate.rangeStart,
    rangeEnd: projected.candidate.rangeEnd,
  };
  const parsed = conversationalRectificationTurnSchema.safeParse({
    caseId: input.caseId,
    journeyProtocol: "conversational-evidence-v3",
    status,
    turnVersion: input.turnVersion,
    narrative: input.narrative.narrative,
    candidate,
    technicalReceipt: exactTechnicalReceipt(input.packet),
    evidenceRequest,
    evidenceRecap: evidenceRecap(input.evidence),
    actions: actionsFor(status),
    pendingConsultationQuestion: input.pendingConsultationQuestion,
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return parsed.data;
}

function privateCandidateFromPacket(input: {
  readonly packet: RectificationTechnicalPacket;
  readonly resultId: string | null;
  readonly iteration: number;
}): PrivateCandidate {
  const packet = input.packet;
  const parsed = privateCandidateSchema.safeParse({
    resultId: input.resultId,
    representativeTime: packet.candidate.representativeTime,
    rangeStart: packet.candidate.range.startTime,
    rangeEnd: packet.candidate.range.endTime,
    calculationVersion: packet.calculationVersion,
    candidateWeights: Object.entries(packet.candidateWeights)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([, weight]) => weight),
    candidateModelRefs: packet.candidateModelRefs,
    d1Stability: packet.d1Stability,
    boundaryDistanceMinutes: packet.boundaryDistanceMinutes,
    supportedSensitiveLayers: packet.supportedSensitiveLayers,
    scoredHistoricalEvidence: packet.scoredHistoricalEvidence,
    suggestedDomains: packet.suggestedDomains.map((item) => item.domain),
    futureWindows: packet.futureWindows,
    workingState: {
      phase: packet.candidate.status === "ready_for_confirmation" ? "ready" : "collecting_evidence",
      iteration: input.iteration,
      notes: [],
    },
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return parsed.data;
}

function changedTurn(input: {
  readonly current: LoadedConversationalRectificationCase;
  readonly status: "paused" | "abandoned" | "completed";
  readonly narrative: string;
  readonly receipt?: ValidationReceipt;
}): { readonly turn: ConversationalRectificationTurn; readonly receipt: ValidationReceipt } {
  const current = input.current.latestTurn;
  const actions = input.status === "paused"
    ? ["answer", "abandon"]
    : input.status === "completed" && current.pendingConsultationQuestion
      ? ["continue_original_question"]
      : [];
  const candidate = input.status === "completed"
    ? { ...current.candidate, status: "confirmed" as const }
    : current.candidate;
  const parsed = conversationalRectificationTurnSchema.safeParse({
    ...current,
    status: input.status,
    turnVersion: input.current.turnVersion + 1,
    narrative: input.narrative,
    candidate,
    evidenceRequest: input.status === "completed" ? null : current.evidenceRequest,
    actions,
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return { turn: parsed.data, receipt: input.receipt ?? transitionReceipt() };
}

function boundedNarrative(previous: string, suffix: string): string {
  const room = Math.max(1, 12_000 - suffix.length - 2);
  return `${previous.slice(0, room)}\n\n${suffix}`.slice(0, 12_000);
}

function domainsForClarification(
  current: ConversationalRectificationTurn,
  hint: RectificationEvidenceDomain | undefined,
): readonly RectificationEvidenceDomain[] {
  const values = [
    hint,
    ...(current.evidenceRequest?.domains ?? []),
    "career" as const,
    "relationship" as const,
  ].filter((value): value is RectificationEvidenceDomain => Boolean(value));
  return [...new Set(values)].slice(0, 4).length >= 2
    ? [...new Set(values)].slice(0, 4)
    : ["career", "relationship"];
}

function nonScoringTurn(input: {
  readonly current: LoadedConversationalRectificationCase;
  readonly newEvidence: ReadonlyArray<LifeEventEvidenceInput>;
  readonly domain?: RectificationEvidenceDomain;
  readonly directionChange: boolean;
  readonly scoringFallback?: boolean;
}): { readonly turn: ConversationalRectificationTurn; readonly receipt: ValidationReceipt } {
  const allEvidence = [...input.current.eventEvidence, ...input.newEvidence];
  const hasFuture = input.newEvidence.some((item) => item.extractionStatus !== "needs_clarification"
    && item.scoreable === false && item.dateValue !== null);
  const narrative = input.scoringFallback
    ? "本轮原文已安全保存，但新的专业解释未通过事实一致性校验，因此候选没有推进。请稍后重试，或继续补充一件已经发生并带有年月的事件。"
    : input.directionChange
      ? "好的，我们不沿用不符合你的方向。你可以自由描述另一件已经发生的生活变化，尽量写明年月；我会根据事实继续，而不是让你选择宽泛年份。"
      : hasFuture
        ? "已保存这段描述。未来事件只能作为背景，不能用于校正评分；请再说一件已经发生的事件，并尽量写明年月。"
        : "我已保存你的原话，但还缺少可用于区分候选的明确时间。请用自己的话补充这件已经发生的事大约是哪一年、哪一月；不需要选择固定答案。";
  const status = input.current.status === "confirming" ? "confirming" : "active";
  const actions = actionsFor(status);
  const evidenceRequest = status === "confirming" && input.current.latestTurn.evidenceRequest === null
    ? null
    : {
        domains: domainsForClarification(input.current.latestTurn, input.domain),
        datePrecision: "month_preferred" as const,
        freeTextAllowed: true as const,
      };
  const parsed = conversationalRectificationTurnSchema.safeParse({
    ...input.current.latestTurn,
    status,
    turnVersion: input.current.turnVersion + 1,
    narrative,
    evidenceRequest,
    evidenceRecap: evidenceRecap(allEvidence),
    actions,
  });
  if (!parsed.success) throw new ConversationalRectificationError("service_unavailable");
  return {
    turn: parsed.data,
    receipt: transitionReceipt(input.scoringFallback
      ? "deterministic-scoring-safety-fallback"
      : "deterministic-evidence-clarification"),
  };
}

function requireLoaded(
  value: LoadedConversationalRectificationCase | null,
): LoadedConversationalRectificationCase {
  if (!value) throw new ConversationalRectificationError("case_not_found");
  return value;
}

function requireExactVersion(current: LoadedConversationalRectificationCase, expected: number) {
  if (current.turnVersion !== expected) throw new ConversationalRectificationError("stale_turn");
}

function requireMutable(current: LoadedConversationalRectificationCase) {
  if (!(["active", "paused", "confirming"] as const).includes(
    current.status as "active" | "paused" | "confirming",
  )) {
    throw new ConversationalRectificationError("invalid_transition");
  }
}

export function createConversationalRectificationService(
  ports: ConversationalRectificationServicePorts,
): ConversationalRectificationService {
  async function load(userId: string, caseId: string) {
    try {
      return requireLoaded(await ports.store.loadCase({ userId, caseId }));
    } catch (error) {
      throw safeFailure(error);
    }
  }

  async function replayMutation(
    userId: string,
    command: MutableCommand,
    actionKind: "save_turn" | "pause" | "abandon" | "confirm",
    fingerprint: string,
  ): Promise<ConversationalRectificationTurn | null> {
    try {
      const receipt = await ports.store.loadActionReceipt({
        userId,
        caseId: command.caseId,
        expectedVersion: command.turnVersion,
        actionId: command.actionId,
        actionKind,
        commandFingerprint: fingerprint,
      });
      return receipt ? publicTurn(receipt) : null;
    } catch (error) {
      throw safeFailure(error);
    }
  }

  function extractedEvidence(command: CommandOf<"answer">): readonly LifeEventEvidence[] {
    let extracted: readonly LifeEventEvidence[];
    try {
      extracted = extractLifeEventEvidence({
        rawText: command.answer,
        sourceTurnId: command.actionId,
        asOfDate: ports.asOfDate(),
      }).map((item) => ({
        ...item,
        domain: item.domain === "other" && command.domain && command.domain !== "other"
          ? command.domain
          : item.domain,
      }));
    } catch {
      throw new ConversationalRectificationError("invalid_command");
    }
    if (extracted.length > 20) throw new ConversationalRectificationError("invalid_command");
    return extracted;
  }

  return Object.freeze({
    async start(userId, rawCommand) {
      const command = parseCommand("start", rawCommand);
      let profile: ConversationalRectificationProfile;
      try {
        profile = await ports.loadDeclaredProfile(userId);
      } catch (error) {
        throw safeFailure(error);
      }
      const declared = declaredBirthInputSchema.safeParse(profile.declaredBirthInput);
      if (!declared.success) throw new ConversationalRectificationError("profile_incomplete");

      let price: number;
      try {
        price = ports.rectificationPriceCredits;
      } catch {
        throw new ConversationalRectificationError("service_unavailable");
      }
      if (!Number.isSafeInteger(price) || price < 1 || price > 1_000_000) {
        throw new ConversationalRectificationError("service_unavailable");
      }

      const caseId = command.actionId;
      let existing: LoadedConversationalRectificationCase | null;
      try {
        existing = await ports.store.loadCase({ userId, caseId });
      } catch (error) {
        throw safeFailure(error);
      }
      if (existing) {
        if (existing.pendingConsultationQuestion !== (command.pendingConsultationQuestion ?? null)) {
          throw new ConversationalRectificationError("action_conflict");
        }
        if (existing.billingState === "reserved") {
          try {
            await ports.billing.complete({
              userId,
              caseId,
              expectedVersion: 0,
              actionId: command.actionId,
            });
          } catch (error) {
            try {
              await ports.billing.release({
                userId,
                caseId,
                expectedVersion: 0,
                actionId: command.actionId,
                price,
              });
            } catch {
              throw new ConversationalRectificationError("billing_failed");
            }
            throw safeFailure(error);
          }
        } else if (existing.billingState !== "charged"
          && existing.billingState !== "migration_waived") {
          throw new ConversationalRectificationError("billing_failed");
        }
        return publicTurn(existing);
      }

      let reserved = false;
      try {
        const reservation = await ports.billing.reserve({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
          price,
        });
        reserved = reservation.billingState === "reserved";
        const computed = await ports.buildTechnicalPacket({
          userId,
          caseId,
          asOfDate: ports.asOfDate(),
          declaredBirthInput: declared.data,
          privateCandidate: null,
          evidence: [],
        });
        const narrative = await generateRectificationNarrative({
          phase: "first",
          packet: computed.packet,
          generator: ports.narrativeGenerator,
        });
        const privateCandidate = privateCandidateFromPacket({
          packet: computed.packet,
          resultId: computed.resultId,
          iteration: 0,
        });
        const firstTurn = turnFromNarrative({
          caseId,
          turnVersion: 0,
          pendingConsultationQuestion: command.pendingConsultationQuestion ?? null,
          packet: computed.packet,
          narrative,
          evidence: [],
        });
        const created = await ports.store.createCaseWithFirstTurn({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
          revisionOfCaseId: profile.revisionOfCaseId,
          pendingConsultationQuestion: command.pendingConsultationQuestion ?? null,
          declaredBirthInput: declared.data,
          firstTurn,
          validationReceipt: narrative.validationReceipt,
          privateCandidate,
        });
        await ports.billing.complete({
          userId,
          caseId,
          expectedVersion: 0,
          actionId: command.actionId,
        });
        return publicTurn(created);
      } catch (error) {
        if (reserved) {
          try {
            await ports.billing.release({
              userId,
              caseId,
              expectedVersion: 0,
              actionId: command.actionId,
              price,
            });
          } catch {
            throw new ConversationalRectificationError("billing_failed");
          }
        }
        throw safeFailure(error);
      }
    },

    async resume(userId, rawCommand) {
      const command = parseCommand("resume", rawCommand);
      const current = await load(userId, command.caseId);
      return publicTurn(current);
    },

    async answer(userId, rawCommand) {
      const command = parseCommand("answer", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "save_turn", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      requireMutable(current);
      const evidence = evidenceForDeclaredBirthDate(
        extractedEvidence(command),
        current.declaredBirthInput.birthDate,
      );

      if (current.turnVersion === command.turnVersion + 1) {
        try {
          const replayed = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            evidence,
            validationReceipt: latestReceipt(current),
            privateCandidate: current.privateCandidate,
          });
          return publicTurn(replayed);
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);

      const scoreableEvidence = evidence.filter((item) => item.scoreable === true
        && item.extractionStatus !== "needs_clarification");
      const explicitDirectionChange = explicitDirectionChangePattern.test(command.answer);
      const directionChange = explicitDirectionChange
        || (scoreableEvidence.length === 0 && genericUncertaintyPattern.test(command.answer));
      if (directionChange || scoreableEvidence.length === 0) {
        const next = nonScoringTurn({
          current,
          newEvidence: evidence,
          domain: command.domain,
          directionChange,
        });
        try {
          const saved = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: next.turn,
            evidence,
            validationReceipt: next.receipt,
            privateCandidate: current.privateCandidate,
          });
          return publicTurn(saved);
        } catch (error) {
          throw safeFailure(error);
        }
      }

      try {
        const allScoreable = [...current.eventEvidence, ...evidence]
          .filter((item) => item.scoreable === true
            && item.extractionStatus !== "needs_clarification"
            && !evidencePredatesBirthDate(item, current.declaredBirthInput.birthDate));
        const computed = await ports.buildTechnicalPacket({
          userId,
          caseId: command.caseId,
          asOfDate: ports.asOfDate(),
          declaredBirthInput: current.declaredBirthInput,
          privateCandidate: current.privateCandidate,
          evidence: allScoreable,
        });
        const phase = computed.packet.candidate.status === "ready_for_confirmation"
          ? "final" as const
          : "intermediate" as const;
        const narrative = await generateRectificationNarrative({
          phase,
          packet: computed.packet,
          generator: ports.narrativeGenerator,
        });
        if (!narrative.allowEvidenceScoringAdvance) {
          const next = nonScoringTurn({
            current,
            newEvidence: evidence,
            domain: command.domain,
            directionChange: false,
            scoringFallback: true,
          });
          const saved = await ports.store.saveTurn({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: next.turn,
            evidence,
            validationReceipt: narrative.validationReceipt,
            privateCandidate: current.privateCandidate,
          });
          return publicTurn(saved);
        }
        const privateCandidate = privateCandidateFromPacket({
          packet: computed.packet,
          resultId: computed.resultId,
          iteration: (current.privateCandidate.workingState?.iteration ?? 0) + 1,
        });
        const turn = turnFromNarrative({
          caseId: command.caseId,
          turnVersion: command.turnVersion + 1,
          pendingConsultationQuestion: current.pendingConsultationQuestion,
          packet: computed.packet,
          narrative,
          evidence: [...current.eventEvidence, ...evidence],
        });
        const saved = await ports.store.saveTurn({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn,
          evidence,
          validationReceipt: narrative.validationReceipt,
          privateCandidate,
        });
        return publicTurn(saved);
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async pause(userId, rawCommand) {
      const command = parseCommand("pause", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "pause", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "paused") {
        try {
          const replayed = await ports.store.pause({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          });
          return publicTurn(replayed);
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      if (current.status !== "active" && current.status !== "confirming") {
        throw new ConversationalRectificationError("invalid_transition");
      }
      const next = changedTurn({
        current,
        status: "paused",
        narrative: boundedNarrative(current.latestTurn.narrative, "校正已暂停，现有证据和候选已保存；继续时不会重复扣点。"),
      });
      try {
        return publicTurn(await ports.store.pause({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async abandon(userId, rawCommand) {
      const command = parseCommand("abandon", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "abandon", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "abandoned") {
        try {
          return publicTurn(await ports.store.abandon({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          }));
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      requireMutable(current);
      const next = changedTurn({
        current,
        status: "abandoned",
        narrative: boundedNarrative(current.latestTurn.narrative, "本次校正已放弃；再次校正期间原有确认时间始终没有被替换。"),
      });
      try {
        return publicTurn(await ports.store.abandon({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },

    async confirm(userId, rawCommand) {
      const command = parseCommand("confirm", rawCommand);
      const fingerprint = commandFingerprint(command);
      const receipt = await replayMutation(userId, command, "confirm", fingerprint);
      if (receipt) return receipt;
      const current = await load(userId, command.caseId);
      if (current.turnVersion === command.turnVersion + 1 && current.status === "completed") {
        const resultId = current.privateCandidate.resultId;
        if (!resultId) throw new ConversationalRectificationError("candidate_changed");
        try {
          return publicTurn(await ports.store.confirm({
            userId,
            caseId: command.caseId,
            expectedVersion: command.turnVersion,
            actionId: command.actionId,
            commandFingerprint: fingerprint,
            resultId,
            time: command.time,
            calculationVersion: current.privateCandidate.calculationVersion,
            turn: current.latestTurn,
            validationReceipt: latestReceipt(current),
          }));
        } catch (error) {
          throw safeFailure(error);
        }
      }
      requireExactVersion(current, command.turnVersion);
      const resultId = current.privateCandidate.resultId;
      if (current.status !== "confirming"
        || current.latestTurn.candidate.status !== "ready_for_confirmation"
        || !resultId
        || current.privateCandidate.representativeTime !== command.time
        || current.latestTurn.candidate.representativeTime !== command.time) {
        throw new ConversationalRectificationError("candidate_changed");
      }
      const next = changedTurn({
        current,
        status: "completed",
        narrative: boundedNarrative(
          current.latestTurn.narrative,
          current.pendingConsultationQuestion
            ? "你已明确确认这个候选时间。现在可以使用新确认时间继续回答原问题。"
            : "你已明确确认这个候选时间，账户当前排盘时间已原子更新。",
        ),
      });
      try {
        return publicTurn(await ports.store.confirm({
          userId,
          caseId: command.caseId,
          expectedVersion: command.turnVersion,
          actionId: command.actionId,
          commandFingerprint: fingerprint,
          resultId,
          time: command.time,
          calculationVersion: current.privateCandidate.calculationVersion,
          turn: next.turn,
          validationReceipt: next.receipt,
        }));
      } catch (error) {
        throw safeFailure(error);
      }
    },
  });
}
