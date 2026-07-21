import assert from "node:assert/strict";
import test from "node:test";
import {
  createOnboardingCacheIdentity,
  decideOnboardingCache,
  ONBOARDING_CLAIM_TTL_MS,
} from "../src/lib/onboarding-cache-policy.ts";

const profileA = {
  name: "林遥",
  birthDate: "1990-06-15",
  birthTime: "12:30",
  activeBirthTime: "12:30",
  birthTimeStatus: "confirmed",
  countryCode: "CN",
  provinceCode: "110000",
  cityCode: "110100",
} as const;

test("changed profile cannot reuse a ready cache from the previous profile", () => {
  // Given: profile A has a valid ready cache.
  const identityA = createOnboardingCacheIdentity(profileA);
  const identityB = createOnboardingCacheIdentity({ ...profileA, name: "周宁" });

  // When: profile B observes A's ready version.
  const decision = decideOnboardingCache({
    identity: identityB,
    observedVersion: identityA.readyVersion,
    generatedAtMs: Date.parse("2026-07-19T10:00:00.000Z"),
    nowMs: Date.parse("2026-07-19T10:00:01.000Z"),
    cachedPayload: {},
  });

  // Then: B must claim its own pending identity from the exact observed version.
  assert.deepEqual(decision, {
    kind: "claim",
    expectedVersion: identityA.readyVersion,
    pendingVersion: identityB.pendingVersion,
  });
  assert.notEqual(identityA.readyVersion, identityB.readyVersion);
  assert.doesNotMatch(identityB.readyVersion, /周宁|1990|12:30|110000/);
});

test("changed profile cannot wait on the previous profile's active pending claim", () => {
  // Given: profile A has a fresh pending claim.
  const identityA = createOnboardingCacheIdentity(profileA);
  const identityB = createOnboardingCacheIdentity({ ...profileA, activeBirthTime: "12:45" });

  // When: profile B observes A's pending version within the claim TTL.
  const decision = decideOnboardingCache({
    identity: identityB,
    observedVersion: identityA.pendingVersion,
    generatedAtMs: Date.parse("2026-07-19T10:00:00.000Z"),
    nowMs: Date.parse("2026-07-19T10:00:01.000Z"),
    cachedPayload: null,
  });

  // Then: B claims immediately instead of returning A's pending response.
  assert.deepEqual(decision, {
    kind: "claim",
    expectedVersion: identityA.pendingVersion,
    pendingVersion: identityB.pendingVersion,
  });
});

test("period-only declaration fields participate in the onboarding cache identity", () => {
  const earlyMorning = {
    ...profileA,
    birthTime: null,
    activeBirthTime: null,
    birthTimeStatus: "reported",
    reportedBirthTime: null,
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
    birthTimeClue: "凌晨或清晨",
    uncertaintyBeforeMinutes: null,
    uncertaintyAfterMinutes: null,
  };
  const morning = { ...earlyMorning, birthTimePeriod: "morning" };

  assert.notEqual(
    createOnboardingCacheIdentity(earlyMorning).readyVersion,
    createOnboardingCacheIdentity(morning).readyVersion,
  );
});

test("current profile accepts only valid ready content and an active current pending claim", () => {
  // Given: one current profile identity and a valid cached payload.
  const identity = createOnboardingCacheIdentity(profileA);
  const payload = { greeting: "current" };
  const nowMs = Date.parse("2026-07-19T10:01:00.000Z");

  // When/Then: exact ready and fresh pending identities retain their existing behavior.
  assert.deepEqual(decideOnboardingCache({
    identity,
    observedVersion: identity.readyVersion,
    generatedAtMs: nowMs - 60_000,
    nowMs,
    cachedPayload: payload,
  }), { kind: "ready", payload });
  assert.deepEqual(decideOnboardingCache({
    identity,
    observedVersion: identity.pendingVersion,
    generatedAtMs: nowMs - 60_000,
    nowMs,
    cachedPayload: null,
  }), { kind: "pending" });
});

test("invalid ready content and expired pending claims are reclaimed", () => {
  // Given: the current profile sees unusable ready content or an expired pending claim.
  const identity = createOnboardingCacheIdentity(profileA);
  const nowMs = Date.parse("2026-07-19T10:03:00.000Z");
  const observations = [
    {
      identity,
      observedVersion: identity.readyVersion,
      generatedAtMs: nowMs - 1_000,
      nowMs,
      cachedPayload: null,
    },
    {
      identity,
      observedVersion: identity.pendingVersion,
      generatedAtMs: nowMs - 180_000,
      nowMs,
      cachedPayload: null,
    },
  ] as const;

  // When/Then: each stale state becomes a compare-and-set claim for the current identity.
  for (const observation of observations) {
    assert.deepEqual(decideOnboardingCache(observation), {
      kind: "claim",
      expectedVersion: observation.observedVersion,
      pendingVersion: identity.pendingVersion,
    });
  }
});

test("every selected profile input participates in the cache identity", () => {
  // Given: the exact eight profile inputs used by onboarding generation/completeness.
  const baseIdentity = createOnboardingCacheIdentity(profileA);
  const mutations = [
    { field: "name", profile: { ...profileA, name: "周宁" } },
    { field: "birthDate", profile: { ...profileA, birthDate: "1991-06-15" } },
    { field: "birthTime", profile: { ...profileA, birthTime: "12:31" } },
    { field: "activeBirthTime", profile: { ...profileA, activeBirthTime: "12:45" } },
    { field: "birthTimeStatus", profile: { ...profileA, birthTimeStatus: "candidate" } },
    { field: "countryCode", profile: { ...profileA, countryCode: "TW" } },
    { field: "provinceCode", profile: { ...profileA, provinceCode: "310000" } },
    { field: "cityCode", profile: { ...profileA, cityCode: "310100" } },
  ] as const;

  // When/Then: mutating any one input changes both ready and pending identities.
  for (const mutation of mutations) {
    const changed = createOnboardingCacheIdentity(mutation.profile);
    assert.notEqual(changed.readyVersion, baseIdentity.readyVersion, mutation.field);
    assert.notEqual(changed.pendingVersion, baseIdentity.pendingVersion, mutation.field);
  }
});

test("pending claim TTL is active through TTL minus one and reclaimable at TTL", () => {
  // Given: the current profile owns the pending identity at a fixed time.
  const identity = createOnboardingCacheIdentity(profileA);
  const nowMs = Date.parse("2026-07-19T10:03:00.000Z");

  // When/Then: the exact boundary preserves the existing strict-less-than policy.
  assert.deepEqual(decideOnboardingCache({
    identity,
    observedVersion: identity.pendingVersion,
    generatedAtMs: nowMs - ONBOARDING_CLAIM_TTL_MS + 1,
    nowMs,
    cachedPayload: null,
  }), { kind: "pending" });
  assert.deepEqual(decideOnboardingCache({
    identity,
    observedVersion: identity.pendingVersion,
    generatedAtMs: nowMs - ONBOARDING_CLAIM_TTL_MS,
    nowMs,
    cachedPayload: null,
  }), {
    kind: "claim",
    expectedVersion: identity.pendingVersion,
    pendingVersion: identity.pendingVersion,
  });
});

test("pending claims with null or invalid generation timestamps are reclaimed", () => {
  // Given: null and invalid timestamps have both been normalized to non-finite milliseconds.
  const identity = createOnboardingCacheIdentity(profileA);
  const observations = [Number.NaN, Date.parse("not-a-timestamp")];

  // When/Then: neither timestamp can keep a pending claim active.
  for (const generatedAtMs of observations) {
    assert.deepEqual(decideOnboardingCache({
      identity,
      observedVersion: identity.pendingVersion,
      generatedAtMs,
      nowMs: Date.parse("2026-07-19T10:03:00.000Z"),
      cachedPayload: null,
    }), {
      kind: "claim",
      expectedVersion: identity.pendingVersion,
      pendingVersion: identity.pendingVersion,
    });
  }
});
