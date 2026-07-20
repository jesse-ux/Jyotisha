"use client";

import { useState, useSyncExternalStore } from "react";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
  createConversationalRectificationActionRegistry,
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

export type ConversationalRectificationControllerSnapshot = Readonly<{
  turn: ConversationalRectificationTurn | null;
  draft: string;
  selectedDomain: EvidenceDomain | null;
  pending: boolean;
  error: string;
}>;

type MutationResult = Promise<ConversationalRectificationTurn | null>;

export type ConversationalRectificationController = ConversationalRectificationControllerSnapshot & Readonly<{
  getSnapshot(): ConversationalRectificationControllerSnapshot;
  subscribe(listener: () => void): () => void;
  setDraft(value: string): void;
  selectDomain(domain: EvidenceDomain | null): void;
  start(pendingConsultationQuestion?: string | null): MutationResult;
  resume(): MutationResult;
  answer(domain?: EvidenceDomain): MutationResult;
  pause(): MutationResult;
  abandon(): MutationResult;
  confirm(time?: string): MutationResult;
}>;

type ControllerInput = Readonly<{
  initialTurn?: ConversationalRectificationTurn | null;
  send?: (command: ConversationalRectificationCommand) => Promise<ConversationalRectificationTurn>;
  createActionId?: () => string;
  onTurn?: (turn: ConversationalRectificationTurn) => void;
}>;

type Mutation = Readonly<{
  identity: ConversationalRectificationActionIdentity;
  command(actionId: string): ConversationalRectificationCommand;
  clearDraftOnSuccess?: boolean;
}>;

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
  const registry = createConversationalRectificationActionRegistry(input.createActionId);
  const listeners = new Set<() => void>();
  let snapshot: ConversationalRectificationControllerSnapshot = {
    turn: input.initialTurn ?? null,
    draft: "",
    selectedDomain: null,
    pending: false,
    error: "",
  };
  let activeMutation: MutationResult | null = null;

  const publish = (next: ConversationalRectificationControllerSnapshot) => {
    snapshot = next;
    for (const listener of listeners) listener();
  };
  const patch = (next: Partial<ConversationalRectificationControllerSnapshot>) => {
    publish({ ...snapshot, ...next });
  };
  const acceptTurn = (
    turn: ConversationalRectificationTurn,
    clearDraft: boolean,
  ) => {
    patch({
      turn,
      error: "",
      ...(clearDraft ? { draft: "", selectedDomain: null } : {}),
    });
    input.onTurn?.(turn);
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
    if (activeMutation) return activeMutation;
    patch({ pending: true, error: "" });
    const turnAtStart = snapshot.turn;
    const operation = registry.run(
      mutation.identity,
      (actionId) => send(mutation.command(actionId)),
    ).then((turn) => acceptTurn(turn, mutation.clearDraftOnSuccess === true))
      .catch(async (error: unknown) => {
        if (turnAtStart && staleTurn(error)) {
          try {
            const recovered = await recoverLatest(turnAtStart);
            return acceptTurn(recovered, false);
          } catch (recoveryError) {
            patch({ error: displayError(recoveryError) });
            throw recoveryError;
          }
        }
        patch({ error: displayError(error) });
        throw error;
      })
      .finally(() => {
        activeMutation = null;
        patch({ pending: false });
      });
    activeMutation = operation;
    return operation;
  };
  const currentTurn = () => snapshot.turn;
  const currentMutation = (
    operation: Exclude<ConversationalRectificationCommand["type"], "start">,
    payload: unknown,
    command: (turn: ConversationalRectificationTurn, actionId: string) => ConversationalRectificationCommand,
    clearDraftOnSuccess = false,
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
    });
  };

  const controller = {
    get turn() { return snapshot.turn; },
    get draft() { return snapshot.draft; },
    get selectedDomain() { return snapshot.selectedDomain; },
    get pending() { return snapshot.pending; },
    get error() { return snapshot.error; },
    getSnapshot: () => snapshot,
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setDraft(value: string) {
      patch({ draft: value });
    },
    selectDomain(domain: EvidenceDomain | null) {
      patch({ selectedDomain: domain });
    },
    start(pendingConsultationQuestion: string | null = null) {
      return run({
        identity: {
          caseId: "new-case",
          turnVersion: 0,
          operation: "start",
          payload: { pendingConsultationQuestion },
        },
        command: (actionId) => ({ type: "start", actionId, pendingConsultationQuestion }),
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
    answer(domain: EvidenceDomain | undefined = snapshot.selectedDomain ?? undefined) {
      const turn = currentTurn();
      const answer = snapshot.draft.trim();
      if (!turn || !answer || !turn.actions.includes("answer")) return Promise.resolve(turn);
      const payload = { answer, ...(domain ? { domain } : {}) };
      return currentMutation("answer", payload, (current, actionId) => ({
        type: "answer",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
        answer,
        ...(domain ? { domain } : {}),
      }), true);
    },
    pause() {
      const turn = currentTurn();
      if (!turn?.actions.includes("pause")) return activeMutation ?? Promise.resolve(turn);
      return currentMutation("pause", {}, (current, actionId) => ({
        type: "pause",
        caseId: current.caseId,
        actionId,
        turnVersion: current.turnVersion,
      }));
    },
    abandon() {
      const turn = currentTurn();
      if (!turn?.actions.includes("abandon")) return activeMutation ?? Promise.resolve(turn);
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
        || !candidateTime) return activeMutation ?? Promise.resolve(turn);
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
  const [controller] = useState(() => createConversationalRectificationController(input));
  const snapshot = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  );
  return { ...controller, ...snapshot };
}
