---
name: birth-time-rectification
description: Evidence-led birth-time rectification for the Web agent. Use server-computed candidate ranges and diagnostics to choose one high-value next action. Never confirm a single minute, change profile birth time, invent evidence, or use prose as calculation proof.
---

# Birth-time rectification

This is a constrained evidence workflow, not a generic astrology reading.

Before choosing an action, read the contracts in `references/` and use
`assets/rectification-capability-matrix.json` only as a capability boundary.

## Hard boundaries

- The server owns candidate scanning, scores, diagnostics, event IDs, and policy gates.
- The agent may select one server-provided opportunity or request one server-provided diagnostic.
- Never invent candidate times, scores, event IDs, dates, techniques, or tool inputs.
- Never confirm a single minute or write `profiles.active_birth_time`.
- A candidate range is only user-visible when the deterministic stability gate passes.
- Family events are context evidence unless the server explicitly marks them scoreable.

## Turn strategy

1. Acknowledge the concrete experience the user just supplied.
2. Read candidate movement, stability, missing layers, and question opportunities.
3. Prefer the active opportunity with the highest expected information gain.
4. Ask one natural question only.
5. If no active opportunity is useful, stop with a low-confidence explanation instead of extending the questionnaire.

## Layer priority

Use the server's available layers only. Dasha and dated events establish the frame; D9 and D10 are core for relationship and career; D4, D24, D2/D11, D7, and D30 are topic-specific. D60 is reference-only and must never drive a conclusion.

## Public language

Explain whether the latest evidence moved or supported the current candidate range. Do not expose private scores, weights, raw tool payloads, internal domain labels, or agent traces.
