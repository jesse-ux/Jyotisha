"use client";

import { useEffect, useLayoutEffect, useState, useSyncExternalStore } from "react";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
  createConversationalRectificationActionRegistry,
  conversationalRectificationHistoryForTurn,
  sendConversationalRectificationCommand,
  type ConversationalRectificationActionIdentity,
} from "../lib/conversational-rectification/client.ts";
import type {
  ConversationalRectificationCommand,
  ConversationalRectificationTurn,
} from "../lib/conversational-rectification/contracts.ts";

type EvidenceDomain = NonNullable<
  ConversationalRectificationTurn["evidenceRequest"]
>["domains"][number];
type EvidenceRecapEntry = ConversationalRectificationTurn["evidenceRecap"][number];

export type ConversationalRectificationMessage = Readonly<{
  role: "assistant" | "user";
  text: string;
  renderKey: string;
}>;

export type ConversationalRectificationStoredMessage = Readonly<{
  role: "assistant" | "user";
  text: string;
}>;

function assistantText(turn: ConversationalRectificationTurn): string {
  return turn.narrative.trim();
}

function initialMessages(turn: ConversationalRectificationTurn | null): ConversationalRectificationMessage[] {
  if (!turn) return [];
  if (turn.evidenceRecap.length === 0) {
    return [{ role: "assistant", text: assistantText(turn), renderKey: `assistant-${turn.turnVersion}` }];
  }
  const latestEvidence = turn.evidenceRecap.at(-1);
  return [
    ...(latestEvidence ? [{
      role: "user" as const,
      text: `${latestEvidence.dateLabel} · ${latestEvidence.summary}${latestEvidence.isCorrection ? "（已修订）" : ""}`,
      renderKey: `user-${latestEvidence.id}`,
    }] : []),
    { role: "assistant", text: assistantText(turn), renderKey: `assistant-${turn.turnVersion}` },
  ];
}

function restoredMessages(
  turn: ConversationalRectificationTurn | null,
  messages?: readonly ConversationalRectificationStoredMessage[],
): ConversationalRectificationMessage[] {
  const durableMessages = messages?.length
    ? messages
    : turn
      ? conversationalRectificationHistoryForTurn(turn)
      : [];
  if (!durableMessages.length) return initialMessages(turn);
  return durableMessages.map((message, index) => ({
    ...message,
    renderKey: `persisted-${turn?.caseId ?? "unbound"}-${index}`,
  }));
}

export type ConversationalRectificationControllerSnapshot = Readonly<{
  turn: ConversationalRectificationTurn | null;
  messages?: readonly ConversationalRectificationMessage[];
  draft: string;
  selectedDomain: EvidenceDomain | null;
  correctionTarget: EvidenceRecapEntry | null;
  pending: boolean;
  error: string;
}>;

type MutationResult = Promise<ConversationalRectificationTurn | null>;

export type ConversationalRectificationController = ConversationalRectificationControllerSnapshot & Readonly<{
  getSnapshot(): ConversationalRectificationControllerSnapshot;
  subscribe(listener: () => void): () => void;
  synchronizeInitialTurn(
    turn: ConversationalRectificationTurn | null,
    messages?: readonly ConversationalRectificationStoredMessage[],
  ): void;
  setDraft(value: string): void;
  selectDomain(domain: EvidenceDomain | null): void;
  beginEvidenceCorrection(evidenceId: string): void;
  cancelEvidenceCorrection(): void;
  start(pendingConsultationQuestion?: string | null): MutationResult;
  resume(): MutationResult;
  answer(domain?: EvidenceDomain, answerOverride?: string): MutationResult;
  regenerate(): MutationResult;
  pause(): MutationResult;
  abandon(): MutationResult;
  confirm(time?: string): MutationResult;
}>;

type ControllerInput = Readonly<{
  initialTurn?: ConversationalRectificationTurn | null;
  initialMessages?: readonly ConversationalRectificationStoredMessage[];
  modelId?: string;
  getModelId?: () => string | undefined;
  send?: (command: ConversationalRectificationCommand) => Promise<ConversationalRectificationTurn>;
  createActionId?: () => string;
  onTurn?: (
    turn: ConversationalRectificationTurn,
    messages: readonly ConversationalRectificationMessage[],
  ) => void;
  onPendingChange?: (pending: boolean) => void;
}>;

type Mutation = Readonly<{
  identity: ConversationalRectificationActionIdentity;
  command(actionId: string): ConversationalRectificationCommand;
  clearDraftOnSuccess?: boolean;
  userMessage?: string;
  replaceLatestAssistant?: boolean;
}>;

type ActiveMutation = Readonly<{
  caseContext: number;
  token: symbol;
  promise: MutationResult;
}>;

function createLatestControllerInput(initial: ControllerInput) {
  let current = initial;
  return {
    update(next: ControllerInput) {
      current = next;
    },
    modelId() {
      return current.modelId;
    },
    send(command: ConversationalRectificationCommand) {
      return (current.send ?? sendConversationalRectificationCommand)(command);
    },
    onTurn(
      turn: ConversationalRectificationTurn,
      messages: readonly ConversationalRectificationMessage[],
    ) {
      current.onTurn?.(turn, messages);
    },
    onPendingChange(pending: boolean) {
      current.onPendingChange?.(pending);
    },
  };
}

function displayError(error: unknown): string {
  return error instanceof ConversationalRectificationRequestError
    ? error.message
    : CONVERSATIONAL_RECTIFICATION_UNAVAILABLE;
}

function staleTurn(error: unknown): boolean {
  return error instanceof ConversationalRectificationRequestError
    && error.status === 409
    && error.code === "stale_turn";
}

export function createConversationalRectificationController(
  input: ControllerInput = {},
): ConversationalRectificationController {
  const send = input.send ?? sendConversationalRectificationCommand;
  const selectedModelId = () => (input.getModelId?.() ?? input.modelId)?.trim() || undefined;
  const registry = createConversationalRectificationActionRegistry(input.createActionId);
  const listeners = new Set<() => void>();
  let snapshot: ConversationalRectificationControllerSnapshot = {
    turn: input.initialTurn ?? null,
    messages: restoredMessages(input.initialTurn ?? null, input.initialMessages),
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    error: "",
  };
  let activeMutation: ActiveMutation | null = null;
  let caseContext = 0;

  const publish = (next: ConversationalRectificationControllerSnapshot) => {
    snapshot = next;
    for (const listener of listeners) listener();
  };
  const patch = (next: Partial<ConversationalRectificationControllerSnapshot>) => {
    publish({ ...snapshot, ...next });
  };
  const setPending = (pending: boolean) => {
    if (snapshot.pending === pending) return;
    patch({ pending });
    try {
      input.onPendingChange?.(pending);
    } catch {
      // Parent locks are observational and cannot change durable mutation state.
    }
  };
  const acceptTurn = (
    turn: ConversationalRectificationTurn,
    clearDraft: boolean,
    expectedCaseContext: number,
    userMessage?: string,
    replaceLatestAssistant = false,
  ) => {
    const current = snapshot.turn;
    if (caseContext !== expectedCaseContext) return turn;
    const durableMessages = conversationalRectificationHistoryForTurn(turn);
    const restoredDurableMessages = durableMessages.length > 0
      ? restoredMessages(turn, durableMessages)
      : [];
    if (current?.caseId === turn.caseId && current.turnVersion > turn.turnVersion) return turn;
    if (current?.caseId === turn.caseId && current.turnVersion === turn.turnVersion) {
      const latestDurableAssistant = durableMessages.findLast((message) => message.role === "assistant");
      const repairsCurrentTranscript = restoredDurableMessages.length > (snapshot.messages?.length ?? 0)
        && latestDurableAssistant?.text.trim() === assistantText(current);
      if (!repairsCurrentTranscript) return turn;
      patch({
        messages: restoredDurableMessages,
        error: "",
        ...(clearDraft ? { draft: "" } : {}),
      });
      try {
        input.onTurn?.(current, restoredDurableMessages);
      } catch {
        // A consumer callback is observational. It must never turn a durable success into a failure.
      }
      return turn;
    }
    const selectedDomain = clearDraft
      ? null
      : snapshot.selectedDomain && turn.evidenceRequest?.domains.includes(snapshot.selectedDomain)
        ? snapshot.selectedDomain
        : null;
    const correctionTarget = clearDraft
      ? null
      : snapshot.correctionTarget
        ? turn.evidenceRecap.find((entry) => entry.id === snapshot.correctionTarget?.id) ?? null
        : null;
    const nextMessages = restoredDurableMessages.length > 0
      ? restoredDurableMessages
      : replaceLatestAssistant
      ? (() => {
          const messages = [...(snapshot.messages ?? [])];
          const lastAssistantIndex = messages.findLastIndex((message) => message.role === "assistant");
          const replacement = {
            role: "assistant" as const,
            text: assistantText(turn),
            renderKey: `assistant-${turn.turnVersion}`,
          };
          if (lastAssistantIndex < 0) return [...messages, replacement];
          messages[lastAssistantIndex] = replacement;
          return messages;
        })()
      : userMessage
      ? [
          ...(snapshot.messages ?? []),
          { role: "user" as const, text: userMessage, renderKey: `user-${turn.turnVersion}` },
          { role: "assistant" as const, text: assistantText(turn), renderKey: `assistant-${turn.turnVersion}` },
        ]
      : current === null || current.caseId !== turn.caseId
        ? initialMessages(turn)
        : snapshot.messages ?? [];
    patch({
      turn,
      messages: nextMessages,
      error: "",
      selectedDomain,
      correctionTarget,
      ...(clearDraft ? { draft: "" } : {}),
    });
    try {
      input.onTurn?.(turn, nextMessages);
    } catch {
      // A consumer callback is observational. It must never turn a durable success into a failure.
    }
    return turn;
  };
  const recoverLatest = async (turn: ConversationalRectificationTurn) => registry.run({
    caseId: turn.caseId,
    turnVersion: turn.turnVersion,
    operation: "resume",
    payload: {},
  }, (actionId) => send({
    type: "resume",
    caseId: turn.caseId,
    actionId,
    turnVersion: turn.turnVersion,
  }));
  const run = (mutation: Mutation): MutationResult => {
    if (activeMutation?.caseContext === caseContext) return activeMutation.promise;
    patch({ error: "" });
    setPending(true);
    const turnAtStart = snapshot.turn;
    const caseContextAtStart = caseContext;
    const mutationToken = Symbol("conversational-rectification-mutation");
    const ownsCurrentContext = () => caseContext === caseContextAtStart
      && activeMutation?.token === mutationToken;
    const operation = registry.run(
      mutation.identity,
      (actionId) => send(mutation.command(actionId)),
    ).then((turn) => acceptTurn(
      turn,
      mutation.clearDraftOnSuccess === true,
      caseContextAtStart,
      mutation.userMessage,
      mutation.replaceLatestAssistant === true,
    ))
      .catch(async (error: unknown) => {
        if (turnAtStart && staleTurn(error) && caseContext === caseContextAtStart) {
          try {
            const recovered = await recoverLatest(turnAtStart);
            return acceptTurn(recovered, false, caseContextAtStart);
          } catch (recoveryError) {
            if (ownsCurrentContext()) patch({ error: displayError(recoveryError) });
            throw recoveryError;
          }
        }
        if (ownsCurrentContext()) patch({ error: displayError(error) });
        throw error;
      })
      .finally(() => {
        if (activeMutation?.token !== mutationToken) return;
        activeMutation = null;
        if (caseContext === caseContextAtStart) setPending(false);
      });
    activeMutation = {
      caseContext: caseContextAtStart,
      token: mutationToken,
      promise: operation,
    };
    return operation;
  };
  const activeMutationForCurrentContext = () => (
    activeMutation?.caseContext === caseContext ? activeMutation.promise : null
  );
  const currentTurn = () => snapshot.turn;
  const currentMutation = (
    operation: Exclude<ConversationalRectificationCommand["type"], "start">,
    payload: unknown,
    command: (turn: ConversationalRectificationTurn, actionId: string) => ConversationalRectificationCommand,
    clearDraftOnSuccess = false,
    userMessage?: string,
    replaceLatestAssistant = false,
  ): MutationResult => {
    const turn = currentTurn();
    if (!turn) return Promise.resolve(null);
    return run({
      identity: {
        caseId: turn.caseId,
        turnVersion: turn.turnVersion,
        operation,
        payload,
      },
      command: (actionId) => command(turn, actionId),
      clearDraftOnSuccess,
      userMessage,
      replaceLatestAssistant,
    });
  };

  const controller = {
    get turn() { return snapshot.turn; },
    get messages() { return snapshot.messages; },
    get draft() { return snapshot.draft; },
    get selectedDomain() { return snapshot.selectedDomain; },
    get correctionTarget() { return snapshot.correctionTarget; },
    get pending() { return snapshot.pending; },
    get error() { return snapshot.error; },
    getSnapshot: () => snapshot,
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    synchronizeInitialTurn(
      turn: ConversationalRectificationTurn | null,
      messages?: readonly ConversationalRectificationStoredMessage[],
    ) {
      const current = snapshot.turn;
      if (turn === null) {
        if (current === null) return;
        caseContext += 1;
        activeMutation = null;
        try {
          input.onPendingChange?.(false);
        } catch {
          // Parent locks are observational.
        }
        patch({
          turn: null,
          messages: [],
          draft: "",
          selectedDomain: null,
          correctionTarget: null,
          pending: false,
          error: "",
        });
        return;
      }
      if (current === null || current.caseId !== turn.caseId) {
        caseContext += 1;
        activeMutation = null;
        try {
          input.onPendingChange?.(false);
        } catch {
          // Parent locks are observational.
        }
        patch({
          turn,
          messages: restoredMessages(turn, messages),
          draft: "",
          selectedDomain: null,
          correctionTarget: null,
          pending: false,
          error: "",
        });
        return;
      }
      if (turn.turnVersion <= current.turnVersion) {
        const restored = messages?.length ? restoredMessages(turn, messages) : [];
        if (turn.turnVersion === current.turnVersion
          && restored.length > (snapshot.messages?.length ?? 0)) {
          patch({ messages: restored });
        }
        return;
      }
      patch({
        turn,
        messages: [
          ...(snapshot.messages ?? []),
          { role: "assistant", text: assistantText(turn), renderKey: `assistant-${turn.turnVersion}` },
        ],
        error: "",
        selectedDomain: snapshot.selectedDomain
          && turn.evidenceRequest?.domains.includes(snapshot.selectedDomain)
          ? snapshot.selectedDomain
          : null,
        correctionTarget: snapshot.correctionTarget
          ? turn.evidenceRecap.find((entry) => entry.id === snapshot.correctionTarget?.id) ?? null
          : null,
      });
    },
    setDraft(value: string) {
      patch({ draft: value });
    },
    selectDomain(domain: EvidenceDomain | null) {
      patch({ selectedDomain: domain });
    },
    beginEvidenceCorrection(evidenceId: string) {
      const target = snapshot.turn?.evidenceRecap.find((entry) => entry.id === evidenceId);
      if (!target || !snapshot.turn?.actions.includes("answer")) return;
      patch({
        correctionTarget: target,
        // Keep the old fact visible in the correction banner, but out of the new raw evidence.
        // Otherwise its old date can make an appended replacement date look ambiguous.
        draft: "",
      });
    },
    cancelEvidenceCorrection() {
      patch({ correctionTarget: null, draft: "" });
    },
    start(pendingConsultationQuestion: string | null = null) {
      const modelId = selectedModelId();
      return run({
        identity: {
          caseId: "new-case",
          turnVersion: 0,
          operation: "start",
          payload: { pendingConsultationQuestion, ...(modelId ? { modelId } : {}) },
        },
        command: (actionId) => ({
          type: "start",
          actionId,
          pendingConsultationQuestion,
          ...(modelId ? { modelId } : {}),
        }),
      });
    },
    resume() {
      return currentMutation("resume", {}, (turn, actionId) => ({
        type: "resume",
        caseId: turn.caseId,
        actionId,
        turnVersion: turn.turnVersion,
      }));
    },
    answer(
      domain: EvidenceDomain | undefined = snapshot.selectedDomain ?? undefined,
      answerOverride?: string,
    ) {
      const turn = currentTurn();
      const answer = (answerOverride ?? snapshot.draft).trim();
      if (!turn || !answer || !turn.actions.includes("answer")) return Promise.resolve(turn);
      const correctsEvidenceId = snapshot.correctionTarget?.id;
      const modelId = selectedModelId();
      const payload = {
        answer,
        ...(modelId ? { modelId } : {}),
        ...(domain ? { domain } : {}),
        ...(correctsEvidenceId ? { correctsEvidenceId } : {}),
      };
      return currentMutation("answer", payload, (current, actionId) => ({
        type: "answer",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
        answer,
        ...(modelId ? { modelId } : {}),
        ...(domain ? { domain } : {}),
        ...(correctsEvidenceId ? { correctsEvidenceId } : {}),
      }), true, answer);
    },
    regenerate() {
      const turn = currentTurn();
      if (!turn?.actions.includes("answer")) {
        return activeMutationForCurrentContext() ?? Promise.resolve(turn);
      }
      const modelId = selectedModelId();
      return currentMutation("regenerate", modelId ? { modelId } : {}, (current, actionId) => ({
        type: "regenerate",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
        ...(modelId ? { modelId } : {}),
      }), false, undefined, true);
    },
    pause() {
      const turn = currentTurn();
      if (!turn?.actions.includes("pause")) {
        return activeMutationForCurrentContext() ?? Promise.resolve(turn);
      }
      return currentMutation("pause", {}, (current, actionId) => ({
        type: "pause",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
      }));
    },
    abandon() {
      const turn = currentTurn();
      if (!turn?.actions.includes("abandon")) {
        return activeMutationForCurrentContext() ?? Promise.resolve(turn);
      }
      return currentMutation("abandon", {}, (current, actionId) => ({
        type: "abandon",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
      }));
    },
    confirm(time?: string) {
      const turn = currentTurn();
      const candidateTime = time ?? turn?.candidate.representativeTime ?? null;
      if (!turn?.actions.includes("confirm") || turn.candidate.status !== "ready_for_confirmation"
        || !candidateTime) {
        return activeMutationForCurrentContext() ?? Promise.resolve(turn);
      }
      return currentMutation("confirm", { time: candidateTime }, (current, actionId) => ({
        type: "confirm",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
        time: candidateTime,
      }));
    },
  } satisfies ConversationalRectificationController;

  return controller;
}

export function useConversationalRectification(
  input: ControllerInput = {},
): ConversationalRectificationController {
  const [latestInput] = useState(() => createLatestControllerInput(input));
  const [controller] = useState(() => createConversationalRectificationController({
    initialTurn: input.initialTurn,
    initialMessages: input.initialMessages,
    createActionId: input.createActionId,
    getModelId: () => latestInput.modelId(),
    send: latestInput.send,
    onTurn: latestInput.onTurn,
    onPendingChange: latestInput.onPendingChange,
  }));
  const snapshot = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  );
  useLayoutEffect(() => {
    latestInput.update(input);
  }, [input, latestInput]);
  useEffect(() => {
    controller.synchronizeInitialTurn(input.initialTurn ?? null, input.initialMessages);
  }, [controller, input.initialMessages, input.initialTurn]);
  return { ...controller, ...snapshot };
}
