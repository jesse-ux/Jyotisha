# Private Consultation Entrypoints Design

## Goal

Make the “今日星语” and “生时校正” cards behave like concise product entrypoints without exposing internal consultation instructions in the composer, transcript, browser bundle, or persisted chat history.

## Approved interaction

- Clicking anywhere on the 今日星语 card places `深入看今日` in the composer.
- Clicking the 生时校正 card places `生时校正` before a result exists and `再次校正` after a candidate or confirmed time exists.
- Each card remains a semantic `article`; one stretched native button covers the card, and a quiet action label with an arrow sits at the lower-right edge.
- The cards contain no nested visible button, so mobile layouts do not create a large control in the middle of the content.
- Keyboard focus, disabled state, and the 44px interaction requirement apply to the whole-card button.

## Request contract

The browser may send one optional, closed entrypoint value:

```ts
type ConsultationEntrypoint =
  | "daily_starlanguage"
  | "birth_time_rectification";
```

The visible `question` remains the exact short sentence displayed to the user. The server validates the optional entrypoint and expands it into the internal model question. Arbitrary template names or client-authored prompt content are rejected by schema validation.

Normal typed questions omit `entrypoint` and retain their current behavior.

## Composer and transcript behavior

- Card selection stores the short visible question plus an internal entrypoint enum in React state.
- Any manual edit to the composer clears the entrypoint enum, so edited text is treated as an ordinary user question.
- Sending clears both fields.
- Undo/cancel restores both fields, preserving the same behavior when the user retries.
- Optimistic messages, persisted chat sessions, sharing, and future conversation history store only the visible short question.

## Server behavior

- A server-only resolver owns both internal prompt templates.
- `daily_starlanguage` expands with authoritative server time, the validated birth/chart input, the requested daily sections, and the existing non-deterministic boundary.
- `birth_time_rectification` expands with the validated birth/chart input, a request to continue or restart evidence-led rectification, and the existing rule that a candidate is not a proven birth minute.
- The expanded question is used both in the final Agent message and in `consultationInputSchema` passed to the calculation tool.
- User-visible history remains unchanged and never receives the expanded text.
- Prompt-extraction safety continues to inspect user-controlled visible content; the trusted server expansion is not treated as user input.

## Failure behavior

- Unknown entrypoint values return the existing 400 invalid-request response before billing.
- A valid entrypoint with an edited visible sentence is impossible through the product UI because editing clears the enum; the server still treats the enum as authoritative if a direct API client supplies both.
- Billing, cancellation settlement, streaming, model selection, and ordinary questions retain their current paths.

## Verification

- Unit tests prove each entrypoint selects a server expansion without pinning natural-language prompt prose.
- Route contract tests prove the enum is optional, invalid values fail, and the expanded question reaches both Agent and tool input.
- Client tests prove the browser source no longer contains the internal daily or rectification prompt builders, manual editing clears intent, and cancellation restores it.
- Browser QA verifies whole-card click, short composer text, keyboard focus, and desktop/390px mobile layout.
