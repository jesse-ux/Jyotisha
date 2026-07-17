# Lightweight Palette Restoration Implementation Plan

**Goal:** Restore the light, precise material balance of commit `1b91667` while preserving the current product structure, typography, responsive layout, and chat behavior.

**Design rule:** Use warm light surfaces for roughly ninety percent of the interface. Reserve dark ink for compact, high-signal controls and user-authored messages. Use deep brown as a scarce accent, not as a page-scale fill.

## Task 1: Lock the palette contract

- Add a focused static test for the approved warm-gray palette.
- Assert that page-scale components no longer use dark surface tokens.
- Run the test once to prove it fails against the current design.

## Task 2: Update the design system contract

- Update `frontend/DESIGN.md` with the restored palette values.
- Document the light sidebar, light editorial recommendation cards, light authentication story panel, light account summary, and light admin table.
- Keep the existing typography, spacing, motion, and responsive rules.

## Task 3: Restore the palette and material distribution

- Update `frontend/src/app/globals.css` tokens and Tailwind theme aliases.
- Convert the sidebar to a translucent warm-gray surface with dark text.
- Convert page-scale dark panels to light surfaces and warm hairlines.
- Keep primary buttons and compact message accents visually decisive.
- Add reduced-transparency fallbacks for frosted header, composer, and sidebar surfaces.

## Task 4: Verify behavior and presentation

- Run the focused palette contract test, existing frontend contract tests, lint, type checking, and the production build.
- Inspect login, empty chat, active conversation, account sheet, and admin views at 375px, 768px, and 1280px.
- Fix only regressions introduced by this palette restoration.
