import { z } from "zod";

const onboardingResponseSchema = z.object({
  greeting: z.string().transform((value) => value.replace(/\s+/g, " ").trim().slice(0, 180)).pipe(z.string().min(8)),
  suggestions: z.tuple([
    z.object({ theme: z.literal("career"), text: z.string().transform(normalizeSuggestion).pipe(z.string().min(1)) }),
    z.object({ theme: z.literal("marriage"), text: z.string().transform(normalizeSuggestion).pipe(z.string().min(1)) }),
    z.object({ theme: z.literal("timing"), text: z.string().transform(normalizeSuggestion).pipe(z.string().min(1)) }),
  ]),
  source: z.enum(["agent", "cache", "fallback", "pending"]),
});

const defaultPolicy = {
  requestTimeoutMs: 12_000,
  retryDelayMs: 4_000,
  maxAttempts: 3,
} as const;

type OnboardingRecoveryPolicy = {
  readonly requestTimeoutMs: number;
  readonly retryDelayMs: number;
  readonly maxAttempts: number;
};

type OnboardingAttemptResult =
  | { readonly kind: "response"; readonly response: Response; readonly payload: unknown }
  | { readonly kind: "timeout"; readonly error: unknown }
  | { readonly kind: "network"; readonly error: unknown }
  | { readonly kind: "invalid-response"; readonly error: unknown };

export type OnboardingSuggestion = {
  readonly theme: "career" | "marriage" | "timing";
  readonly text: string;
};

export type OnboardingContent = {
  readonly greeting: string;
  readonly suggestions: readonly OnboardingSuggestion[];
};

export class OnboardingAuthenticationError extends Error {
  readonly name = "OnboardingAuthenticationError";
  readonly status = 401;

  constructor() {
    super("登录后才能准备初始问题。");
  }
}

export class OnboardingRequestError extends Error {
  readonly name = "OnboardingRequestError";
  readonly reason: "http" | "invalid-response" | "timeout" | "network" | "pending";
  readonly status: number | null;

  constructor(
    reason: "http" | "invalid-response" | "timeout" | "network" | "pending",
    status: number | null = null,
    options?: ErrorOptions,
  ) {
    super("暂时无法准备初始问题", options);
    this.reason = reason;
    this.status = status;
  }
}

function normalizeSuggestion(value: string): string {
  return value.replace(/\s+/g, " ").trim().slice(0, 80);
}

function abortReason(signal: AbortSignal): unknown {
  return signal.reason ?? new DOMException("The operation was aborted", "AbortError");
}

function waitForRetry(delayMs: number, signal: AbortSignal): Promise<void> {
  signal.throwIfAborted();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", handleAbort);
      resolve();
    }, delayMs);
    function handleAbort() {
      clearTimeout(timer);
      reject(abortReason(signal));
    }
    signal.addEventListener("abort", handleAbort, { once: true });
  });
}

async function fetchAttempt(
  signal: AbortSignal,
  timeoutMs: number,
): Promise<OnboardingAttemptResult> {
  signal.throwIfAborted();
  const controller = new AbortController();
  let timedOut = false;
  let responseReceived = false;
  const handleAbort = () => controller.abort(abortReason(signal));
  signal.addEventListener("abort", handleAbort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort(new DOMException("The operation timed out", "TimeoutError"));
  }, timeoutMs);

  try {
    const response = await fetch("/api/onboarding", {
      method: "POST",
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) return { kind: "response", response, payload: null };
    responseReceived = true;
    const payload: unknown = await response.json();
    return { kind: "response", response, payload };
  } catch (error) {
    if (signal.aborted) throw abortReason(signal);
    if (timedOut) return { kind: "timeout", error };
    if (responseReceived) return { kind: "invalid-response", error };
    return { kind: "network", error };
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", handleAbort);
  }
}

export async function requestOnboardingWithRecovery(
  signal: AbortSignal,
  onSlow: () => void,
  policy: OnboardingRecoveryPolicy = defaultPolicy,
): Promise<OnboardingContent> {
  let slowReported = false;
  let lastError: OnboardingRequestError | null = null;

  for (let attempt = 1; attempt <= policy.maxAttempts; attempt += 1) {
    const result = await fetchAttempt(signal, policy.requestTimeoutMs);
    switch (result.kind) {
      case "timeout":
        if (!slowReported) {
          slowReported = true;
          onSlow();
        }
        lastError = new OnboardingRequestError("timeout", null, { cause: result.error });
        break;
      case "network":
        lastError = new OnboardingRequestError("network", null, { cause: result.error });
        break;
      case "invalid-response":
        throw new OnboardingRequestError("invalid-response", null, { cause: result.error });
      case "response": {
        if (result.response.status === 401) throw new OnboardingAuthenticationError();
        if (!result.response.ok) {
          lastError = new OnboardingRequestError("http", result.response.status);
          break;
        }
        const parsed = onboardingResponseSchema.safeParse(result.payload);
        if (!parsed.success) throw new OnboardingRequestError("invalid-response", null, { cause: parsed.error });
        if (parsed.data.source !== "pending") {
          return { greeting: parsed.data.greeting, suggestions: parsed.data.suggestions };
        }
        lastError = new OnboardingRequestError("pending");
        break;
      }
      default: {
        const exhaustiveResult: never = result;
        throw exhaustiveResult;
      }
    }

    if (attempt < policy.maxAttempts) await waitForRetry(policy.retryDelayMs, signal);
  }

  throw lastError ?? new OnboardingRequestError("pending");
}
