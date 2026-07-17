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

### Navigation item

- **Structure:** title, optional metadata, current-state marker.
- **States:** default, hover, current, focus, disabled.
- **Surface:** translucent warm-gray sidebar; current uses a white glass surface and deep-brown marker.

### Message

- **Variants:** assistant editorial text on canvas; user text on warm card surface; streaming; error.
- **Identity:** every assistant message carries the 32px Jyotisha logo avatar; user messages stay visually lighter and avatar-free.
- **Typography:** assistant body 16px with serif subheadings; user body 14px.
- **Suggestions:** keep follow-up actions compact, with 8px internal horizontal padding and a narrower 680px group width.
- **Motion:** new messages enter with a short opacity/translate transition only.

### Suggestion card

- **Structure:** topic label, question, directional icon. Categories are not numbered because they have no required order. At tablet widths, the cards stack into one column so Chinese questions keep natural phrase boundaries beside the persistent sidebar.
- **Surface:** warm light cards; the lead card uses the pale brown emphasis surface and border instead of a dark block.
- **States:** default, hover, active, focus, disabled, loading, fallback notice.

### Start greeting

- **Content:** invite the user to ask what matters now; do not repeat that birth data is ready or explain setup state.
- **Timing:** use the browser's local hour: morning 05:00–10:59, noon 11:00–13:59, afternoon 14:00–17:59, evening 18:00–22:59, and late night 23:00–04:59.
- **Variation:** each time band has three concise prompts; select one once per visit so re-renders do not change the sentence.

### Account sheet

- **Structure:** title, account summary, redeem section, profile form, actions.
- **Surface:** canvas sheet over warm scrim; the account summary and sections are separated by hairlines rather than dark cards.
- **States:** closed, opening, open, validation error, success, saving.

### Admin panel and data table

- **Structure:** editorial header, cream form panels, and a light data table separated by warm hairlines.
- **States:** loading, empty, populated, generated codes, error, copy success.
- **Responsive:** form collapses to two columns then one; table scrolls horizontally.

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
|---|---:|---|---|
| Micro | 120ms | ease-out | Button and row feedback |
| Standard | 180ms | `cubic-bezier(.22, 1, .36, 1)` | Sheet, sidebar, message entry |
| Emphasis | 360ms | `cubic-bezier(.16, 1, .3, 1)` | Loading mark only |

Only `transform`, `opacity`, and color/filter transitions animate. Reduced-motion disables non-essential animation. Motion communicates state; decorative looping is limited to an active loading state.

## 7. Depth & Surface

Strategy: warm tonal shifts, restrained translucency, and fine hairlines. Most depth comes from the page floor, main canvas, warm cards, and selected white glass. Standard UI uses no drop shadow. Modal and raised-sheet depth use one restrained two-stage token: `--shadow-elevated: 0 1px 2px rgba(29, 29, 31, .07), 0 12px 28px -16px rgba(29, 29, 31, .18)`. Interactive rings use `0 0 0 1px` or the focus ring; no generic card shadows or atmospheric gradients. When transparency is reduced, frosted surfaces fall back to opaque warm neutrals.
