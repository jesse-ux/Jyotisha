import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";

type PollResult =
  | { readonly kind: "completed"; readonly turn: JourneyClientResponse }
  | { readonly kind: "cancelled"; readonly turn: JourneyClientResponse }
  | { readonly kind: "exhausted"; readonly turn: JourneyClientResponse };

type PollInput = {
  readonly initial: JourneyClientResponse;
  readonly maxAttempts: number;
  readonly signal: AbortSignal;
  readonly poll: () => Promise<JourneyClientResponse>;
  readonly delay: (attempt: number, signal: AbortSignal) => Promise<void>;
};

function isPending(turn: JourneyClientResponse): boolean {
  return turn.nextAction.kind === "score_pending";
}

export async function runBirthTimeScoringPoll(input: PollInput): Promise<PollResult> {
  let latest = input.initial;
  for (let attempt = 0; attempt < input.maxAttempts; attempt += 1) {
    if (input.signal.aborted) return { kind: "cancelled", turn: latest };
    latest = await input.poll();
    if (input.signal.aborted) return { kind: "cancelled", turn: latest };
    if (!isPending(latest)) return { kind: "completed", turn: latest };
    if (attempt + 1 < input.maxAttempts) await input.delay(attempt, input.signal);
  }
  return input.signal.aborted
    ? { kind: "cancelled", turn: latest }
    : { kind: "exhausted", turn: latest };
}

export function scoringPollDelay(attempt: number, signal: AbortSignal): Promise<void> {
  const duration = Math.min(400 * (2 ** attempt), 3_200);
  return new Promise((resolve) => {
    const timer = window.setTimeout(resolve, duration);
    signal.addEventListener("abort", () => {
      window.clearTimeout(timer);
      resolve();
    }, { once: true });
  });
}
