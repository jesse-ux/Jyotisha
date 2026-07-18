import {
  draftEvidencePrompt,
  fallbackQuestionCopy,
  guideQuestionResponseSchema,
  parseEvidenceDraftOutput,
  parseGuideQuestionOutput,
  parseJsonObject,
  renderQuestionPrompt,
  type BirthTimeGuideGenerator,
} from "./birth-time-guide-agent.ts";
import {
  bindDynamicQuestion,
  bindFallbackDynamicQuestion,
  generateDynamicQuestionPrompt,
  isRecoverableDynamicQuestionError,
  parseDynamicQuestionText,
} from "./birth-time-dynamic-question-validator.ts";
import { toPublicDynamicChoiceQuestion } from "./birth-time-dynamic-choice-internal.ts";
import type {
  CandidateDifferenceBuild,
  PersistedDynamicChoiceQuestion,
} from "./birth-time-dynamic-choice-internal.ts";
import type { DynamicNextAction } from "./birth-time-journey-turn-protocol.ts";
import type { EvidenceDraftProposal } from "./birth-time-evidence.ts";
import { currentJourneyTurn, storedJourneyResponse } from "./birth-time-journey-response.ts";
import type {
  StoredRectificationCase,
  VersionedJourneyResponse,
} from "./birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-turn-persistence.ts";
import { questionFromTurn } from "./birth-time-journey-transitions.ts";
type DraftRequest = {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly message: string;
};
export type DynamicQuestionGenerationCommand = {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly unmatchedNote: string | null;
};
export type DynamicQuestionGenerationCommit = {
  readonly nextAction: Extract<DynamicNextAction,
    { readonly kind: "ask_dynamic_choice" | "present_low_result" }
  >;
};
type GuideServicePorts = {
  readonly generator: BirthTimeGuideGenerator | null;
  readonly timeoutMs?: number;
  readonly loadCase: (
    userId: string,
    caseId: string,
  ) => Promise<StoredRectificationCase | null>;
  readonly proposeEvidenceDraft: (
    userId: string,
    caseId: string,
    actionId: string,
    turnVersion: number,
    proposal: EvidenceDraftProposal,
  ) => Promise<VersionedJourneyResponse>;
  readonly loadDynamicQuestionBuild?: (
    userId: string,
    command: DynamicQuestionGenerationCommand,
  ) => Promise<CandidateDifferenceBuild>;
  readonly commitDynamicQuestion?: (
    userId: string,
    command: DynamicQuestionGenerationCommand,
    question: PersistedDynamicChoiceQuestion | null,
    commit: DynamicQuestionGenerationCommit,
  ) => Promise<DynamicQuestionGenerationCommit>;
  readonly createDynamicId?: () => string;
};
export class BirthTimeGuideActionError extends Error {
  readonly name = "BirthTimeGuideActionError";
  readonly reason: "case_not_found" | "invalid_turn";

  constructor(reason: "case_not_found" | "invalid_turn") {
    super(`Birth-time guide action ${reason}`);
    this.reason = reason;
  }
}
class BirthTimeGuideTimeoutError extends Error {
  readonly name = "BirthTimeGuideTimeoutError";
}
async function generatedText(
  generator: BirthTimeGuideGenerator | null,
  prompt: string,
  timeoutMs: number,
): Promise<string | null> {
  if (!generator) return null;
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const timeout = new Promise<never>((_resolve, reject) => {
      timer = setTimeout(() => reject(new BirthTimeGuideTimeoutError()), timeoutMs);
    });
    const result = await Promise.race([generator.generate(prompt), timeout]);
    return result.text;
  } catch {
    return null;
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

function currentQuestion(stored: StoredRectificationCase) {
  const turn = currentJourneyTurn(stored);
  const question = questionFromTurn(turn);
  if (!question) throw new BirthTimeGuideActionError("invalid_turn");
  return { turn, question };
}

async function generatedQuestion(
  generator: BirthTimeGuideGenerator | null,
  prompt: string,
  question: Parameters<typeof parseGuideQuestionOutput>[1],
  timeoutMs: number,
): Promise<string | null> {
  const text = await generatedText(generator, prompt, timeoutMs);
  if (text === null) return null;
  try {
    return parseGuideQuestionOutput(parseJsonObject(text), question);
  } catch {
    return null;
  }
}

async function generatedProposal(
  generator: BirthTimeGuideGenerator | null,
  prompt: string,
  requiredDomain: Parameters<typeof parseEvidenceDraftOutput>[1]["requiredDomain"],
  sourceMessage: string,
  timeoutMs: number,
): Promise<EvidenceDraftProposal> {
  const text = await generatedText(generator, prompt, timeoutMs);
  if (text !== null) {
    try {
      const parsed = parseEvidenceDraftOutput(parseJsonObject(text), {
        requiredDomain,
        sourceMessage,
      });
      return { domain: parsed.domain, precision: parsed.precision, date: parsed.date };
    } catch {
      return { domain: requiredDomain, precision: null, date: null };
    }
  }
  return { domain: requiredDomain, precision: null, date: null };
}

export function createBirthTimeGuideService(ports: GuideServicePorts) {
  const timeoutMs = ports.timeoutMs ?? 8_000;

  return {
    async generateQuestion(userId: string, command: DynamicQuestionGenerationCommand) {
      if (!ports.loadDynamicQuestionBuild || !ports.commitDynamicQuestion) {
        throw new BirthTimeGuideActionError("invalid_turn");
      }
      const build = await ports.loadDynamicQuestionBuild(userId, command);
      if (build.packet.caseId !== command.caseId) {
        throw new BirthTimeGuideActionError("invalid_turn");
      }
      const createId = ports.createDynamicId ?? (() => globalThis.crypto.randomUUID());
      let question: PersistedDynamicChoiceQuestion | null = null;
      if (build.packet.opportunities.length > 0) {
        const prompt = generateDynamicQuestionPrompt(build.packet, command.unmatchedNote);
        for (let attempt = 0; attempt < 2 && question === null; attempt += 1) {
          const text = await generatedText(ports.generator, prompt, timeoutMs);
          if (text === null) continue;
          try {
            const output = parseDynamicQuestionText(text, build.packet);
            if (output.kind === "no_useful_question") break;
            question = bindDynamicQuestion(output, build, createId);
          } catch (error) {
            if (!isRecoverableDynamicQuestionError(error)) throw error;
          }
        }
        question ??= bindFallbackDynamicQuestion(build, createId);
      }
      const nextAction = question === null
        ? { kind: "present_low_result" as const, resultId: null }
        : { kind: "ask_dynamic_choice" as const, question: toPublicDynamicChoiceQuestion(question) };
      return ports.commitDynamicQuestion(userId, command, question, { nextAction });
    },

    async renderQuestion(userId: string, caseId: string) {
      const stored = await ports.loadCase(userId, caseId);
      if (!stored) throw new BirthTimeGuideActionError("case_not_found");
      const { turn, question } = currentQuestion(stored);
      const generated = await generatedQuestion(
        ports.generator,
        renderQuestionPrompt(),
        question,
        timeoutMs,
      );
      return guideQuestionResponseSchema.parse({
        type: "question",
        caseId,
        turnVersion: turn.turnVersion,
        questionId: question.questionId,
        question: generated ?? fallbackQuestionCopy(question),
        source: generated === null ? "fallback" : "agent",
      });
    },

    async draftEvidence(userId: string, request: DraftRequest) {
      const stored = await ports.loadCase(userId, request.caseId);
      if (!stored) throw new BirthTimeGuideActionError("case_not_found");
      const receipt = request.actionId.toLowerCase();
      if (stored.processedActionIds?.includes(receipt)) {
        return {
          type: "evidence_draft" as const,
          actionId: request.actionId,
          requestedTurnVersion: request.turnVersion,
          turn: storedJourneyResponse(stored),
        };
      }
      const current = currentJourneyTurn(stored);
      if (current.turnVersion !== request.turnVersion) {
        throw new StaleJourneyTurnError(
          request.caseId,
          request.turnVersion,
          current.turnVersion,
        );
      }
      const question = questionFromTurn(current);
      if (!question) throw new BirthTimeGuideActionError("invalid_turn");
      const proposal = await generatedProposal(
        ports.generator,
        draftEvidencePrompt(question, request.message),
        question.domain,
        request.message,
        timeoutMs,
      );
      const turn = await ports.proposeEvidenceDraft(
        userId,
        request.caseId,
        request.actionId,
        request.turnVersion,
        proposal,
      );
      return {
        type: "evidence_draft" as const,
        actionId: request.actionId,
        requestedTurnVersion: request.turnVersion,
        turn,
      };
    },
  };
}
