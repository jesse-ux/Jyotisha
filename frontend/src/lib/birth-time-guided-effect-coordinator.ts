import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";

export function createIdentityRequestCache<T>() {
  const requests = new Map<string, Promise<T>>();
  return {
    run(identity: string, load: () => Promise<T>): Promise<T> {
      const existing = requests.get(identity);
      if (existing) return existing;
      const request = load();
      requests.set(identity, request);
      return request;
    },
  };
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
