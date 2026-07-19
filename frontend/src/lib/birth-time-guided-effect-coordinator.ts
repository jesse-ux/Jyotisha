import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";

type StableActionIdentityInput = {
  readonly caseId: string;
  readonly turnVersion: number;
  readonly operation: string;
  readonly payload?: readonly string[];
};

export function stableActionIdentity(input: StableActionIdentityInput): string {
  return JSON.stringify([
    input.caseId,
    input.turnVersion,
    input.operation,
    ...(input.payload ?? []),
  ]);
}

export function createIdentityRequestCache<T>() {
  const requests = new Map<string, Promise<T>>();
  return {
    run(identity: string, load: () => Promise<T>): Promise<T> {
      const existing = requests.get(identity);
      if (existing) return existing;
      const request = load();
      requests.set(identity, request);
      void request.catch(() => {
        if (requests.get(identity) === request) requests.delete(identity);
      });
      return request;
    },
  };
}

export function createStableActionIdentityRegistry(
  createId: () => string = () => globalThis.crypto.randomUUID(),
) {
  const actionIds = new Map<string, string>();
  return {
    async run<T>(identity: string, operation: (actionId: string) => Promise<T>): Promise<T> {
      const actionId = actionIds.get(identity) ?? createId();
      actionIds.set(identity, actionId);
      const result = await operation(actionId);
      if (actionIds.get(identity) === actionId) actionIds.delete(identity);
      return result;
    },
  };
}

export type StableActionIdentityRegistry = ReturnType<typeof createStableActionIdentityRegistry>;

export function runStableJourneyAction<T>(
  registry: StableActionIdentityRegistry,
  identity: StableActionIdentityInput,
  operation: (actionId: string) => Promise<T>,
): Promise<T> {
  return registry.run(stableActionIdentity(identity), operation);
}

export function scheduleCancellableStart(start: () => void): () => void {
  const timer = globalThis.setTimeout(start, 0);
  return () => globalThis.clearTimeout(timer);
}

type PublishCurrentJourneyInput = {
  readonly expected: JourneyClientResponse;
  readonly current: JourneyClientResponse | null;
  readonly next: JourneyClientResponse;
  readonly publish: (journey: JourneyClientResponse) => void;
};

export function publishCurrentJourney(input: PublishCurrentJourneyInput): boolean {
  if (
    input.current?.caseId !== input.expected.caseId
    || input.current.turnVersion !== input.expected.turnVersion
  ) return false;
  input.publish(input.next);
  return true;
}

export function claimMutation(gate: { current: boolean }): (() => void) | null {
  if (gate.current) return null;
  gate.current = true;
  return () => { gate.current = false; };
}
