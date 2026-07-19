import { createHash } from "node:crypto";

const ONBOARDING_VERSION = "ayanam-onboarding-v3";
export const ONBOARDING_CLAIM_TTL_MS = 2 * 60 * 1000;

type OnboardingProfileInput = {
  readonly name: string | null;
  readonly birthDate: string | null;
  readonly birthTime: string | null;
  readonly activeBirthTime: string | null;
  readonly birthTimeStatus: string | null;
  readonly countryCode: string | null;
  readonly provinceCode: string | null;
  readonly cityCode: string | null;
};

export type OnboardingCacheIdentity = {
  readonly readyVersion: string;
  readonly pendingVersion: string;
};

type OnboardingCacheObservation<Payload> = {
  readonly identity: OnboardingCacheIdentity;
  readonly observedVersion: string | null;
  readonly generatedAtMs: number;
  readonly nowMs: number;
  readonly cachedPayload: Payload | null;
};

type OnboardingCacheDecision<Payload> =
  | { readonly kind: "ready"; readonly payload: Payload }
  | { readonly kind: "pending" }
  | {
    readonly kind: "claim";
    readonly expectedVersion: string | null;
    readonly pendingVersion: string;
  };

export function createOnboardingCacheIdentity(
  profile: OnboardingProfileInput,
): OnboardingCacheIdentity {
  const fingerprint = createHash("sha256")
    .update(JSON.stringify([
      profile.name,
      profile.birthDate,
      profile.birthTime,
      profile.activeBirthTime,
      profile.birthTimeStatus,
      profile.countryCode,
      profile.provinceCode,
      profile.cityCode,
    ]))
    .digest("hex");

  return {
    readyVersion: `${ONBOARDING_VERSION}:${fingerprint}`,
    pendingVersion: `${ONBOARDING_VERSION}:pending:${fingerprint}`,
  };
}

export function decideOnboardingCache<Payload>(
  observation: OnboardingCacheObservation<Payload>,
): OnboardingCacheDecision<Payload> {
  if (observation.observedVersion === observation.identity.readyVersion
    && observation.cachedPayload !== null) {
    return { kind: "ready", payload: observation.cachedPayload };
  }

  if (observation.observedVersion === observation.identity.pendingVersion
    && Number.isFinite(observation.generatedAtMs)
    && observation.nowMs - observation.generatedAtMs < ONBOARDING_CLAIM_TTL_MS) {
    return { kind: "pending" };
  }

  return {
    kind: "claim",
    expectedVersion: observation.observedVersion,
    pendingVersion: observation.identity.pendingVersion,
  };
}
