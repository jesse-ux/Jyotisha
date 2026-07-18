# Jyotisha Web Design System

This file adapts the full visual analysis in `CLAUDE_DESIGN.md` to the shipped Jyotisha application. `CLAUDE_DESIGN.md` remains the upstream reference; this file is the implementation contract.

## 1. Atmosphere & Identity

Jyotisha feels like a private reading room: warm, editorial, grounded, and quiet enough for reflective conversation. The signature is a pale parchment canvas, translucent warm-gray navigation, fine neutral hairlines, and restrained deep-brown accents. Serif display type gives astrological guidance the gravity of a considered essay rather than a generic chatbot.

## 2. Color

### Palette

| Role | Token | Value | Usage |
|---|---|---:|---|
| Canvas | `--color-canvas` | `#fbfaf7` | Main reading surface, inputs, light controls |
| Page floor | `--color-canvas-soft` | `#f3f2ee` | App background and quiet secondary bands |
| Warm surface | `--color-canvas-muted` | `#ebe9e3` | Cards, user messages, table headings |
| Strong neutral | `--color-canvas-strong` | `#e1ded6` | Pressed and emphasized neutral surfaces |
| Sidebar glass | `--color-sidebar` | `rgba(235, 233, 227, .86)` | Desktop and mobile navigation |
| Selected surface | `--color-selected` | `rgba(255, 255, 255, .62)` | Current navigation and raised light rows |
| Ink | `--color-ink` | `#1d1d1f` | Headlines and primary text |
| Body | `--color-ink-strong` | `#32322f` | Strong body copy |
| Secondary text | `--color-ink-secondary` | `#676762` | Supporting copy and labels |
| Tertiary text | `--color-ink-tertiary` | `#8a8983` | Hints and metadata |
| Primary action | `--color-action` | `#85432f` | High-signal links, rings, and compact actions |
| Primary soft | `--color-action-soft` | `#f4e8e2` | Editorial emphasis without a dark block |
| Primary active | `--color-action-hover` | `#6f3627` | Hover and pressed action |
| Dark punctuation | `--color-surface-dark` | `#1d1d1f` | Compact primary buttons and user-authored emphasis only |
| On dark | `--color-on-dark` | `#fbfaf7` | Text on compact dark controls |
| Hairline | `--color-border` | `#d8d6cf` | Default separators and controls |
| Strong hairline | `--color-border-strong` | `#b8b5ad` | Inputs and higher-contrast dividers |
| Success | `--color-success` | `#28633e` | Available and completed states |
| Warning | `--color-warning` | `#b07b22` | Caution states |
| Error | `--color-danger` | `#9a2f2f` | Errors and destructive actions |
| Accessible focus | `--color-focus` | `#85432f` | Keyboard focus and input focus |

Rules: neutrals stay warm; the action color is scarce; roughly ninety percent of the interface remains light. Dark ink is punctuation, never a page-scale surface. No raw color may appear in UI styles outside these tokens and their documented alpha mixes.

## 3. Typography

### Font stacks

- Display: `"Tiempos Headline", "Songti SC", "STSong", "Noto Serif CJK SC", Georgia, serif`. The licensed Copernicus/Tiempos files are unavailable; the Chinese Song serif stack is the declared production substitute.
- Body/UI: `StyreneB, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`.
- Code/data: `"JetBrains Mono", "SFMono-Regular", Consolas, monospace`.

### Scale

| Token | Size | Weight | Line height | Tracking | Usage |
|---|---:|---:|---:|---:|---|
| `--type-display-lg` | `48px` | 400 | 1.1 | `-1px` | Desktop page titles |
| `--type-display-md` | `36px` | 400 | 1.15 | `-.5px` | Dialog and mobile page titles |
| `--type-display-sm` | `28px` | 400 | 1.2 | `-.3px` | Section titles |
| `--type-title-lg` | `22px` | 500 | 1.3 | 0 | Prominent UI titles |
| `--type-title-md` | `18px` | 500 | 1.4 | 0 | Card and message headings |
| `--type-title-sm` | `16px` | 500 | 1.4 | 0 | List titles |
| `--type-body-md` | `16px` | 400 | 1.55 | 0 | Default reading text |
| `--type-body-sm` | `14px` | 400 | 1.55 | 0 | Compact UI text |
| `--type-caption` | `13px` | 500 | 1.4 | 0 | Labels and metadata |
| `--type-overline` | `12px` | 500 | 1.4 | `1.5px` | Eyebrows and badges |

Display headings use the serif stack at weight 400. Body copy never drops below 14px; 12–13px is reserved for short labels and metadata. CJK text uses `text-wrap: pretty`; display text uses `text-wrap: balance`.

## 4. Spacing & Layout

The base unit is 4px. Tokens are `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--space-5: 20px`, `--space-6: 24px`, `--space-8: 32px`, `--space-10: 40px`, `--space-12: 48px`, `--space-16: 64px`, and `--space-24: 96px`.

- Chat reading width: 760px for the welcome/composer and 900px for long answers.
- Admin content width: 1200px, centered.
- Desktop shell: 288px sidebar plus flexible reading panel.
- Breakpoints: mobile below 768px, tablet 768–1023px, desktop 1024px and above.
- All full-height surfaces use `100dvh`. Touch targets are at least 44px.

## 5. Components

### Brand mark

- **Structure:** image-backed mark plus serif wordmark.
- **Variants:** light canvas, dark sidebar.
- **States:** static; never animated.
- **Accessibility:** decorative image is hidden when adjacent text names the product.

### Button

- **Variants:** ink primary, cream secondary, text, circular icon, deep-brown emphasis.
- **Spacing:** 44px minimum height; radii 8px for standard and full radius for icon-only.
- **States:** default, hover, active, focus-visible, disabled, loading.
- **Motion:** 120ms transform/color; active translates by 1px or scales to .98.

### Input and composer

- **Structure:** warm canvas field, hairline, typed value, optional icon action.
- **States:** default, hover, focus with deep-brown ring, disabled, invalid, loading.
- **Accessibility:** persistent label where practical; composer has an explicit accessible label.

### Birth time intake

- **Structure:** birth date, five radio choice rows for time knowledge, then only the time, uncertainty, period, or clue field required by the selected source.
- **Surface:** choice rows use the warm canvas and hairline system; the selected row uses `--color-action-soft` with a deep-brown border, never a dark promotional card.
- **States:** no source selected, source selected, source-specific details incomplete, ready to continue, assessing, rectifying, candidate saved, confirmed.
- **Copy:** labels describe what the user actually knows. Candidate results explicitly distinguish a reported time, a candidate range, and an active chart time.
- **Accessibility:** native radio inputs remain focusable, every conditional field has a persistent label, status text uses live regions, and the complete flow is keyboard operable.
- **Motion:** source-dependent fields enter with the existing 180ms opacity/vertical reveal; reduced-motion removes the translation.
- **Life-event evidence:** after deterministic questionnaire completion, render three structured event rows by default and allow up to six. Each row uses a domain select, a precision select, and a matching year/month/day control; free-form descriptions are not part of scoring.
- **Candidate result:** keep the reported range, candidate interval, confidence, and active-time status visually separate. Low confidence keeps evidence editing open; medium offers save or add evidence; high uses a separate confirmation action and never labels the representative minute as the true birth time.
- **Evidence accessibility:** every row keeps visible labels, validation errors use live regions, add/remove controls retain 44px targets, and scoring/confirmation loading states disable duplicate submission without hiding the existing evidence.
- **One-question guide:** the guided journey renders only the persisted `nextAction` and one server-selected question. A deterministic question is visible immediately; Agent wording may replace it without changing the question identity, domain, precision request, progress, or permissions. The composer explicitly permits an approximate year and keeps skip and pause as secondary 44px actions.
- **Draft review:** natural-language answers become one inline review card. The evidence domain is read-only and uses its Chinese label; precision controls which exact year, month, or day input is available. Incomplete drafts keep edit and skip paths visible, while confirmation is disabled until the structured date is valid. Status and errors use polite or assertive live regions without clearing the persisted journey.
- **Scoring and retry:** `score_pending` is a quiet progress surface with cancellable bounded polling and no manual compare control. `retry_scoring` preserves the confirmed evidence and exposes one explicit retry action. Refresh and device changes resume from the persisted action rather than inferring progress from copy.
- **Guided candidate states:** low confidence presents the saved candidate range and either another evidence question or a safe finish; medium confidence can save the range but never apply a representative minute; high confidence names both “候选时间” and “当前排盘使用时间” before explicit confirmation; ready states that the current chart time changed while the original report remains preserved. No state calls a candidate the true birth minute.
- **Guided responsive/accessibility contract:** body copy remains at least 14px, labels at least 12px, and all controls at least 44px. Focus is always visible, the composer is keyboard operable, semantic Chinese phrases remain together at 390px, and reduced-motion removes entrance translation while retaining state changes.

### Birth date picker

- **Composition:** shadcn outline Button trigger, Base UI Popover, and a single-select React DayPicker Calendar.
- **Range:** local dates from 1900-01-01 through today; future dates are disabled. Month and year dropdowns provide direct navigation, with newest years first.
- **Value:** display Chinese long dates while emitting the existing `YYYY-MM-DD` profile value without UTC conversion.
- **States:** empty, open, selected, focus-visible, disabled confirmed profile, and unavailable date.
- **Accessibility:** visible label, explicit trigger naming, 44px targets, keyboard calendar navigation, focus return, and collision-safe popup positioning.

### Model selector

- **Structure:** a compact text trigger sits below the composer and opens an upward popover aligned to its left edge. The trigger shows only the active model name; each option shows only its model name and radio selection state.
- **Width:** the popover is capped at 180px with viewport collision protection.
- **Surface:** canvas trigger with no card treatment; the popover uses the elevated canvas recipe, warm hairlines, and one selected-surface row. The action color is reserved for the selected indicator and focus ring.
- **States:** closed, open, hover, focus-visible, selected, disabled, and unavailable catalog. Selecting a model closes the popover and only affects later messages in the current conversation.
- **Accessibility:** the trigger and every option meet the 44px touch target; options are a native radio group, with a small roving-focus fallback so Tab, arrow keys, Space, and screen readers consistently expose the selected model inside the popover.
- **Motion:** the popup enters over 120ms with opacity and a 4px vertical translation; reduced-motion removes the translation.

### Navigation item

- **Structure:** title, optional metadata, current-state marker.
- **States:** default, hover, current, focus, disabled.
- **Request behavior:** existing sessions remain selectable for reading while a request is active; creating or sending another request stays locked until the active request settles.
- **Surface:** translucent warm-gray sidebar; current uses a white glass surface and deep-brown marker.

### Sidebar shell

- **Composition:** provider, fixed header, one scroll-owning content region, fixed footer, trigger, rail, and flexible chat inset.
- **Trigger placement:** the single visible collapse/expand trigger sits beside the active session title in the chat header. The sidebar brand row has no duplicate trigger.
- **Desktop:** 288px expanded by default at 1024px and above; 64px collapsed icon rail.
- **Tablet:** 64px collapsed by default from 768px through 1023px; 240px when expanded.
- **Mobile:** no icon rail; an off-canvas drawer uses `min(86vw, 320px)` and closes through its scrim or Escape.
- **Collapsed content:** logo, new-chat action, one history expansion action, and account avatar. Individual sessions do not become indistinguishable repeated icons.
- **Scroll ownership:** header and footer remain fixed; `SidebarContent` is the sole sidebar scroll owner.
- **Motion:** Sidebar state changes are immediate on desktop, tablet, and mobile. The 44px trigger keeps one stable 18px sidebar glyph and never enters an intermediate scale or opacity state.
- **Accessibility:** Command/Control+B shortcut outside editable controls, contextual trigger labels, 44px targets, focus return, collapsed-only tooltips, reduced-motion, reduced-transparency, and increased-contrast support.
- **State:** session-local; reload uses breakpoint defaults rather than cookie or local-storage persistence.

### Message

- **Variants:** assistant editorial text on canvas; user text on warm card surface; streaming; error.
- **Identity:** every assistant message carries the 32px Jyotisha logo avatar; user messages stay visually lighter and avatar-free.
- **Typography:** assistant body 16px with serif subheadings; user body 14px.
- **Suggestions:** keep follow-up actions compact, with 8px internal horizontal padding and a narrower 680px group width. The current set remains visible while the user types or selects a suggestion and leaves only when that question is submitted.
- **Motion:** new messages enter with a short opacity/translate transition only.

### Suggestion card

- **Structure:** topic label, question, directional icon. Categories are not numbered because they have no required order. At tablet widths, the cards stack into one column so Chinese questions keep natural phrase boundaries beside the persistent sidebar.
- **Surface:** warm light cards; the lead card uses the pale brown emphasis surface and border instead of a dark block.
- **States:** default, hover, active, focus, disabled, loading, fallback notice.
- **Visibility:** the three initial cards remain visible while the user types or chooses a question. They leave only after the question is submitted and the session receives its first user message.

### Start greeting

- **Content:** invite the user to ask what matters now; do not repeat that birth data is ready or explain setup state.
- **Timing:** use the browser's local hour: morning 05:00–10:59, noon 11:00–13:59, afternoon 14:00–17:59, evening 18:00–22:59, and late night 23:00–04:59.
- **Variation:** each time band has three concise prompts; select one once per visit so re-renders do not change the sentence.

### Account popover

- **Structure:** identity header, profile action, redeem action with balance, administrator-only code-management link, divider, and logout action.
- **Surface:** 280px elevated canvas popover anchored above the sidebar account trigger; warm hairline, existing elevated shadow, no nested cards.
- **States:** closed, open, hover, focus-visible, administrator, and logout routing.
- **Accessibility:** `aria-expanded`, `aria-controls`, menu semantics, 44px rows, outside-click and Escape dismissal, and focus return.

### Profile dialog

- **Structure:** profile title, existing profile fields, inline result, and save action.
- **Width:** 560px desktop maximum with viewport-safe spacing and internal scrolling.
- **States:** open, invalid, saving, success, and error.

### Redeem dialog

- **Structure:** current balance, redemption-code form, and inline result.
- **Width:** 420px desktop maximum.
- **States:** open, submitting, success, and error.

### Logout dialog

- **Structure:** confirmation title and explanation, cancel action, and destructive confirm action.
- **Width:** 400px desktop maximum.
- **States:** open, signing out, and error.

### Admin panel and data table

- **Structure:** editorial header, cream form panels, and a light data table separated by warm hairlines.
- **States:** loading, empty, populated, generated codes, error, copy success.
- **Responsive:** form collapses to two columns then one; table scrolls horizontally.

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
|---|---:|---|---|
| Micro | 120ms | ease-out | Button and row feedback |
| Standard | 180ms | `cubic-bezier(.22, 1, .36, 1)` | Sheet and message entry |
| Spatial | Instant | None | Sidebar state changes and mobile drawer |
| Emphasis | 360ms | `cubic-bezier(.16, 1, .3, 1)` | Loading mark only |

Only `transform`, `opacity`, and color/filter transitions animate. Reduced-motion disables non-essential animation. Motion communicates state; decorative looping is limited to an active loading state.

## 7. Depth & Surface

Strategy: warm tonal shifts, restrained translucency, and fine hairlines. Most depth comes from the page floor, main canvas, warm cards, and selected white glass. Standard UI uses no drop shadow. Modal and raised-sheet depth use one restrained two-stage token: `--shadow-elevated: 0 1px 2px rgba(29, 29, 31, .07), 0 12px 28px -16px rgba(29, 29, 31, .18)`. Interactive rings use `0 0 0 1px` or the focus ring; no generic card shadows or atmospheric gradients. When transparency is reduced, frosted surfaces fall back to opaque warm neutrals.

## 8. Agent wording and accuracy boundary

The Birth-Time Guide Agent controls wording only: it may choose a safe tone or extract a reviewable
draft, but it cannot select evidence domains, change `nextAction`, rank candidates, set confidence,
or grant save/apply permissions. Those decisions remain in the deterministic, versioned journey
state machine and its server-side scorer.

`confidence` is an internal, versioned safety gate for this product flow. It is not an external oracle,
clinical claim, or proof from calibrated real cases. Until matching external-engine parity and real-
case validation are complete, low and medium results never apply a minute, and high results still
require explicit confirmation of the matching representative time. Journey telemetry is limited to
metric name, phase, and optional confidence; it never records messages, dates, coordinates, case IDs,
or user IDs.
