# Chat Header Sidebar Trigger Design

## Problem

The production chat header renders its sidebar trigger as an empty button, so the control exists in the layout but has no visible icon. The header also uses `display: flex` with `justify-content: space-between`, which makes the active session title appear centered between the invisible trigger and the credit control instead of anchoring it to the left.

## Scope

Fix the existing chat shell without changing session data, sidebar state ownership, keyboard shortcuts, request flow, or account behavior. The header keeps exactly one visible sidebar trigger beside the active session title on every viewport.

## Selected Approach

The shared `SidebarTrigger` primitive renders a stable `PanelLeft` icon and retains its current localized `aria-label`, `aria-expanded`, click composition, and 44px target. The app sidebar brand row stops rendering a duplicate trigger.

The chat header becomes a three-column grid:

1. sidebar trigger (`auto`),
2. flexible title and status (`minmax(0, 1fr)`),
3. credit control (`auto`).

The title column is explicitly left-aligned and may shrink safely. Existing ellipsis behavior remains in place for long session titles. Mobile keeps the same column order and compact spacing.

## Component and State Behavior

- `SidebarTrigger` owns its icon so every consumer receives a visible, accessible control.
- The inset trigger opens or collapses the sidebar using the existing provider state.
- The mobile drawer closes through its scrim or Escape; focus moves to the drawer surface when opened and returns to the inset trigger when closed.
- Desktop and tablet keep their existing expanded and collapsed widths.
- Sidebar state changes remain immediate; the trigger glyph does not morph, scale, or fade.

## Design-System Update

`frontend/DESIGN.md` will record the single-trigger placement and immediate sidebar motion. Existing color, typography, spacing, radius, and focus tokens remain unchanged.

## Failure Boundaries

- A consumer-provided trigger click handler may still cancel the default toggle with `preventDefault()`.
- Long or CJK session titles must truncate inside the flexible column without pushing the credit control off-screen.
- The fix must not make the sidebar brand row expose a second collapse control.
- The mobile drawer must remain keyboard closable and must not lose its focus target after the duplicate trigger is removed.

## Verification

- Extend the sidebar contract tests for the `PanelLeft` icon, single trigger placement, grid columns, left alignment, stable focus target, and immediate state changes.
- Run the complete frontend test suite, lint, and production build.
- Exercise desktop and mobile layouts in a real browser: visible trigger, title alignment, collapse/expand, drawer open/close, long-title truncation, keyboard focus, and credit-control positioning.
- After deployment, verify the production login route, logged-out account response, internal API health, and the authenticated chat header visually.
