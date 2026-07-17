# Composable Collapsible Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the page-local navigation shell with a shadcn-style composable sidebar that expands to 288px on desktop, collapses to a useful 64px icon rail, defaults to a compact rail on tablet, and remains an off-canvas drawer on mobile.

**Architecture:** Put deterministic breakpoint and initial-state decisions in a pure sidebar-state module; put provider state, responsive mechanics, shortcuts, tooltips, and semantic primitives in `components/ui/sidebar.tsx`; put Jyotisha-specific brand, new-chat, history, and account composition in `components/app-sidebar.tsx`. Keep sessions, request locks, account mutations, dialogs, and API calls in `app/page.tsx`, which supplies typed data and callbacks to the product component.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 5, Base UI 1.6 Popover/Tooltip, Tailwind CSS 4 infrastructure with existing global token CSS, Lucide icons, Node test runner, ESLint.

## Global Constraints

- Follow `docs/superpowers/specs/2026-07-17-composable-sidebar-design.md` and `frontend/DESIGN.md`; when they disagree, the dated sidebar spec governs this feature.
- Treat the user's pasted Base Nova sidebar documentation as the composition reference. Do not import the stock shadcn visual palette.
- Do not run `shadcn add sidebar` against the working tree: it may overwrite the existing Base UI `Button`. Task 3 inspects the registry source read-only, then hand-adapts only the retained primitives.
- Add no dependency unless an imported Base UI primitive is demonstrably absent from the existing `@base-ui/react` package.
- Use only Jyotisha color, spacing, radius, shadow, typography, and motion tokens; no raw colors or new shadow recipes.
- Preserve all session selection, request lock, onboarding, model selection, cancellation, credit, profile, redemption, administrator, and logout behavior.
- Existing sessions remain clickable while another session is answering. Only new requests and new-chat creation retain their current request locks.
- Keep the account task dialogs in `page.tsx`. The extracted account menu may only route to callbacks.
- Do not persist sidebar state in cookies or local storage. Reload defaults are desktop expanded, tablet collapsed, and mobile closed.
- Do not animate grid-column width or another layout property. Animate only opacity, transform, and colors; respect reduced-motion.
- Keep the current unrelated working-tree changes untouched. Do not push during implementation.
- Run commands that reference `node_modules/`, `src/`, `tests/`, `npm`, `npx`, or `tsc` from `frontend/`. Run `git` commands from the repository root so the paths shown below resolve exactly.

---

## Target File Map

| File | Responsibility |
|---|---|
| `frontend/src/lib/sidebar-state.ts` | Pure viewport classification and default-state rules. |
| `frontend/src/hooks/use-sidebar-viewport.ts` | One browser subscription for mobile/tablet/desktop viewport state and hydration readiness. |
| `frontend/src/components/ui/sidebar.tsx` | Provider, context, generic semantic primitives, trigger, rail, tooltip, mobile focus/keyboard mechanics. |
| `frontend/src/components/app-sidebar.tsx` | Jyotisha brand, new-chat action, session history, collapsed history control, account menu composition. |
| `frontend/src/app/page.tsx` | Business state and callbacks; provider/app-sidebar integration; existing task dialogs. |
| `frontend/src/app/globals.css` | Token aliases, shell widths, responsive drawer/rail states, account popover, tooltip, accessibility preferences. |
| `frontend/tests/sidebar-state.test.ts` | Pure state unit tests. |
| `frontend/tests/sidebar-contract.test.ts` | Source-level architecture and token contract tests. |
| `frontend/tests/starter-questions.test.ts` | Update existing account/session assertions to follow extracted markup. |
| `frontend/DESIGN.md` | Shipped component contract for the new shell. |

---

### Task 1: Lock the architecture and design contract

**Files:**
- Create: `frontend/tests/sidebar-contract.test.ts`
- Modify: `frontend/DESIGN.md`

**Interfaces:**
- Consumes: the approved design spec and existing source-contract testing style.
- Produces: an initially red architecture test that prevents a partial migration or stock-theme regression.

- [ ] **Step 1: Read the local Next.js 16 guidance before touching client boundaries**

Run:

```bash
sed -n '1,220p' node_modules/next/dist/docs/01-app/01-getting-started/05-server-and-client-components.md
sed -n '1,180p' node_modules/next/dist/docs/01-app/03-api-reference/01-directives/use-client.md
sed -n '1,180p' node_modules/next/dist/docs/01-app/02-guides/preventing-flash-before-hydration.md
```

Expected: confirm that the sidebar provider and product sidebar are client components, props crossing boundaries remain serializable only where a Server Component boundary exists, and initial responsive markup must not depend on reading `window` during render.

- [ ] **Step 2: Add the failing structural contract test**

Create `frontend/tests/sidebar-contract.test.ts`:

```ts
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const projectFile = (path: string) => new URL(`../${path}`, import.meta.url);
const readProjectFile = (path: string) => readFileSync(projectFile(path), "utf8");

test("uses a composable sidebar instead of page-local navigation state", () => {
  assert.equal(existsSync(projectFile("src/components/ui/sidebar.tsx")), true);
  assert.equal(existsSync(projectFile("src/components/app-sidebar.tsx")), true);

  const page = readProjectFile("src/app/page.tsx");
  assert.match(page, /<SidebarProvider>/);
  assert.match(page, /<AppSidebar/);
  assert.match(page, /<SidebarInset/);
  assert.match(page, /<SidebarTrigger/);
  assert.doesNotMatch(page, /mobileSidebarOpen|setMobileSidebarOpen/);
  assert.doesNotMatch(page, /className="sidebar-backdrop"/);
  assert.doesNotMatch(page, /<aside className="sidebar"/);
});

test("exports only the retained sidebar composition surface", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  for (const name of [
    "SidebarProvider", "Sidebar", "SidebarHeader", "SidebarContent",
    "SidebarGroup", "SidebarGroupLabel", "SidebarGroupContent",
    "SidebarMenu", "SidebarMenuItem", "SidebarMenuButton",
    "SidebarFooter", "SidebarInset", "SidebarTrigger", "SidebarRail", "useSidebar",
  ]) {
    assert.match(sidebar, new RegExp(`export (?:function|const) ${name}\\b`));
  }
  assert.doesNotMatch(sidebar, /SidebarMenuBadge|SidebarMenuSkeleton|SidebarMenuSub|side\?:|variant\?:/);
});

test("maps sidebar semantics to Jyotisha tokens", () => {
  const styles = readProjectFile("src/app/globals.css");
  assert.match(styles, /--sidebar-background:\s*var\(--color-sidebar\)/);
  assert.match(styles, /--sidebar-solid:\s*var\(--color-sidebar-solid\)/);
  assert.match(styles, /--sidebar-foreground:\s*var\(--color-ink\)/);
  assert.match(styles, /--sidebar-accent:\s*var\(--color-selected\)/);
  assert.match(styles, /--sidebar-border:\s*var\(--color-border\)/);
  assert.match(styles, /--sidebar-ring:\s*var\(--color-focus\)/);
});
```

- [ ] **Step 3: Run the new test and confirm the intended red state**

Run: `node --test tests/sidebar-contract.test.ts`

Expected: failures report missing `ui/sidebar.tsx`, missing `app-sidebar.tsx`, and the old page-local state. A syntax/import failure is not the expected red state and must be corrected first.

- [ ] **Step 4: Add the shipped Sidebar primitive to `frontend/DESIGN.md`**

Insert after `### Navigation item`:

```md
### Sidebar shell

- **Composition:** provider, fixed header, one scroll-owning content region, fixed footer, trigger, rail, and flexible chat inset.
- **Desktop:** 288px expanded by default at 1024px and above; 64px collapsed icon rail.
- **Tablet:** 64px collapsed by default from 768px through 1023px; 240px when expanded.
- **Mobile:** no icon rail; an off-canvas drawer uses `min(86vw, 320px)` and closes through its scrim, trigger, or Escape.
- **Collapsed content:** logo, new-chat action, one history expansion action, and account avatar. Individual sessions do not become indistinguishable repeated icons.
- **Scroll ownership:** header and footer remain fixed; `SidebarContent` is the sole sidebar scroll owner.
- **Accessibility:** Command/Control+B shortcut outside editable controls, contextual trigger labels, 44px targets, focus return, collapsed-only tooltips, reduced-motion, reduced-transparency, and increased-contrast support.
- **State:** session-local; reload uses breakpoint defaults rather than cookie or local-storage persistence.
```

- [ ] **Step 5: Check the contract artifacts without committing a broken test state**

Run:

```bash
git diff --check -- frontend/DESIGN.md frontend/tests/sidebar-contract.test.ts
```

Expected: whitespace check passes. Leave both files uncommitted until Task 3 makes the structural contract green; never create a commit that knowingly breaks the frontend test suite.

---

### Task 2: Implement deterministic responsive state

**Files:**
- Create: `frontend/src/lib/sidebar-state.ts`
- Create: `frontend/src/hooks/use-sidebar-viewport.ts`
- Create: `frontend/tests/sidebar-state.test.ts`

**Interfaces:**

```ts
export type SidebarViewport = "mobile" | "tablet" | "desktop";
export function sidebarViewportForWidth(width: number): SidebarViewport;
export function defaultSidebarOpen(viewport: SidebarViewport): boolean;
export function shouldHandleSidebarShortcut(event: Pick<KeyboardEvent, "key" | "metaKey" | "ctrlKey" | "altKey" | "shiftKey" | "target">): boolean;
export function useSidebarViewport(): { viewport: SidebarViewport; ready: boolean };
```

- [ ] **Step 1: Write pure-state tests first**

Create `frontend/tests/sidebar-state.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import {
  defaultSidebarOpen,
  shouldHandleSidebarShortcut,
  sidebarViewportForWidth,
} from "../src/lib/sidebar-state.ts";

test("classifies the exact sidebar breakpoints", () => {
  assert.equal(sidebarViewportForWidth(0), "mobile");
  assert.equal(sidebarViewportForWidth(767), "mobile");
  assert.equal(sidebarViewportForWidth(768), "tablet");
  assert.equal(sidebarViewportForWidth(1023), "tablet");
  assert.equal(sidebarViewportForWidth(1024), "desktop");
});

test("uses the approved reload defaults", () => {
  assert.equal(defaultSidebarOpen("mobile"), false);
  assert.equal(defaultSidebarOpen("tablet"), false);
  assert.equal(defaultSidebarOpen("desktop"), true);
});

test("accepts Command/Control+B only outside editable controls", () => {
  const shortcut = { key: "b", metaKey: true, ctrlKey: false, altKey: false, shiftKey: false };
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: null }), true);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: { tagName: "TEXTAREA" } }), false);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: { isContentEditable: true } }), false);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, key: "k", target: null }), false);
});
```

- [ ] **Step 2: Run the state test and confirm red**

Run: `node --test tests/sidebar-state.test.ts`

Expected: module-not-found for `src/lib/sidebar-state.ts`.

- [ ] **Step 3: Implement the pure rules**

Create `frontend/src/lib/sidebar-state.ts`:

```ts
export type SidebarViewport = "mobile" | "tablet" | "desktop";

export function sidebarViewportForWidth(width: number): SidebarViewport {
  if (width < 768) return "mobile";
  if (width < 1024) return "tablet";
  return "desktop";
}

export function defaultSidebarOpen(viewport: SidebarViewport) {
  return viewport === "desktop";
}

export function shouldHandleSidebarShortcut(
  event: {
    key: string;
    metaKey: boolean;
    ctrlKey: boolean;
    altKey: boolean;
    shiftKey: boolean;
    target: { tagName?: string; isContentEditable?: boolean } | null;
  },
) {
  const target = event.target;
  const editable = Boolean(target
    && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName ?? "")));
  return !editable
    && event.key.toLowerCase() === "b"
    && (event.metaKey || event.ctrlKey)
    && !event.altKey
    && !event.shiftKey;
}
```

Keep `HTMLElement` usage inside the browser-called function; the current unit tests import but do not invoke that branch in Node.

- [ ] **Step 4: Add one viewport subscription hook**

Create `frontend/src/hooks/use-sidebar-viewport.ts` as a client module. Initialize `{ viewport: "desktop", ready: false }` so server and first-client markup match. In one effect:

1. classify `window.innerWidth`;
2. set `{ viewport, ready: true }`;
3. subscribe to `window.resize` with the same classifier;
4. remove the listener on cleanup.

Do not read `window` in a state initializer and do not create three independent `matchMedia` subscriptions.

- [ ] **Step 5: Run state tests and static checks**

Run:

```bash
node --test tests/sidebar-state.test.ts
npx tsc --noEmit
git diff --check -- frontend/src/lib/sidebar-state.ts frontend/src/hooks/use-sidebar-viewport.ts frontend/tests/sidebar-state.test.ts
```

Expected: both state tests pass; TypeScript and whitespace checks exit 0.

- [ ] **Step 6: Commit the responsive state unit**

Run:

```bash
git add frontend/src/lib/sidebar-state.ts frontend/src/hooks/use-sidebar-viewport.ts frontend/tests/sidebar-state.test.ts
git commit -m "feat: add responsive sidebar state model"
```

---

### Task 3: Build the retained generic sidebar primitives

**Files:**
- Create: `frontend/src/components/ui/sidebar.tsx`
- Modify: `frontend/tests/sidebar-contract.test.ts`

**Interfaces:**

```ts
export type SidebarState = "expanded" | "collapsed";

export type SidebarContextValue = {
  state: SidebarState;
  open: boolean;
  setOpen: (open: boolean) => void;
  openMobile: boolean;
  setOpenMobile: (open: boolean) => void;
  viewport: SidebarViewport;
  ready: boolean;
  isMobile: boolean;
  toggleSidebar: () => void;
};

export type SidebarProviderProps = React.ComponentProps<"div"> & {
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  onMobileOpenChange?: (open: boolean) => void;
  escapeBlocked?: boolean;
};

export type SidebarTriggerProps = React.ComponentProps<"button"> & {
  placement?: "inset" | "sidebar";
};
```

- [ ] **Step 1: Inspect the current Base Nova source without mutating files**

Run: `npx shadcn@latest view sidebar`

Expected: registry source/API is printed. Compare its provider, data attributes, trigger, rail, and menu semantics with the approved spec. Do not run `add`, do not accept generated `Button`, `Sheet`, skeleton, badge, submenu, right-side, floating, or inset-variant code.

- [ ] **Step 2: Extend the contract test for behavioral invariants**

Append assertions that the primitive source:

- imports `useSidebarViewport`, `defaultSidebarOpen`, and `shouldHandleSidebarShortcut`;
- uses `data-state`, `data-viewport`, and `data-mobile-open`;
- uses one `keydown` listener and calls `preventDefault()` for the accepted shortcut;
- closes `openMobile` when leaving mobile mode;
- imports Base UI Tooltip and never imports a Sheet;
- uses `cn` and never includes raw hex/HSL colors.

Run: `node --test tests/sidebar-contract.test.ts`

Expected: the original missing-file failure changes to specific missing-export/behavior failures after the file is created in the next step.

- [ ] **Step 3: Implement `SidebarProvider` and `useSidebar`**

In `frontend/src/components/ui/sidebar.tsx`:

1. add `"use client"`;
2. create a context initialized to `null` and a `useSidebar` hook that throws outside the provider;
3. support controlled and uncontrolled desktop `open` state;
4. keep mobile `openMobile` independent;
5. use a `userChangedDesktopState` ref so the first ready viewport applies its breakpoint default, while later resizes do not erase a user's explicit desktop/tablet choice;
6. close mobile state whenever `viewport !== "mobile"`;
7. route `toggleSidebar` to `openMobile` on mobile and desktop `open` otherwise;
8. install Command/Control+B through `shouldHandleSidebarShortcut`;
9. render a provider wrapper with `data-state`, `data-viewport`, `data-ready`, and `data-mobile-open`.

The provider wrapper must not calculate viewport-dependent inline markup before `ready`; CSS will use `data-ready="false"` plus media queries for the initial visual width.

- [ ] **Step 4: Implement the semantic primitives**

Each primitive forwards native element props, merges classes with `cn`, and adds stable `data-slot`/`data-sidebar` attributes:

```ts
Sidebar             // aside, id="chat-sidebar", aria-label supplied by caller
SidebarHeader       // div
SidebarContent      // div; sole scroll owner
SidebarGroup        // section
SidebarGroupLabel   // h2 by default, supports tabIndex for empty-history focus
SidebarGroupContent // div
SidebarMenu         // ul
SidebarMenuItem     // li
SidebarMenuButton   // button; accepts isActive and optional collapsed tooltip
SidebarFooter       // div
SidebarInset        // section; combines caller inert with isMobile && openMobile
SidebarTrigger      // button; contextual aria-label and aria-expanded
SidebarRail         // button; desktop/tablet only, aria-label reflects action
```

`SidebarMenuButton` must accept:

```ts
type SidebarMenuButtonProps = React.ComponentProps<"button"> & {
  isActive?: boolean;
  tooltip?: string;
};
```

When `tooltip` is present, wrap only the trigger with Base UI `Tooltip.Root`, `Tooltip.Portal`, `Tooltip.Positioner side="right" sideOffset={8}`, and `Tooltip.Popup`. Mount the tooltip only when `state === "collapsed" && !isMobile`; expanded and mobile states render no tooltip popup.

- [ ] **Step 5: Implement mobile focus and Escape behavior in the provider layer**

Keep refs for the chat-header trigger and mobile sidebar close trigger inside the provider. `SidebarTrigger placement="inset"` registers the return target; `SidebarTrigger placement="sidebar"` registers the drawer target. When the mobile drawer opens, focus the sidebar trigger on the next animation frame. When it closes, return focus to the inset trigger.

The mobile Escape handler must:

1. do nothing while `escapeBlocked` is true;
2. close only the mobile drawer;
3. never collapse desktop/tablet state.

The page supplies `escapeBlocked={accountMenuOpen || activeAccountDialog !== null}`. This makes the Escape priority explicit and independent of effect registration order or DOM class queries.

- [ ] **Step 6: Run the primitive contract and type checks**

Run:

```bash
node --test tests/sidebar-contract.test.ts
npx tsc --noEmit
npm run lint -- src/components/ui/sidebar.tsx src/hooks/use-sidebar-viewport.ts src/lib/sidebar-state.ts
```

Expected: retained-export and provider-behavior assertions pass. The page-integration assertions remain red until Task 5. TypeScript and ESLint exit 0.

- [ ] **Step 7: Commit the primitive foundation**

Run:

```bash
git add frontend/src/components/ui/sidebar.tsx frontend/tests/sidebar-contract.test.ts frontend/DESIGN.md
git commit -m "feat: add composable sidebar primitives"
```

---

### Task 4: Compose the Jyotisha product sidebar and portal account menu

**Files:**
- Create: `frontend/src/components/app-sidebar.tsx`
- Modify: `frontend/tests/sidebar-contract.test.ts`
- Modify: `frontend/tests/starter-questions.test.ts`

**Interfaces:**

```ts
export type SidebarSession = {
  id: string;
  title: string;
  messageCount: number;
};

export type SidebarAccount = {
  name: string;
  email: string;
  credits: number;
  isAdmin: boolean;
  initial: string;
};

export type AppSidebarProps = {
  sessions: readonly SidebarSession[];
  activeSessionId: string | null;
  account: SidebarAccount;
  accountMenuOpen: boolean;
  accountTriggerRef: React.Ref<HTMLButtonElement>;
  newChatDisabled: boolean;
  creatingSession: boolean;
  onAccountMenuOpenChange: (open: boolean) => void;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onOpenProfile: () => void;
  onOpenRedeem: () => void;
  onOpenLogout: () => void;
};
```

- [ ] **Step 1: Add product-composition tests before implementation**

Extend `sidebar-contract.test.ts` to require:

- `AppSidebar` composes `SidebarHeader`, `SidebarContent`, `SidebarFooter`, and `SidebarRail`;
- collapsed history uses one `MessageSquareText` action and not a mapped list of icon-only sessions;
- selecting a session invokes `onSelectSession(session.id)` even while request state exists outside this component;
- account menu imports `Popover` from `@base-ui/react/popover`, uses `Popover.Portal`, and sets `collisionPadding={12}`;
- `AppSidebarProps` contains callbacks/data only and no Supabase, `fetch`, or API import.

Update the account assertions in `starter-questions.test.ts` to read `app-sidebar.tsx` for account popover/admin-link markup while keeping dialog routing assertions against `page.tsx`.

Run: `node --test tests/sidebar-contract.test.ts tests/starter-questions.test.ts`

Expected: product composition tests fail because `app-sidebar.tsx` does not exist.

- [ ] **Step 2: Implement brand and new-chat regions**

Create the header with the existing `brand-mark` plus `Jyotisha` wordmark. Create the existing new-chat button through `SidebarMenuButton`:

- expanded label: `正在创建` or `新对话`;
- collapsed visual: centered Plus icon;
- collapsed tooltip: `新对话`;
- disabled value comes exclusively from `newChatDisabled`;
- mobile activation closes the drawer only after invoking `onNewChat`.

- [ ] **Step 3: Implement history expansion and session rows**

Use `useSidebar()` and refs for the first session and history heading. In collapsed desktop/tablet state render one history control. Its handler must:

```ts
setOpen(true);
window.requestAnimationFrame(() => {
  (firstSessionRef.current ?? historyHeadingRef.current)?.focus();
});
```

Expanded/mobile content renders:

- focusable `聊天记录` heading;
- `暂无对话` for an empty array;
- one row per session with title, optional `${messageCount} 条消息`, `aria-current="page"`, and one-line truncation;
- `onSelectSession(session.id)` without a pending-request disabled prop.

After selection, close the drawer only when `isMobile`; leave desktop/tablet expansion unchanged.

- [ ] **Step 4: Implement the responsive account trigger and menu with Base UI Popover**

Use a controlled `Popover.Root open={accountMenuOpen} onOpenChange={onAccountMenuOpenChange}`. The trigger shows avatar/name expanded and avatar only collapsed. Configure the positioner from sidebar context:

```tsx
<Popover.Positioner
  side={isMobile || state === "expanded" ? "top" : "right"}
  align={isMobile || state === "expanded" ? "end" : "center"}
  sideOffset={8}
  collisionPadding={12}
>
```

Keep the current identity header, profile action, redeem action/balance, administrator-only `/admin/codes` link, separator, and logout action. Each task action first closes the popover and then invokes its callback. Do not render task forms here.

When state or viewport changes while the popover is open, close it through `onAccountMenuOpenChange(false)` so it cannot remain detached from its trigger.

- [ ] **Step 5: Run product tests and checks**

Run:

```bash
node --test tests/sidebar-contract.test.ts tests/starter-questions.test.ts
npx tsc --noEmit
npm run lint -- src/components/app-sidebar.tsx
```

Expected: product/account structural tests pass; page-integration portions remain red. TypeScript and ESLint exit 0.

- [ ] **Step 6: Commit the product composition**

Run:

```bash
git add frontend/src/components/app-sidebar.tsx frontend/tests/sidebar-contract.test.ts frontend/tests/starter-questions.test.ts
git commit -m "feat: compose Jyotisha app sidebar"
```

---

### Task 5: Replace page-local sidebar state and markup

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/tests/sidebar-contract.test.ts`

**Interfaces:**
- Consumes: existing `sessions`, `activeSession`, `profile`, `account`, `creatingSession`, request locks, account dialog handlers, and refs.
- Produces: typed props/callbacks for `AppSidebar`; no sidebar responsive state in the page.

- [ ] **Step 1: Import the new composition and remove obsolete imports/state/refs**

Add imports for `AppSidebar`, `SidebarProvider`, `SidebarInset`, and `SidebarTrigger`. Remove sidebar-only Lucide icons from `page.tsx` once no longer used there.

Delete:

```ts
const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
const accountMenu = useRef<HTMLDivElement>(null);
const mobileMenuTrigger = useRef<HTMLButtonElement>(null);
const sidebar = useRef<HTMLElement>(null);
const sidebarCloseButton = useRef<HTMLButtonElement>(null);
```

Delete the page-local mobile-drawer focus effect and page-local account outside-click/Escape effect; Base UI Popover and `SidebarProvider` now own those interactions. Keep `accountTrigger`, because account dialogs return focus to it.

- [ ] **Step 2: Isolate page-owned session callbacks**

Change `startNewChat` only by removing `setMobileSidebarOpen(false)`.

Add:

```ts
function selectSession(sessionId: string) {
  setActiveSessionId(sessionId);
  setDraft("");
  setComposerNotice("");
}
```

Do not add request-state guards to `selectSession`; reading another session remains available during an answer.

- [ ] **Step 3: Build serializable view data without moving domain types**

Immediately before the successful return, derive:

```ts
const sidebarAccount = {
  name: profile.name.trim() || account.user.email || "账户",
  email: account.user.email || "尚未读取邮箱",
  credits: account.credits,
  isAdmin: account.isAdmin,
  initial: profile.name.trim().slice(0, 1)
    || account.user.email?.slice(0, 1).toUpperCase()
    || "你",
};

const sidebarSessions = sessions.map((session) => ({
  id: session.id,
  title: session.title,
  messageCount: session.messages.length,
}));
```

These are client-to-client props; no server serialization boundary is introduced.

- [ ] **Step 4: Replace the shell markup**

Use this hierarchy:

```tsx
<SidebarProvider escapeBlocked={accountMenuOpen || activeAccountDialog !== null}>
  <main className="chat-app">
    <AppSidebar
      sessions={sidebarSessions}
      activeSessionId={activeSession?.id ?? null}
      account={sidebarAccount}
      accountMenuOpen={accountMenuOpen}
      accountTriggerRef={accountTrigger}
      newChatDisabled={!hydrated || !modelCatalog || creatingSession || Boolean(pendingSessionId) || cancellationPending}
      creatingSession={creatingSession}
      onAccountMenuOpenChange={setAccountMenuOpen}
      onNewChat={() => void startNewChat()}
      onSelectSession={selectSession}
      onOpenProfile={() => openAccountDialog("profile")}
      onOpenRedeem={() => openAccountDialog("redeem")}
      onOpenLogout={() => openAccountDialog("logout")}
    />
    <SidebarInset className="chat-panel" inert={activeAccountDialog !== null}>
      {/* existing chat panel contents */}
    </SidebarInset>
    {/* existing account task-dialog overlays remain siblings inside main */}
  </main>
</SidebarProvider>
```

Pass `escapeBlocked={accountMenuOpen || activeAccountDialog !== null}` to `SidebarProvider`, and render `SidebarTrigger placement="inset"` in the chat header. `AppSidebar` renders `SidebarTrigger placement="sidebar"` as the mobile close control in its brand row; CSS hides it outside the open mobile drawer.

Remove the old backdrop, inline `<aside>`, footer/menu markup, and mobile-only trigger. Put `SidebarTrigger` immediately before the existing chat title block.

`SidebarInset` must combine the caller's modal inertness with its own `isMobile && openMobile`; the page must never calculate drawer inertness itself.

- [ ] **Step 5: Preserve Escape ordering explicitly**

Confirm the existing account-dialog keydown listener remains registered only while a dialog is open. Base UI Popover consumes Escape while the account menu is open. Assert in `sidebar-contract.test.ts` that the page passes `escapeBlocked={accountMenuOpen || activeAccountDialog !== null}` and that the provider's mobile Escape branch returns while `escapeBlocked` is true.

- [ ] **Step 6: Run the page integration contract**

Run:

```bash
node --test tests/sidebar-contract.test.ts tests/starter-questions.test.ts
npx tsc --noEmit
npm run lint -- src/app/page.tsx src/components/app-sidebar.tsx src/components/ui/sidebar.tsx
```

Expected: all sidebar contract assertions pass; existing account/session tests pass; TypeScript and ESLint exit 0.

- [ ] **Step 7: Commit the page migration**

Run:

```bash
git add frontend/src/app/page.tsx frontend/tests/sidebar-contract.test.ts
git commit -m "refactor: migrate chat shell to app sidebar"
```

---

### Task 6: Implement the Jyotisha sidebar visual states

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/tests/sidebar-contract.test.ts`

**Interfaces:**
- Consumes: provider data attributes and stable primitive class/data-slot names.
- Produces: desktop/tablet grid widths, mobile drawer, collapsed rail, portal popup, tooltips, focus, and accessibility preference styles.

- [ ] **Step 1: Add semantic aliases and shell dimensions**

Add aliases beside the existing root tokens:

```css
--sidebar-background: var(--color-sidebar);
--sidebar-solid: var(--color-sidebar-solid);
--sidebar-foreground: var(--color-ink);
--sidebar-muted-foreground: var(--color-ink-secondary);
--sidebar-accent: var(--color-selected);
--sidebar-accent-foreground: var(--color-ink);
--sidebar-border: var(--color-border);
--sidebar-ring: var(--color-focus);
--sidebar-primary: var(--color-surface-dark);
--sidebar-primary-foreground: var(--color-on-dark);
--sidebar-width-desktop: 288px;
--sidebar-width-tablet: 240px;
--sidebar-width-icon: 64px;
--sidebar-width-mobile: min(86vw, 320px);
```

Use these aliases everywhere in the new sidebar selectors.

- [ ] **Step 2: Replace the desktop/tablet shell rules**

The provider wrapper fills `100dvh`. `.chat-app` remains a two-column grid whose first column is selected by provider data:

- desktop expanded: `288px`;
- tablet expanded: `240px`;
- desktop/tablet collapsed: `64px`;
- mobile: `1fr`.

Do not add `transition: width` or `transition: grid-template-columns`. Collapsed labels may use opacity/transform but must also leave the accessibility tree only when their control has a replacement accessible label.

- [ ] **Step 3: Make `SidebarContent` the only sidebar scroll owner**

Set the sidebar shell to a fixed-height flex column. Header/footer use `flex: 0 0 auto`; content uses `min-height: 0; overflow-y: auto`. Remove `overflow-y: auto` from `.session-list` so large histories do not create a nested scrollbar.

Keep one-line session truncation and the existing active marker.

- [ ] **Step 4: Style collapsed rail content**

At `data-state="collapsed"` and non-mobile viewport:

- center the 44px logo/new-chat/history/avatar controls in 64px;
- hide wordmark, session list, metadata, and account text visually;
- keep full accessible names through `aria-label`/tooltip trigger text;
- show `SidebarRail` as a narrow edge target with a visible focus ring;
- do not render or style repeated session icons.

Use 120ms opacity/transform/color transitions only. Disabled new-chat remains visibly disabled.

- [ ] **Step 5: Port the existing mobile drawer to provider data attributes**

Below 768px:

- make grid one column;
- position sidebar fixed at the left with `width: var(--sidebar-width-mobile)`;
- translate it fully off-canvas when `data-mobile-open="false"`;
- show a fixed scrim only when open;
- use the existing 180ms transform/opacity/visibility choreography;
- add safe-area padding;
- hide `SidebarRail`;
- render full expanded labels regardless of desktop `open` state.

Remove all `.sidebar-open` selectors because the class no longer exists.

- [ ] **Step 6: Style portal account menu and collapsed tooltips**

Replace `.account-menu { position: absolute; right: 0; bottom: ... }` with Base UI positioner/popup rules:

- positioner owns z-index and viewport constraints;
- popup width remains `min(280px, calc(100vw - var(--space-6)))`;
- background, border, radius, and shadow stay token-based;
- starting/ending styles use opacity and 4px transform;
- transform origin follows Base UI's origin custom property if exposed.

Tooltip popup uses the sidebar solid/canvas surface, border, caption typography, and a 120ms opacity/translate entry. It must never intercept pointer events.

- [ ] **Step 7: Preserve accessibility preferences**

Extend existing media rules:

```css
@media (prefers-reduced-motion: reduce) { /* remove sidebar/popup/tooltip transforms */ }
@media (prefers-reduced-transparency: reduce) { /* use --sidebar-solid; remove blur */ }
@media (prefers-contrast: more) { /* strengthen border/current marker/focus outline */ }
```

Do not replace the existing rules for other components; merge sidebar selectors into them.

- [ ] **Step 8: Remove obsolete selectors and run contract checks**

Delete old `.sidebar-backdrop`, `.sidebar-close`, `.mobile-menu`, `.sidebar-open`, absolute account-menu anchoring, and redundant session-list scroll rules after their replacements exist.

Run:

```bash
node --test tests/sidebar-contract.test.ts tests/starter-questions.test.ts
npm run lint
npx tsc --noEmit
git diff --check -- frontend/src/app/globals.css frontend/tests/sidebar-contract.test.ts
```

Expected: all tests, lint, TypeScript, and whitespace checks pass; no contract references the old class-based drawer state.

- [ ] **Step 9: Commit the visual implementation**

Run:

```bash
git add frontend/src/app/globals.css frontend/tests/sidebar-contract.test.ts
git commit -m "style: add responsive sidebar rail and drawer"
```

---

### Task 7: Verify behavior, accessibility, and production output

**Files:**
- Modify only if a verified issue is found: sidebar files from Tasks 2–6 and their tests.

- [ ] **Step 1: Run the complete automated suite**

Run:

```bash
npm test
npm run lint
npx tsc --noEmit
npm run build
```

Expected: all commands exit 0. The production build must not report hydration warnings, missing CSS imports, or client/server boundary errors.

- [ ] **Step 2: Start the local preview without real API mutations**

Run: `npm run dev`

Open `http://localhost:3000/?preview=conversation`. Use only preview modes for visual checks unless the user explicitly asks to exercise cloud-backed data.

- [ ] **Step 3: Verify the three required viewport widths**

At 1280px:

- initial width is 288px;
- trigger and rail collapse to 64px and expand again;
- chat resizes beside the rail rather than being covered;
- logo, new-chat, one history action, and account avatar remain useful;
- tooltips appear for keyboard focus and pointer hover only while collapsed.

At 768px:

- initial state is the 64px rail;
- expansion is 240px;
- no overlay or scrim appears;
- Chinese session titles truncate without horizontal overflow.

At 375px:

- initial drawer is closed and no rail remains;
- header trigger opens `min(86vw, 320px)` drawer;
- focus moves into the drawer;
- scrim and Escape close it and return focus;
- chat becomes inert only while the drawer is open.

- [ ] **Step 4: Verify state and content edge cases**

Check empty, one-session, many-session, and very-long-title states. Confirm:

- collapsed history action expands and focuses the first session without selecting it;
- empty history focuses the `聊天记录` heading and shows `暂无对话` expanded;
- long history scrolls only `SidebarContent`; header/footer remain fixed;
- selecting a session while another session answers remains possible;
- selecting on mobile closes the drawer; selecting on desktop/tablet does not collapse it;
- new-chat loading and disabled states match current business locks.

- [ ] **Step 5: Verify account surfaces from every sidebar state**

From desktop expanded, desktop collapsed, tablet collapsed, and mobile drawer:

- account popover is fully visible and collision-safe;
- expanded/mobile placement is above the footer;
- collapsed placement is to the avatar's right;
- profile, redeem, logout confirmation, and administrator navigation route correctly;
- dialogs remain above the drawer/popover and return focus to the account trigger;
- Escape closes one topmost surface at a time.

- [ ] **Step 6: Verify keyboard and preference behavior**

Confirm:

- Command+B on macOS and Control+B elsewhere toggles the sidebar;
- the shortcut does nothing while focus is in input, textarea, select, or contenteditable;
- all controls have a visible focus ring and at least a 44px target;
- reduced-motion removes translations without breaking state changes;
- reduced-transparency uses an opaque warm background and no blur;
- increased contrast preserves borders, focus, and the active-session marker.

- [ ] **Step 7: Inspect runtime evidence**

Confirm the browser console has no React, hydration, accessibility, or Base UI warnings. Confirm there is no invisible scrim, stale `inert`, double scrollbar, clipped popup, or horizontal overflow after repeated resize/open/close cycles.

- [ ] **Step 8: Run the final diff audit**

Run:

```bash
git status --short
git diff --check HEAD
git diff --stat HEAD~5..HEAD
git diff HEAD~5..HEAD -- frontend/src frontend/tests frontend/DESIGN.md
```

Expected: only planned sidebar/design/test files are included; unrelated research manifests, assets, and `frontend/plans/` remain uncommitted and untouched.

- [ ] **Step 9: Commit only verified follow-up fixes, if any**

If QA required changes, stage only the affected planned files and commit:

```bash
git commit -m "fix: polish sidebar interaction states"
```

If QA required no changes, do not create an empty commit. Do not push; hand the verified local branch back to the user for local acceptance.

---

## Completion Gate

Implementation is complete only when all of the following are true:

- [ ] All 13 acceptance criteria in the approved design spec are satisfied.
- [ ] `npm test`, `npm run lint`, `npx tsc --noEmit`, and `npm run build` pass.
- [ ] Manual checks at 375px, 768px, and 1280px pass.
- [ ] Account popover/dialog behavior is unchanged except for responsive anchoring.
- [ ] Session reading remains available during an active answer.
- [ ] No raw colors, stock shadcn palette, nested scroll owner, invisible overlay, stale inert state, or hydration warning remains.
- [ ] The final diff contains no unrelated user changes.
- [ ] No push has been performed.
