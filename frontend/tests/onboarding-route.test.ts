import assert from "node:assert/strict";
import test from "node:test";
import { z } from "zod";
import { createOnboardingCacheIdentity } from "../src/lib/onboarding-cache-policy.ts";
import { createOnboardingPost } from "../src/lib/onboarding-post.ts";
import {
  completeProfileRow,
  StatefulOnboardingProfileRepository,
} from "./onboarding-route-fake.ts";

const payloadA = {
  greeting: "林遥，欢迎开始今天的咨询。",
  suggestions: [
    { theme: "career", text: "林遥的事业方向是什么？" },
    { theme: "marriage", text: "林遥的关系模式是什么？" },
    { theme: "timing", text: "林遥何时适合采取行动？" },
  ],
} as const;

const payloadB = {
  greeting: "周宁，欢迎开始今天的咨询。",
  suggestions: [
    { theme: "career", text: "周宁的事业方向是什么？" },
    { theme: "marriage", text: "周宁的关系模式是什么？" },
    { theme: "timing", text: "周宁何时适合采取行动？" },
  ],
} as const;

function generatedText(payload: typeof payloadA | typeof payloadB): string {
  return JSON.stringify(payload);
}

function deferred<Value>() {
  let settle: (value: Value) => void = () => undefined;
  const promise = new Promise<Value>((resolve) => {
    settle = resolve;
  });
  return { promise, resolve: settle } as const;
}

const responseBodySchema = z.object({
  greeting: z.string(),
  suggestions: z.array(z.object({ theme: z.string(), text: z.string() })),
  source: z.enum(["agent", "cache", "fallback", "pending"]),
});

async function responseBody(response: Response): Promise<z.infer<typeof responseBodySchema>> {
  return responseBodySchema.parse(await response.json());
}

function createPost(
  repository: StatefulOnboardingProfileRepository,
  generateText: (name: string) => Promise<string | null>,
) {
  return createOnboardingPost({
    openSession: async () => ({
      userId: repository.snapshot().id,
      authError: false,
      repository,
    }),
    generateText,
    now: () => new Date("2026-07-19T10:00:00.000Z"),
    warn: () => undefined,
  });
}

test("stale A generation returns pending after profile B replaces its claim", async () => {
  // Given: A owns a claim whose generation remains in flight.
  const repository = new StatefulOnboardingProfileRepository(completeProfileRow());
  const generationA = deferred<string | null>();
  const generationAStarted = deferred<void>();
  const post = createPost(
    repository,
    async (name) => {
      if (name === "林遥") {
        generationAStarted.resolve();
        return generationA.promise;
      }
      return generatedText(payloadB);
    },
  );
  const responseA = post();
  await generationAStarted.promise;

  // When: the persisted profile changes to B, B claims/completes, then A finishes.
  repository.setProfile({ name: "周宁" });
  const bodyB = await responseBody(await post());
  generationA.resolve(generatedText(payloadA));
  const bodyA = await responseBody(await responseA);

  // Then: B remains cached and A is provisional, never a stale terminal payload.
  assert.deepEqual(bodyB, { ...payloadB, source: "agent" });
  assert.equal(bodyA.source, "pending");
  assert.doesNotMatch(JSON.stringify(bodyA), /林遥/);
  assert.deepEqual(repository.snapshot().onboarding_payload, payloadB);
});

test("profile B replaces profile A ready cache instead of returning A content", async () => {
  // Given: A has a ready cache, then the persisted profile changes to B.
  const identityA = createOnboardingCacheIdentity({
    name: "林遥", birthDate: "1990-06-15", birthTime: "12:30", activeBirthTime: "12:30",
    birthTimeStatus: "confirmed", countryCode: "CN", provinceCode: "110000", cityCode: "110100",
  });
  const repository = new StatefulOnboardingProfileRepository(completeProfileRow({
    onboarding_payload: payloadA,
    onboarding_version: identityA.readyVersion,
    onboarding_generated_at: "2026-07-19T09:59:00.000Z",
  }));
  repository.setProfile({ name: "周宁" });
  const post = createPost(repository, async () => generatedText(payloadB));

  // When: B requests onboarding through the real handler seam.
  const body = await responseBody(await post());

  // Then: B is generated and cached; A's ready payload is never returned.
  assert.deepEqual(body, { ...payloadB, source: "agent" });
  assert.deepEqual(repository.snapshot().onboarding_payload, payloadB);
});

test("profile B replaces profile A active pending claim instead of waiting on A", async () => {
  // Given: A has a fresh pending claim, then B changes the active birth time.
  const profile = completeProfileRow();
  const identityA = createOnboardingCacheIdentity({
    name: profile.name, birthDate: profile.birth_date, birthTime: profile.birth_time,
    activeBirthTime: profile.active_birth_time, birthTimeStatus: profile.birth_time_status,
    countryCode: profile.country_code, provinceCode: profile.province_code, cityCode: profile.city_code,
  });
  const repository = new StatefulOnboardingProfileRepository({
    ...profile,
    onboarding_version: identityA.pendingVersion,
    onboarding_generated_at: "2026-07-19T09:59:30.000Z",
  });
  repository.setProfile({ name: "周宁", active_birth_time: "12:45" });
  let generatedFor = "";
  const post = createPost(repository, async (name) => {
    generatedFor = name;
    return generatedText(payloadB);
  });

  // When: B requests onboarding within A's TTL.
  const body = await responseBody(await post());

  // Then: B claims and completes immediately rather than receiving pending for A.
  assert.equal(generatedFor, "周宁");
  assert.deepEqual(body, { ...payloadB, source: "agent" });
});

for (const interference of [
  { name: "observed version", patch: { onboarding_version: "concurrent-version" } },
  { name: "observed timestamp", patch: { onboarding_generated_at: "2026-07-19T09:58:00.000Z" } },
] as const) {
  test(`claim loses when a concurrent writer changes the ${interference.name}`, async () => {
    // Given: another writer changes one observed CAS field just before the claim.
    const repository = new StatefulOnboardingProfileRepository(completeProfileRow({
      onboarding_version: "legacy-ready",
      onboarding_generated_at: "2026-07-19T09:59:00.000Z",
    }));
    repository.interfereBeforeNextClaim(interference.patch);
    let generationCount = 0;
    const post = createPost(repository, async () => {
      generationCount += 1;
      return generatedText(payloadA);
    });

    // When: the handler attempts its observed-row claim.
    const body = await responseBody(await post());

    // Then: compare-and-set loses provisionally and generation never starts.
    assert.equal(body.source, "pending");
    assert.equal(generationCount, 0);
  });
}
