# Chat Header Sidebar Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the production chat session title left-aligned and render the existing sidebar toggle as a visible, accessible control.

**Architecture:** Keep sidebar state in the existing provider and make the shared `SidebarTrigger` responsible for its stable `PanelLeft` glyph. Lay out the chat header as a three-column grid so the trigger, flexible title column, and credit control have deterministic positions at every breakpoint.

**Tech Stack:** Next.js 16, React 19, TypeScript, Lucide React, CSS, Node test runner.

## Global Constraints

- Keep exactly one visible sidebar trigger beside the active session title.
- Keep the trigger target at least 44px and preserve localized `aria-label` and `aria-expanded` state.
- Preserve Command/Control+B, desktop/tablet widths, mobile drawer behavior, session data, requests, and account behavior.
- Keep long and CJK titles inside the flexible column with ellipsis and no credit-control displacement.
- Keep sidebar state changes immediate and the glyph stable.
- Do not modify unrelated dependency or lockfile content.

---

### Task 1: Visible Shared Sidebar Trigger

**Files:**
- Modify: `frontend/tests/sidebar-contract.test.ts`
- Modify: `frontend/src/components/ui/sidebar.tsx`
- Modify: `frontend/src/components/app-sidebar.tsx`

**Interfaces:**
- Consumes: `SidebarProviderContextValue`, `SidebarTriggerProps`, and the existing `toggleSidebar()` action.
- Produces: `SidebarTrigger`, a 44px button with a stable `PanelLeft` child, localized accessible state, and composed click behavior.

- [ ] **Step 1: Write failing trigger and composition assertions**

Add these assertions to `frontend/tests/sidebar-contract.test.ts`:

```ts
assert.match(sidebar, /PanelLeft/);
assert.doesNotMatch(sidebar, /PanelLeftClose|PanelLeftOpen/);
assert.match(sidebar, /<PanelLeft aria-hidden="true" \/>/);
assert.doesNotMatch(appSidebar, /SidebarTrigger/);
assert.match(sidebar, /sidebarSurfaceRef\.current\?\.focus\(\)/);
```

- [ ] **Step 2: Run the focused contract test and confirm failure**

Run:

```bash
node --test tests/sidebar-contract.test.ts
```

Expected: FAIL because `SidebarTrigger` has no `PanelLeft` child, the brand row still renders a duplicate trigger, and mobile focus still targets the removed sidebar trigger.

- [ ] **Step 3: Implement the shared trigger and stable mobile focus target**

In `frontend/src/components/ui/sidebar.tsx`, import and render the icon:

```tsx
import { PanelLeft } from "lucide-react";

return (
  <button
    ref={register}
    type="button"
    data-sidebar="trigger"
    data-slot="sidebar-trigger"
    aria-label={label}
    aria-expanded={expanded}
    className={cn("min-h-11 min-w-11", className)}
    onClick={(event) => {
      onClick?.(event);
      if (!event.defaultPrevented) toggleSidebar();
    }}
    {...props}
  >
    <PanelLeft aria-hidden="true" />
  </button>
);
```

Replace the duplicate sidebar-trigger ref with a drawer-surface ref, register it on the `aside`, and focus it when the mobile drawer opens:

```tsx
readonly setSidebarSurface: (element: HTMLElement | null) => void;
const sidebarSurfaceRef = useRef<HTMLElement | null>(null);
const focusDrawer = window.requestAnimationFrame(() => sidebarSurfaceRef.current?.focus());
```

Remove `SidebarTrigger` from the imports and brand row in `frontend/src/components/app-sidebar.tsx`.

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
node --test tests/sidebar-contract.test.ts
```

Expected: PASS with every sidebar contract test green.

- [ ] **Step 5: Commit the trigger behavior**

```bash
git add frontend/tests/sidebar-contract.test.ts frontend/src/components/ui/sidebar.tsx frontend/src/components/app-sidebar.tsx
git commit -m "fix: show chat sidebar trigger"
```

### Task 2: Left-Aligned Header Layout and Design Contract

**Files:**
- Modify: `frontend/tests/sidebar-contract.test.ts`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/DESIGN.md`

**Interfaces:**
- Consumes: the existing DOM order `SidebarTrigger`, title/status `div`, and `.credit-button` in `frontend/src/app/page.tsx`.
- Produces: `.chat-header` with `grid-template-columns: auto minmax(0, 1fr) auto` and an explicitly left-aligned flexible title column.

- [ ] **Step 1: Write the failing header layout assertion**

Add this test to `frontend/tests/sidebar-contract.test.ts`:

```ts
test("keeps the chat title in the flexible left-aligned header column", () => {
  assert.match(cssBlock(".chat-header"), /grid-template-columns:\s*auto\s+minmax\(0,\s*1fr\)\s+auto/);
  assert.match(cssBlock(".chat-header"), /text-align:\s*left/);
  assert.doesNotMatch(cssBlock(".chat-header"), /justify-content:\s*space-between/);
});
```

Also assert that the trigger SVG is 18px and the sidebar design contract names the single trigger placement and immediate state changes.

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
node --test tests/sidebar-contract.test.ts
```

Expected: FAIL because `.chat-header` still uses flex/space-between and the design contract does not name the placement.

- [ ] **Step 3: Implement deterministic header geometry**

Update `frontend/src/app/globals.css`:

```css
[data-sidebar="trigger"] {
  width: 44px;
  height: 44px;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--sidebar-foreground);
  cursor: pointer;
}

[data-sidebar="trigger"] svg { width: 18px; height: 18px; }

.chat-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  text-align: left;
}

.chat-header > div { min-width: 0; }
```

Remove the duplicate brand-row trigger rules. Keep the existing mobile gap and padding while preserving the three grid columns.

Update `frontend/DESIGN.md` so `Sidebar shell` declares the single header trigger and immediate state changes.

- [ ] **Step 4: Run focused tests and verify the CSS contract**

Run:

```bash
node --test tests/sidebar-contract.test.ts
```

Expected: PASS with the icon, placement, focus, header-grid, mobile, and accessibility assertions green.

- [ ] **Step 5: Commit layout and design contract**

```bash
git add frontend/tests/sidebar-contract.test.ts frontend/src/app/globals.css frontend/DESIGN.md
git commit -m "fix: left align chat session title"
```

### Task 3: Verification and Production Deployment

**Files:**
- Verify: `frontend/src/components/ui/sidebar.tsx`
- Verify: `frontend/src/components/app-sidebar.tsx`
- Verify: `frontend/src/app/globals.css`
- Verify: `frontend/tests/sidebar-contract.test.ts`
- Verify: `frontend/DESIGN.md`

**Interfaces:**
- Consumes: the current branch commits from Tasks 1 and 2.
- Produces: a tested fast-forward of `origin/main` and a production build serving the corrected header.

- [ ] **Step 1: Run complete frontend verification**

Run:

```bash
node --test tests/*.test.ts
npx eslint .
npx next build
```

Expected: all tests pass, ESLint exits 0, and the Next.js production build completes.

- [ ] **Step 2: Capture real-browser visual evidence**

At desktop and mobile viewports, verify:

```text
desktop: trigger visible -> title left aligned -> credits fixed right -> collapse and expand both work
mobile: trigger visible -> drawer opens -> scrim and Escape close -> focus remains visible
long title: ellipsis remains inside the middle column without displacing credits
```

Expected: screenshots show no missing icon, centered title, CJK wrapping defect, or clipped control.

- [ ] **Step 3: Run independent visual QA**

Dispatch the required read-only design-system and visual-fidelity reviews against fresh desktop and mobile captures.

Expected: both return PASS with no blocking product or evidence findings.

- [ ] **Step 4: Push the verified branch as a fast-forward to production main**

```bash
git fetch origin
git merge-base --is-ancestor origin/main HEAD
git push origin HEAD:main
```

Expected: the push is a fast-forward and the repository's automatic production workflow starts.

- [ ] **Step 5: Verify production health and rendered source**

Run the documented production checks:

```bash
curl -fsS https://jyotisha.chat/login
curl -fsS -o /dev/null -w '%{http_code}\n' https://jyotisha.chat/api/account
```

Then verify the internal API health from the web container and inspect the deployed header CSS and trigger component.

Expected: login is 200, logged-out account is 401, internal API health is 200 with `swisseph_available=true`, production CSS uses the three-column grid, and the trigger source contains `PanelLeft`.
