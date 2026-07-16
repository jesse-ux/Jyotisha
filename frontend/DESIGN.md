# Jyotisha Web Design System

This file adapts the full visual analysis in `CLAUDE_DESIGN.md` to the shipped Jyotisha application. `CLAUDE_DESIGN.md` remains the upstream reference; this file is the implementation contract.

## 1. Atmosphere & Identity

Jyotisha feels like a private reading room: warm, editorial, grounded, and quiet enough for reflective conversation. The signature is a parchment canvas paced by terracotta actions and deep ink product surfaces, with serif display type giving astrological guidance the gravity of a considered essay rather than a generic chatbot.

## 2. Color

### Palette

| Role | Token | Value | Usage |
|---|---|---:|---|
| Canvas | `--color-canvas` | `#faf9f5` | Page floor, inputs, light controls |
| Soft canvas | `--color-canvas-soft` | `#f5f0e8` | Secondary bands, table rows |
| Card surface | `--color-canvas-muted` | `#efe9de` | Feature cards, user messages, selected rows |
| Strong cream | `--color-canvas-strong` | `#e8e0d2` | Pressed and emphasized neutral surfaces |
| Ink | `--color-ink` | `#141413` | Headlines and primary text |
| Body | `--color-ink-strong` | `#252523` | Strong body copy |
| Secondary text | `--color-ink-secondary` | `#6c6a64` | Supporting copy and labels |
| Tertiary text | `--color-ink-tertiary` | `#8e8b82` | Hints and metadata |
| Primary action | `--color-action` | `#cc785c` | Primary buttons and high-signal links |
| Primary active | `--color-action-hover` | `#a9583e` | Hover and pressed action |
| Dark surface | `--color-surface-dark` | `#181715` | Sidebar and dark product panels |
| Dark raised | `--color-surface-dark-raised` | `#252320` | Selected navigation and nested dark surfaces |
| Dark soft | `--color-surface-dark-soft` | `#1f1e1b` | Dark secondary panels |
| On dark | `--color-on-dark` | `#faf9f5` | Primary text on dark surfaces |
| On dark muted | `--color-dark-muted` | `#a09d96` | Secondary text on dark surfaces |
| Hairline | `--color-border` | `#e6dfd8` | Default separators and controls |
| Strong hairline | `--color-border-strong` | `#cfc5b8` | Inputs and higher-contrast dividers |
| Success | `--color-success` | `#5d9b6a` | Available and completed states |
| Warning | `--color-warning` | `#b07b22` | Caution states |
| Error | `--color-danger` | `#c64545` | Errors and destructive actions |
| Accessible focus | `--color-focus` | `#a9583e` | Keyboard focus and input focus |

Rules: neutrals stay warm; the action color is scarce; dark surfaces provide pacing rather than a second theme. No raw color may appear in UI styles outside these tokens and their documented alpha mixes.

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

- **Variants:** coral primary, cream secondary, text, circular icon, dark-surface neutral.
- **Spacing:** 44px minimum height; radii 8px for standard and full radius for icon-only.
- **States:** default, hover, active, focus-visible, disabled, loading.
- **Motion:** 120ms transform/color; active translates by 1px or scales to .98.

### Input and composer

- **Structure:** warm canvas field, hairline, typed value, optional icon action.
- **States:** default, hover, focus with terracotta ring, disabled, invalid, loading.
- **Accessibility:** persistent label where practical; composer has an explicit accessible label.

### Navigation item

- **Structure:** title, optional metadata, current-state marker.
- **States:** default, hover, current, focus, disabled.
- **Surface:** dark sidebar; current uses raised dark surface and terracotta marker.

### Message

- **Variants:** assistant editorial text on canvas; user text on warm card surface; streaming; error.
- **Identity:** every assistant message carries the 32px Jyotisha logo avatar; user messages stay visually lighter and avatar-free.
- **Typography:** assistant body 16px with serif subheadings; user body 14px.
- **Suggestions:** keep follow-up actions compact, with 8px internal horizontal padding and a narrower 680px group width.
- **Motion:** new messages enter with a short opacity/translate transition only.

### Suggestion card

- **Structure:** topic label, question, directional icon. Categories are not numbered because they have no required order. At tablet widths, the cards stack into one column so Chinese questions keep natural phrase boundaries beside the persistent sidebar.
- **Surface:** warm card; three responsive editorial cards rather than a generic equal feature row.
- **States:** default, hover, active, focus, disabled, loading, fallback notice.

### Start greeting

- **Content:** invite the user to ask what matters now; do not repeat that birth data is ready or explain setup state.
- **Timing:** use the browser's local hour: morning 05:00–10:59, noon 11:00–13:59, afternoon 14:00–17:59, evening 18:00–22:59, and late night 23:00–04:59.
- **Variation:** each time band has three concise prompts; select one once per visit so re-renders do not change the sentence.

### Account sheet

- **Structure:** title, account summary, redeem section, profile form, actions.
- **Surface:** canvas sheet over warm scrim; sections separated by hairlines.
- **States:** closed, opening, open, validation error, success, saving.

### Admin panel and data table

- **Structure:** editorial header, cream form panels, dark data surface.
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

Strategy: mixed tonal shifts with warm hairlines. Most depth comes from canvas, cream card, dark surface, and terracotta alternation. Standard UI uses no drop shadow. Modal and raised-sheet depth use one restrained two-stage token: `--shadow-elevated: 0 1px 2px rgba(20, 20, 19, .08), 0 12px 28px -16px rgba(20, 20, 19, .22)`. Interactive rings use `0 0 0 1px` or the focus ring; no generic card shadows or atmospheric gradients.
