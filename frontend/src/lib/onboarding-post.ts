import {
  createOnboardingCacheIdentity,
  decideOnboardingCache,
} from "./onboarding-cache-policy.ts";
import {
  fallbackOnboardingPayload,
  type OnboardingPayload,
  parseOnboardingPayload,
  parseOnboardingText,
} from "./onboarding-payload.ts";
import {
  formatBirthDate,
  isDeclaredBirthProfileComplete,
  type BirthTimeSource,
  type BirthTimeStatus,
} from "./birth-time-intake-model.ts";

export type OnboardingProfileRow = {
  readonly id: string;
  readonly name: string | null;
  readonly birth_date: string | Date | null;
  readonly birth_time: string | null;
  readonly reported_birth_time: string | null;
  readonly active_birth_time: string | null;
  readonly birth_time_source: string | null;
  readonly birth_time_period: string | null;
  readonly birth_time_clue: string | null;
  readonly uncertainty_before_minutes: number | null;
  readonly uncertainty_after_minutes: number | null;
  readonly birth_time_status: string | null;
  readonly country_code: string | null;
  readonly province_code: string | null;
  readonly city_code: string | null;
  readonly latitude: number | null;
  readonly longitude: number | null;
  readonly timezone_offset: number | null;
  readonly birth_place_label: string | null;
  readonly timezone_id: string | null;
  readonly onboarding_payload: unknown;
  readonly onboarding_version: string | null;
  readonly onboarding_generated_at: string | null;
};

type RepositoryError = { readonly message: string };
type RepositoryResult<Value> = {
  readonly data: Value | null;
  readonly error: RepositoryError | null;
};

export type OnboardingClaimCommand = {
  readonly userId: string;
  readonly expectedVersion: string | null;
  readonly expectedGeneratedAt: string | null;
  readonly pendingVersion: string;
  readonly claimedAt: string;
};

export type OnboardingCompletionCommand = {
  readonly userId: string;
  readonly expectedPendingVersion: string;
  readonly readyVersion: string;
  readonly payload: OnboardingPayload;
  readonly generatedAt: string;
};

export interface OnboardingProfileRepository {
  loadProfile(userId: string): Promise<RepositoryResult<OnboardingProfileRow>>;
  claimProfile(command: OnboardingClaimCommand): Promise<RepositoryResult<{ readonly id: string }>>;
  completeProfile(command: OnboardingCompletionCommand): Promise<RepositoryResult<{ readonly id: string }>>;
}

type OnboardingSession = {
  readonly userId: string | null;
  readonly authError: boolean;
  readonly repository: OnboardingProfileRepository;
};

type OnboardingPostDependencies = {
  readonly openSession: () => Promise<OnboardingSession>;
  readonly generateText: (name: string, signal: AbortSignal) => Promise<string | null>;
  readonly generationTimeoutMs?: number;
  readonly now: () => Date;
  readonly warn: (message: string, detail: string) => void;
};

const DEFAULT_GENERATION_TIMEOUT_MS = 18_000;

function normalizeBirthDate(value: string | Date | null): string {
  return value instanceof Date ? formatBirthDate(value) : value ?? "";
}

function hasCompleteBirthProfile(profile: OnboardingProfileRow): boolean {
  const persistedTime = profile.active_birth_time || profile.birth_time || "";
  const knownSources: readonly BirthTimeSource[] = [
    "hospital_record", "family_exact", "approximate", "period_only", "unknown", "legacy_import",
  ];
  const source = knownSources.find((item) => item === profile.birth_time_source)
    ?? (persistedTime ? "legacy_import" : "");
  const knownStatuses: readonly BirthTimeStatus[] = [
    "reported", "assessing", "rectifying", "candidate", "confirmed",
  ];
  const status = knownStatuses.find((item) => item === profile.birth_time_status)
    ?? (persistedTime ? "confirmed" : "");
  const clock = (value: string | null) => value ? value.slice(0, 5) : "";
  const birthDraft = {
    date: normalizeBirthDate(profile.birth_date),
    time: clock(persistedTime),
    reportedTime: clock(profile.reported_birth_time)
      || (source === "legacy_import" ? clock(persistedTime) : ""),
    birthTimeSource: source,
    birthTimePeriod: profile.birth_time_period === "early_morning"
      || profile.birth_time_period === "morning"
      || profile.birth_time_period === "afternoon"
      || profile.birth_time_period === "evening"
      || profile.birth_time_period === "late_night"
      ? profile.birth_time_period
      : "",
    birthTimeClue: profile.birth_time_clue ?? "",
    uncertaintyBeforeMinutes: profile.uncertainty_before_minutes,
    uncertaintyAfterMinutes: profile.uncertainty_after_minutes,
    birthTimeStatus: status,
  } as const;
  const globalPlace = profile.birth_place_label && profile.timezone_id
    ? {
        label: profile.birth_place_label,
        lat: profile.latitude ?? Number.NaN,
        lon: profile.longitude ?? Number.NaN,
        tz: profile.timezone_offset,
        timezoneId: profile.timezone_id,
      }
    : null;
  const placeComplete = globalPlace
    ? isDeclaredBirthProfileComplete(birthDraft, globalPlace)
    : Boolean(profile.country_code && profile.province_code && profile.city_code);
  return Boolean(profile.name
    && placeComplete
    && isDeclaredBirthProfileComplete(birthDraft));
}

export function createOnboardingPost(dependencies: OnboardingPostDependencies): () => Promise<Response> {
  return async function onboardingPost(): Promise<Response> {
    let session: OnboardingSession;
    try {
      session = await dependencies.openSession();
    } catch { // no-excuse-ok: catch -- route boundary converts missing configuration.
      return Response.json(
        { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
        { status: 503 },
      );
    }

    if (session.authError || !session.userId) {
      return Response.json(
        { error: "请先登录", message: "登录后才能准备初始问题。" },
        { status: 401 },
      );
    }

    const loaded = await session.repository.loadProfile(session.userId);
    if (loaded.error || !loaded.data) {
      return Response.json(
        { error: "无法读取用户档案", message: loaded.error?.message || "请重新登录后再试。" },
        { status: 503 },
      );
    }
    const profile = loaded.data;
    if (!hasCompleteBirthProfile(profile)) {
      return Response.json(
        { error: "出生资料尚未完成", message: "请先填写称呼、出生日期、时间和地点。" },
        { status: 409 },
      );
    }

    const identity = createOnboardingCacheIdentity({
      name: profile.name,
      birthDate: normalizeBirthDate(profile.birth_date),
      birthTime: profile.birth_time,
      reportedBirthTime: profile.reported_birth_time,
      activeBirthTime: profile.active_birth_time,
      birthTimeSource: profile.birth_time_source,
      birthTimePeriod: profile.birth_time_period,
      birthTimeClue: profile.birth_time_clue,
      uncertaintyBeforeMinutes: profile.uncertainty_before_minutes,
      uncertaintyAfterMinutes: profile.uncertainty_after_minutes,
      birthTimeStatus: profile.birth_time_status,
      countryCode: profile.country_code,
      provinceCode: profile.province_code,
      cityCode: profile.city_code,
    });
    const cachedPayload = parseOnboardingPayload(profile.onboarding_payload);
    const generatedAtMs = profile.onboarding_generated_at === null
      ? Number.NaN
      : Date.parse(profile.onboarding_generated_at);
    const now = dependencies.now();
    const decision = decideOnboardingCache({
      identity,
      observedVersion: profile.onboarding_version,
      generatedAtMs,
      nowMs: now.getTime(),
      cachedPayload,
    });

    switch (decision.kind) {
      case "ready":
        return Response.json({ ...decision.payload, source: "cache" });
      case "pending":
        return Response.json({ ...fallbackOnboardingPayload, source: "pending" });
      case "claim":
        break;
      default: {
        const exhaustiveDecision: never = decision;
        throw exhaustiveDecision;
      }
    }

    const claim = await session.repository.claimProfile({
      userId: session.userId,
      expectedVersion: decision.expectedVersion,
      expectedGeneratedAt: profile.onboarding_generated_at,
      pendingVersion: decision.pendingVersion,
      claimedAt: now.toISOString(),
    });
    if (claim.error) {
      return Response.json(
        { error: "暂时无法准备初始问题", message: claim.error.message },
        { status: 503 },
      );
    }
    if (!claim.data) return Response.json({ ...fallbackOnboardingPayload, source: "pending" });

    let payload = fallbackOnboardingPayload;
    let source: "agent" | "fallback" = "fallback";
    const generationController = new AbortController();
    let generationTimer: ReturnType<typeof setTimeout> | undefined;
    try {
      const timeout = new Promise<null>((resolve) => {
        generationTimer = setTimeout(() => {
          resolve(null);
          generationController.abort(new DOMException("Onboarding generation timed out", "TimeoutError"));
        }, dependencies.generationTimeoutMs ?? DEFAULT_GENERATION_TIMEOUT_MS);
      });
      const text = await Promise.race([
        dependencies.generateText(profile.name ?? "", generationController.signal),
        timeout,
      ]);
      const parsed = text === null ? null : parseOnboardingText(text);
      if (parsed) {
        payload = parsed;
        source = "agent";
      }
    } catch (error) { // no-excuse-ok: catch -- generation failure intentionally uses safe fallback.
      dependencies.warn(
        "[onboarding] agent generation failed; using safe fallback",
        error instanceof Error ? error.message : "unknown error",
      );
    } finally {
      if (generationTimer !== undefined) clearTimeout(generationTimer);
    }

    const completed = await session.repository.completeProfile({
      userId: session.userId,
      expectedPendingVersion: identity.pendingVersion,
      readyVersion: identity.readyVersion,
      payload,
      generatedAt: dependencies.now().toISOString(),
    });
    if (completed.error) {
      dependencies.warn("[onboarding] unable to cache generated content", completed.error.message);
      return Response.json({ ...payload, source });
    }
    return completed.data
      ? Response.json({ ...payload, source })
      : Response.json({ ...fallbackOnboardingPayload, source: "pending" });
  };
}
