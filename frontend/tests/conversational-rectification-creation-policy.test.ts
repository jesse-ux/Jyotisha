import assert from "node:assert/strict";
import test from "node:test";
import {
  conversationalRectificationCreationPolicy,
} from "../src/lib/conversational-rectification/creation-policy.ts";

const deploymentSha = "0123456789abcdef0123456789abcdef01234567";
const smokeUser = "00000000-0000-4000-8000-000000009001";
const ordinaryUser = "00000000-0000-4000-8000-0000000090ab";

function policy(overrides: Partial<Parameters<typeof conversationalRectificationCreationPolicy>[0]> = {}) {
  return conversationalRectificationCreationPolicy({
    userId: ordinaryUser,
    creationEnabled: "true",
    migrationsReady: "true",
    deploymentSha,
    smokeSha: "",
    syntheticSmokeUserIds: smokeUser,
    ...overrides,
  });
}

test("creation pauses unless every base rollout gate is explicitly valid", () => {
  for (const overrides of [
    { creationEnabled: "false" },
    { creationEnabled: undefined },
    { migrationsReady: "false" },
    { migrationsReady: undefined },
    { deploymentSha: "deadbee" },
    { deploymentSha: deploymentSha.toUpperCase() },
  ]) {
    assert.deepEqual(policy(overrides), {
      audience: "paused",
      allowNewCaseCreation: false,
      smokeMatchesDeployment: false,
    });
  }
});

test("pending smoke admits only strictly allowlisted UUIDs and ignores malformed entries", () => {
  const allowlist = `bad,${smokeUser},${ordinaryUser.toUpperCase()},not-a-uuid`;
  assert.deepEqual(policy({ userId: smokeUser, syntheticSmokeUserIds: allowlist }), {
    audience: "smoke_only",
    allowNewCaseCreation: true,
    smokeMatchesDeployment: false,
  });
  assert.deepEqual(policy({ userId: ordinaryUser, syntheticSmokeUserIds: allowlist }), {
    audience: "smoke_only",
    allowNewCaseCreation: false,
    smokeMatchesDeployment: false,
  });
  assert.deepEqual(policy({ syntheticSmokeUserIds: "bad,not-a-uuid" }), {
    audience: "paused",
    allowNewCaseCreation: false,
    smokeMatchesDeployment: false,
  });
});

test("matching smoke SHA opens creation to every authenticated user", () => {
  assert.deepEqual(policy({
    userId: ordinaryUser,
    smokeSha: deploymentSha,
    syntheticSmokeUserIds: "",
  }), {
    audience: "public",
    allowNewCaseCreation: true,
    smokeMatchesDeployment: true,
  });
});
