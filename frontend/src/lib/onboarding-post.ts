import {
  createOnboardingCacheIdentity,
  createOnboardingCompletionTransition,
  decideOnboardingCache,
} from "./onboarding-cache-policy.ts";
import {
  fallbackOnboardingPayload,
  type OnboardingPayload,
  parseOnboardingPayload,
  parseOnboardingText,
} from "./onboarding-payload.ts";

export type OnboardingProfileRow = {
  readonly id: string;
  readonly name: string | null;
  readonly birth_date: string | null;
  readonly birth_time: string | null;
  readonly active_birth_time: string | null;
  readonly birth_time_status: string | null;
  readonly country_code: string | null;
  readonly province_code: string | null;
  readonly city_code: string | null;
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
  readonly generateText: (name: string) => Promise<string | null>;
  readonly now: () => Date;
  readonly warn: (message: string, detail: string) => void;
};

function hasCompleteBirthProfile(profile: OnboardingProfileRow): boolean {
  return Boolean(
    profile.name
    && profile.birth_date
    && (profile.active_birth_time || profile.birth_time)
    && (profile.birth_time_status === "confirmed"
      || profile.birth_time_status === "candidate"
      || (!profile.birth_time_status && profile.birth_time))
    && profile.country_code
    && profile.province_code
    && profile.city_code,
  );
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
      birthDate: profile.birth_date,
      birthTime: profile.birth_time,
      activeBirthTime: profile.active_birth_time,
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
    try {
      const text = await dependencies.generateText(profile.name ?? "");
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
    }

    const completion = createOnboardingCompletionTransition(identity);
    const completed = await session.repository.completeProfile({
      userId: session.userId,
      expectedPendingVersion: completion.expectedVersion,
      readyVersion: completion.readyVersion,
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
