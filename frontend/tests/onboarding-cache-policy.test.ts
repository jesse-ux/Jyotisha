import assert from "node:assert/strict";
import test from "node:test";
import {
  createOnboardingCacheIdentity,
  createOnboardingCompletionTransition,
  decideOnboardingCache,
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

test("stale profile completion loses ownership after the current profile claims", () => {
  // Given: B has replaced A's pending identity in the row.
  const identityA = createOnboardingCacheIdentity(profileA);
  const identityB = createOnboardingCacheIdentity({ ...profileA, cityCode: "310100" });
  const rowVersionAfterBClaims = identityB.pendingVersion;

  // When: each completion prepares an exact compare-and-set transition.
  const completionA = createOnboardingCompletionTransition(identityA);
  const completionB = createOnboardingCompletionTransition(identityB);

  // Then: A cannot match the row, while B can commit its own ready identity.
  assert.notEqual(rowVersionAfterBClaims, completionA.expectedVersion);
  assert.equal(rowVersionAfterBClaims, completionB.expectedVersion);
  assert.equal(completionB.readyVersion, identityB.readyVersion);
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
