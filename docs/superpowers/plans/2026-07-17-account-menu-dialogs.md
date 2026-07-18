# Account Menu and Task Dialogs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the right-side account sheet with an anchored account popover plus focused profile, redeem, and logout-confirmation dialogs.

**Architecture:** Keep account/profile data and API mutations in `frontend/src/app/page.tsx`, but split presentation state into `accountMenuOpen` and `activeAccountDialog`. The sidebar trigger owns the non-modal menu; the credit button and system fallbacks route directly to the redeem dialog; each modal renders only its own task and shares one focus-trapped overlay contract.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 5, vanilla CSS design tokens, Node test runner, existing Lucide icons.

## Global Constraints

- Preserve the warm editorial design tokens in `frontend/DESIGN.md`; add no raw colors, arbitrary shadow recipes, or new dependencies.
- The sidebar account trigger opens a popover; the upper-right credit trigger opens the redeem dialog directly.
- The administrator-only `管理兑换码` action navigates to `/admin/codes` in the same tab.
- `退出登录` must open a confirmation dialog; only `确认退出` signs out.
- Missing-profile and insufficient-credit flows open their task dialogs directly.
- Popover rows and dialog controls retain a minimum 44px target.
- Support outside click where appropriate, Escape, focus trapping, focus return, keyboard navigation, and reduced motion.
- Remove the former right-side account sheet markup, CSS, and overloaded state.
- Do not commit or push unrelated working-tree changes.

---

### Task 1: Lock the interaction contract and design-system primitives

**Files:**
- Modify: `frontend/tests/starter-questions.test.ts`
- Modify: `frontend/DESIGN.md`

**Interfaces:**
- Consumes: existing source-contract test helpers `pageSource`, `globalStyles`, and `sourceBetween`.
- Produces: failing assertions for the account popover, direct redeem route, three dialogs, and removal of the sheet; documented `Account popover`, `Profile dialog`, `Redeem dialog`, and `Logout dialog` primitives.

- [ ] **Step 1: Add failing structural tests**

Append tests that inspect behavior-bearing names and relationships rather than prose copy:

```ts
test("routes account actions through a popover and focused dialogs", () => {
  assert.match(pageSource, /const \[accountMenuOpen, setAccountMenuOpen\] = useState\(false\)/);
  assert.match(pageSource, /const \[activeAccountDialog, setActiveAccountDialog\] = useState<AccountDialog>\(null\)/);
  assert.match(pageSource, /className="account-menu"/);
  assert.match(pageSource, /onClick=\{\(\) => openAccountDialog\("profile"\)\}/);
  assert.match(pageSource, /onClick=\{\(\) => openAccountDialog\("redeem"/);
  assert.match(pageSource, /onClick=\{\(\) => openAccountDialog\("logout"\)\}/);
});

test("removes the monolithic account sheet", () => {
  assert.doesNotMatch(pageSource, /profile-overlay|profile-dialog|openAccount\(/);
  assert.doesNotMatch(globalStyles, /\.profile-overlay|\.profile-dialog/);
});

test("keeps admin navigation separate from task dialogs", () => {
  const menu = sourceBetween(pageSource, 'className="account-menu"', '</div>\n        </div>');
  assert.match(menu, /href="\/admin\/codes"/);
  assert.match(menu, /account\?\.isAdmin/);
});
```

- [ ] **Step 2: Run the targeted tests and confirm the expected red state**

Run: `npm test -- --test-name-pattern="account|sheet|admin navigation"`

Expected: the new tests fail because `accountMenuOpen`, `activeAccountDialog`, `.account-menu`, and focused-dialog routes do not exist yet.

- [ ] **Step 3: Update the design contract before styling**

Replace `### Account sheet` in `frontend/DESIGN.md` with four documented primitives:

```md
### Account popover

- **Structure:** identity header, profile action, redeem action with balance, administrator-only code-management link, divider, and logout action.
- **Surface:** 280px elevated canvas popover anchored above the sidebar account trigger; warm hairline, existing elevated shadow, no nested cards.
- **States:** closed, open, hover, focus-visible, administrator, signing-out transition.
- **Accessibility:** `aria-expanded`, `aria-controls`, menu semantics, 44px rows, outside-click and Escape dismissal, focus return.

### Profile dialog

- **Structure:** profile title, existing profile fields, inline result, save action.
- **Width:** 560px desktop maximum with viewport-safe spacing and internal scrolling.
- **States:** open, invalid, saving, success, error.

### Redeem dialog

- **Structure:** current balance, redemption-code form, inline result.
- **Width:** 420px desktop maximum.
- **States:** open, submitting, success, error.

### Logout dialog

- **Structure:** confirmation title and explanation, cancel action, destructive confirm action.
- **States:** open, signing out, error.
```

- [ ] **Step 4: Verify the documentation diff**

Run: `git diff --check -- frontend/DESIGN.md frontend/tests/starter-questions.test.ts`

Expected: exit 0 with no whitespace errors.

---

### Task 2: Split surface state and route every account entry correctly

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes: existing `Profile`, `Account`, `redeem`, `saveProfile`, `signOut`, `keepFocusWithin`, `accountTrigger`, `redeemInput`, and `closeButton` behavior.
- Produces: `type AccountDialog = "profile" | "redeem" | "logout" | null`, `accountMenuOpen`, `activeAccountDialog`, `toggleAccountMenu`, `openAccountDialog`, and `closeAccountDialog`.

- [ ] **Step 1: Replace the overloaded state and refs**

Add the dialog type beside other UI-state types:

```ts
type AccountDialog = "profile" | "redeem" | "logout" | null;
```

Replace `profileOpen` and `redeemOpen` with:

```ts
const [accountMenuOpen, setAccountMenuOpen] = useState(false);
const [activeAccountDialog, setActiveAccountDialog] = useState<AccountDialog>(null);
```

Replace the sheet ref with explicit surface refs:

```ts
const accountMenu = useRef<HTMLDivElement>(null);
const accountDialog = useRef<HTMLElement>(null);
const creditTrigger = useRef<HTMLButtonElement>(null);
const dialogReturnTarget = useRef<HTMLButtonElement | null>(null);
```

- [ ] **Step 2: Add explicit open and close handlers**

Replace `openAccount` and `closeAccount` with handlers shaped as follows:

```ts
function toggleAccountMenu() {
  setActiveAccountDialog(null);
  setAccountMenuOpen((current) => !current);
}

function openAccountDialog(dialog: Exclude<AccountDialog, null>, returnTarget = accountTrigger.current) {
  dialogReturnTarget.current = returnTarget;
  setAccountMenuOpen(false);
  setAccountError("");
  if (dialog === "profile") {
    if (profileComplete) setProfileDraft(profile);
    setProfileNotice("");
  }
  if (dialog === "redeem") {
    setRedeemError("");
    setRedeemMessage("");
  }
  setActiveAccountDialog(dialog);
}

function closeAccountDialog() {
  if (signingOut) return;
  setActiveAccountDialog(null);
  const returnTarget = dialogReturnTarget.current;
  window.requestAnimationFrame(() => returnTarget?.focus());
}
```

- [ ] **Step 3: Replace the sheet focus effect with menu dismissal and dialog focus trapping**

Use one document listener for the non-modal popover:

```ts
useEffect(() => {
  if (!accountMenuOpen) return;
  const dismissMenu = (event: MouseEvent) => {
    if (!accountMenu.current?.contains(event.target as Node)) setAccountMenuOpen(false);
  };
  const closeOnEscape = (event: globalThis.KeyboardEvent) => {
    if (event.key !== "Escape") return;
    setAccountMenuOpen(false);
    window.requestAnimationFrame(() => accountTrigger.current?.focus());
  };
  document.addEventListener("mousedown", dismissMenu);
  window.addEventListener("keydown", closeOnEscape);
  return () => {
    document.removeEventListener("mousedown", dismissMenu);
    window.removeEventListener("keydown", closeOnEscape);
  };
}, [accountMenuOpen]);
```

Use `activeAccountDialog` for modal initial focus, Escape, and `keepFocusWithin`. Focus `redeemInput` for redeem and `closeButton` for profile/logout.

- [ ] **Step 4: Route system fallbacks directly**

Replace every `openAccount(true)` call with:

```ts
openAccountDialog("redeem", creditTrigger.current);
```

Replace the incomplete-profile branch with:

```ts
setProfileDraft(profile);
setProfileNotice("请先补充出生资料，才能进行星盘计算。");
openAccountDialog("profile");
```

Use `activeAccountDialog === null` in the onboarding focus effect and `activeAccountDialog !== null` for modal background inertness.

- [ ] **Step 5: Run targeted tests**

Run: `npm test -- --test-name-pattern="account|sheet|admin navigation"`

Expected: the state/routing assertions pass; markup or CSS assertions may remain red until Tasks 3 and 4.

---

### Task 3: Replace the sheet markup with the account popover and three dialogs

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes: Task 2 state, handlers, refs, existing profile and redeem forms, and `/admin/codes` route.
- Produces: `.account-menu`, `.account-modal-overlay`, `.account-modal`, `.profile-modal`, `.redeem-modal`, and `.logout-modal` markup.

- [ ] **Step 1: Add the anchored popover beside the sidebar account trigger**

Wrap the trigger and menu in the existing `.sidebar-footer`. Add `aria-expanded`, `aria-controls`, and a rotating chevron state. Render the menu only while open:

```tsx
<button
  className="profile-trigger"
  ref={accountTrigger}
  type="button"
  aria-expanded={accountMenuOpen}
  aria-controls="account-menu"
  onClick={toggleAccountMenu}
>
  ...
</button>
{accountMenuOpen && (
  <div className="account-menu" id="account-menu" ref={accountMenu} role="menu">
    <div className="account-menu-identity">...</div>
    <button role="menuitem" type="button" onClick={() => openAccountDialog("profile")}>...</button>
    <button role="menuitem" type="button" onClick={() => openAccountDialog("redeem")}>...</button>
    {account?.isAdmin && <Link role="menuitem" href="/admin/codes">...</Link>}
    <div className="account-menu-separator" />
    <button className="account-menu-danger" role="menuitem" type="button" onClick={() => openAccountDialog("logout")}>...</button>
  </div>
)}
```

- [ ] **Step 2: Route the credit button directly to redeem**

Add `ref={creditTrigger}` and change its handler and accessible name:

```tsx
onClick={() => openAccountDialog("redeem", creditTrigger.current)}
aria-label={account ? `余额 ${account.credits} 点，兑换点数` : accountError || "读取余额中"}
```

- [ ] **Step 3: Render a profile-only modal**

When `activeAccountDialog === "profile"`, render the shared scrim, dialog header, existing `ProfileFields`, inline notice/error, and save action. Do not render account email, credits, redemption form, admin link, or logout control inside this modal.

- [ ] **Step 4: Render a redeem-only modal**

When `activeAccountDialog === "redeem"`, render the current balance, existing redemption-code form, inline error/success, and close control. Do not render profile fields.

- [ ] **Step 5: Render the logout confirmation modal**

When `activeAccountDialog === "logout"`, render the confirmation copy, cancel action, inline `accountError`, and destructive confirmation:

```tsx
<button className="button-primary danger-primary" type="button" onClick={() => void signOut()} disabled={signingOut}>
  {signingOut ? "正在退出" : "确认退出"}
</button>
```

- [ ] **Step 6: Remove the old account sheet markup completely**

Delete `.profile-overlay`, `.profile-dialog`, `.account-summary`, `.sheet-section`, `.section-toggle`, and `.account-actions` JSX usage. Remove obsolete `Minus` import if no longer used.

- [ ] **Step 7: Run the complete frontend tests**

Run: `npm test`

Expected: all existing and new tests pass.

---

### Task 4: Style the popover and modal family with existing tokens

**Files:**
- Modify: `frontend/src/app/globals.css`

**Interfaces:**
- Consumes: Task 3 class names and tokens documented in `frontend/DESIGN.md`.
- Produces: collision-safe account menu, centered modal shell, responsive form layout, focus/hover/active states, and reduced-motion behavior.

- [ ] **Step 1: Add account popover styles**

Implement the menu with existing tokens:

```css
.sidebar-footer { position: relative; }
.account-menu { position: absolute; z-index: 30; right: 0; bottom: calc(100% + var(--space-2)); width: min(280px, calc(100vw - var(--space-6))); overflow: hidden; padding: var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-canvas); box-shadow: var(--shadow-elevated); transform-origin: bottom right; animation: account-menu-enter 120ms var(--ease-out) both; }
.account-menu button, .account-menu a { width: 100%; min-height: 44px; display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); padding: 0 var(--space-3); border: 0; border-radius: var(--radius-md); background: transparent; color: var(--color-ink); text-align: left; text-decoration: none; }
```

Add identity, separator, trailing balance, danger, hover, active, and focus-visible rules using only existing tokens.

- [ ] **Step 2: Replace sheet CSS with centered modal CSS**

Use one overlay and width variants:

```css
.account-modal-overlay { position: fixed; z-index: 40; inset: 0; display: grid; place-items: center; padding: var(--space-4); background: var(--color-scrim); animation: account-overlay-enter 180ms ease-out both; }
.account-modal { width: min(100%, 560px); max-height: min(84dvh, 760px); overflow-y: auto; padding: var(--space-8); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-canvas); box-shadow: var(--shadow-elevated); animation: account-dialog-enter 180ms var(--ease-out) both; }
.redeem-modal { width: min(100%, 420px); }
.logout-modal { width: min(100%, 400px); }
```

Keep the existing profile-grid, location-grid, input, button, form-result, and focus styles. Add `.dialog-actions`, `.redeem-balance`, and `.danger-primary` with documented tokens.

- [ ] **Step 3: Add responsive and reduced-motion behavior**

At mobile widths, retain 16px viewport spacing, keep the popover within the sidebar/viewport, collapse profile grids at 480px, and cap dialog height. Under `prefers-reduced-motion: reduce`, disable menu and dialog transform animations.

- [ ] **Step 4: Confirm the source contract and CSS cleanup**

Run: `npm test`

Expected: all tests pass, including removal of `.profile-overlay` and `.profile-dialog`.

Run: `rg -n "profile-overlay|profile-dialog|openAccount\(|redeemOpen|section-toggle|account-summary" frontend/src frontend/tests`

Expected: no obsolete account-sheet hits.

---

### Task 5: Verify behavior through the shipped surface and commit atomically

**Files:**
- Verify: `frontend/src/app/page.tsx`
- Verify: `frontend/src/app/globals.css`
- Verify: `frontend/DESIGN.md`
- Verify: `frontend/tests/starter-questions.test.ts`

**Interfaces:**
- Consumes: completed Tasks 1–4.
- Produces: verified build, browser evidence across breakpoints, and one feature commit without unrelated files.

- [ ] **Step 1: Run static and production gates**

Run from `frontend/`:

```bash
npm test
npx tsc --noEmit
npm run lint
npm run build
```

Expected: every command exits 0.

- [ ] **Step 2: Run repository hygiene checks**

Run:

```bash
git diff --check
git diff -- frontend/DESIGN.md frontend/src/app/page.tsx frontend/src/app/globals.css frontend/tests/starter-questions.test.ts
```

Expected: no whitespace errors and only the confirmed account-surface changes plus previously approved hint/card removals in the already-dirty frontend files.

- [ ] **Step 3: Manual browser QA at 1280px, 768px, and 375px**

At each breakpoint verify:

1. Sidebar account trigger opens the anchored popover and leaves the chat readable.
2. Identity, profile, redeem, admin visibility, and logout rows are correctly ordered.
3. Credit trigger opens redeem directly.
4. Profile dialog contains no account/redeem/logout content.
5. Redeem success updates all balances; failure preserves the code.
6. Logout opens confirmation; cancel returns focus; confirm exposes pending state.
7. Escape, outside click, focus return, focus trap, and keyboard navigation work.
8. No right-side account sheet appears and no console error/warning is emitted.

- [ ] **Step 4: Stage only feature files and inspect the staged diff**

```bash
git add frontend/DESIGN.md frontend/src/app/page.tsx frontend/src/app/globals.css frontend/tests/starter-questions.test.ts docs/superpowers/plans/2026-07-17-account-menu-dialogs.md
git diff --staged --check
git diff --staged --stat
git diff --staged
```

Expected: unrelated research manifests, image assets, and `frontend/plans/` remain unstaged.

- [ ] **Step 5: Commit without pushing**

```bash
git commit -m "feat: add focused account dialogs"
git log -1 --oneline
git status --short
```

Expected: the feature commit is created locally; no push occurs; unrelated user changes remain in the working tree.
