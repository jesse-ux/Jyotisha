# Composable collapsible sidebar

Date: 2026-07-17

## 1. Decision

Replace the page-local sidebar implementation with a project-specific adaptation of the official shadcn Sidebar composition model.

The implementation will keep the shadcn structural vocabulary and interaction foundation—provider state, header/content/footer regions, desktop icon collapse, mobile off-canvas behavior, a shared trigger, keyboard shortcut, and rail—but it will not adopt the stock shadcn palette or ship the unmodified demo. Jyotisha's existing `frontend/DESIGN.md` remains the visual source of truth.

## 2. Goals

- Make the sidebar composable rather than embedding its layout and responsive state directly in the chat page.
- Let desktop users collapse the 288px sidebar into a useful 64px icon rail.
- Keep mobile behavior as an off-canvas drawer rather than an icon rail.
- Unify desktop, tablet, and mobile sidebar control behind one provider and one trigger contract.
- Preserve all current chat, session, account, onboarding, cancellation, and billing behavior.
- Preserve the warm editorial color, typography, radius, depth, and motion system.

## 3. Non-goals

- Do not redesign the chat header, conversation content, composer, model selector, or account dialogs.
- Do not introduce shadcn's default neutral palette or replace existing design tokens.
- Do not add a second navigation hierarchy, nested conversation folders, pinned sessions, search, session actions, or drag-to-resize.
- Do not render every conversation as an indistinguishable icon in collapsed mode.
- Do not persist the collapsed preference across page reloads in this version. The sidebar starts expanded after a reload on wide desktop and collapsed on tablet-sized layouts.
- Do not change API routes, database schema, session data, or account data contracts.

## 4. Architecture

The application shell will use this composition:

```text
SidebarProvider
├── AppSidebar
│   ├── SidebarHeader
│   │   └── brand
│   ├── SidebarContent
│   │   ├── new-chat action
│   │   └── conversation-history group
│   ├── SidebarFooter
│   │   └── account trigger and account popover
│   └── SidebarRail
└── SidebarInset
    └── chat panel
        └── chat header with SidebarTrigger
```

The generic primitives live in `frontend/src/components/ui/sidebar.tsx`. They own sidebar state, data attributes, responsive branching, keyboard shortcut behavior, and layout mechanics.

The product composition lives in `frontend/src/components/app-sidebar.tsx`. It owns Jyotisha-specific structure and labels, but receives all business data and actions through props. It does not fetch account data, mutate sessions, or call APIs.

The chat page remains the owner of sessions, the active session, account data, request locks, account dialogs, and navigation callbacks. It renders `SidebarProvider`, passes product state to `AppSidebar`, and wraps the existing chat panel in `SidebarInset`.

## 5. Generic sidebar primitives

The project-specific adaptation retains these public primitives:

- `SidebarProvider`: owns desktop expanded/collapsed state, mobile open state, current responsive mode, and `toggleSidebar`.
- `Sidebar`: the shell container and responsive desktop/mobile branch.
- `SidebarHeader`: fixed brand region.
- `SidebarContent`: the only vertically scrollable region inside the sidebar.
- `SidebarGroup`, `SidebarGroupLabel`, and `SidebarGroupContent`: semantic conversation-history grouping.
- `SidebarMenu`, `SidebarMenuItem`, and `SidebarMenuButton`: navigation structure with active and tooltip states.
- `SidebarFooter`: fixed account region.
- `SidebarInset`: the flexible chat surface beside the sidebar.
- `SidebarTrigger`: the single visible control used by desktop, tablet, and mobile.
- `SidebarRail`: the narrow desktop edge target that toggles expanded/collapsed state.
- `useSidebar`: exposes `state`, `open`, `setOpen`, `openMobile`, `setOpenMobile`, `isMobile`, and `toggleSidebar`.

Unused demo capabilities are removed rather than carried indefinitely. This version does not need right-side placement, inset/floating visual variants, nested submenu components, badges, skeleton loaders, or resizable width.

## 6. Product sidebar composition

### Header

Expanded state shows the Jyotisha logo and serif wordmark. Collapsed state shows only the logo, centered in the 64px rail. The logo remains static and is not itself used as the collapse control.

The chat header contains `SidebarTrigger` immediately before the conversation title. This replaces the separate mobile-only menu button. The trigger has an accessible label that reflects the current action: expand, collapse, open navigation, or close navigation.

### New-chat action

Expanded state shows the existing full-width `新对话` action with the Plus icon. Collapsed state shows a centered 44px icon button with a `新对话` tooltip.

The existing disabled and loading rules remain unchanged. Collapsing the sidebar never bypasses request locks or makes a disabled new-chat action interactive.

### Conversation history

Expanded state shows the existing `聊天记录` label and complete session list. Each row retains the title, optional message count, current-session marker, hover state, focus state, and current request behavior.

Collapsed state hides the individual session rows. It shows one conversation-history icon button with a `聊天记录` tooltip. Activating it expands the sidebar and, after the expanded content mounts, moves focus to the first session row. When history is empty, focus moves to a programmatically focusable group heading instead. This is intentional: conversations do not have distinct icons, so repeating one generic chat icon for every session would create an unusable rail.

Selecting a session keeps the current semantics:

- update the active session;
- clear the draft and composer notice;
- close the mobile drawer;
- leave the desktop sidebar state unchanged;
- remain available while another session is answering, as already documented in `frontend/DESIGN.md`.

### Footer and account

Expanded state shows the existing avatar and display name. Collapsed state shows only the centered avatar with an account tooltip.

The account popover remains the entry point for identity, profile, redemption, administrator codes, and logout confirmation. Its positioning changes by sidebar state:

- expanded desktop/tablet: above the account row, aligned within the sidebar;
- collapsed desktop/tablet: to the right of the avatar;
- mobile drawer: above the account row and within viewport collision bounds.

The popover must render through a portal or equivalent floating layer with collision protection so the collapsed sidebar cannot clip it. Existing account action routing and dialogs remain unchanged.

## 7. State model

The provider owns two independent state channels:

- desktop/tablet: `open`, represented as `expanded` or `collapsed`;
- mobile: `openMobile`, represented as drawer open or closed.

Account menu and account dialog state remain separate. Opening or closing the sidebar must not silently open or close a task dialog. Closing the mobile drawer closes the account popover if it is open, matching the current behavior.

Initial state:

- viewport at least 1024px wide: expanded;
- viewport from 768px through 1023px: collapsed;
- viewport below 768px: drawer closed.

Changing between responsive modes closes the mobile drawer and preserves a valid desktop state. A viewport transition must not leave the main chat surface inert or leave an invisible overlay mounted.

The collapsed preference is session-local. Reloading the page uses the initial state above. Persistent cookie or local-storage state is deferred to avoid introducing a server cookie read, hydration shift, or a dynamic rendering requirement into the current static homepage.

## 8. Interaction and keyboard behavior

- `SidebarTrigger` toggles the relevant desktop or mobile state.
- `SidebarRail` toggles desktop/tablet expanded state and is hidden on mobile.
- `Command+B` on macOS and `Control+B` elsewhere toggles the sidebar unless the shortcut originates from an editable control that already consumes the combination.
- Escape closes the topmost surface only: account dialog, then account popover, then mobile drawer. Desktop collapse is never triggered by Escape.
- Opening the mobile drawer moves focus to its close/trigger control.
- Closing the mobile drawer returns focus to the chat-header trigger.
- Opening conversation history from the collapsed rail expands the sidebar and focuses the first session row without selecting it; empty history focuses the group heading.
- Tooltips appear only in collapsed desktop/tablet state. They do not appear in the expanded sidebar or mobile drawer.
- Every trigger, rail action, menu row, and account control has a minimum 44px target.

## 9. Responsive layout and scroll ownership

### Desktop, 1024px and above

- Expanded sidebar: 288px.
- Collapsed sidebar: 64px.
- Sidebar and chat surface occupy a fixed `100dvh` shell.
- Changing width updates the shell boundary; it does not overlay the chat.

### Tablet, 768px through 1023px

- Default state: 64px icon rail.
- Users may expand to the existing compact 240px width.
- Expansion remains part of the shell and reduces the chat surface rather than covering it.

### Mobile, below 768px

- No icon rail is rendered.
- The same sidebar content opens as an off-canvas drawer.
- Width remains `min(86vw, 320px)`.
- A scrim closes the drawer on outside activation.
- Safe-area padding and the current 180ms transform/visibility behavior remain.

Scroll ownership is explicit:

- sidebar header and footer never scroll;
- `SidebarContent` owns sidebar vertical scrolling;
- the session list may fill available content height but does not create a second nested scrollbar;
- the chat conversation remains the chat panel's only reading scroll container;
- the composer and chat header remain fixed shell rows.

All flex/grid children that own scrolling receive `min-height: 0` or the logical equivalent so long histories cannot push the footer off-screen.

## 10. Visual system mapping

The shadcn semantic sidebar variables are aliases to Jyotisha tokens rather than a new palette:

| Sidebar role | Jyotisha source |
|---|---|
| background | `--color-sidebar` |
| solid reduced-transparency background | `--color-sidebar-solid` |
| foreground | `--color-ink` |
| secondary foreground | `--color-ink-secondary` |
| accent/selected | `--color-selected` |
| accent foreground | `--color-ink` |
| border | `--color-border` |
| focus ring | `--color-focus` |
| primary action | `--color-surface-dark` |
| primary action foreground | `--color-on-dark` |

No stock shadcn neutral colors, raw hex values, or untracked shadows may enter the sidebar styles. Existing typography, radii, selected-session marker, focus ring, translucent glass recipe, and reduced-transparency fallback remain authoritative.

Motion uses the existing system:

- 120ms for row, tooltip, and control feedback;
- 180ms with `--ease-out` for the mobile drawer transform;
- desktop shell width changes without interpolating a layout property; internal labels and icons use a short opacity/transform transition to clarify the state change;
- only transform, opacity, and color animate;
- reduced-motion makes the state change immediate without removing access to the state.

## 11. Dependency and generated-source policy

The repository is already configured for shadcn `base-nova`, Tailwind CSS 4, class variance authority, `cn`, and Lucide icons.

Implementation may begin with the official Sidebar registry source, but the generated diff must be reviewed before it is accepted:

- do not overwrite the existing `Button` implementation without an explicit compatibility review;
- add only the supporting primitives actually required by the retained Sidebar surface;
- keep Base UI conventions already used by the repository;
- remove unused generated variants and demo-only exports;
- map all generated theme variables to `frontend/DESIGN.md` before rendering the component.

The adapted component becomes maintained project source. It is not expected to remain byte-for-byte identical to future registry releases.

## 12. Error and edge states

- Empty history keeps the group label and an understated `暂无对话` state when expanded; collapsed mode still shows the history expansion control.
- Very long titles truncate to one line and expose their full title through the existing accessible name or tooltip behavior.
- Large session counts keep the header and footer visible and scroll only the content region.
- Missing account data preserves the existing loading/fallback label rather than rendering a broken avatar.
- An open account popover is repositioned or closed when the sidebar state changes; it must never become detached from its trigger.
- Mobile drawer overlays and modal overlays use the existing z-index order so a task dialog remains above navigation.
- Reduced transparency uses `--color-sidebar-solid` and removes backdrop blur.
- Higher contrast retains the strong border and visible current-session marker.

## 13. Migration sequence

1. Update `frontend/DESIGN.md` with the sidebar primitive, width states, scroll ownership, tooltip rules, and account-popover positioning.
2. Add and trim `frontend/src/components/ui/sidebar.tsx` plus only its required supporting primitives.
3. Create `frontend/src/components/app-sidebar.tsx` with typed data and callback props.
4. Wrap the chat shell with `SidebarProvider` and `SidebarInset`.
5. Replace the page-local mobile sidebar state, backdrop, trigger, and sidebar markup with the shared provider composition.
6. Adapt the account popover to portal-based responsive positioning without changing its task routing.
7. Remove obsolete sidebar CSS only after the new component covers desktop, tablet, and mobile states.
8. Run automated and manual verification before committing the implementation.

At each step, unrelated account, onboarding, consultation, birth-time, and model-selection logic remains untouched.

## 14. Acceptance criteria

1. The sidebar uses the documented shadcn-style composition and no longer embeds its structural markup directly in the chat page.
2. Desktop expands to 288px and collapses to a 64px icon rail without overlaying the chat.
3. Tablet defaults to a 64px rail and can expand to 240px.
4. Mobile uses the existing off-canvas interaction with no persistent icon rail.
5. The chat-header trigger and `Command/Control+B` control the correct responsive state.
6. Collapsed mode shows logo, new chat, conversation history, and account controls with useful tooltips.
7. Collapsed mode does not render one indistinguishable icon per session; the history control expands the list instead.
8. Header and footer remain fixed while long conversation history scrolls inside `SidebarContent`.
9. Current-session styling, session switching, request locks, new-chat behavior, and message counts remain unchanged.
10. The account popover works in expanded, collapsed, and mobile states without clipping; all account dialogs retain their current behavior.
11. The component uses Jyotisha design tokens exclusively and adds no stock shadcn palette.
12. Focus return, Escape priority, tooltips, 44px targets, reduced motion, reduced transparency, and increased contrast work in every responsive state.
13. No invisible drawer overlay, stale inert state, double scrollbar, horizontal overflow, hydration warning, or console error remains.

## 15. Verification plan

Automated checks:

- structural tests for provider composition and removal of page-local sidebar state;
- component behavior tests for desktop collapse, mobile open state, and history expansion routing where the logic can be isolated;
- existing frontend tests;
- TypeScript, ESLint, and production build.

Manual browser QA at 375px, 768px, and 1280px covers:

- expanded, collapsed, and drawer states;
- trigger, rail, and keyboard shortcut;
- empty, one-session, many-session, and very-long-title content;
- new-chat enabled, disabled, and loading states;
- session switching while another session is answering;
- account popover and all task dialogs from every sidebar state;
- Escape ordering, focus return, outside activation, and tooltip keyboard behavior;
- reduced motion, reduced transparency, and increased contrast;
- console warnings, hydration warnings, clipping, overflow, and scroll ownership.
