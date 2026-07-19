# Production Onboarding and Consultation Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the production timing-theme 400 and let a slow personalized onboarding request recover from cache without a page reload.

**Architecture:** Project public consultation themes into the Python workflow's narrower report-theme vocabulary in one pure adapter. Move onboarding parsing, request timeouts, pending detection, and bounded cache retry into a focused client module; the page owns only state publication and navigation.

**Tech Stack:** Next.js 16, React 19, TypeScript, Zod, Node test runner, Playwright/Chromium.

## Global Constraints

- Preserve the visible question and transcript; private routing enrichment never appears in user-authored copy.
- Keep the first onboarding wait at 12 seconds and show existing safe defaults when it expires.
- Treat `source: "pending"` as provisional and retry; accept `agent`, `cache`, or final `fallback` as terminal.
- Do not change CSS, layout, breakpoints, billing, Supabase schema, or birth-time confidence gates.
- Add failing tests before production edits and keep every new TypeScript module below 250 pure LOC.

---

### Task 1: Project homepage themes into a legal workflow request

**Files:**
- Create: `frontend/src/lib/consultation-workflow-request.ts`
- Modify: `frontend/src/mastra/index.ts`
- Test: `frontend/tests/consultation-workflow-request.test.ts`

**Interfaces:**
- Produces: `consultationThemeValues`, `ConsultationTheme`, and `projectConsultationWorkflowRequest(question, theme)`.
- Consumed by: `consultationInputSchema` and `runConsultationWorkflow`.

- [ ] **Step 1: Write the failing projection test**

```ts
test("timing questions use a legal report theme and preserve a timing route hint", () => {
  assert.deepEqual(projectConsultationWorkflowRequest("未来哪些阶段值得把握？", "timing"), {
    question: "应期与阶段问题：未来哪些阶段值得把握？",
    themes: ["career"],
  });
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `node --test tests/consultation-workflow-request.test.ts`

Expected: FAIL because `consultation-workflow-request.ts` does not exist.

- [ ] **Step 3: Implement the exhaustive projection**

```ts
export const consultationThemeValues = ["career", "marriage", "wealth", "timing", "general"] as const;
export type ConsultationTheme = typeof consultationThemeValues[number];

export function projectConsultationWorkflowRequest(question: string, theme: ConsultationTheme) {
  switch (theme) {
    case "career": case "marriage": case "wealth":
      return { question, themes: [theme] } as const;
    case "timing":
      return { question: `应期与阶段问题：${question}`, themes: ["career"] } as const;
    case "general":
      return { question, themes: ["career", "marriage", "wealth"] } as const;
  }
}
```

Use the projection for `question`, `question_text`, and `theme` in the Python request body. Use `z.enum(consultationThemeValues)` for the public input boundary.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `node --test tests/consultation-workflow-request.test.ts tests/consultation-workflow-contract.test.ts`

Expected: all tests pass.

- [ ] **Step 5: Commit the adapter with its tests**

```bash
git add frontend/src/lib/consultation-workflow-request.ts frontend/src/mastra/index.ts frontend/tests/consultation-workflow-request.test.ts
git commit -m "fix: route timing consultations through a legal theme"
```

### Task 2: Recover personalized onboarding after the first timeout

**Files:**
- Create: `frontend/src/lib/onboarding-client.ts`
- Modify: `frontend/src/app/page.tsx`
- Test: `frontend/tests/onboarding-client.test.ts`
- Test: `frontend/tests/starter-questions.test.ts`

**Interfaces:**
- Produces: `OnboardingContent`, `OnboardingAuthenticationError`, and `requestOnboardingWithRecovery(signal, onSlow, policy?)`.
- Consumed by: the homepage onboarding effect.

- [ ] **Step 1: Write the failing recovery test**

Create a fake fetch sequence whose first request aborts, second response is `source: "pending"`, and third response is `source: "cache"` with personalized content. Assert that `onSlow` fires once and the final cache content is returned.

- [ ] **Step 2: Run the test and verify RED**

Run: `node --test tests/onboarding-client.test.ts`

Expected: FAIL because the recovery client does not exist.

- [ ] **Step 3: Implement bounded recovery**

Use this production policy:

```ts
const defaultPolicy = {
  requestTimeoutMs: 12_000,
  retryDelayMs: 4_000,
  maxAttempts: 3,
} as const;
```

Each attempt gets its own timeout controller linked to the page lifecycle signal. Timeout calls `onSlow`, waits without blocking cancellation, and retries. `pending` waits and retries. Invalid schemas, non-401 HTTP errors, and exhausted failures produce a typed error; 401 produces `OnboardingAuthenticationError`.

- [ ] **Step 4: Replace the page-owned parser and one-shot effect**

Import the client types and request function. Use an identity ref keyed by account/profile to start one recovery sequence, set the existing fallback error when `onSlow` fires, replace it with returned content, and clear the error. Redirect only for `OnboardingAuthenticationError`.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run: `node --test tests/onboarding-client.test.ts tests/starter-questions.test.ts`

Expected: all tests pass.

- [ ] **Step 6: Commit the recovery module with its tests**

```bash
git add frontend/src/lib/onboarding-client.ts frontend/src/app/page.tsx frontend/tests/onboarding-client.test.ts frontend/tests/starter-questions.test.ts
git commit -m "fix: recover slow personalized starters"
```

### Task 3: Verify, integrate, and deploy

**Files:**
- Verify all files changed since base `02ecced`.

**Interfaces:**
- Consumes: Tasks 1 and 2 plus existing terminal-completion commits.
- Produces: tested `main` and a verified production deployment.

- [ ] **Step 1: Run automated gates**

Run:

```bash
node --test tests/*.test.ts
node node_modules/eslint/bin/eslint.js .
npm run build
git diff --check 02ecced..HEAD
```

Expected: 0 test failures, 0 lint errors, build exit 0, and no whitespace errors.

- [ ] **Step 2: Run real-browser QA**

At 390×844, 768×1024, and 1280×900 verify safe starter cards become available after a simulated slow first response and then replace with personalized cache content. Submit the timing starter and assert its internal workflow request is accepted. Recheck the terminal low CTA and completion transition.

- [ ] **Step 3: Merge without disturbing the dirty main workspace**

Fetch `origin`, verify `origin/main` remains the feature base, and push the tested descendant directly to `origin/main`. Do not stage, stash, or overwrite unrelated local main-workspace changes.

- [ ] **Step 4: Track deployment and verify production**

Wait for the production workflow to complete. Verify `/api/health` reports the pushed SHA, production source serves the new CTA, the 12:48 terminal record can complete, personalized starters recover, and the timing starter no longer returns `Unknown high-rigor theme: timing`.
