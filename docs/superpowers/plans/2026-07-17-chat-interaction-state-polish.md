# Chat Interaction State Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep suggestions stable until submission, allow read-only session switching during a request, and tighten two compact header/composer layouts.

**Architecture:** Preserve request, billing, and session persistence logic. Change only JSX visibility/disabled guards and token-driven CSS, with source contract tests that fail on regression.

**Tech Stack:** Next.js 16, React 19, TypeScript, Node test runner, CSS design tokens.

## Global Constraints

- Do not enable concurrent sends.
- Do not alter billing, cancellation, or model routing.
- Do not push the branch.
- Preserve unrelated working-tree changes.

---

### Task 1: Suggestion visibility

**Files:**
- Modify: `frontend/tests/starter-questions.test.ts`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/DESIGN.md`

- [ ] Add failing contracts proving neither initial nor follow-up visibility guards reference `draft`.
- [ ] Run `node --test tests/starter-questions.test.ts` and confirm the follow-up contract fails.
- [ ] Remove the draft guard from follow-up suggestions while retaining loading and cancellation guards.
- [ ] Re-run the focused test and confirm it passes.

### Task 2: Session navigation during requests

**Files:**
- Modify: `frontend/tests/starter-questions.test.ts`
- Modify: `frontend/src/app/page.tsx`

- [ ] Add a failing contract proving session-history buttons do not use `pendingSessionId` or `cancellationPending` as `disabled` state.
- [ ] Remove the disabled prop from existing-session buttons only; keep new-chat and send locks unchanged.
- [ ] Re-run the focused test and confirm it passes.

### Task 3: Compact model selector and aligned credits

**Files:**
- Modify: `frontend/tests/starter-questions.test.ts`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/DESIGN.md`

- [ ] Add failing CSS contracts for a 180px model popup and a one-line centered credit value.
- [ ] Change the popup width to `min(180px, calc(100vw - var(--space-6)))`.
- [ ] Make the credit value an inline flex box with `line-height: 1` and retain the existing 16px icon.
- [ ] Re-run the focused test and confirm it passes.

### Task 4: Verification and commit

**Files:**
- Verify all modified frontend files.

- [ ] Run `npm test`, `npx tsc --noEmit`, and `npm run lint`.
- [ ] Run `npm run build` with the local environment loaded.
- [ ] Verify the empty-session preview keeps cards during typing and removes them after submit; verify follow-up suggestions follow the same rule.
- [ ] Inspect the final diff for unrelated files and debug artifacts.
- [ ] Commit only this feature's files; do not push.
