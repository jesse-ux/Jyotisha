import { z } from "zod";

type GreetingPeriod = "morning" | "noon" | "afternoon" | "evening" | "late-night";

const greetingVariants: Record<GreetingPeriod, readonly ((name: string) => string)[]> = {
  morning: [
    (name) => `早上好，${name}。今天最想先看什么？`,
    (name) => `${name}，早安。今天最该关注哪件事？`,
    (name) => `早上好，${name}。想从哪个问题开始？`,
  ],
  noon: [
    (name) => `中午好，${name}。现在最想理清哪件事？`,
    (name) => `${name}，中午好。什么问题最需要方向？`,
    (name) => `午间好，${name}。事业、关系或选择，想先聊哪个？`,
  ],
  afternoon: [
    (name) => `${name}，下午好。现在最想推进哪件事？`,
    (name) => `下午好，${name}。今天想先理清什么？`,
    (name) => `${name}，下午好。事业、关系或选择，想先聊哪个？`,
  ],
  evening: [
    (name) => `晚上好，${name}。今天最挂心的是哪件事？`,
    (name) => `${name}，晚上好。此刻最想聊哪件事？`,
    (name) => `晚上好，${name}。把心里的问题告诉我吧。`,
  ],
  "late-night": [
    (name) => `夜深了，${name}。此刻最想问什么？`,
    (name) => `${name}，还没休息吗？想从哪件事说起？`,
    (name) => `这么晚还醒着，${name}。直接说说最在意的问题吧。`,
  ],
};

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

type OnboardingProfileFingerprintInput = {
  readonly name: string;
  readonly date: string;
  readonly time: string;
  readonly reportedTime: string;
  readonly birthTimeSource: string;
  readonly birthTimePeriod: string;
  readonly birthTimeClue: string;
  readonly uncertaintyBeforeMinutes: number | null;
  readonly uncertaintyAfterMinutes: number | null;
  readonly birthTimeStatus: string;
  readonly rectificationCaseId: string;
  readonly countryCode: string;
  readonly provinceCode: string;
  readonly cityCode: string;
  readonly districtCode: string;
};

export type OnboardingSuggestion = {
  readonly theme: "career" | "marriage" | "timing";
  readonly text: string;
};

export type OnboardingContent = {
  readonly greeting: string;
  readonly suggestions: readonly OnboardingSuggestion[];
};

export function createStartGreeting(
  name: string,
  now = new Date(),
  variantSelection = Math.random(),
): string {
  const displayName = name.trim() || "你好";
  const hour = now.getHours();
  const period: GreetingPeriod = hour >= 5 && hour < 11
    ? "morning"
    : hour >= 11 && hour < 14
      ? "noon"
      : hour >= 14 && hour < 18
        ? "afternoon"
        : hour >= 18 && hour < 23 ? "evening" : "late-night";
  const variants = greetingVariants[period];
  return variants[Math.floor(variantSelection * variants.length)](displayName);
}

export function createOnboardingFallbackGreeting(name: string): string {
  return `${name.trim()}，从你此刻最关心的问题开始吧。`;
}

export function onboardingProfileFingerprint(profile: OnboardingProfileFingerprintInput): string {
  return JSON.stringify([
    profile.name,
    profile.date,
    profile.time,
    profile.reportedTime,
    profile.birthTimeSource,
    profile.birthTimePeriod,
    profile.birthTimeClue,
    profile.uncertaintyBeforeMinutes,
    profile.uncertaintyAfterMinutes,
    profile.birthTimeStatus,
    profile.rectificationCaseId,
    profile.countryCode,
    profile.provinceCode,
    profile.cityCode,
    profile.districtCode,
  ]);
}

export function onboardingRequestIdentity(accountId: string, profileFingerprint: string): string {
  return JSON.stringify([accountId, profileFingerprint]);
}

export function isCurrentOnboardingRequest(currentIdentity: string, completedIdentity: string): boolean {
  return currentIdentity.length > 0 && currentIdentity === completedIdentity;
}

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
