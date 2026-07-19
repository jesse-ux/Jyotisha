# Private Consultation Entrypoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep homepage entrypoint copy short and public while expanding the actual consultation instructions only on the server, and make each entry card one responsive click target.

**Architecture:** The client sends an optional closed `entrypoint` enum beside the visible `question`. A server-only resolver expands trusted entrypoints before constructing Agent and calculation-tool input; persisted history continues to use the public question. Existing card articles gain a stretched native button rather than nested action buttons.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Zod, Node test runner, token-driven CSS.

## Global Constraints

- Public composer/history copy is exactly `深入看今日`, `生时校正`, or `再次校正`.
- Internal entrypoint instructions must not remain in `frontend/src/app/page.tsx` or the browser bundle.
- Ordinary typed questions, billing, undo, streaming, and persistence behavior must not change.
- Do not assert natural-language prompt prose in tests; assert routing and data ownership.
- Use existing `DESIGN.md` tokens and 44px keyboard-accessible card controls.

---

### Task 1: Server-owned entrypoint resolver

**Files:**
- Create: `frontend/src/lib/consultation-entrypoint.ts`
- Create: `frontend/tests/consultation-entrypoint.test.ts`

**Interfaces:**
- Produces: `consultationEntrypointSchema` and `resolveConsultationQuestion({ entrypoint, visibleQuestion, name, currentDate })`.
- Returns: `{ kind: "plain" | "expanded"; modelQuestion: string }`.

- [x] **Step 1: Write the failing routing tests**

```ts
assert.equal(resolveConsultationQuestion({ entrypoint: undefined, visibleQuestion: "普通问题", name: "林遥", currentDate: "2026-07-19" }).kind, "plain");
const daily = resolveConsultationQuestion({ entrypoint: "daily_starlanguage", visibleQuestion: "深入看今日", name: "林遥", currentDate: "2026-07-19" });
assert.equal(daily.kind, "expanded");
assert.notEqual(daily.modelQuestion, "深入看今日");
```

- [x] **Step 2: Run the focused test and confirm RED**

Run: `/opt/homebrew/bin/node --test tests/consultation-entrypoint.test.ts`

Expected: FAIL because the resolver module does not exist.

- [x] **Step 3: Implement the strict enum and resolver**

Use a Zod enum for `daily_starlanguage` and `birth_time_rectification`. Keep template strings in this server-imported module and return the visible question unchanged only for the plain branch.

- [x] **Step 4: Run the focused test and confirm GREEN**

Run: `/opt/homebrew/bin/node --test tests/consultation-entrypoint.test.ts`

Expected: all entrypoint routing tests pass.

### Task 2: Consultation API and client state

**Files:**
- Modify: `frontend/src/app/api/consult/route.ts`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/tests/consultation-entrypoint.test.ts`
- Modify: `frontend/tests/sidebar-contract.test.ts`

**Interfaces:**
- Consumes: optional `entrypoint` enum and `resolveConsultationQuestion`.
- Produces: Agent/tool requests using `modelQuestion`, while `userSession.messages` keeps `question`.

- [x] **Step 1: Add failing API/client ownership tests**

Assert structurally that the route schema includes the optional enum, tool input overrides `question` with `modelQuestion`, and the page contains no `buildDailyStarlanguageQuestion` or `buildBirthTimeRectificationQuestion` functions.

- [x] **Step 2: Run the focused tests and confirm RED**

Run: `/opt/homebrew/bin/node --test tests/consultation-entrypoint.test.ts tests/sidebar-contract.test.ts`

- [x] **Step 3: Wire the server expansion**

Resolve once after validation. Use the expanded question for `consultationInputSchema.parse({ ...parsed.data, question: resolved.modelQuestion })` and the final Agent user content. Keep prompt-extraction checks and history based on user-controlled visible text.

- [x] **Step 4: Wire the client entrypoint state**

Add `draftEntrypoint` to composer state and `PendingConsultation`. Card selection sets it; textarea edits clear it; sending includes it and clears it; undo restores it. Keep optimistic/persisted `Message.text` equal to the visible composer question.

- [x] **Step 5: Run the focused tests and confirm GREEN**

Run: `/opt/homebrew/bin/node --test tests/consultation-entrypoint.test.ts tests/sidebar-contract.test.ts`

### Task 3: Whole-card interaction

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/DESIGN.md` only if the existing entrypoint-card contract cannot express the stretched action.

**Interfaces:**
- Consumes: card selection helpers from Task 2.
- Produces: two semantic articles, each with one absolute inset native button and one lower-right visual action label.

- [x] **Step 1: Add a failing source contract**

Assert that both card articles contain a dedicated whole-card action and no nested visible action button inside `.daily-starlanguage-heading`.

- [x] **Step 2: Run the source contract and confirm RED**

Run: `/opt/homebrew/bin/node --test tests/sidebar-contract.test.ts`

- [x] **Step 3: Implement whole-card markup and token-driven states**

Keep `article`, `dl`, and explanatory copy. Add a stretched button with an accessible name; render the visible action text in the lower-right. Add hover, active, focus-visible, disabled, and reduced-motion states using existing tokens.

- [x] **Step 4: Run the source contract and confirm GREEN**

Run: `/opt/homebrew/bin/node --test tests/sidebar-contract.test.ts`

### Task 4: Regression and real-browser QA

**Files:**
- Modify only files required by observed regressions.

- [x] **Step 1: Run the full frontend suite**

Run: `/opt/homebrew/bin/node --test tests/*.test.ts`

Expected: all tests pass.

- [x] **Step 2: Run lint and production build**

Run: `/opt/homebrew/bin/node node_modules/eslint/bin/eslint.js .`

Run: `/opt/homebrew/bin/node node_modules/next/dist/bin/next build --webpack`

Expected: zero lint errors and a successful production build.

- [x] **Step 3: Browser QA at desktop and 390px**

Use `?preview=birth-time-candidate-complete`. Click each full card and verify the composer contains only the short public text. Edit the composer and verify the request becomes ordinary. Verify focus ring, disabled behavior, CJK wrapping, no large middle button, and profile result visibility.

- [x] **Step 4: Verify request ownership**

Inspect the browser request body: it may contain only the public `question` plus the enum. Confirm the internal template is absent from page source, DOM, transcript, and persisted message objects.
